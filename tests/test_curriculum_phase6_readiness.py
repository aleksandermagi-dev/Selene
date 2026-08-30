from __future__ import annotations

import json

import pytest

from selene.curriculum_authorization import (
    CURRICULUM_GROUP_MANIFESTS,
    curriculum_group_readiness,
)
from selene.db import connect, init_db
from selene.module_router import route_request


GROUP_1 = "f1_science_inquiry_group_1"
GROUP_2 = "f1_language_number_group_2"


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _authorize_group_1(conn):
    return route_request(
        conn,
        "curriculum.authorization.activate_f1",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Synthetic bounded authorization for the Phase 6A group-one readiness test.",
        },
    )["result"]


def _authorize_group_2(conn):
    return route_request(
        conn,
        "curriculum.authorization.activate_f1_language_math",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Synthetic bounded authorization for the Phase 6A group-two readiness test.",
        },
    )["result"]


def _insert_approved_concepts(conn, concept_keys):
    for concept_key in concept_keys:
        conn.execute(
            """
            INSERT INTO selene_comprehension_concepts
            (concept_key, title, domain, central_claim, source_refs,
             provenance_boundary, retention_state, chat_use_permission,
             state, review_status, payload_json)
            VALUES (?, ?, 'synthetic.phase6a', ?, '["synthetic:test-only"]',
                    'synthetic disposable prerequisite fixture',
                    'retained_reviewed_knowledge', 'available_as_knowledge_resource',
                    'approved_knowledge_resource', 'approved', '{}')
            """,
            (concept_key, f"Synthetic completion for {concept_key}", concept_key),
        )
    conn.commit()


def test_status_exposes_one_typed_readiness_receipt_without_score_pressure(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "curriculum.authorization.status")["result"]
    first = status["first_group"]["readiness"]
    second = status["second_group"]["readiness"]

    assert status["readiness_states"] == [
        "ready",
        "needs_prerequisite",
        "source_review_required",
        "authorization_required",
        "complete",
    ]
    assert first["status"] == "authorization_required"
    assert second["status"] == "needs_prerequisite"
    assert second["unmet_predecessor_groups"] == [GROUP_1]
    assert second["unmet_concept_keys"] == CURRICULUM_GROUP_MANIFESTS[GROUP_1]["concept_keys"]
    assert second["source_acceptance_receipt"]["status"] == "accepted_for_bounded_teaching"
    assert second["source_acceptance_receipt"]["artifact_checksum_refs"]
    assert second["source_acceptance_receipt"]["source_shelf_record"].endswith(
        "SELENE_CURRICULUM_SOURCE_SHELF_20260719.md"
    )
    assert second["score"] is None and second["deadline"] is None
    assert second["replay_or_reteaching_performed"] is False


def test_active_authorization_cannot_bypass_prerequisites_or_create_candidate_text(tmp_path):
    conn = _conn(tmp_path)
    activated = _authorize_group_2(conn)

    assert activated["readiness"]["status"] == "needs_prerequisite"
    with pytest.raises(ValueError, match=r"needs_prerequisite; unmet groups=f1_science_inquiry_group_1"):
        route_request(conn, "curriculum.foundation.prepare_f1_language_math", {})
    with pytest.raises(ValueError, match=r"needs_prerequisite; unmet groups=f1_science_inquiry_group_1"):
        route_request(conn, "curriculum.foundation.teach_f1_language_math", {})

    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_teaching_lifecycles").fetchone()[0] == 0


def test_prepare_and_coverage_consume_the_same_ready_receipt(tmp_path):
    conn = _conn(tmp_path)
    _insert_approved_concepts(conn, CURRICULUM_GROUP_MANIFESTS[GROUP_1]["concept_keys"])
    _authorize_group_2(conn)

    before = curriculum_group_readiness(conn, GROUP_2)
    prepared = route_request(conn, "curriculum.foundation.prepare_f1_language_math", {})["result"]
    concept_id = prepared["created"][0]["concept_id"]
    coverage = route_request(conn, "curriculum.authorization.evaluate", {"concept_id": concept_id})["result"]

    assert before["status"] == "ready"
    assert prepared["readiness"]["status"] == "ready"
    assert coverage["readiness"]["status"] == "ready"
    assert coverage["exceptions"] == ["lifecycle_or_understanding_incomplete"]
    assert prepared["created_count"] == len(CURRICULUM_GROUP_MANIFESTS[GROUP_2]["concept_keys"])


def test_unaccepted_source_stops_before_content_enters_candidate_text(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _authorize_group_1(conn)
    source_receipt = dict(CURRICULUM_GROUP_MANIFESTS[GROUP_1]["source_acceptance_receipt"])
    source_receipt["status"] = "source_review_required"
    monkeypatch.setitem(
        CURRICULUM_GROUP_MANIFESTS[GROUP_1],
        "source_acceptance_receipt",
        source_receipt,
    )

    readiness = curriculum_group_readiness(conn, GROUP_1)
    assert readiness["status"] == "source_review_required"
    assert readiness["unmet_source_ids"] == source_receipt["source_ids"]
    with pytest.raises(ValueError, match="source_review_required; unaccepted sources="):
        route_request(conn, "curriculum.foundation.prepare_f1", {})
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 0


def test_existing_complete_group_migrates_descriptively_without_replay(tmp_path):
    conn = _conn(tmp_path)
    concept_keys = CURRICULUM_GROUP_MANIFESTS[GROUP_2]["concept_keys"]
    _insert_approved_concepts(conn, concept_keys)
    before = [dict(row) for row in conn.execute("SELECT * FROM selene_comprehension_concepts ORDER BY id")]

    readiness = curriculum_group_readiness(conn, GROUP_2)
    prepared = route_request(conn, "curriculum.foundation.prepare_f1_language_math", {})["result"]
    after = [dict(row) for row in conn.execute("SELECT * FROM selene_comprehension_concepts ORDER BY id")]

    assert readiness["status"] == "complete"
    assert readiness["descriptive_migration_only"] is True
    assert readiness["unmet_predecessor_groups"] == [GROUP_1]
    assert prepared["created_count"] == 0
    assert prepared["existing_count"] == len(concept_keys)
    assert prepared["readiness"]["status"] == "complete"
    assert json.dumps(before, sort_keys=True, default=str) == json.dumps(after, sort_keys=True, default=str)
