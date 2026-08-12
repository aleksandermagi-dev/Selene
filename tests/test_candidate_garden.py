from __future__ import annotations

import http.client
import json
import threading

from selene.candidate_garden import candidate_garden_status, cultivate_candidate_garden
from selene.construction_lattice import build_construction_lattice
from selene.db import connect, init_db
from selene.language_formation import build_semantic_frame, realize_semantic_frame
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.sidecar import SeleneHandler, SeleneServer


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(payload):
    assert payload["meaning_change_allowed"] is False
    assert payload["fact_generation_allowed"] is False
    assert payload["certainty_change_allowed"] is False
    assert payload["source_change_allowed"] is False
    assert payload["memory_write_active"] is False
    assert payload["identity_change_allowed"] is False
    assert payload["governance_change_allowed"] is False
    assert payload["authority_change_allowed"] is False
    assert payload["coordinated_expression_contract_active"] is True
    assert payload["database_write_performed"] is False
    assert payload["hidden_chain_of_thought_exposed"] is False


def _structured_frame():
    return build_semantic_frame(
        {
            "semantic_frame": {
                "response_depth": "standard",
                "source_refs": ["test:supported-meaning"],
                "propositions": [
                    {
                        "id": "inspect",
                        "subject": "Selene",
                        "predicate": "inspect",
                        "object": "the evidence",
                        "meaning_keys": ["inspect available evidence"],
                    },
                    {
                        "id": "compare",
                        "subject": "she",
                        "predicate": "compare",
                        "object": "the explanations",
                        "condition": "more than one explanation fits",
                        "relation": "sequence",
                        "meaning_keys": ["compare fitting explanations"],
                    },
                ],
            }
        }
    )


def test_candidate_garden_generates_complete_bounded_candidates_and_checks_invariants():
    frame = _structured_frame()
    lattice = build_construction_lattice(frame)
    garden = cultivate_candidate_garden(
        frame,
        lattice,
        variation_key="candidate-invariants",
        contextual_plan={
            "response_depth": "standard",
            "task_kind": "explanation",
            "sentence_distribution": {"target_words_per_sentence": [5, 24]},
            "decisions": {"opening": "thesis_first"},
        },
        supported_discourse={
            "all_obligations_grounded": True,
            "uncovered_obligation_ids": [],
        },
    )

    assert garden["status"] == "candidate_garden_selected"
    assert 2 <= garden["generated_candidate_count"] <= 8
    assert garden["distinct_candidate_count"] >= 2
    assert garden["selectable_candidate_count"] >= 2
    assert garden["selection_pass_count"] == 1
    assert garden["recursive_generation_used"] is False
    assert garden["provider_generation_used"] is False
    assert garden["required_semantic_unit_ids"] == ["inspect", "compare"]
    assert garden["meaning_signature"] == [
        "inspect available evidence",
        "compare fitting explanations",
    ]
    for item in garden["candidates"]:
        if item["selectable"]:
            assert item["invariant_check"]["passed"] is True
            assert item["formation"]["required_semantic_units_preserved"] is True
            assert item["formation"]["source_refs"] == ["test:supported-meaning"]
    _assert_locked(garden)


def test_candidate_garden_uses_recent_distance_to_choose_one_safe_alternative():
    frame = _structured_frame()
    lattice = build_construction_lattice(frame)
    default_spec = next(
        item
        for item in lattice["constructions"]
        if item["construction_id"] == "construction:as_supplied"
    )
    default = realize_semantic_frame(
        frame,
        variation_key="recent-distance",
        construction_specification=default_spec,
    )["candidate_text"]

    garden = cultivate_candidate_garden(
        frame,
        lattice,
        variation_key="recent-distance",
        recent_texts=[default],
        contextual_plan={
            "response_depth": "standard",
            "task_kind": "explanation",
            "sentence_distribution": {"target_words_per_sentence": [5, 24]},
            "decisions": {"opening": "thesis_first"},
        },
    )

    assert garden["selection_active"] is True
    assert garden["selected_candidate_text"] != default
    default_candidate = next(
        item
        for item in garden["candidates"]
        if item["construction_id"] == "construction:as_supplied"
    )
    assert default_candidate["score_breakdown"]["recent_surface_distance"] == -35.0
    assert garden["selected_formation"]["meaning_preserved"] is True


def test_candidate_garden_holds_duplicate_surfaces_and_semantically_invalid_specs():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "id": "answer",
                        "subject": "Selene",
                        "predicate": "answer",
                        "object": "the supported question",
                    }
                ]
            }
        }
    )
    lattice = build_construction_lattice(frame)
    bad = {
        **lattice["constructions"][0],
        "construction_id": "construction:invalid_evidence_change",
        "evidence_and_certainty_change_allowed": True,
    }
    duplicate = {
        **lattice["constructions"][0],
        "construction_id": "construction:duplicate_surface",
    }
    lattice = {
        **lattice,
        "constructions": [lattice["constructions"][0], duplicate, bad],
        "construction_count": 3,
    }

    garden = cultivate_candidate_garden(frame, lattice)
    by_id = {item["construction_id"]: item for item in garden["candidates"]}

    assert by_id["construction:duplicate_surface"]["selectable"] is False
    assert by_id["construction:duplicate_surface"]["held_reason"] == "duplicate_surface_realization"
    assert by_id["construction:invalid_evidence_change"]["selectable"] is False
    assert by_id["construction:invalid_evidence_change"]["held_reason"] == "semantic_invariant_failed"
    assert by_id["construction:invalid_evidence_change"]["invariant_check"]["passed"] is False


def test_text_grounded_and_exactness_locked_language_remain_one_candidate_unchanged():
    for frame in (
        build_semantic_frame({"content_seed": "Keep this supported wording exactly."}),
        build_semantic_frame(
            {
                "semantic_frame": {
                    "propositions": [
                        {
                            "id": "route",
                            "subject": "the route",
                            "predicate": "remain",
                            "object": "native_language.realize",
                            "exactness_lock": True,
                        }
                    ]
                }
            }
        ),
    ):
        lattice = build_construction_lattice(frame)
        garden = cultivate_candidate_garden(frame, lattice)

        assert garden["status"] == "candidate_garden_as_supplied_only"
        assert garden["generated_candidate_count"] == 1
        assert garden["distinct_candidate_count"] == 1
        assert garden["selection_active"] is False
        assert garden["selected_construction_id"] == "construction:as_supplied"


def test_candidate_limit_is_hard_bounded_while_preserving_dimension_coverage():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "id": f"unit_{index}",
                        "subject": "Selene",
                        "predicate": "inspect",
                        "object": f"supported item {index}",
                        "condition": f"condition {index} applies",
                        "reason": f"reason {index} matters",
                    }
                    for index in range(1, 7)
                ]
            }
        }
    )
    lattice = build_construction_lattice(frame)
    garden = cultivate_candidate_garden(frame, lattice, max_candidates=4)

    assert lattice["construction_count"] > 12
    assert garden["candidate_limit"] == 4
    assert garden["generated_candidate_count"] == 4
    assert garden["selection_pass_count"] == 1


def test_nlo_uses_selected_candidate_once_without_writing_or_changing_authority(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    result = realize_native_language(
        conn,
        {
            "prompt": "How should we compare the explanations?",
            "semantic_propositions": _structured_frame()["propositions"],
            "source_refs": ["test:supported-meaning"],
            "intent_decision": {
                "intent": "reasoning",
                "answer_shape": "best_current_answer",
            },
            "conversation_context": {"turn_count": 2},
        },
        record_run=False,
    )

    garden = result["candidate_garden"]
    assert result["version"] == "v32_human_conversational_realization"
    assert garden["generated_candidate_count"] >= 2
    assert garden["selection_pass_count"] == 1
    assert result["formation"]["construction_id"] == garden["selected_construction_id"]
    assert result["formation"]["required_semantic_units_preserved"] is True
    assert result["revision"]["unsupported_content_generated"] is False
    assert result["memory_write_active"] is False
    assert result["autonomous_action_allowed"] is False
    assert conn.total_changes == changes_before


def test_candidate_status_preview_and_http_routes_are_read_only(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    payload = {
        "semantic_frame": {
            "source_refs": ["test:route"],
            "propositions": [
                {
                    "id": "ask",
                    "subject": "Selene",
                    "predicate": "ask",
                    "object": "for context",
                    "condition": "the source is unclear",
                }
            ],
        }
    }
    status = route_request(conn, "native_language.candidates.status")["result"]
    preview = route_request(conn, "native_language.candidates.preview", payload)["result"]

    assert status["status"] == "candidate_garden_ready"
    assert preview["generated_candidate_count"] == 3
    assert conn.total_changes == changes_before
    _assert_locked(status)
    _assert_locked(preview)

    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        client.request("GET", "/api/native-language/candidates/status")
        status_response = client.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        client.request(
            "POST",
            "/api/native-language/candidates/preview",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        preview_response = client.getresponse()
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        client.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert status_response.status == 200
    assert status_payload["status"] == "candidate_garden_ready"
    assert preview_response.status == 200
    assert preview_payload["generated_candidate_count"] == 3
