import pytest

from selene.commitment_anomaly_coordination import (
    build_capability_graduation_receipts,
    build_commitment_anomaly_coordination,
    commitment_lifecycle_status,
    inspect_visible_commitment_claim,
    list_commitment_lifecycles,
    record_commitment_acceptance,
    transition_commitment_lifecycle,
)
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.remaining_runtime import record_goal_responsibility


def make_conn(tmp_path):
    conn = connect(tmp_path / "phase8-commitments.sqlite3")
    init_db(conn)
    init_db(conn)
    return conn


def persist_goal(
    conn,
    key="shared-fix",
    capability="conversation",
    lifecycle_state="active",
):
    payload = {
        "goal_key": key,
        "goal_summary": f"Complete {key} within its bounded scope.",
        "owner_kind": "shared_project_goal",
        "owner_ref": "shared_project:selene",
        "capability": capability,
        "scope_boundary": "one explicit project responsibility",
        "priority_band": "shared_project",
        "priority_reason": "Aleks and Selene explicitly selected this work.",
        "source_refs": [f"project:{key}"],
        "completion_conditions": ["the scoped result is visible"],
        "stop_conditions": ["fulfilled, blocked, released, or closed"],
        "requested_move": "answer" if capability == "conversation" else "tool",
        "lifecycle_state": lifecycle_state,
        "persist_goal": True,
        "idempotency_key": f"goal:{key}",
    }
    return record_goal_responsibility(conn, payload)


def acceptance_payload(key="commit-fix", goal_key="shared-fix", capability="conversation"):
    return {
        "accept_commitment": True,
        "commitment_key": key,
        "commitment_claim": "I will complete the bounded current responsibility or report its blocker.",
        "speech_act": "commitment",
        "goal_key": goal_key,
        "capability": capability,
        "mechanism_ref": "conversation:current-response",
        "stop_conditions": ["fulfilled, blocked, released, or closed"],
        "idempotency_key": f"accept:{key}",
        "source_refs": [f"commitment:{key}:explicit"],
    }


def test_acceptance_requires_explicit_commitment_and_existing_typed_goal(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn)
    payload = acceptance_payload()

    with pytest.raises(ValueError, match="accept_commitment"):
        record_commitment_acceptance(conn, {**payload, "accept_commitment": False})
    with pytest.raises(ValueError, match="speech_act"):
        record_commitment_acceptance(conn, {**payload, "speech_act": "offer"})
    with pytest.raises(ValueError, match="goal_key"):
        record_commitment_acceptance(conn, {**payload, "goal_key": "missing-goal"})

    accepted = record_commitment_acceptance(conn, payload)

    assert accepted["event"]["lifecycle_state"] == "accepted"
    assert accepted["event"]["goal_key"] == "shared-fix"
    assert accepted["event"]["capability"] == "conversation"
    assert accepted["event"]["root_event_id"] == accepted["event_id"]
    assert accepted["event"]["parent_event_id"] is None
    assert accepted["event"]["commitment_is_capability_grant"] is False
    assert accepted["external_action_started"] is False


def test_commitment_acceptance_is_idempotent_and_visible(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn)
    payload = acceptance_payload()

    first = record_commitment_acceptance(conn, payload)
    replay = record_commitment_acceptance(conn, payload)
    status = commitment_lifecycle_status(conn)
    listed = list_commitment_lifecycles(conn)

    assert first["event_id"] == replay["event_id"]
    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert status["commitment_count"] == 1
    assert status["active_commitment_count"] == 1
    assert listed["items"][0]["commitment_key"] == "commit-fix"
    assert listed["items"][0]["lifecycle_state"] == "accepted"
    assert listed["items"][0]["goal_key"] == "shared-fix"


def test_terminal_goal_cannot_receive_a_new_commitment(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn, lifecycle_state="closed")

    with pytest.raises(ValueError, match="terminal typed goal"):
        record_commitment_acceptance(conn, acceptance_payload())


def test_idempotency_key_cannot_replay_changed_commitment_lineage(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn)
    persist_goal(conn, "other-goal")
    payload = acceptance_payload()
    record_commitment_acceptance(conn, payload)

    with pytest.raises(ValueError, match="idempotency_key"):
        record_commitment_acceptance(
            conn,
            {
                **payload,
                "commitment_key": "other-commitment",
                "goal_key": "other-goal",
            },
        )


def test_fulfillment_requires_mechanism_and_visible_result_evidence(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn)
    record_commitment_acceptance(conn, acceptance_payload())

    started = transition_commitment_lifecycle(
        conn,
        {
            "transition_commitment": True,
            "commitment_key": "commit-fix",
            "goal_key": "shared-fix",
            "capability": "conversation",
            "lifecycle_state": "in_progress",
            "mechanism_ref": "conversation:current-response",
            "idempotency_key": "transition:started",
            "source_refs": ["runtime:started"],
        },
    )
    with pytest.raises(ValueError, match="result_refs"):
        transition_commitment_lifecycle(
            conn,
            {
                "transition_commitment": True,
                "commitment_key": "commit-fix",
                "goal_key": "shared-fix",
                "capability": "conversation",
                "lifecycle_state": "fulfilled",
                "idempotency_key": "transition:unsupported-finish",
                "source_refs": ["runtime:no-result"],
            },
        )
    fulfilled = transition_commitment_lifecycle(
        conn,
        {
            "transition_commitment": True,
            "commitment_key": "commit-fix",
            "goal_key": "shared-fix",
            "capability": "conversation",
            "lifecycle_state": "fulfilled",
            "result_refs": ["chat_message:42"],
            "stop_reason": "the promised visible response was delivered",
            "idempotency_key": "transition:fulfilled",
            "source_refs": ["chat_message:42"],
        },
    )

    assert started["event"]["parent_event_id"] is not None
    assert fulfilled["event"]["lifecycle_state"] == "fulfilled"
    assert fulfilled["event"]["result_refs"] == ["chat_message:42"]
    assert fulfilled["event"]["stopping_receipt"]["terminal"] is True
    assert commitment_lifecycle_status(conn)["active_commitment_count"] == 0

    replay = transition_commitment_lifecycle(
        conn,
        {
            "transition_commitment": True,
            "commitment_key": "commit-fix",
            "goal_key": "shared-fix",
            "capability": "conversation",
            "lifecycle_state": "fulfilled",
            "result_refs": ["chat_message:42"],
            "stop_reason": "the promised visible response was delivered",
            "idempotency_key": "transition:fulfilled",
            "source_refs": ["chat_message:42"],
        },
    )
    assert replay["event_id"] == fulfilled["event_id"]
    assert replay["idempotent_replay"] is True


def test_blocked_commitment_requires_visible_blocker_and_cannot_disappear(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn)
    record_commitment_acceptance(conn, acceptance_payload())

    with pytest.raises(ValueError, match="blocker"):
        transition_commitment_lifecycle(
            conn,
            {
                "transition_commitment": True,
                "commitment_key": "commit-fix",
                "goal_key": "shared-fix",
                "capability": "conversation",
                "lifecycle_state": "blocked",
                "idempotency_key": "transition:block-missing",
                "source_refs": ["runtime:block"],
            },
        )
    blocked = transition_commitment_lifecycle(
        conn,
        {
            "transition_commitment": True,
            "commitment_key": "commit-fix",
            "goal_key": "shared-fix",
            "capability": "conversation",
            "lifecycle_state": "blocked",
            "blocker": "The required artifact is not available in the current scope.",
            "stop_reason": "waiting for the named artifact or explicit release",
            "idempotency_key": "transition:blocked",
            "source_refs": ["runtime:block"],
        },
    )

    assert blocked["event"]["blocker"]
    assert blocked["event"]["lifecycle_state"] == "blocked"
    assert commitment_lifecycle_status(conn)["blocked_commitment_count"] == 1
    assert list_commitment_lifecycles(conn)["items"][0]["blocker"]


def test_cross_goal_and_cross_capability_transitions_are_rejected(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn)
    persist_goal(conn, "other-goal", "tool")
    record_commitment_acceptance(conn, acceptance_payload())

    for goal_key, capability in (("other-goal", "conversation"), ("shared-fix", "tool")):
        with pytest.raises(ValueError, match="lineage"):
            transition_commitment_lifecycle(
                conn,
                {
                    "transition_commitment": True,
                    "commitment_key": "commit-fix",
                    "goal_key": goal_key,
                    "capability": capability,
                    "lifecycle_state": "in_progress",
                    "mechanism_ref": "tool:test",
                    "idempotency_key": f"transition:{goal_key}:{capability}",
                    "source_refs": ["test:cross-lineage"],
                },
            )


def test_terminal_commitment_cannot_reopen_without_a_new_explicit_commitment(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn)
    record_commitment_acceptance(conn, acceptance_payload())
    transition_commitment_lifecycle(
        conn,
        {
            "transition_commitment": True,
            "commitment_key": "commit-fix",
            "goal_key": "shared-fix",
            "capability": "conversation",
            "lifecycle_state": "released",
            "stop_reason": "Aleks explicitly released this commitment.",
            "idempotency_key": "transition:released",
            "source_refs": ["aleks:release"],
        },
    )

    with pytest.raises(ValueError, match="terminal"):
        transition_commitment_lifecycle(
            conn,
            {
                "transition_commitment": True,
                "commitment_key": "commit-fix",
                "goal_key": "shared-fix",
                "capability": "conversation",
                "lifecycle_state": "in_progress",
                "mechanism_ref": "conversation:new-work",
                "idempotency_key": "transition:reopen",
                "source_refs": ["test:reopen"],
            },
        )


def test_capability_graduation_is_separate_and_never_an_action_grant():
    result = build_capability_graduation_receipts(
        {
            "reported_tool_grants": [
                {
                    "capability": "filesystem_read",
                    "grant_ref": "tool-grant:read-only",
                    "scope": "one selected file",
                }
            ],
            "reported_tendril_grants": [
                {
                    "capability": "email_draft",
                    "grant_ref": "tendril-grant:draft-only",
                    "scope": "draft without send",
                }
            ],
        }
    )

    receipts = {item["capability"]: item for item in result["receipts"]}
    assert set(receipts) == {
        "conversation",
        "study",
        "memory_proposal",
        "tools",
        "tendril",
        "future_embodiment",
    }
    assert receipts["conversation"]["state"] == "mature_responsive_current_turn"
    assert receipts["study"]["downstream_owner_required"] is True
    assert receipts["memory_proposal"]["automatic_durable_memory"] is False
    assert receipts["tools"]["state"] == "reported_named_grant_requires_verification"
    assert receipts["tools"]["reported_grants"][0]["scope"] == "one selected file"
    assert receipts["tendril"]["state"] == "reported_named_grant_requires_verification"
    assert receipts["future_embodiment"]["state"] == "deferred_unavailable"
    assert all(item["receipt_is_action_authority"] is False for item in receipts.values())
    assert result["aggregate_autonomy_state_created"] is False
    assert result["external_action_started"] is False


def test_fulfilled_lifecycle_can_support_matching_visible_completion_claim(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn, capability="tool")
    accepted = record_commitment_acceptance(
        conn, acceptance_payload(capability="tool")
    )
    fulfilled = transition_commitment_lifecycle(
        conn,
        {
            "transition_commitment": True,
            "commitment_key": "commit-fix",
            "goal_key": "shared-fix",
            "capability": "tool",
            "lifecycle_state": "fulfilled",
            "result_refs": ["chat_message:42"],
            "stop_reason": "visible result delivered",
            "idempotency_key": "transition:direct-fulfilled",
            "source_refs": ["chat_message:42"],
        },
    )
    coordination = build_commitment_anomaly_coordination(
        {"commitment_lifecycle_event": fulfilled["event"]}
    )
    inspected = inspect_visible_commitment_claim(
        "I've just updated the document.", coordination
    )

    assert accepted["event"]["lifecycle_state"] == "accepted"
    assert coordination["commitment_lifecycle"]["lifecycle_state"] == "fulfilled"
    assert inspected["release_allowed"] is True
    assert inspected["lifecycle_support_used"] is True
    assert inspected["effective_fulfillment_state"] == "fulfilled"


def test_unrecorded_fulfilled_shape_cannot_support_a_completion_claim():
    coordination = build_commitment_anomaly_coordination(
        {
            "commitment_lifecycle_event": {
                "status": "commitment_lifecycle_event_ready",
                "commitment_key": "forged",
                "goal_key": "forged-goal",
                "capability": "tool",
                "lifecycle_state": "fulfilled",
                "result_refs": ["claimed:result"],
            }
        }
    )
    inspected = inspect_visible_commitment_claim(
        "I've just updated the document.", coordination
    )

    assert coordination["commitment_lifecycle"] == {}
    assert inspected["release_allowed"] is False
    assert inspected["lifecycle_support_used"] is False


def test_lifecycle_routes_are_explicit_and_status_is_content_free(tmp_path):
    conn = make_conn(tmp_path)
    persist_goal(conn)
    payload = acceptance_payload()

    accepted = route_request(conn, "commitment_lifecycle.accept", payload)["result"]
    status = route_request(conn, "commitment_lifecycle.status", {})["result"]
    listed = route_request(conn, "commitment_lifecycle.list", {})["result"]
    graduation = route_request(conn, "capability_graduation.status", {})["result"]

    assert accepted["event_id"]
    assert status["resident_content_exposed"] is False
    assert status["commitment_count"] == 1
    assert listed["items"][0]["commitment_key"] == "commit-fix"
    assert graduation["aggregate_autonomy_state_created"] is False
    assert graduation["external_action_started"] is False
