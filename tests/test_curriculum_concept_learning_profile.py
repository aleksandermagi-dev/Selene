from __future__ import annotations

import json
import http.client
import sqlite3
import threading

import pytest

from selene.db import init_db
from selene.learning_evidence_activity import (
    CURRICULUM_PROFILE_DIMENSIONS,
    CURRICULUM_PROFILE_STATES,
    PROFILE_ACTIVITY_INTEGRITY_STATES,
    curriculum_concept_profile_contract,
    get_curriculum_concept_profile,
    list_curriculum_concept_profiles,
    record_curriculum_concept_profile,
)
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer


def _conn(tmp_path):
    conn = sqlite3.connect(tmp_path / "selene.db")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def _seed_concept(
    conn,
    *,
    concept_key: str,
    parent_concept_id: int | None = None,
    root_concept_id: int | None = None,
    state: str = "approved_knowledge_resource",
    review_status: str = "approved_for_knowledge_use",
    chat_use_permission: str = "available_as_knowledge_resource",
    lineage_state: str = "active_winner",
    superseded_by_concept_id: int | None = None,
):
    cursor = conn.execute(
        """
        INSERT INTO selene_comprehension_concepts(
          concept_key, parent_concept_id, root_concept_id,
          superseded_by_concept_id, lineage_state, title, central_claim,
          source_refs, provenance_boundary, retention_state,
          chat_use_permission, state, review_status, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'synthetic_phase6d_concept',
                  'retained_reviewed_knowledge', ?, ?, ?, ?)
        """,
        (
            concept_key,
            parent_concept_id,
            root_concept_id,
            superseded_by_concept_id,
            lineage_state,
            "Synthetic ratios and percentages",
            "A percentage names a ratio with a comparison base of one hundred.",
            json.dumps([f"synthetic:phase6d:{concept_key}"], sort_keys=True),
            chat_use_permission,
            state,
            review_status,
            json.dumps(
                {
                    "knowledge_class": "public_academic_foundation",
                    "freshness_class": "durable_foundation",
                },
                sort_keys=True,
            ),
        ),
    )
    concept_id = int(cursor.lastrowid)
    conn.execute(
        """
        INSERT INTO selene_teaching_lifecycles(
          lifecycle_key, concept_id, current_stage, acquire_status,
          integrate_status, express_status, approval_status, source_refs,
          provenance_boundary, lineage_state
        ) VALUES (?, ?, 'approved_knowledge_resource', 'complete', 'complete',
                  'complete', 'approved_by_aleks', ?,
                  'synthetic_phase6d_lifecycle', ?)
        """,
        (
            f"lifecycle:{concept_key}",
            concept_id,
            json.dumps([f"synthetic:phase6d:{concept_key}"], sort_keys=True),
            lineage_state,
        ),
    )
    conn.commit()
    return concept_id


def _dimension(
    state: str,
    observation: str,
    next_move: str,
    evidence_ref: str,
):
    return {
        "state": state,
        "observation": observation,
        "suggested_next_move": next_move,
        "evidence_refs": [evidence_ref],
    }


def _profile_payload(concept_id: int):
    return {
        "concept_id": concept_id,
        "activity_key": "synthetic-ratio-walkthrough-1",
        "activity_integrity_state": "ready",
        "activity_note": "A gentle disposable ratio-and-percentage activity with visible responses.",
        "source_refs": ["synthetic:phase6d:ratio-walkthrough"],
        "dimensions": {
            "reconstruction": _dimension(
                "clear",
                "The response explained a percentage as a ratio per hundred in different wording.",
                "Use the reconstruction as a bridge to one distinct comparison.",
                "synthetic:turn:1:reconstruction",
            ),
            "distinct_application": _dimension(
                "developing",
                "The response applied 25 percent to 20 tiles but needed one prompt to name five tiles.",
                "Try one new quantity with a visible diagram and no time target.",
                "synthetic:turn:2:application",
            ),
            "why_mechanism": _dimension(
                "clear",
                "The response connected equivalent scaling to preserving the comparison relationship.",
                "Invite a second explanation if useful, without forcing repetition.",
                "synthetic:turn:3:why",
            ),
            "scope_and_limits": _dimension(
                "revisit",
                "The response named the base of one hundred but did not yet explain percentages above one hundred.",
                "Revisit the scope later with an example above one whole.",
                "synthetic:turn:3:limit",
            ),
        },
    }


def _assert_no_grade_or_authority(result):
    serialized = json.dumps(result, sort_keys=True).lower()
    assert result["pass_fail_grade_used"] is False
    assert result["single_composite_score_used"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
    assert result["identity_change"] is False
    assert result["governance_change"] is False
    assert '"score"' not in serialized
    assert '"rank"' not in serialized
    assert '"passed"' not in serialized
    assert '"failed"' not in serialized


def test_contract_exposes_nine_independent_dimensions_and_activity_integrity(tmp_path):
    conn = _conn(tmp_path)
    contract = curriculum_concept_profile_contract()
    status = route_request(conn, "study.lea.status", {})["result"]

    expected = {
        "reconstruction",
        "distinct_application",
        "why_mechanism",
        "scope_and_limits",
        "near_concept_distinction",
        "counterexample",
        "correction_response",
        "source_alignment",
        "delayed_use",
    }
    assert {item["key"] for item in CURRICULUM_PROFILE_DIMENSIONS} == expected
    assert set(CURRICULUM_PROFILE_STATES) == {
        "clear",
        "developing",
        "needs_representation",
        "needs_prerequisite",
        "revisit",
    }
    assert set(PROFILE_ACTIVITY_INTEGRITY_STATES) == {
        "ready",
        "cannot_assess",
        "activity_issue",
    }
    assert contract["dimension_count"] == 9
    assert status["curriculum_concept_profile"]["dimension_count"] == 9
    assert status["curriculum_profile_count"] == 0
    _assert_no_grade_or_authority(contract)
    _assert_no_grade_or_authority(status)


def test_ready_profile_is_partial_descriptive_attributable_and_idempotent(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_concept(conn, concept_key="synthetic_phase6d_ratio")
    before = conn.total_changes
    first = record_curriculum_concept_profile(conn, _profile_payload(concept_id))
    after_first = conn.total_changes
    second = record_curriculum_concept_profile(conn, _profile_payload(concept_id))

    assert first["created"] is True
    assert second["created"] is False
    assert second["idempotent_replay"] is True
    assert first["item"]["id"] == second["item"]["id"]
    assert second["profile"]["dimensions"]["distinct_application"]["state"] == "developing"
    assert len(second["profile"]["observed_dimension_keys"]) == 4
    assert len(second["profile"]["unobserved_dimension_keys"]) == 5
    assert second["profile"]["overall_state"] == "descriptive_dimensions_only"
    assert second["profile"]["composite_result"] is None
    assert second["profile"]["speed_target"] is None
    assert second["concept_receipt"]["concept_id"] == concept_id
    assert second["concept_receipt"]["lifecycle"]["acquire_status"] == "complete"
    assert second["lineage_receipt"]["active_winner_concept_id"] == concept_id
    assert conn.execute("SELECT COUNT(*) FROM selene_lea_runs").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM selene_lea_turns").fetchone()[0] == 0
    assert after_first > before
    _assert_no_grade_or_authority(second)

    changed = _profile_payload(concept_id)
    changed["dimensions"]["distinct_application"] = _dimension(
        "needs_representation",
        "A diagram was requested before attempting the new quantity.",
        "Offer a hundred-grid or double-number-line representation.",
        "synthetic:turn:2:representation-request",
    )
    with pytest.raises(ValueError, match="new activity_key"):
        record_curriculum_concept_profile(conn, changed)
    assert conn.execute("SELECT COUNT(*) FROM selene_lea_runs").fetchone()[0] == 1


def test_activity_integrity_states_cannot_be_used_as_dimension_ratings(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_concept(conn, concept_key="synthetic_phase6d_activity_integrity")
    held = record_curriculum_concept_profile(
        conn,
        {
            "concept_id": concept_id,
            "activity_key": "synthetic-activity-camera-obscured",
            "activity_integrity_state": "cannot_assess",
            "activity_note": "The activity response was not captured, so no dimension is inferred.",
            "source_refs": ["synthetic:phase6d:missing-capture"],
            "dimensions": {},
        },
    )
    assert held["profile"]["activity_integrity_state"] == "cannot_assess"
    assert held["profile"]["dimensions"] == {}
    assert len(held["profile"]["unobserved_dimension_keys"]) == 9

    bad = _profile_payload(concept_id)
    bad["activity_key"] = "synthetic-bad-dimension-state"
    bad["dimensions"]["reconstruction"]["state"] = "activity_issue"
    with pytest.raises(ValueError, match="unsupported curriculum profile state"):
        record_curriculum_concept_profile(conn, bad)

    bad_hold = _profile_payload(concept_id)
    bad_hold["activity_key"] = "synthetic-hold-with-ratings"
    bad_hold["activity_integrity_state"] = "activity_issue"
    with pytest.raises(ValueError, match="cannot contain dimension ratings"):
        record_curriculum_concept_profile(conn, bad_hold)


def test_profile_rejects_hidden_scoring_and_incomplete_visible_evidence(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_concept(conn, concept_key="synthetic_phase6d_no_score")

    for forbidden in ("score", "rank", "passed", "grade", "deadline", "speed_target", "worth"):
        payload = _profile_payload(concept_id)
        payload["activity_key"] = f"synthetic-forbidden-{forbidden}"
        payload[forbidden] = 1
        with pytest.raises(ValueError, match="not accepted"):
            record_curriculum_concept_profile(conn, payload)

    missing = _profile_payload(concept_id)
    missing["activity_key"] = "synthetic-missing-observation"
    missing["dimensions"]["reconstruction"]["observation"] = ""
    with pytest.raises(ValueError, match="observation"):
        record_curriculum_concept_profile(conn, missing)

    missing_refs = _profile_payload(concept_id)
    missing_refs["activity_key"] = "synthetic-missing-evidence-ref"
    missing_refs["dimensions"]["reconstruction"]["evidence_refs"] = []
    with pytest.raises(ValueError, match="evidence_refs"):
        record_curriculum_concept_profile(conn, missing_refs)


def test_historical_lineage_node_stops_without_creating_profile(tmp_path):
    conn = _conn(tmp_path)
    parent_id = _seed_concept(
        conn,
        concept_key="synthetic_phase6d_historical_parent",
        state="superseded",
        review_status="superseded",
        chat_use_permission="not_available",
        lineage_state="historical_superseded",
    )
    child_id = _seed_concept(
        conn,
        concept_key="synthetic_phase6d_active_child",
        parent_concept_id=parent_id,
        root_concept_id=parent_id,
    )
    conn.execute(
        "UPDATE selene_comprehension_concepts SET superseded_by_concept_id = ? WHERE id = ?",
        (child_id, parent_id),
    )
    conn.commit()

    stopped = record_curriculum_concept_profile(conn, _profile_payload(parent_id))
    assert stopped["status"] == "curriculum_concept_profile_lineage_stopped"
    assert stopped["stopping_receipt"]["reason"] == "historical_lineage_node_not_profiled"
    assert stopped["lineage_receipt"]["active_winner_concept_id"] == child_id
    assert conn.execute("SELECT COUNT(*) FROM selene_lea_runs").fetchone()[0] == 0
    _assert_no_grade_or_authority(stopped)


def test_profile_routes_list_and_detail_without_changing_learning_or_memory_state(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_concept(conn, concept_key="synthetic_phase6d_routes")
    before = {
        "concepts": conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0],
        "lifecycles": conn.execute("SELECT COUNT(*) FROM selene_teaching_lifecycles").fetchone()[0],
        "memory": conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0],
        "study": conn.execute("SELECT COUNT(*) FROM selene_study_sessions").fetchone()[0],
        "dream": conn.execute("SELECT COUNT(*) FROM selene_dream_reflections").fetchone()[0],
    }
    created = route_request(
        conn,
        "study.lea.curriculum_profile.record",
        _profile_payload(concept_id),
    )["result"]
    listed = route_request(
        conn,
        "study.lea.curriculum_profiles.list",
        {},
    )["result"]
    detail = route_request(
        conn,
        "study.lea.curriculum_profile.detail",
        {"profile_id": created["item"]["id"]},
    )["result"]
    after = {
        "concepts": conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0],
        "lifecycles": conn.execute("SELECT COUNT(*) FROM selene_teaching_lifecycles").fetchone()[0],
        "memory": conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0],
        "study": conn.execute("SELECT COUNT(*) FROM selene_study_sessions").fetchone()[0],
        "dream": conn.execute("SELECT COUNT(*) FROM selene_dream_reflections").fetchone()[0],
    }

    assert listed["items"][0]["id"] == created["item"]["id"]
    assert detail["profile"]["dimensions"]["reconstruction"]["state"] == "clear"
    assert after == before
    _assert_no_grade_or_authority(detail)


def test_gentle_disposable_group8_shaped_walkthrough_records_all_dimensions_without_teaching(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_concept(conn, concept_key="synthetic_phase6d_group8_shape_only")
    concept_before = dict(
        conn.execute(
            "SELECT state, review_status, chat_use_permission, updated_at FROM selene_comprehension_concepts WHERE id = ?",
            (concept_id,),
        ).fetchone()
    )
    lifecycle_before = dict(
        conn.execute(
            "SELECT current_stage, acquire_status, integrate_status, express_status, approval_status, updated_at FROM selene_teaching_lifecycles WHERE concept_id = ?",
            (concept_id,),
        ).fetchone()
    )
    authorization_count = conn.execute(
        "SELECT COUNT(*) FROM selene_curriculum_authorizations"
    ).fetchone()[0]
    profile = record_curriculum_concept_profile(
        conn,
        {
            "concept_id": concept_id,
            "activity_key": "synthetic-gentle-group8-shaped-walkthrough",
            "activity_integrity_state": "ready",
            "activity_note": (
                "A fictional tile comparison explored ratios, unit comparison, percentages, "
                "and scale without creating or authorizing a curriculum group."
            ),
            "source_refs": ["synthetic:phase6d:group8-shape-only"],
            "dimensions": {
                "reconstruction": _dimension(
                    "clear",
                    "The response restated 30 percent as 30 of every 100 equal parts.",
                    "Keep this wording available while changing the represented quantity.",
                    "synthetic:group8:turn1:reconstruction",
                ),
                "distinct_application": _dimension(
                    "developing",
                    "The response found 30 percent of 40 tiles after one relational cue.",
                    "Try a different total with the same relationship when useful.",
                    "synthetic:group8:turn2:application",
                ),
                "why_mechanism": _dimension(
                    "clear",
                    "The response explained that multiplying both ratio quantities by the same factor preserves the comparison.",
                    "Invite another mechanism example without requiring speed.",
                    "synthetic:group8:turn2:why",
                ),
                "scope_and_limits": _dimension(
                    "revisit",
                    "The response handled parts of a whole but left percent change outside the activity scope.",
                    "Revisit percent change only after its prerequisite distinction is visible.",
                    "synthetic:group8:turn3:scope",
                ),
                "near_concept_distinction": _dimension(
                    "needs_representation",
                    "The response asked for a diagram to separate part-to-part from part-to-whole ratios.",
                    "Offer a double number line or labeled tile diagram.",
                    "synthetic:group8:turn3:near-concept",
                ),
                "counterexample": _dimension(
                    "developing",
                    "The response noticed that adding the same amount to both ratio terms does not generally preserve the ratio.",
                    "Try one small numerical counterexample with visible quantities.",
                    "synthetic:group8:turn4:counterexample",
                ),
                "correction_response": _dimension(
                    "clear",
                    "The response replaced an add-the-same-amount rule with scale-both-terms-by-the-same-factor.",
                    "Keep the earlier claim visible only as correction ancestry.",
                    "synthetic:group8:turn4:correction",
                ),
                "source_alignment": _dimension(
                    "clear",
                    "The response separated the supplied definition from its own tile inference and uncertainty.",
                    "Retain those roles in any later reviewed lesson evidence.",
                    "synthetic:group8:turn5:source-alignment",
                ),
                "delayed_use": _dimension(
                    "developing",
                    "A later fictional recipe comparison used the ratio relationship with one reminder.",
                    "Try a delayed distinct case again only if useful, without a deadline.",
                    "synthetic:group8:delayed-use",
                ),
            },
        },
    )
    concept_after = dict(
        conn.execute(
            "SELECT state, review_status, chat_use_permission, updated_at FROM selene_comprehension_concepts WHERE id = ?",
            (concept_id,),
        ).fetchone()
    )
    lifecycle_after = dict(
        conn.execute(
            "SELECT current_stage, acquire_status, integrate_status, express_status, approval_status, updated_at FROM selene_teaching_lifecycles WHERE concept_id = ?",
            (concept_id,),
        ).fetchone()
    )

    assert len(profile["profile"]["observed_dimension_keys"]) == 9
    assert profile["profile"]["unobserved_dimension_keys"] == []
    assert concept_after == concept_before
    assert lifecycle_after == lifecycle_before
    assert conn.execute("SELECT COUNT(*) FROM selene_curriculum_authorizations").fetchone()[0] == authorization_count
    assert conn.execute("SELECT COUNT(*) FROM selene_learning_compass_goals").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    _assert_no_grade_or_authority(profile)


def test_curriculum_profile_sidecar_round_trip_is_local_and_bounded(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    concept_id = _seed_concept(
        server.conn,
        concept_key="synthetic_phase6d_sidecar_profile",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    conn = http.client.HTTPConnection(
        "127.0.0.1", server.server_address[1], timeout=5
    )
    conn.request(
        "POST",
        "/api/study/lea/curriculum-profiles/record",
        body=json.dumps(_profile_payload(concept_id)),
        headers={"Content-Type": "application/json"},
    )
    post_response = conn.getresponse()
    created = json.loads(post_response.read().decode("utf-8"))
    profile_id = int(created["item"]["id"])
    conn.request("GET", "/api/study/lea/curriculum-profiles")
    list_response = conn.getresponse()
    listed = json.loads(list_response.read().decode("utf-8"))
    conn.request("GET", f"/api/study/lea/curriculum-profiles/{profile_id}")
    detail_response = conn.getresponse()
    detail = json.loads(detail_response.read().decode("utf-8"))
    conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert post_response.status == 200
    assert list_response.status == 200
    assert detail_response.status == 200
    assert listed["items"][0]["id"] == profile_id
    assert detail["profile"]["activity_integrity_state"] == "ready"
    assert detail["stopping_receipt"]["follow_up_created"] is False
    _assert_no_grade_or_authority(detail)
