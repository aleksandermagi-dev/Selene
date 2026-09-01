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


def test_multiple_collapsed_seed_units_render_one_structured_formation_only():
    discourse = build_supported_discourse_plan(
        {
            "content_seed": "The first condition holds. The second condition also holds.",
            "response_depth": "standard",
        }
    )
    formation = {
        "candidate_text": "Both supplied conditions hold.",
        "formation_mode": "structured",
        "meaning_preserved": True,
    }

    loom = weave_supported_discourse(
        discourse,
        selected_formation=formation,
        response_depth="standard",
    )

    assert loom["collapsed_seed_content_unit_ids"] == ["content_1", "content_2"]
    assert loom["selected_candidate_text"] == "Both supplied conditions hold."
    assert loom["selected_paragraphs"][0]["content_unit_ids"] == [
        "structured_formation"
    ]


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
            {"thread_id": "branch", "thread_action": "branch", "thread_traversal_index": 1, "grounded": True, "content_unit_ids": ["branch"]},
            {"thread_id": "original", "thread_action": "revise_with_dependency", "thread_traversal_index": 2, "grounded": True, "content_unit_ids": ["return"]},
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
    assert "On the related point:" in threaded["candidate_text"]
    assert "Bringing that back with the new piece:" in threaded["candidate_text"]
    assert threaded["candidate_text"].index("side condition") < threaded["candidate_text"].index("original recommendation")
    assert "On the related point" not in " ".join(
        item["text"] for item in discourse["content_units"]
    )


def test_typed_spine_selects_x_y_x_with_y_z_return_and_stops_once():
    discourse = build_supported_discourse_plan(
        {
            "content_seed": (
                "Place the beds first. "
                "Check the water schedule. "
                "Revise bed spacing from that schedule. "
                "Then record the bounded layout."
            ),
            "response_depth": "developed",
            "response_obligations": [
                {
                    "id": "x-start",
                    "source_text": "Place the beds.",
                    "coverage_terms": ["place", "beds"],
                    "thread_id": "x",
                    "thread_action": "start",
                    "thread_traversal_index": 1,
                },
                {
                    "id": "y-branch",
                    "source_text": "Check the water schedule.",
                    "coverage_terms": ["water", "schedule"],
                    "thread_id": "y",
                    "thread_action": "branch",
                    "thread_traversal_index": 2,
                },
                {
                    "id": "x-return",
                    "source_text": "Revise bed spacing.",
                    "coverage_terms": ["revise", "spacing"],
                    "thread_id": "x",
                    "thread_action": "revise_with_dependency",
                    "thread_traversal_index": 3,
                    "dependency_thread_id": "y",
                },
                {
                    "id": "z-land",
                    "source_text": "Record the layout.",
                    "coverage_terms": ["record", "layout"],
                    "thread_id": "z",
                    "thread_action": "land",
                    "thread_traversal_index": 4,
                    "dependency_thread_id": "x",
                },
            ],
            "thread_braid": {
                "braided": True,
                "turn_traversal": [
                    {"index": 1, "thread_id": "x", "action": "start"},
                    {"index": 2, "thread_id": "y", "action": "branch"},
                    {"index": 3, "thread_id": "x", "action": "revise_with_dependency", "dependency_thread_id": "y"},
                    {"index": 4, "thread_id": "z", "action": "land", "dependency_thread_id": "x"},
                ],
            },
        }
    )
    loom = weave_supported_discourse(
        discourse,
        response_depth="developed",
        contextual_plan={"response_depth": "developed", "supported_content_unit_count": 4},
    )

    assert loom["selected_loom_specification_id"] == "discourse:thread_traversal"
    text = loom["selected_candidate_text"]
    assert text.index("Place the beds") < text.index("water schedule")
    assert text.index("water schedule") < text.index("Revise bed spacing")
    assert text.index("Revise bed spacing") < text.index("record the bounded layout")
    assert "Bringing that back with the new piece:" in text
    assert "For the final point:" in text
    assert loom["terminal_stopping_receipt_count"] == 1
    assert loom["recursive_generation_used"] is False


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


def test_discourse_loom_preserves_typed_section_receipts_and_one_terminal_stop():
    discourse = build_supported_discourse_plan(
        {
            "supported_content_units": [
                {
                    "id": "thesis",
                    "text": "Use the reversible option.",
                    "role": "thesis",
                    "supported": True,
                    "source_kind": "prompt_grounded_method",
                    "certainty": "supported",
                },
                {
                    "id": "example",
                    "text": "A one-week pilot can be undone.",
                    "role": "example",
                    "supported": True,
                    "source_kind": "fictional_invention",
                    "certainty": "illustrative_only",
                },
            ],
            "response_depth": "developed",
        }
    )
    loom = weave_supported_discourse(discourse, response_depth="developed")

    assert loom["section_plan_id"] == discourse["discourse_spine"]["plan_id"]
    assert [item["function"] for item in loom["section_receipts"]] == ["thesis", "example"]
    assert all(item["state"] == "realized_from_declared_supported_units" for item in loom["section_receipts"])
    assert all(item["source_and_epistemic_bindings_preserved"] is True for item in loom["section_receipts"])
    assert loom["terminal_stopping_receipt"]["terminal"] is True
    assert loom["terminal_stopping_receipt_count"] == 1
    assert loom["terminal_stopping_receipt"]["further_generation_allowed"] is False
    assert loom["paragraph_limit"] == 8
    _assert_locked(loom)


def test_discourse_loom_exposes_local_revision_receipt_without_resetting_other_sections():
    base_payload = {
        "supported_content_units": [
            {"id": "thesis", "text": "Run the pilot.", "role": "thesis", "supported": True},
            {"id": "reason", "text": "It is reversible.", "role": "explanation", "supported": True},
            {"id": "limit", "text": "The result is local.", "role": "qualification", "supported": True},
        ],
        "response_depth": "developed",
    }
    initial = build_supported_discourse_plan(base_payload)
    target = initial["discourse_spine"]["section_plan"][1]["section_id"]
    revised = build_supported_discourse_plan(
        {
            **base_payload,
            "supported_content_units": [
                *base_payload["supported_content_units"],
                {"id": "reason_v2", "text": "It is reversible and observable.", "role": "explanation", "supported": True},
            ],
            "section_revision": {
                "prior_discourse_spine": initial["discourse_spine"],
                "target_section_id": target,
                "replacement_content_unit_ids": ["reason_v2"],
            },
        }
    )
    loom = weave_supported_discourse(revised, response_depth="developed")

    assert loom["local_revision_receipt"]["status"] == "local_section_revision_applied"
    assert loom["local_revision_receipt"]["other_sections_changed"] is False
    assert loom["local_revision_receipt"]["conversation_reset"] is False
    assert "It is reversible and observable." in loom["selected_candidate_text"]
    assert "It is reversible." not in loom["selected_candidate_text"]


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
    assert result["discourse_plan"]["supported_discourse"]["discourse_spine"]["status"] == "typed_discourse_spine_ready"
    assert result["discourse_plan"]["supported_discourse"]["discourse_spine"]["release_alignment"] == {
        "state": "pre_expression_release_alignment_carried",
        "content_source_release_allowed": False,
        "final_release_owner": "Conversation Spine and Chat",
        "planner_has_release_authority": False,
    }
    assert loom["terminal_stopping_receipt_count"] == 1
    selected_candidate = next(
        item
        for item in loom["candidates"]
        if item["discourse_candidate_id"] == loom["selected_discourse_candidate_id"]
    )
    assert loom["section_receipts"] == selected_candidate["section_receipts"]
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
