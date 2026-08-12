from __future__ import annotations

import http.client
import json
import threading

from selene.context_expression_selector import (
    build_expression_selection_context,
    context_expression_selector_status,
    select_candidate_garden,
    select_discourse_loom,
)
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.sidecar import SeleneHandler, SeleneServer


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _safe_formation(candidate_id, text, score=0.0, *, selectable=True, passed=True):
    return {
        "candidate_id": candidate_id,
        "construction_id": f"construction:{candidate_id}",
        "construction_dimensions": [],
        "candidate_text": text,
        "formation": {
            "candidate_text": text,
            "formation_mode": "structured",
            "meaning_preserved": passed,
            "construction_specification": {},
        },
        "invariant_check": {"passed": passed},
        "score": score,
        "selectable": selectable,
    }


def _safe_discourse(candidate_id, specification_id, text, paragraphs, score=0.0):
    return {
        "discourse_candidate_id": candidate_id,
        "loom_specification_id": specification_id,
        "candidate_text": text,
        "paragraphs": paragraphs,
        "included_content_unit_ids": ["thesis"],
        "invariant_check": {"passed": True},
        "score": score,
        "selectable": True,
    }


def _assert_locked(payload):
    assert payload["meaning_change_allowed"] is False
    assert payload["fact_generation_allowed"] is False
    assert payload["certainty_change_allowed"] is False
    assert payload["source_change_allowed"] is False
    assert payload["memory_write_active"] is False
    assert payload["identity_change_allowed"] is False
    assert payload["personality_change_allowed"] is False
    assert payload["governance_change_allowed"] is False
    assert payload["authority_change_allowed"] is False


def test_context_packet_is_visible_bounded_and_keeps_affect_optional():
    context = build_expression_selection_context(
        {
            "contextual_plan": {
                "response_depth": "developed",
                "register": "technical_explanation",
                "sentence_rhythm": "natural_varied",
                "decisions": {
                    "callback": "carry_attributed_visible_callback",
                    "pivot": "resume_named_thread",
                    "stopping": "answer_and_stop_when_complete",
                },
            },
            "affect_expression_guidance": {
                "expression_posture": "warm_focused",
                "guidance_is_optional": True,
                "recommended_voice_category": "warmth_care",
            },
            "recent_texts": ["Earlier supported wording."],
        }
    )

    assert context["response_depth"] == "developed"
    assert context["callback_decision"] == "carry_attributed_visible_callback"
    assert context["affect_guidance_is_optional"] is True
    assert context["affect_may_rank_safe_expression_but_not_prescribe_emotion"] is True
    assert context["recent_assistant_texts"] == ["Earlier supported wording."]
    _assert_locked(context)


def test_invalid_formation_candidate_is_held_before_context_scoring():
    garden = {
        "candidates": [
            _safe_formation("candidate:1", "A clear supported answer.", 5),
            _safe_formation(
                "candidate:2",
                "An attractive but invalid answer.",
                10000,
                selectable=False,
                passed=False,
            ),
        ]
    }
    selected = select_candidate_garden(
        garden,
        build_expression_selection_context({"response_depth": "brief"}),
    )
    report = selected["context_expression_selection"]

    assert selected["selected_candidate_id"] == "candidate:1"
    assert report["eligible_candidate_count"] == 1
    assert report["held_before_scoring_count"] == 1
    assert report["invalid_candidates_scored"] is False
    assert report["invalid_candidate_rescue_used"] is False
    assert [item["candidate_id"] for item in report["scored_candidates"]] == ["candidate:1"]


def test_exact_domain_ownership_allows_only_as_supplied_formation():
    garden = {
        "default_construction_id": "construction:as_supplied",
        "candidates": [
            {
                **_safe_formation("candidate:1", "The exact answer as supplied.", 1),
                "construction_id": "construction:as_supplied",
            },
            {
                **_safe_formation("candidate:2", "The exact answer rearranged.", 1000),
                "construction_id": "construction:alternate",
            },
        ],
    }
    context = build_expression_selection_context(
        {"contextual_plan": {"exact_domain_structure_locked": True}}
    )
    selected = select_candidate_garden(garden, context)
    report = selected["context_expression_selection"]

    assert selected["selected_construction_id"] == "construction:as_supplied"
    assert report["eligible_candidate_count"] == 1
    assert report["ownership_hold_reason"] == "exact_domain_structure_locked"
    assert [item["candidate_id"] for item in report["scored_candidates"]] == ["candidate:1"]


def test_discourse_selection_uses_grounded_callback_fit_without_adding_words():
    plain = _safe_discourse(
        "discourse_candidate:1",
        "discourse:integrated_complete",
        "The first supported point. The second supported point.",
        ["The first supported point. The second supported point."],
    )
    threaded = _safe_discourse(
        "discourse_candidate:2",
        "discourse:thread_traversal",
        "The first supported point.\n\nReturning to that thread: The second supported point.",
        ["The first supported point.", "Returning to that thread: The second supported point."],
    )
    context = build_expression_selection_context(
        {
            "contextual_plan": {
                "response_depth": "developed",
                "decisions": {
                    "callback": "carry_attributed_visible_callback",
                    "pivot": "resume_named_thread",
                },
            }
        }
    )
    selected = select_discourse_loom({"candidates": [plain, threaded]}, context)

    assert selected["selected_discourse_candidate_id"] == "discourse_candidate:2"
    assert selected["selected_candidate_text"] == threaded["candidate_text"]
    assert selected["context_expression_selection"]["selection_changed_meaning"] is False


def test_nlo_runs_both_context_selection_passes_without_writing(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    result = realize_native_language(
        conn,
        {
            "prompt": "Explain the pilot, give the example, and state its limit.",
            "content_seed": "The pilot is worth running.",
            "response_depth": "developed",
            "support_points": ["It creates evidence."],
            "examples": ["A one-week trial can compare both approaches."],
            "answer_support": {"limitations": ["The result remains local."]},
            "source_refs": ["test:phase5"],
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
        },
        record_run=False,
    )

    selector = result["context_expression_selection"]
    assert result["version"] == "v32_human_conversational_realization"
    assert selector["formation_selection"]["selection_performed"] is True
    assert selector["discourse_selection"]["selection_performed"] is True
    assert selector["invalid_candidate_rescue_used"] is False
    assert result["revision"]["context_expression_selection_checked"] is True
    assert result["revision"]["affect_changed_supported_meaning"] is False
    assert result["voice_handoff"]["context_expression_selection"] == selector
    assert conn.total_changes == changes_before


def test_selector_status_preview_and_http_routes_are_read_only(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    payload = {
        "content_seed": "The pilot is worth running.",
        "response_depth": "developed",
        "support_points": ["It creates evidence."],
        "answer_support": {"limitations": ["The result remains local."]},
        "source_refs": ["test:route"],
    }
    status = route_request(conn, "native_language.expression_selection.status")["result"]
    preview = route_request(conn, "native_language.expression_selection.preview", payload)["result"]

    assert status["status"] == "context_expression_selector_ready"
    assert preview["status"] == "context_expression_selection_preview_ready"
    assert preview["formation_selection"]["selection_performed"] is True
    assert preview["discourse_selection"]["selection_performed"] is True
    assert conn.total_changes == changes_before
    _assert_locked(status)
    _assert_locked(preview)

    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request("GET", "/api/native-language/expression-selection/status")
        status_response = client.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request(
            "POST",
            "/api/native-language/expression-selection/preview",
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
    assert status_payload["status"] == "context_expression_selector_ready"
    assert preview_response.status == 200
    assert preview_payload["formation_selection"]["selection_performed"] is True


def test_status_declares_selection_not_generation():
    status = context_expression_selector_status()
    assert status["language_generation_allowed"] is False
    assert status["invalid_candidate_rescue_allowed"] is False
    assert status["affect_guidance_is_optional"] is True
    _assert_locked(status)
