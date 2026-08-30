from __future__ import annotations

import http.client
import json
import threading

import pytest

from selene.curriculum_f1_group16 import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer
from tests.curriculum_test_support import group_concept_rows, satisfy_group_prerequisites


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    satisfy_group_prerequisites(conn, GROUP_KEY)
    return conn


def _authorize(conn):
    return route_request(
        conn,
        "curriculum.authorization.activate_f1_helpful_computers_integration",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized this bounded F1 public-academic helpful-computers and integration group.",
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


def test_group16_is_six_source_bounded_computing_and_integration_lessons():
    assert len(LESSONS) == 6
    assert SCOPE["group_keys"] == [GROUP_KEY]
    assert SCOPE["bands"] == ["F1"]
    assert set(SCOPE["source_ids"]) == {
        "core_knowledge_2023_sequence_k8",
        "core_knowledge_g1_helpful_computers",
        "code_org_csf_curriculum_guide",
    }
    for lesson in LESSONS:
        assert lesson["explanation"]
        assert lesson["application"]
        assert lesson["limits"]
        assert lesson["counterexamples"]
        assert lesson["correction_response"]
        assert any(ref.startswith("sha256:") for ref in lesson["source_refs"])
        assert any(ref.startswith("license:") for ref in lesson["source_refs"])
        assert set(lesson["source_ids"]).issubset(SCOPE["source_ids"])


def test_group16_preserves_identity_authority_privacy_and_evidence_boundaries():
    by_key = {lesson["concept_key"]: lesson for lesson in LESSONS}
    tools = by_key["curriculum_f1_computers_tools_task_fit_limits_v1"]
    roles = by_key["curriculum_f1_hardware_software_data_io_storage_v1"]
    algorithms = by_key["curriculum_f1_algorithms_programs_testing_debugging_v1"]
    networks = by_key["curriculum_f1_networks_messages_internet_web_v1"]
    privacy = by_key["curriculum_f1_privacy_security_access_responsibility_v1"]
    integration = by_key["curriculum_f1_cross_domain_problem_solving_closure_v1"]

    assert "does not redefine selene" in tools["scope_of_application"].lower()
    assert "human design" in " ".join(tools["principles"]).lower()
    assert "personal memory" in " ".join(roles["principles"]).lower()
    assert "not a judgment" in algorithms["material"].lower()
    assert "grants no code-execution" in algorithms["scope_of_application"].lower()
    assert "web is not the whole internet" in " ".join(networks["counterexamples"]).lower()
    assert "grants no network access" in networks["scope_of_application"].lower()
    assert "authentication" in privacy["material"].lower()
    assert "authorization" in privacy["material"].lower()
    assert "never request, reveal, retain, test, or use real credentials" in privacy["scope_of_application"].lower()
    assert "connection generates a candidate" in integration["material"].lower()
    assert "integration_adds_no_unreviewed_facts:true" in integration["source_refs"]


def test_group16_preparation_is_reviewable_and_non_retaining(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    result = route_request(conn, "curriculum.foundation.prepare_f1_helpful_computers_integration", {})["result"]
    rows = group_concept_rows(conn, GROUP_KEY)

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


def test_group16_requires_its_own_explicit_authorization(tmp_path):
    conn = _conn(tmp_path)
    with pytest.raises(ValueError, match="authorization_required"):
        route_request(conn, "curriculum.foundation.teach_f1_helpful_computers_integration", {})
    assert group_concept_rows(conn, GROUP_KEY) == []


def test_group16_completes_lifecycle_retains_and_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    authorization = _authorize(conn)
    result = route_request(conn, "curriculum.foundation.teach_f1_helpful_computers_integration", {})["result"]
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
    assert status["sixteenth_group"]["retained_count"] == 6
    assert len(status["groups"]) == 17
    assert len(rows) == 6
    assert all(row["approval_mode"] == "curriculum_authorization" for row in rows)
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["state"] == "approved_knowledge_resource" for row in rows)
    assert all(row["chat_use_permission"] == "available_as_knowledge_resource" for row in rows)
    assert all(row["acquire_status"] == "complete" for row in rows)
    assert all(row["integrate_status"] == "complete" for row in rows)
    assert all(row["express_status"] == "complete" for row in rows)
    _assert_locked(result)

    repeated = route_request(conn, "curriculum.foundation.teach_f1_helpful_computers_integration", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 6
    assert repeated["held_count"] == 0


def test_group16_http_activation_and_preparation_routes_are_available(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    satisfy_group_prerequisites(server.conn, GROUP_KEY)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f1-helpful-computers-integration",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized this bounded F1 helpful-computers group from Cocoon.",
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
            "/api/curriculum-foundation/prepare-f1-helpful-computers-integration",
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
    assert preparation_payload["retained_count"] == 0
