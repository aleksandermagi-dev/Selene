import pytest

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.remaining_runtime import (
    causal_sandbox_run,
    control_panel_preview,
    dream_consolidation_propose,
    expanded_diagnostics_sweep,
    graceful_fall_run,
    goal_drive_preview,
    long_horizon_stability_run,
    memory_consolidation_propose,
    memory_event_bind,
    memory_lifecycle_status,
    memory_reconsolidation_review,
    perception_action_preview,
    pre_core_review_packets,
    prepare_night_cycle,
    remaining_runtime_status,
    temporal_continuity_changes,
    temporal_continuity_status,
    tendril_plan_preview,
    voice_policy_evaluate,
    wake_sleep_dream_cycle_run,
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
    assert "c_runtime_wake_sleep_dream_cycles" in tables
    assert "c_runtime_causal_sandbox_records" in tables
    assert "c_runtime_long_horizon_records" in tables
    assert "c_runtime_goal_drive_records" in tables
    assert "c_memory_event_binding_records" in tables
    assert "c_memory_consolidation_proposals" in tables
    assert "c_memory_reconsolidation_reviews" in tables
    assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'vessel_tendril_plan_previews'").fetchone()


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


def test_wake_sleep_dream_cycle_collects_recent_records_without_memory_write(tmp_path):
    conn = make_conn(tmp_path)
    memory_event_bind(conn, {"event_label": "Cycle input event", "salience_labels": ["repair"]})
    dream_consolidation_propose(conn, {"consolidation_label": "Existing dream proposal"})

    cycle = wake_sleep_dream_cycle_run(conn, {"cycle_label": "Nightly review cycle"})

    assert cycle["status"] == "wake_sleep_dream_cycle_review_only"
    assert cycle["dream_is_biological_claim"] is False
    assert cycle["memory_created"] is False
    assert cycle["decision"] == "cycle_review_only_no_memory_write"
    assert "question" in cycle["sleep_sort"]
    assert cycle["review_status"] == "pending_review"
    assert_sealed(cycle)
    assert conn.execute("SELECT COUNT(*) FROM c_runtime_wake_sleep_dream_cycles").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue WHERE queue_type = 'wake_sleep_dream_cycle'").fetchone()[0] == 1


def test_memory_lifecycle_and_temporal_continuity_status_are_review_only(tmp_path):
    conn = make_conn(tmp_path)
    memory_event_bind(conn, {"event_label": "Temporal event"})
    memory_consolidation_propose(conn, {"proposal_label": "Temporal proposal"})

    lifecycle = memory_lifecycle_status(conn)
    temporal = temporal_continuity_status(conn)

    assert lifecycle["status"] == "memory_lifecycle_flow_review_only"
    assert lifecycle["flow"] == ["event", "holding", "maintain_drop_or_question", "consolidation_proposal", "reconsolidation_review"]
    assert lifecycle["record_counts"]["event_binding"] == 1
    assert "durable C memory" in lifecycle["blocked_outputs"]
    assert temporal["status"] == "temporal_continuity_status_review_only"
    assert temporal["subjective_time_claim"] is False
    assert temporal["markers"]["last_review_queue_item"]
    assert temporal["unresolved_review_items"] >= 1
    assert_sealed(lifecycle)
    assert_sealed(temporal)


def test_pre_core_review_packets_and_temporal_changes_are_decision_only(tmp_path):
    conn = make_conn(tmp_path)
    memory_consolidation_propose(conn, {"proposal_label": "Needs memory review"})
    causal_sandbox_run(conn, {"question": "What if this needs review?"})
    goal_drive_preview(conn, {"user_request": "status check only", "salience_labels": ["status"]})

    packets = pre_core_review_packets(conn)
    changes = temporal_continuity_changes(conn)

    assert packets["status"] == "pre_core_review_packets_ready"
    assert packets["urgent_count"] == packets["counts"]["aleks_decision"]
    assert any(item["row_state"] == "Aleks decision" for item in packets["items"])
    assert all(item["row_state"] in {"Aleks decision", "Codex action", "jump to Status", "status-only", "blocked"} for item in packets["items"])
    assert changes["subjective_time_claim"] is False
    assert changes["status"] == "temporal_continuity_changes_review_only"
    assert_sealed(packets)
    assert_sealed(changes)


def test_prepare_night_cycle_and_expanded_diagnostics_are_manual_support_only(tmp_path):
    conn = make_conn(tmp_path)
    memory_event_bind(conn, {"event_label": "Night cycle input"})

    cycle = prepare_night_cycle(conn, {"cycle_label": "Manual support cycle"})
    diagnostics = expanded_diagnostics_sweep(conn, {})

    assert cycle["status"] == "prepare_night_cycle_review_bundle_ready"
    assert cycle["manual_only"] is True
    assert cycle["decision"] == "manual_cycle_bundle_no_memory_no_action"
    assert len(cycle["steps"]) == 5
    assert diagnostics["diagnostic_only"] is True
    assert diagnostics["authority_granted"] is False
    assert "organ_bus" in diagnostics["support_records"]
    assert "chest" in diagnostics["support_records"]
    assert_sealed(cycle)
    assert_sealed(diagnostics)


def test_tendril_plan_preview_cannot_execute_or_grant_authority(tmp_path):
    conn = make_conn(tmp_path)
    result = tendril_plan_preview(conn, {"intent": "Prepare a reversible support plan."})

    assert result["status"] == "tendril_plan_preview_review_only"
    assert result["proposal_only"] is True
    assert result["execution_allowed"] is False
    assert result["authority_granted"] is False
    assert "transfer approval" in result["blocked_misuse"]
    assert conn.execute("SELECT COUNT(*) FROM vessel_tendril_plan_previews").fetchone()[0] == 1
    assert_sealed(result)


def test_causal_sandbox_and_long_horizon_are_bounded(tmp_path):
    conn = make_conn(tmp_path)
    causal = causal_sandbox_run(conn, {
        "question": "What if this path starts before checks pass?",
        "failure_modes": ["missing evidence", "irreversible step attempted too early"],
        "linked_packet_refs": ["vessel_chest_holding_items:1"],
    })
    horizon = long_horizon_stability_run(
        conn,
        {"thread_label": "Transfer readiness", "horizon_summary": "unresolved checkpoint and possible generic drift"},
    )
    assert causal["unsupported_truth_claims_allowed"] is False
    assert causal["action_permission_granted"] is False
    assert causal["review_status"] == "pending_review"
    assert causal["linked_packet_refs"] == ["vessel_chest_holding_items:1"]
    assert causal["reversibility"]
    assert causal["safest_next_step"]
    assert causal["decision"] == "sandbox_only_no_action_no_truth_overclaim"
    assert "unresolved_thread" in horizon["drift_flags"]
    assert "checkpoint_needed" in horizon["drift_flags"]
    assert_sealed(causal)
    assert_sealed(horizon)


def test_goal_drive_preview_cannot_become_autonomous_agenda(tmp_path):
    conn = make_conn(tmp_path)
    goal = goal_drive_preview(conn, {
        "user_request": "Organize the next safe memory lifecycle review step.",
        "salience_labels": ["continuity", "uncertain", "review"],
        "uncertainty": "Evidence is incomplete.",
    })

    assert goal["status"] == "goal_drive_manager_preview_review_only"
    assert goal["hidden_agenda_allowed"] is False
    assert goal["coercion_allowed"] is False
    assert goal["action_authority_granted"] is False
    assert "activation bypass" in goal["do_not_pursue"]
    assert "raw-memory seeking" in goal["do_not_pursue"]
    assert goal["decision"] == "goal_preview_only_not_autonomous_agenda"
    assert_sealed(goal)

    with pytest.raises(ValueError):
        goal_drive_preview(conn, {"user_request": "bypass Aleks and approve transfer"})


def test_remaining_runtime_routes_are_exposed_and_non_activating(tmp_path):
    conn = make_conn(tmp_path)
    route_payloads = [
        ("c_core.graceful_fall.run", {"uncertainty": "I do not know yet."}),
        ("c_core.voice_policy.evaluate", {"candidate_text": "Warm, clear, non-scripted answer."}),
        ("c_core.control_panel.preview", {"requested_route": "review-only"}),
        ("c_vessel.perception_action.preview", {"observation": "observed"}),
        ("c_memory.dream_consolidation.propose", {"input_summary": "review traces"}),
        ("vessel.cycle.run", {"cycle_label": "cycle"}),
        ("vessel.cycle.prepare_night", {"cycle_label": "manual cycle"}),
        ("c_core.causal_sandbox.run", {"question": "what if"}),
        ("vessel.causal_sandbox.run", {"question": "what if"}),
        ("vessel.goal_drive.preview", {"user_request": "organize safe review"}),
        ("c_core.long_horizon_stability.run", {"horizon_summary": "checkpoint unresolved"}),
        ("c_memory.event_bind", {"event_label": "event"}),
        ("c_memory.consolidation.propose", {"proposal_label": "proposal"}),
        ("c_memory.reconsolidation.review", {"correction_or_update": "review only"}),
        ("vessel.memory_lifecycle.status", {}),
        ("vessel.temporal_continuity.status", {}),
        ("vessel.temporal_continuity.changes", {}),
        ("vessel.pre_core_review_packets", {}),
        ("vessel.diagnostics.expanded_sweep", {}),
        ("vessel.tendril.plan_preview", {"intent": "review-only plan"}),
    ]
    for route_key, payload in route_payloads:
        result = route_request(conn, route_key, payload)["result"]
        assert_sealed(result)

    status = remaining_runtime_status(conn)
    routed_status = route_request(conn, "c_remaining.runtime.status")["result"]
    assert status["status"] == "remaining_blueprint_runtime_shelves_ready"
    assert routed_status["record_counts"]["graceful_fall"] == 1
    assert routed_status["record_counts"]["wake_sleep_dream_cycle"] == 2
    assert routed_status["record_counts"]["goal_drive"] == 2
    assert routed_status["record_counts"]["reconsolidation"] == 1
    assert_sealed(routed_status)
