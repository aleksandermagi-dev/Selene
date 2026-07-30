from __future__ import annotations

import http.client
import json
import threading

import pytest

from selene.curriculum_f1_group7 import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _authorize(conn):
    return route_request(
        conn,
        "curriculum.authorization.activate_f1_community_rules",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized the bounded F1 public-academic community, rules, and civic-reasoning foundation group.",
        },
    )["result"]


def _assert_locked(result):
    assert result["identity_change"] is False
    assert result["governance_change"] is False
    assert result["personality_change"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def test_group7_is_six_ordered_source_bounded_lessons_with_why_and_limits():
    assert len(LESSONS) == 6
    assert SCOPE["group_keys"] == [GROUP_KEY]
    assert SCOPE["bands"] == ["F1"]
    assert set(SCOPE["source_ids"]) == {
        "core_knowledge_2023_sequence_k8",
        "core_knowledge_g1_civics",
    }
    for lesson in LESSONS:
        assert lesson["explanation"]
        assert lesson["application"]
        assert lesson["limits"]
        assert lesson["counterexamples"]
        assert lesson["correction_response"]
        assert lesson["source_refs"]
        assert any(ref.startswith("sha256:") for ref in lesson["source_refs"])
        assert "license:CC-BY-NC-SA-4.0" in lesson["source_refs"]
        assert set(lesson["source_ids"]).issubset(set(SCOPE["source_ids"]))


def test_group7_preserves_people_rules_law_and_fairness_distinctions():
    community = next(
        lesson
        for lesson in LESSONS
        if lesson["concept_key"] == "curriculum_f1_community_membership_scale_v1"
    )
    cooperation = next(
        lesson
        for lesson in LESSONS
        if lesson["concept_key"] == "curriculum_f1_cooperation_roles_boundaries_v1"
    )
    authority = next(
        lesson
        for lesson in LESSONS
        if lesson["concept_key"] == "curriculum_f1_rule_law_custom_distinction_v1"
    )
    fairness = next(
        lesson
        for lesson in LESSONS
        if lesson["concept_key"] == "curriculum_f1_fairness_consistent_relevance_v1"
    )

    assert "does not define the whole individual" in " ".join(
        community["principles"]
    )
    assert "does not mean uncritical compliance" in cooperation[
        "near_concept_distinctions"
    ][0]
    assert "not every rule is a law" in " ".join(authority["principles"]).lower()
    assert "not legal advice" in " ".join(authority["limits"]).lower()
    assert "identical treatment is not always fair" in fairness["material"]
    assert all("American identity" not in lesson["material"] for lesson in LESSONS)


def test_group7_preparation_is_reviewable_and_non_retaining(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(
        conn, "curriculum.foundation.prepare_f1_community_rules", {}
    )["result"]
    rows = conn.execute(
        "SELECT * FROM selene_comprehension_concepts ORDER BY id"
    ).fetchall()

    assert result["created_count"] == 6
    assert result["retained_count"] == 0
    assert len(rows) == 6
    assert all(row["state"] == "proposed_understanding" for row in rows)
    assert all(
        row["chat_use_permission"] == "not_active_until_approved" for row in rows
    )
    for row in rows:
        metadata = json.loads(row["payload_json"])["source_metadata"]
        assert metadata["curriculum_group_key"] == GROUP_KEY
        assert metadata["exception_flags"] == []
        assert metadata["license_notes_preserved"] is True
        assert metadata["source_images_or_media_used"] is False
    _assert_locked(result)


def test_group7_requires_its_own_explicit_authorization(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(
        ValueError, match="activate this bounded F1 curriculum authorization"
    ):
        route_request(conn, "curriculum.foundation.teach_f1_community_rules", {})

    assert (
        conn.execute(
            "SELECT COUNT(*) FROM selene_comprehension_concepts"
        ).fetchone()[0]
        == 0
    )


def test_group7_completes_lifecycle_retains_and_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    authorization = _authorize(conn)

    result = route_request(
        conn, "curriculum.foundation.teach_f1_community_rules", {}
    )["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    rows = conn.execute(
        """
        SELECT concept.*, lifecycle.approval_mode, lifecycle.authorization_id,
               lifecycle.acquire_status, lifecycle.integrate_status,
               lifecycle.express_status
        FROM selene_comprehension_concepts AS concept
        JOIN selene_teaching_lifecycles AS lifecycle
          ON lifecycle.concept_id = concept.id
        ORDER BY concept.id
        """
    ).fetchall()

    assert authorization["item"]["authorization_key"] == AUTHORIZATION_KEY
    assert authorization["item"]["scope"]["group_keys"] == [GROUP_KEY]
    assert result["status"] == "curriculum_foundation_group_taught"
    assert result["retained_count"] == 6
    assert result["held_count"] == 0
    assert status["seventh_group"]["prepared_count"] == 6
    assert status["seventh_group"]["retained_count"] == 6
    assert len(status["groups"]) == 7
    assert len(rows) == 6
    assert all(
        row["approval_mode"] == "curriculum_authorization" for row in rows
    )
    assert all(
        row["authorization_id"] == authorization["item"]["id"] for row in rows
    )
    assert all(row["state"] == "approved_knowledge_resource" for row in rows)
    assert all(
        row["chat_use_permission"] == "available_as_knowledge_resource"
        for row in rows
    )
    assert all(row["acquire_status"] == "complete" for row in rows)
    assert all(row["integrate_status"] == "complete" for row in rows)
    assert all(row["express_status"] == "complete" for row in rows)
    _assert_locked(result)

    repeated = route_request(
        conn, "curriculum.foundation.teach_f1_community_rules", {}
    )["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 6
    assert repeated["held_count"] == 0


def test_group7_http_activation_and_preparation_routes_are_available(tmp_path):
    server = SeleneServer(
        ("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3"
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f1-community-rules",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized this bounded F1 community-and-rules group from Cocoon.",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        authorization_response = conn.getresponse()
        authorization_payload = json.loads(
            authorization_response.read().decode("utf-8")
        )
        conn.close()

        conn = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5
        )
        conn.request(
            "POST",
            "/api/curriculum-foundation/prepare-f1-community-rules",
            body="{}",
            headers={"Content-Type": "application/json"},
        )
        preparation_response = conn.getresponse()
        preparation_payload = json.loads(
            preparation_response.read().decode("utf-8")
        )
        conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert authorization_response.status == 200
    assert authorization_payload["item"]["authorization_key"] == AUTHORIZATION_KEY
    assert preparation_response.status == 200
    assert preparation_payload["created_count"] == 6
    _assert_locked(authorization_payload)
    _assert_locked(preparation_payload)
