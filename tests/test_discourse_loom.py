from __future__ import annotations

import http.client
import json
import threading

from selene.db import connect, init_db
from selene.discourse_loom import discourse_loom_status, weave_supported_discourse
from selene.discourse_planner import build_supported_discourse_plan
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
    assert payload["unsupported_example_generation_allowed"] is False
    assert payload["filler_generation_allowed"] is False
    assert payload["certainty_change_allowed"] is False
    assert payload["source_change_allowed"] is False
    assert payload["memory_write_active"] is False
    assert payload["identity_change_allowed"] is False
    assert payload["governance_change_allowed"] is False
    assert payload["authority_change_allowed"] is False
    assert payload["coordinated_expression_contract_active"] is True
    assert payload["database_write_performed"] is False
    assert payload["hidden_chain_of_thought_exposed"] is False


def _developed_discourse():
    return build_supported_discourse_plan(
        {
            "content_seed": "The pilot is worth running.",
            "response_depth": "developed",
            "support_points": ["It creates evidence under controlled conditions."],
            "examples": ["A one-week trial can compare both approaches."],
            "answer_support": {
                "limitations": ["The result applies only to the tested conditions."],
                "what_would_change_the_answer": [
                    "A larger trial reverses the observed result."
                ],
            },
            "source_refs": ["test:pilot"],
        }
    )


def test_discourse_loom_realizes_supported_roles_without_filler_or_missing_content():
    discourse = _developed_discourse()
    loom = weave_supported_discourse(
        discourse,
        response_depth="developed",
        contextual_plan={
            "response_depth": "developed",
            "supported_content_unit_count": 5,
        },
    )

    assert loom["status"] == "discourse_loom_selected"
    assert loom["generated_candidate_count"] == 2
    assert loom["distinct_candidate_count"] == 2
    assert loom["selection_pass_count"] == 1
    assert loom["selected_loom_specification_id"] == "discourse:plan_order"
    assert len(loom["selected_paragraphs"]) == 3
    assert "For example: A one-week trial" in loom["selected_candidate_text"]
    assert "One limit: The result applies" in loom["selected_candidate_text"]
    assert "What would change this: A larger trial" in loom["selected_candidate_text"]
    assert loom["natural_stop_used"] is False
    assert loom["forced_closure_added"] is False
    for item in loom["candidates"]:
        if item["selectable"]:
            assert item["invariant_check"]["passed"] is True
            assert set(loom["required_content_unit_ids"]).issubset(
                item["included_content_unit_ids"]
            )
    _assert_locked(loom)


def test_structured_candidate_becomes_thesis_without_repeating_the_old_seed():
    discourse = build_supported_discourse_plan(
        {
            "content_seed": "The original supported answer has two parts. Both parts remain provisional.",
            "response_depth": "developed",
            "support_points": ["A later observation could revise the comparison."],
            "source_refs": ["test:structured"],
        }
    )
    formation = {
        "candidate_text": "The two-part answer remains provisional.",
        "formation_mode": "structured",
        "meaning_preserved": True,
    }

    loom = weave_supported_discourse(
        discourse,
        selected_formation=formation,
        response_depth="developed",
        contextual_plan={
            "response_depth": "developed",
            "supported_content_unit_count": 3,
        },
    )

    assert loom["structured_formation_used_as_thesis"] is True
    assert loom["collapsed_seed_content_unit_ids"] == ["content_1", "content_2"]
    assert loom["selected_candidate_text"].startswith(
        "The two-part answer remains provisional."
    )
    assert "The original supported answer" not in loom["selected_candidate_text"]
    assert loom["selected_candidate_text"].count("remains provisional") == 1
    assert "A later observation could revise" in loom["selected_candidate_text"]


def test_structured_formation_retains_coverage_ancestry_for_a_subsumed_obligated_example():
    discourse = build_supported_discourse_plan(
        {
            "content_seed": "The pilot is worth running.",
            "examples": ["A one-week trial can compare both approaches."],
            "response_obligations": [
                {
                    "id": "example",
                    "kind": "direct_request",
                    "source_text": "Give the example.",
                    "coverage_terms": ["give", "example"],
                    "required": True,
                }
            ],
        }
    )
    formation = {
        "candidate_text": "The pilot is worth running. A one-week trial can compare both approaches.",
        "formation_mode": "structured",
        "meaning_preserved": True,
    }

    loom = weave_supported_discourse(
        discourse,
        selected_formation=formation,
        response_depth="developed",
    )

    assert loom["collapsed_seed_content_unit_ids"] == ["content_1", "content_2"]
    assert loom["obligation_bound_content_unit_ids"] == ["structured_formation"]
    assert loom["selectable_candidate_count"] >= 1
    assert all(
        item["invariant_check"]["obligation_bound_content_unit_ids"] == ["structured_formation"]
        for item in loom["candidates"]
    )


def test_structured_candidate_can_supply_the_thesis_when_no_text_seed_exists():
    discourse = build_supported_discourse_plan(
        {
            "content_seed": "",
            "response_depth": "standard",
            "support_points": ["The comparison remains bounded by the observed cases."],
        }
    )
    formation = {
        "candidate_text": "The two explanations fit the current observation.",
        "formation_mode": "structured",
        "meaning_preserved": True,
    }

    loom = weave_supported_discourse(
        discourse,
        selected_formation=formation,
        response_depth="standard",
    )

    assert loom["structured_formation_used_as_thesis"] is True
    assert loom["collapsed_seed_content_unit_ids"] == []
    assert loom["selected_candidate_text"].startswith(
        "The two explanations fit the current observation."
    )
    assert "bounded by the observed cases" in loom["selected_candidate_text"]


def test_obligation_order_keeps_the_thesis_first_and_carries_bound_units():
    discourse = {
        "status": "supported_discourse_plan_ready",
        "content_units": [
            {"id": "thesis", "text": "Use the smaller pilot first.", "role": "thesis", "source": "seed", "supported": True},
            {"id": "reason", "text": "It creates reversible evidence.", "role": "support", "source": "support", "supported": True},
            {"id": "limit", "text": "The result is local to this trial.", "role": "limitation", "source": "support", "supported": True},
        ],
        "paragraph_plan": [{"index": 1, "role": "answer", "content_unit_ids": ["thesis", "reason", "limit"]}],
        "obligation_bindings": [
            {"obligation_id": "why", "required": True, "grounded": True, "content_unit_ids": ["reason"]},
            {"obligation_id": "scope", "required": True, "grounded": True, "content_unit_ids": ["limit"]},
        ],
        "closure_plan": {"mode": "bounded_limit", "content_unit_id": "limit", "text": "The result is local to this trial."},
        "uncovered_obligation_ids": [],
        "source_refs": ["test:obligations"],
    }

    loom = weave_supported_discourse(discourse, response_depth="standard")

    assert loom["obligation_bound_content_unit_ids"] == ["reason", "limit"]
    for item in loom["candidates"]:
        if item["selectable"]:
            assert item["included_content_unit_ids"][0] == "thesis"
            assert {"reason", "limit"}.issubset(item["included_content_unit_ids"])


def test_attributed_thread_return_uses_traversal_order_without_inventing_callback_content():
    discourse = {
        "status": "supported_discourse_plan_ready",
        "content_units": [
            {"id": "thesis", "text": "The answer has two connected parts.", "role": "thesis", "source": "seed", "supported": True},
            {"id": "branch", "text": "The side condition changes the timing.", "role": "support", "source": "seed", "supported": True},
            {"id": "return", "text": "The original recommendation still holds.", "role": "conclusion", "source": "seed", "supported": True},
        ],
        "paragraph_plan": [{"index": 1, "role": "answer", "content_unit_ids": ["thesis", "branch", "return"]}],
        "obligation_bindings": [],
        "thread_obligation_bindings": [
            {"thread_id": "branch", "thread_traversal_index": 1, "grounded": True, "content_unit_ids": ["branch"]},
            {"thread_id": "original", "thread_traversal_index": 2, "grounded": True, "content_unit_ids": ["return"]},
        ],
        "closure_plan": {"mode": "supported_next_step", "content_unit_id": "return", "text": "The original recommendation still holds."},
        "uncovered_obligation_ids": [],
        "source_refs": ["test:thread"],
    }

    loom = weave_supported_discourse(
        discourse,
        response_depth="developed",
        contextual_plan={"response_depth": "developed", "supported_content_unit_count": 3},
    )
    threaded = next(
        item
        for item in loom["candidates"]
        if item["loom_specification_id"] == "discourse:thread_traversal"
    )

    assert threaded["selectable"] is True
    assert threaded["included_content_unit_ids"] == ["thesis", "branch", "return"]
    assert threaded["candidate_text"].count("Returning to that thread:") == 2
    assert threaded["candidate_text"].index("side condition") < threaded["candidate_text"].index("original recommendation")
    assert "Returning to that thread" not in " ".join(
        item["text"] for item in discourse["content_units"]
    )


def test_brief_discourse_may_omit_optional_support_but_not_required_limits_or_obligations():
    discourse = {
        "status": "supported_discourse_plan_ready",
        "content_units": [
            {"id": "thesis", "text": "Choose the reversible option.", "role": "thesis", "source": "seed", "supported": True},
            {"id": "optional", "text": "It is also easier to observe.", "role": "support", "source": "support", "supported": True},
            {"id": "required_reason", "text": "It can be undone if the result is poor.", "role": "support", "source": "support", "supported": True},
            {"id": "limit", "text": "The choice still depends on local conditions.", "role": "limitation", "source": "support", "supported": True},
        ],
        "paragraph_plan": [{"index": 1, "role": "answer", "content_unit_ids": ["thesis", "required_reason"]}],
        "obligation_bindings": [
            {"obligation_id": "why", "required": True, "grounded": True, "content_unit_ids": ["required_reason"]}
        ],
        "closure_plan": {"mode": "bounded_limit", "content_unit_id": "limit", "text": "The choice still depends on local conditions."},
        "uncovered_obligation_ids": [],
        "source_refs": [],
    }

    loom = weave_supported_discourse(
        discourse,
        response_depth="brief",
        contextual_plan={"response_depth": "brief"},
    )

    brief = next(
        item
        for item in loom["candidates"]
        if item["loom_specification_id"] == "discourse:brief_required"
    )
    assert brief["selectable"] is True
    assert brief["included_content_unit_ids"] == ["thesis", "required_reason", "limit"]
    assert "optional" not in brief["included_content_unit_ids"]
    assert loom["selected_loom_specification_id"] == "discourse:brief_required"


def test_no_supported_closure_means_stop_without_a_forced_question_or_ending():
    discourse = build_supported_discourse_plan(
        {
            "content_seed": "The answer is clear enough to use.",
            "support_points": ["The available observation supports it."],
            "response_depth": "standard",
        }
    )
    loom = weave_supported_discourse(discourse, response_depth="standard")

    assert loom["closure_content_unit_id"] == ""
    assert loom["natural_stop_used"] is True
    assert loom["forced_closure_added"] is False
    assert not loom["selected_candidate_text"].endswith("?")
    assert "anything else" not in loom["selected_candidate_text"].lower()


def test_exact_and_specialized_social_structures_remain_as_supplied_only():
    discourse = _developed_discourse()
    for contextual_plan, expected_reason in (
        ({"exact_domain_structure_locked": True}, "exact_domain_structure_locked"),
        ({"social_act_structure_owned_elsewhere": True}, "specialized_social_structure_owned_elsewhere"),
    ):
        loom = weave_supported_discourse(
            discourse,
            response_depth="developed",
            contextual_plan=contextual_plan,
        )

        assert loom["status"] == "discourse_loom_as_supplied_only"
        assert loom["generated_candidate_count"] == 1
        assert loom["selection_active"] is False
        assert loom["hold_reason"] == expected_reason
        assert "For example:" not in loom["selected_candidate_text"]
        assert "One limit:" not in loom["selected_candidate_text"]


def test_nlo_uses_discourse_loom_for_supported_long_form_without_writing(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    result = realize_native_language(
        conn,
        {
            "prompt": "Go deeper: explain the pilot, give the example, and state the limit.",
            "content_seed": "The pilot is worth running.",
            "response_depth": "developed",
            "semantic_propositions": [
                {
                    "id": "pilot",
                    "subject": "the pilot",
                    "predicate": "be",
                    "object": "worth running",
                    "example": "a one-week trial can compare both approaches",
                }
            ],
            "intelligence_support": {
                "used": True,
                "confidence": "clear_enough_to_continue",
                "support_points": ["It creates evidence under controlled conditions."],
            },
            "answer_engine_support": {
                "used": True,
                "selected_domain": "comparison_planning",
                "answer_packet": {
                    "limitations": ["The result applies only to the tested conditions."],
                    "unanswered_obligations": [],
                },
            },
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
        },
        record_run=False,
    )

    loom = result["discourse_loom"]
    assert result["version"] == "v32_human_conversational_realization"
    assert loom["selection_performed"] is True
    assert loom["structured_formation_used_as_thesis"] is True
    assert "for example" in result["candidate_text"].lower()
    assert result["candidate_text"].lower().count("one-week trial") == 1
    assert "One limit:" in result["candidate_text"]
    assert loom["visible_speech_applied"] is True
    assert result["revision"]["discourse_loom_checked"] is True
    assert result["revision"]["selected_discourse_invariants_passed"] is True
    assert result["revision"]["forced_closure_added"] is False
    assert result["revision"]["unsupported_content_generated"] is False
    assert result["memory_write_active"] is False
    assert conn.total_changes == changes_before


def test_discourse_loom_status_preview_and_http_routes_are_read_only(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    payload = {
        "content_seed": "The pilot is worth running.",
        "response_depth": "developed",
        "support_points": ["It creates evidence."],
        "answer_support": {"limitations": ["The result remains local."]},
        "source_refs": ["test:route"],
    }
    status = route_request(conn, "native_language.discourse_loom.status")["result"]
    preview = route_request(conn, "native_language.discourse_loom.preview", payload)["result"]

    assert status["status"] == "discourse_loom_ready"
    assert preview["selection_performed"] is True
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
        client.request("GET", "/api/native-language/discourse-loom/status")
        status_response = client.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        client.request(
            "POST",
            "/api/native-language/discourse-loom/preview",
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
    assert status_payload["status"] == "discourse_loom_ready"
    assert preview_response.status == 200
    assert preview_payload["selection_performed"] is True
