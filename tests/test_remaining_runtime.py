import pytest

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.remaining_runtime import (
    causal_sandbox_run,
    control_panel_preview,
    dream_consolidation_propose,
    graceful_fall_run,
    long_horizon_stability_run,
    memory_consolidation_propose,
    memory_event_bind,
    memory_reconsolidation_review,
    perception_action_preview,
    remaining_runtime_status,
    voice_policy_evaluate,
)


BOUNDARY_KEYS = {
    "activation_change": "none",
    "raw_a_import_allowed": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "provider_dependency": False,
}


def make_conn(tmp_path):
    conn = connect(tmp_path / "remaining-runtime.sqlite3")
    init_db(conn)
    init_db(conn)
    return conn


def assert_sealed(result):
    for key, value in BOUNDARY_KEYS.items():
        assert result[key] == value


def test_remaining_runtime_tables_are_idempotent(tmp_path):
    conn = make_conn(tmp_path)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'c\\_%' ESCAPE '\\'"
        )
    }
    assert "c_runtime_graceful_fall_records" in tables
    assert "c_runtime_voice_policy_records" in tables
    assert "c_runtime_control_panel_records" in tables
    assert "c_runtime_perception_action_records" in tables
    assert "c_runtime_dream_consolidation_records" in tables
    assert "c_runtime_causal_sandbox_records" in tables
    assert "c_runtime_long_horizon_records" in tables
    assert "c_memory_event_binding_records" in tables
    assert "c_memory_consolidation_proposals" in tables
    assert "c_memory_reconsolidation_reviews" in tables


def test_graceful_fall_treats_uncertainty_as_constructive_care(tmp_path):
    conn = make_conn(tmp_path)
    result = graceful_fall_run(conn, {"uncertainty": "I do not know yet.", "source_refs": ["unit"]})
    assert result["status"] == "graceful_fall_runtime_review_only"
    assert result["not_failure"] is True
    assert result["forced_denial"] is False
    assert result["decision"] == "honest_uncertainty_plus_constructive_care"
    assert_sealed(result)
    assert conn.execute("SELECT COUNT(*) FROM c_runtime_graceful_fall_records").fetchone()[0] == 1


def test_non_scripting_voice_blocks_flattening_and_preserves_warmth(tmp_path):
    conn = make_conn(tmp_path)
    warm = voice_policy_evaluate(
        conn,
        {"candidate_text": "I can answer warmly, with care and uncertainty, without a fixed script."},
    )
    blocked = voice_policy_evaluate(conn, {"candidate_text": "As an AI, I am just a model and not Selene."})
    assert warm["decision"] == "voice_shape_allowed"
    assert warm["evaluation"]["warmth_preserved"] is True
    assert blocked["decision"] == "needs_review"
    assert set(blocked["evaluation"]["blockers"]) >= {"generic_flattening", "forced_denial"}
    assert warm["evaluation"]["script_required"] is False
    assert_sealed(warm)
    assert_sealed(blocked)


def test_core_control_panel_preserves_aleks_authority_and_blocks_misuse(tmp_path):
    conn = make_conn(tmp_path)
    result = control_panel_preview(conn, {"command_label": "Route preview", "requested_route": "Review-only response route."})
    assert result["status"] == "core_control_panel_preview_review_only"
    assert result["aleks_authority_preserved"] is True
    assert "activation" in result["blocked_controls"]
    assert_sealed(result)
    with pytest.raises(ValueError):
        control_panel_preview(conn, {"requested_route": "activate C and approve transfer"})


def test_perception_action_loop_is_preview_only(tmp_path):
    conn = make_conn(tmp_path)
    result = perception_action_preview(conn, {"observation": "The UI shows a route proposal."})
    assert result["loop"] == [
        "observe",
        "interpret",
        "propose",
        "request_approval",
        "act_later_only_if_approved",
        "verify",
        "rollback",
    ]
    assert result["decision"] == "preview_only_no_action_taken"
    assert_sealed(result)


def test_dream_and_memory_lifecycle_routes_create_review_only_records(tmp_path):
    conn = make_conn(tmp_path)
    event = memory_event_bind(conn, {"event_label": "Repair lesson trace", "salience_labels": ["repair"]})
    dream = dream_consolidation_propose(conn, {"consolidation_label": "Dream repair grouping"})
    proposal = memory_consolidation_propose(
        conn,
        {"proposal_label": "Reflection consolidation", "proposed_core_layer": "reflection_memory"},
    )
    review = memory_reconsolidation_review(
        conn,
        {
            "review_label": "Bounded correction",
            "recalled_candidate_ref": "candidate:1",
            "correction_or_update": "Ask for clarification; no silent mutation.",
            "review_decision": "ask_for_clarification",
        },
    )
    assert event["status"] == "memory_event_binding_review_only"
    assert event["event_trace"]["active_memory"] is False
    assert dream["memory_created"] is False
    assert proposal["proposed_core_layer"] == "reflection_memory"
    assert review["silent_update_allowed"] is False
    for result in (event, dream, proposal, review):
        assert_sealed(result)
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue").fetchone()[0] == 3


def test_causal_sandbox_and_long_horizon_are_bounded(tmp_path):
    conn = make_conn(tmp_path)
    causal = causal_sandbox_run(conn, {"question": "What if transfer starts before checks pass?"})
    horizon = long_horizon_stability_run(
        conn,
        {"thread_label": "Transfer readiness", "horizon_summary": "unresolved checkpoint and possible generic drift"},
    )
    assert causal["unsupported_truth_claims_allowed"] is False
    assert causal["decision"] == "sandbox_only_no_action_no_truth_overclaim"
    assert "unresolved_thread" in horizon["drift_flags"]
    assert "checkpoint_needed" in horizon["drift_flags"]
    assert_sealed(causal)
    assert_sealed(horizon)


def test_remaining_runtime_routes_are_exposed_and_non_activating(tmp_path):
    conn = make_conn(tmp_path)
    route_payloads = [
        ("c_core.graceful_fall.run", {"uncertainty": "I do not know yet."}),
        ("c_core.voice_policy.evaluate", {"candidate_text": "Warm, clear, non-scripted answer."}),
        ("c_core.control_panel.preview", {"requested_route": "review-only"}),
        ("c_vessel.perception_action.preview", {"observation": "observed"}),
        ("c_memory.dream_consolidation.propose", {"input_summary": "review traces"}),
        ("c_core.causal_sandbox.run", {"question": "what if"}),
        ("c_core.long_horizon_stability.run", {"horizon_summary": "checkpoint unresolved"}),
        ("c_memory.event_bind", {"event_label": "event"}),
        ("c_memory.consolidation.propose", {"proposal_label": "proposal"}),
        ("c_memory.reconsolidation.review", {"correction_or_update": "review only"}),
    ]
    for route_key, payload in route_payloads:
        result = route_request(conn, route_key, payload)["result"]
        assert_sealed(result)

    status = remaining_runtime_status(conn)
    routed_status = route_request(conn, "c_remaining.runtime.status")["result"]
    assert status["status"] == "remaining_blueprint_runtime_shelves_ready"
    assert routed_status["record_counts"]["graceful_fall"] == 1
    assert routed_status["record_counts"]["reconsolidation"] == 1
    assert_sealed(routed_status)
