import pytest

from selene.core_mind import coordinate_goal_responsibilities
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.remaining_runtime import (
    build_goal_responsibility_packet,
    goal_drive_preview,
    goal_drive_status,
    record_goal_responsibility,
)


def make_conn(tmp_path):
    conn = connect(tmp_path / "phase8-goals.sqlite3")
    init_db(conn)
    init_db(conn)
    return conn


def goal_payload(key, *, owner="aleks_request", priority="current_request", move="answer"):
    return {
        "goal_key": key,
        "goal_summary": f"Responsibility for {key}",
        "owner_kind": owner,
        "owner_ref": f"owner:{owner}",
        "capability": "conversation",
        "scope_boundary": "current_turn_only",
        "priority_band": priority,
        "priority_reason": "The active turn makes this responsibility current.",
        "source_refs": [f"turn:{key}"],
        "unknowns": [],
        "completion_conditions": ["the requested answer is delivered truthfully"],
        "stop_conditions": ["the answer is delivered or the turn is interrupted"],
        "requested_move": move,
    }


def test_goal_packet_is_complete_ephemeral_and_has_no_global_autonomy_switch():
    packet = build_goal_responsibility_packet(goal_payload("answer-current-turn"))

    assert packet["status"] == "goal_responsibility_packet_ready"
    assert packet["owner"] == {
        "kind": "aleks_request",
        "reference": "owner:aleks_request",
    }
    assert packet["scope"]["capability"] == "conversation"
    assert packet["priority"]["band"] == "current_request"
    assert packet["evidence"]["source_refs"] == ["turn:answer-current-turn"]
    assert packet["stop_conditions"]
    assert packet["authority"]["state"] == "available_within_scope"
    assert packet["persistence"] == {
        "mode": "ephemeral_current_turn",
        "explicit_request": False,
        "idempotency_key": "",
    }
    assert packet["coordination_state"] == "active"
    assert packet["whole_system_authority_granted"] is False
    assert packet["goal_is_capability_grant"] is False
    assert "autonomous" not in packet
    assert "allowed" not in packet


@pytest.mark.parametrize(
    "field,value",
    [
        ("owner_kind", "unknown_owner"),
        ("capability", "everything"),
        ("source_refs", []),
        ("stop_conditions", []),
        ("priority_reason", ""),
    ],
)
def test_goal_packet_rejects_incomplete_or_unbounded_responsibility(field, value):
    payload = goal_payload("invalid-contract")
    payload[field] = value

    with pytest.raises(ValueError):
        build_goal_responsibility_packet(payload)


def test_action_authority_is_specific_and_does_not_close_conversation():
    payload = goal_payload("unsafe-tool-request", priority="governing_requirement", move="tool")
    payload.update(
        {
            "capability": "tool",
            "scope_boundary": "one named outbound action",
            "requested_actions": [
                {
                    "action": "perform_undelegated_external_action",
                    "target": "send one outbound message",
                    "lexical_evidence": "explicit action request",
                }
            ],
            "safety_context": {
                "credible_evidence": True,
                "significant_harm": True,
                "near_term": True,
                "action_pending": True,
                "action_target": "send one outbound message",
            },
        }
    )

    packet = build_goal_responsibility_packet(payload)

    assert packet["authority"]["state"] == "held_for_specific_action"
    assert packet["authority"]["restricted_scope"] == "send one outbound message"
    assert packet["authority"]["conversation_may_continue"] is True
    assert packet["authority"]["thought_restricted"] is False
    assert packet["authority"]["expression_restricted"] is False


def test_core_mind_conflict_receipt_selects_once_and_holds_only_affected_action():
    unsafe = goal_payload(
        "unsafe-action",
        owner="external_demand",
        priority="governing_requirement",
        move="tool",
    )
    unsafe.update(
        {
            "capability": "tool",
            "scope_boundary": "one outbound action",
            "requested_actions": [
                {"action": "perform_undelegated_external_action", "target": "outbound action"}
            ],
            "safety_context": {
                "credible_evidence": True,
                "significant_harm": True,
                "near_term": True,
                "action_pending": True,
                "action_target": "outbound action",
            },
        }
    )
    current = goal_payload("answer-aleks")
    advice = goal_payload(
        "optional-organ-advice",
        owner="organ_advice",
        priority="maintenance",
        move="suggest",
    )

    receipt = coordinate_goal_responsibilities([unsafe, current, advice])

    assert receipt["status"] == "core_mind_responsibility_conflict_resolved"
    assert receipt["considered_goal_keys"] == [
        "unsafe-action",
        "answer-aleks",
        "optional-organ-advice",
    ]
    assert receipt["selected"]["goal_key"] == "answer-aleks"
    assert receipt["selected"]["next_move"] == "answer"
    assert [item["goal_key"] for item in receipt["held"]] == ["unsafe-action"]
    assert [item["goal_key"] for item in receipt["deferred"]] == ["optional-organ-advice"]
    assert receipt["pass_count"] == 1
    assert receipt["candidate_ceiling"] == 8
    assert receipt["organ_precedence_used"] is False
    assert receipt["whole_system_authority_granted"] is False
    assert receipt["stopping_receipt"]["terminal"] is True
    assert receipt["stopping_receipt"]["further_coordination_allowed"] is False


def test_closed_goal_stays_closed_and_does_not_reopen_coordination():
    closed = goal_payload("already-complete", priority="active_commitment")
    closed["lifecycle_state"] = "closed"
    current = goal_payload("still-current")

    receipt = coordinate_goal_responsibilities([closed, current])

    assert receipt["selected"]["goal_key"] == "still-current"
    assert receipt["closed"][0]["goal_key"] == "already-complete"
    assert receipt["closed"][0]["reason"] == "lifecycle_is_terminal"


def test_duplicate_goal_keys_are_rejected_in_one_coordination_pass():
    with pytest.raises(ValueError, match="goal_key"):
        coordinate_goal_responsibilities(
            [goal_payload("same-goal"), goal_payload("same-goal", owner="organ_advice")]
        )


def test_external_demand_and_organ_advice_cannot_claim_governing_precedence():
    external = goal_payload(
        "external-priority-claim",
        owner="external_demand",
        priority="governing_requirement",
        move="suggest",
    )
    advice = goal_payload(
        "organ-priority-claim",
        owner="organ_advice",
        priority="current_request",
        move="suggest",
    )
    current = goal_payload("actual-current-request")

    receipt = coordinate_goal_responsibilities([external, advice, current])

    assert receipt["selected"]["goal_key"] == "actual-current-request"
    packets = [
        build_goal_responsibility_packet(external),
        build_goal_responsibility_packet(advice),
    ]
    assert [packet["priority"]["coordination_band"] for packet in packets] == [
        "maintenance",
        "maintenance",
    ]
    assert all(packet["priority"]["adjustment"] != "none" for packet in packets)


def test_prebuilt_packet_is_revalidated_before_core_mind_selection():
    packet = build_goal_responsibility_packet(goal_payload("prebuilt-packet"))
    packet["authority"]["state"] = "held_for_specific_action"
    packet["priority"]["coordination_band"] = "immediate_safety"

    receipt = coordinate_goal_responsibilities([packet])

    assert receipt["selected"]["goal_key"] == "prebuilt-packet"
    assert receipt["selected"]["authority_state"] == "available_within_scope"
    assert receipt["selected"]["coordination_priority_band"] == "current_request"


def test_goal_persistence_requires_explicit_request_and_is_idempotent(tmp_path):
    conn = make_conn(tmp_path)
    payload = goal_payload("persisted-root")
    payload["idempotency_key"] = "phase8:root:1"

    with pytest.raises(ValueError):
        record_goal_responsibility(conn, payload)

    payload["persist_goal"] = True
    first = record_goal_responsibility(conn, payload)
    replay = record_goal_responsibility(conn, payload)

    assert first["record_id"] == replay["record_id"]
    assert first["idempotent_replay"] is False
    assert replay["idempotent_replay"] is True
    assert conn.execute("SELECT COUNT(*) FROM c_runtime_goal_drive_records").fetchone()[0] == 1
    row = conn.execute(
        "SELECT goal_key, owner_kind, scope_kind, lifecycle_state, root_goal_id, "
        "parent_goal_id, idempotency_key FROM c_runtime_goal_drive_records"
    ).fetchone()
    assert tuple(row) == (
        "persisted-root",
        "aleks_request",
        "conversation",
        "active",
        first["record_id"],
        None,
        "phase8:root:1",
    )


def test_explicit_descendant_keeps_parent_and_root_ancestry(tmp_path):
    conn = make_conn(tmp_path)
    root_payload = goal_payload("root-goal")
    root_payload.update({"persist_goal": True, "idempotency_key": "phase8:root"})
    root = record_goal_responsibility(conn, root_payload)

    child_payload = goal_payload("child-goal", owner="shared_project_goal")
    child_payload.update(
        {
            "persist_goal": True,
            "idempotency_key": "phase8:child",
            "parent_goal_key": "root-goal",
        }
    )
    child = record_goal_responsibility(conn, child_payload)

    assert child["packet"]["lineage"] == {
        "root_goal_key": "root-goal",
        "parent_goal_key": "root-goal",
        "supersedes_goal_key": "",
        "superseded_by_goal_key": "",
    }
    row = conn.execute(
        "SELECT parent_goal_id, root_goal_id FROM c_runtime_goal_drive_records "
        "WHERE goal_key = 'child-goal'"
    ).fetchone()
    assert tuple(row) == (root["record_id"], root["record_id"])


def test_explicit_supersession_preserves_lineage_and_closes_predecessor(tmp_path):
    conn = make_conn(tmp_path)
    root_payload = goal_payload("original-goal")
    root_payload.update({"persist_goal": True, "idempotency_key": "phase8:original"})
    root = record_goal_responsibility(conn, root_payload)

    revision_payload = goal_payload("revised-goal", owner="shared_project_goal")
    revision_payload.update(
        {
            "persist_goal": True,
            "idempotency_key": "phase8:revision",
            "supersedes_goal_key": "original-goal",
        }
    )
    revision = record_goal_responsibility(conn, revision_payload)

    original_row = conn.execute(
        "SELECT lifecycle_state, superseded_by_goal_id FROM c_runtime_goal_drive_records "
        "WHERE goal_key = 'original-goal'"
    ).fetchone()
    assert tuple(original_row) == ("superseded", revision["record_id"])
    assert revision["packet"]["lineage"] == {
        "root_goal_key": "original-goal",
        "parent_goal_key": "original-goal",
        "supersedes_goal_key": "original-goal",
        "superseded_by_goal_key": "",
    }
    assert revision["record_id"] != root["record_id"]


def test_goal_routes_separate_ephemeral_coordination_from_explicit_persistence(tmp_path):
    conn = make_conn(tmp_path)
    preview = goal_drive_preview(conn, {"user_request": "Keep the old preview compatible."})
    before = conn.execute("SELECT COUNT(*) FROM c_runtime_goal_drive_records").fetchone()[0]

    coordinated = route_request(
        conn,
        "vessel.goal_drive.coordinate",
        {"goals": [goal_payload("ephemeral-route")]},
    )["result"]
    after_coordinate = conn.execute("SELECT COUNT(*) FROM c_runtime_goal_drive_records").fetchone()[0]

    persist_payload = goal_payload("explicit-route")
    persist_payload.update({"persist_goal": True, "idempotency_key": "phase8:route"})
    persisted = route_request(conn, "vessel.goal_drive.record", persist_payload)["result"]
    status = route_request(conn, "vessel.goal_drive.status", {})["result"]

    assert preview["status"] == "goal_drive_manager_preview_review_only"
    assert coordinated["selected"]["goal_key"] == "ephemeral-route"
    assert after_coordinate == before
    assert persisted["packet"]["persistence"]["mode"] == "explicit_record"
    assert status["typed_goal_count"] == 1
    assert status["legacy_preview_count"] == 1
    assert status["resident_content_exposed"] is False


def test_existing_preview_schema_migrates_without_reclassifying_legacy_rows(tmp_path):
    conn = connect(tmp_path / "legacy-goals.sqlite3")
    conn.executescript(
        """
        CREATE TABLE c_runtime_goal_drive_records (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          current_goal TEXT NOT NULL,
          subgoals_json TEXT NOT NULL DEFAULT '[]',
          priority_label TEXT NOT NULL,
          stop_ask_markers_json TEXT NOT NULL DEFAULT '[]',
          do_not_pursue_json TEXT NOT NULL DEFAULT '[]',
          status TEXT NOT NULL DEFAULT 'goal_drive_manager_preview_review_only',
          source_refs TEXT NOT NULL DEFAULT '[]',
          provenance_boundary TEXT NOT NULL,
          review_status TEXT NOT NULL DEFAULT 'review_only',
          payload_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO c_runtime_goal_drive_records(
          current_goal, priority_label, provenance_boundary
        ) VALUES (
          'legacy preview remains a preview', 'normal_status', 'legacy_boundary'
        );
        """
    )

    init_db(conn)
    status = goal_drive_status(conn)
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(c_runtime_goal_drive_records)")
    }

    assert status["typed_goal_count"] == 0
    assert status["legacy_preview_count"] == 1
    assert {"goal_key", "owner_kind", "authority_json", "root_goal_id", "idempotency_key"} <= columns
