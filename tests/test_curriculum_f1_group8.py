from __future__ import annotations

import http.client
import json
import threading

import pytest

from selene.curriculum_f1_group8 import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
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
        "curriculum.authorization.activate_f1_history_evidence",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized this bounded F1 public-academic history and evidence foundation group.",
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


def test_group8_is_six_source_bounded_history_evidence_lessons():
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
        assert any(ref.startswith("sha256:") for ref in lesson["source_refs"])
        assert "license:CC-BY-NC-SA-4.0" in lesson["source_refs"]
        assert set(lesson["source_ids"]).issubset(SCOPE["source_ids"])


def test_group8_preserves_history_evidence_distinctions():
    by_key = {lesson["concept_key"]: lesson for lesson in LESSONS}
    chronology = by_key["curriculum_f1_chronology_relationships_v1"]
    sources = by_key["curriculum_f1_historical_sources_traces_v1"]
    accounts = by_key["curriculum_f1_differing_accounts_perspective_v1"]
    why = by_key["curriculum_f1_historical_why_multiple_causes_v1"]

    assert "not automatically the cause" in chronology["material"]
    assert "not the past itself" in sources["material"]
    assert "truth only a matter of preference" in " ".join(accounts["principles"])
    assert "several causes" in why["title"]
    assert "similarities and material differences" in " ".join(why["principles"])


def test_group8_preparation_is_reviewable_and_non_retaining(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(conn, "curriculum.foundation.prepare_f1_history_evidence", {})["result"]
    rows = conn.execute("SELECT * FROM selene_comprehension_concepts ORDER BY id").fetchall()

    assert result["created_count"] == 6
    assert result["retained_count"] == 0
    assert len(rows) == 6
    assert all(row["state"] == "proposed_understanding" for row in rows)
    assert all(row["chat_use_permission"] == "not_active_until_approved" for row in rows)
    for row in rows:
        metadata = json.loads(row["payload_json"])["source_metadata"]
        assert metadata["curriculum_group_key"] == GROUP_KEY
        assert metadata["exception_flags"] == []
        assert metadata["license_notes_preserved"] is True
        assert metadata["source_images_or_media_used"] is False
    _assert_locked(result)


def test_group8_requires_its_own_explicit_authorization(tmp_path):
    conn = _conn(tmp_path)
    with pytest.raises(ValueError, match="activate this bounded F1 curriculum authorization"):
        route_request(conn, "curriculum.foundation.teach_f1_history_evidence", {})
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 0


def test_group8_completes_lifecycle_retains_and_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    authorization = _authorize(conn)
    result = route_request(conn, "curriculum.foundation.teach_f1_history_evidence", {})["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    rows = conn.execute(
        """
        SELECT concept.*, lifecycle.approval_mode, lifecycle.authorization_id,
               lifecycle.acquire_status, lifecycle.integrate_status, lifecycle.express_status
        FROM selene_comprehension_concepts AS concept
        JOIN selene_teaching_lifecycles AS lifecycle ON lifecycle.concept_id = concept.id
        ORDER BY concept.id
        """
    ).fetchall()

    assert authorization["item"]["authorization_key"] == AUTHORIZATION_KEY
    assert result["status"] == "curriculum_foundation_group_taught"
    assert result["retained_count"] == 6
    assert result["held_count"] == 0
    assert status["eighth_group"]["retained_count"] == 6
    assert len(status["groups"]) == 8
    assert len(rows) == 6
    assert all(row["approval_mode"] == "curriculum_authorization" for row in rows)
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["state"] == "approved_knowledge_resource" for row in rows)
    assert all(row["chat_use_permission"] == "available_as_knowledge_resource" for row in rows)
    assert all(row["acquire_status"] == "complete" for row in rows)
    assert all(row["integrate_status"] == "complete" for row in rows)
    assert all(row["express_status"] == "complete" for row in rows)
    _assert_locked(result)

    repeated = route_request(conn, "curriculum.foundation.teach_f1_history_evidence", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 6
    assert repeated["held_count"] == 0


def test_group8_http_activation_and_preparation_routes_are_available(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f1-history-evidence",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized this bounded F1 history-and-evidence group from Cocoon.",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        auth_response = conn.getresponse()
        auth_payload = json.loads(auth_response.read().decode("utf-8"))
        conn.close()

        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(
            "POST",
            "/api/curriculum-foundation/prepare-f1-history-evidence",
            body="{}",
            headers={"Content-Type": "application/json"},
        )
        preparation_response = conn.getresponse()
        preparation_payload = json.loads(preparation_response.read().decode("utf-8"))
        conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert auth_response.status == 200
    assert auth_payload["item"]["authorization_key"] == AUTHORIZATION_KEY
    assert preparation_response.status == 200
    assert preparation_payload["created_count"] == 6
    _assert_locked(auth_payload)
    _assert_locked(preparation_payload)
