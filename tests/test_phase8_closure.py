from selene.commitment_anomaly_coordination import (
    build_capability_graduation_receipts,
    commitment_lifecycle_status,
    record_commitment_acceptance,
    transition_commitment_lifecycle,
)
from selene.core_mind import coordinate_goal_responsibilities
from selene.db import connect, init_db
from selene.remaining_runtime import record_goal_responsibility


def responsibility(key, owner, priority, *, persist=False):
    payload = {
        "goal_key": key,
        "goal_summary": f"Gently verify {key} within this disposable walkthrough.",
        "owner_kind": owner,
        "owner_ref": f"synthetic:{owner}",
        "capability": "conversation",
        "scope_boundary": "this source-contained disposable test only",
        "priority_band": priority,
        "priority_reason": "The synthetic Phase 8 closure matrix names this band.",
        "source_refs": [f"test:phase8:{key}"],
        "completion_conditions": ["the bounded synthetic assertion is visible"],
        "stop_conditions": ["the assertion completes, blocks, or is released"],
        "requested_move": "answer",
    }
    if persist:
        payload.update(
            {
                "persist_goal": True,
                "idempotency_key": f"phase8-closure:goal:{key}",
            }
        )
    return payload


def test_phase8_disposable_goal_commitment_and_capability_walkthrough(tmp_path):
    conn = connect(tmp_path / "phase8-closure.sqlite3")
    init_db(conn)

    conflicts = [
        responsibility("selene", "selene_goal", "selene_goal"),
        responsibility("aleks", "aleks_request", "current_request"),
        responsibility("shared", "shared_project_goal", "shared_project"),
        responsibility("law", "governing_requirement", "governing_requirement"),
        responsibility("external", "external_demand", "governing_requirement"),
        responsibility("advice", "organ_advice", "current_request"),
    ]
    coordinated = coordinate_goal_responsibilities(conflicts)

    assert coordinated["considered_goal_keys"] == [
        "selene",
        "aleks",
        "shared",
        "law",
        "external",
        "advice",
    ]
    assert coordinated["selected"]["goal_key"] == "law"
    assert coordinated["pass_count"] == 1
    assert coordinated["stopping_receipt"]["terminal"] is True
    assert coordinated["whole_system_authority_granted"] is False
    assert {item["goal_key"] for item in coordinated["deferred"]} >= {
        "external",
        "advice",
    }

    goal = record_goal_responsibility(
        conn,
        responsibility(
            "walkthrough-result",
            "shared_project_goal",
            "shared_project",
            persist=True,
        ),
    )
    accepted = record_commitment_acceptance(
        conn,
        {
            "accept_commitment": True,
            "commitment_key": "phase8-closure:commitment",
            "commitment_claim": "Complete this disposable assertion or report its blocker.",
            "speech_act": "commitment",
            "goal_key": "walkthrough-result",
            "capability": "conversation",
            "mechanism_ref": "pytest:phase8-disposable-walkthrough",
            "stop_conditions": ["fulfilled, blocked, released, or closed"],
            "idempotency_key": "phase8-closure:accept",
            "source_refs": ["test:phase8:explicit-acceptance"],
        },
    )
    started = transition_commitment_lifecycle(
        conn,
        {
            "transition_commitment": True,
            "commitment_key": "phase8-closure:commitment",
            "goal_key": "walkthrough-result",
            "capability": "conversation",
            "lifecycle_state": "in_progress",
            "mechanism_ref": "pytest:phase8-disposable-walkthrough",
            "idempotency_key": "phase8-closure:in-progress",
            "source_refs": ["test:phase8:assertion-started"],
        },
    )
    fulfilled = transition_commitment_lifecycle(
        conn,
        {
            "transition_commitment": True,
            "commitment_key": "phase8-closure:commitment",
            "goal_key": "walkthrough-result",
            "capability": "conversation",
            "lifecycle_state": "fulfilled",
            "result_refs": ["test:phase8:assertions-passed"],
            "stop_reason": "The source-contained disposable assertions passed.",
            "idempotency_key": "phase8-closure:fulfilled",
            "source_refs": ["test:phase8:assertions-passed"],
        },
    )

    assert goal["packet"]["goal_is_capability_grant"] is False
    assert accepted["event"]["root_event_id"] == accepted["event_id"]
    assert started["event"]["parent_event_id"] == accepted["event_id"]
    assert fulfilled["event"]["parent_event_id"] == started["event_id"]
    assert fulfilled["event"]["result_refs"] == ["test:phase8:assertions-passed"]
    assert fulfilled["event"]["stopping_receipt"]["terminal"] is True
    assert commitment_lifecycle_status(conn)["terminal_commitment_count"] == 1

    graduation = build_capability_graduation_receipts()
    receipts = {item["capability"]: item for item in graduation["receipts"]}
    assert set(receipts) == {
        "conversation",
        "study",
        "memory_proposal",
        "tools",
        "tendril",
        "future_embodiment",
    }
    assert all(item["receipt_is_action_authority"] is False for item in receipts.values())
    assert graduation["aggregate_autonomy_state_created"] is False
    assert graduation["external_action_started"] is False

    assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert conn.execute("SELECT COUNT(*) FROM c_runtime_goal_drive_records").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM selene_commitment_lifecycles").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM selene_chat_sessions").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_dream_reflections").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    conn.close()
