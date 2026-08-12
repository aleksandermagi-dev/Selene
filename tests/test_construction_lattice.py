from __future__ import annotations

import http.client
import json
import threading

from selene.construction_lattice import (
    build_construction_lattice,
    construction_lattice_status,
)
from selene.db import connect, init_db
from selene.language_formation import build_semantic_frame, realize_semantic_frame
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.sidecar import SeleneHandler, SeleneServer


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _construction(lattice, construction_id):
    return next(
        item
        for item in lattice["constructions"]
        if item["construction_id"] == construction_id
    )


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


def test_construction_lattice_describes_executable_shapes_without_generating_candidates():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "id": "ask_when_unclear",
                        "subject": "Selene",
                        "predicate": "ask",
                        "object": "for context",
                        "condition": "the source is unclear",
                        "reason": "the missing detail changes the answer",
                        "meaning_keys": ["ask when material context is missing"],
                    },
                    {
                        "id": "keep_uncertainty",
                        "subject": "she",
                        "predicate": "keep",
                        "object": "the uncertainty visible",
                        "relation": "support",
                    },
                ]
            }
        }
    )

    lattice = build_construction_lattice(frame)

    assert lattice["status"] == "construction_lattice_ready"
    assert lattice["construction_count"] >= 9
    assert {
        "condition_position",
        "reason_position",
        "clause_linking",
        "development_depth",
    }.issubset(lattice["available_dimensions"])
    assert lattice["complete_response_candidates_generated"] is False
    assert lattice["candidate_selection_active"] is False
    assert lattice["required_semantic_unit_ids"] == [
        "ask_when_unclear",
        "keep_uncertainty",
    ]
    _assert_locked(lattice)


def test_condition_and_reason_positions_execute_while_preserving_supported_units():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "id": "ask",
                        "subject": "Selene",
                        "predicate": "ask",
                        "object": "for context",
                        "condition": "the source is unclear",
                        "reason": "the detail changes the answer",
                        "meaning_keys": ["context changes answer"],
                    }
                ]
            }
        }
    )
    lattice = build_construction_lattice(frame)

    condition_front = realize_semantic_frame(
        frame,
        construction_specification=_construction(
            lattice, "construction:condition_front:ask"
        ),
    )
    condition_end = realize_semantic_frame(
        frame,
        construction_specification=_construction(
            lattice, "construction:condition_end:ask"
        ),
    )
    reason_front = realize_semantic_frame(
        frame,
        construction_specification=_construction(
            lattice, "construction:reason_front:ask"
        ),
    )

    assert condition_front["candidate_text"].startswith("When the source is unclear")
    assert "when the source is unclear" in condition_end["candidate_text"].lower()
    assert not condition_end["candidate_text"].startswith("When the source is unclear")
    assert reason_front["candidate_text"].startswith("Because the detail changes the answer")
    for result in (condition_front, condition_end, reason_front):
        assert result["meaning_preserved"] is True
        assert result["required_semantic_unit_ids"] == ["ask"]
        assert result["meaning_signature"] == ["context changes answer"]


def test_joined_split_compact_and_developed_specs_keep_every_unit():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {"id": "one", "subject": "Selene", "predicate": "inspect", "object": "the evidence"},
                    {"id": "two", "subject": "she", "predicate": "compare", "object": "the explanations", "relation": "sequence"},
                    {"id": "three", "subject": "she", "predicate": "keep", "object": "the question open", "relation": "conclusion"},
                ]
            }
        }
    )
    lattice = build_construction_lattice(frame)

    joined = realize_semantic_frame(
        frame,
        construction_specification=_construction(lattice, "construction:clauses_joined"),
    )
    split = realize_semantic_frame(
        frame,
        construction_specification=_construction(lattice, "construction:clauses_split"),
    )
    developed = realize_semantic_frame(
        frame,
        construction_specification=_construction(lattice, "construction:developed"),
    )

    assert ";" in joined["candidate_text"]
    assert ";" not in split["candidate_text"]
    assert "\n\n" in developed["candidate_text"]
    for result in (joined, split, developed):
        assert result["realized_semantic_unit_ids"] == ["one", "two", "three"]
        assert result["required_semantic_units_preserved"] is True


def test_dialogue_act_requires_explicit_permission_and_voice_requires_role_mapping():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "id": "review",
                        "subject": "Aleks",
                        "predicate": "review",
                        "object": "the lesson",
                        "allowed_moods": ["declarative", "interrogative"],
                        "voice_alternatives": {
                            "passive": {
                                "subject": "the lesson",
                                "predicate": "review",
                                "object": "",
                                "agent": "Aleks",
                                "meaning_equivalent": True,
                            }
                        },
                    }
                ]
            }
        }
    )
    lattice = build_construction_lattice(frame)

    question = realize_semantic_frame(
        frame,
        construction_specification=_construction(
            lattice, "construction:interrogative:review"
        ),
    )
    passive = realize_semantic_frame(
        frame,
        construction_specification=_construction(
            lattice, "construction:passive_focus:review"
        ),
    )

    assert question["candidate_text"] == "Does Aleks review the lesson?"
    assert passive["candidate_text"] == "The lesson is reviewed by Aleks."

    unlicensed = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {"id": "fixed_act", "subject": "Selene", "predicate": "answer", "object": "the question"}
                ]
            }
        }
    )
    held = build_construction_lattice(unlicensed)
    assert all("interrogative" not in item["construction_id"] for item in held["constructions"])
    assert all("passive_focus" not in item["construction_id"] for item in held["constructions"])


def test_text_grounded_and_exactness_locked_frames_remain_as_supplied_only():
    text_frame = build_semantic_frame(
        {"content_seed": "Keep this exact supported wording."}
    )
    exact_frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "id": "exact",
                        "subject": "the route",
                        "predicate": "remain",
                        "object": "native_language.realize",
                        "exactness_lock": True,
                    }
                ]
            }
        }
    )

    text_lattice = build_construction_lattice(text_frame)
    exact_lattice = build_construction_lattice(exact_frame)

    assert text_lattice["status"] == "construction_lattice_as_supplied_only"
    assert exact_lattice["status"] == "construction_lattice_as_supplied_only"
    assert text_lattice["construction_count"] == 1
    assert exact_lattice["construction_count"] == 1
    assert text_lattice["text_grounded_unit_ids"] == ["semantic_1"]
    assert exact_lattice["exactness_locked_unit_ids"] == ["exact"]


def test_nlo_exposes_lattice_but_keeps_as_supplied_as_the_active_construction(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    result = realize_native_language(
        conn,
        {
            "prompt": "What happens when the source is unclear?",
            "semantic_propositions": [
                {
                    "id": "ask",
                    "subject": "Selene",
                    "predicate": "ask",
                    "object": "for context",
                    "condition": "the source is unclear",
                }
            ],
            "intent_decision": {
                "intent": "reasoning",
                "answer_shape": "best_current_answer",
            },
        },
        record_run=False,
    )

    assert result["version"] == "v32_human_conversational_realization"
    assert result["construction_lattice"]["construction_count"] == 3
    assert result["construction_lattice"]["candidate_selection_active"] is False
    assert result["formation"]["construction_id"] == "construction:as_supplied"
    assert result["revision"]["unsupported_content_generated"] is False
    assert result["memory_write_active"] is False
    assert conn.total_changes == changes_before


def test_construction_status_preview_and_http_routes_are_read_only(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    status = route_request(conn, "native_language.construction.status")["result"]
    preview = route_request(
        conn,
        "native_language.construction.preview",
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "id": "ask",
                        "subject": "Selene",
                        "predicate": "ask",
                        "object": "for context",
                        "condition": "the source is unclear",
                    }
                ]
            }
        },
    )["result"]

    assert status["status"] == "construction_lattice_ready"
    assert preview["construction_count"] == 3
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
        client.request("GET", "/api/native-language/construction/status")
        status_response = client.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        client.request(
            "POST",
            "/api/native-language/construction/preview",
            body=json.dumps(
                {
                    "semantic_frame": {
                        "propositions": [
                            {
                                "id": "ask",
                                "subject": "Selene",
                                "predicate": "ask",
                                "object": "for context",
                                "condition": "the source is unclear",
                            }
                        ]
                    }
                }
            ),
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
    assert status_payload["status"] == "construction_lattice_ready"
    assert preview_response.status == 200
    assert preview_payload["construction_count"] == 3
