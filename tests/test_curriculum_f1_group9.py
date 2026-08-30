from __future__ import annotations

import http.client
import json
import threading

import pytest

from selene.curriculum_f1_group9 import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
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
        "curriculum.authorization.activate_f1_materials_change_motion",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized this bounded F1 public-academic materials, change, and motion group.",
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


def test_group9_is_six_source_bounded_materials_change_motion_lessons():
    assert len(LESSONS) == 6
    assert SCOPE["group_keys"] == [GROUP_KEY]
    assert SCOPE["bands"] == ["F1"]
    assert set(SCOPE["source_ids"]) == {
        "core_knowledge_2023_sequence_k8",
        "core_knowledge_g1_science_literacy",
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


def test_group9_preserves_material_change_and_motion_distinctions():
    by_key = {lesson["concept_key"]: lesson for lesson in LESSONS}
    objects = by_key["curriculum_f1_objects_materials_properties_v1"]
    states = by_key["curriculum_f1_solids_liquids_shape_behavior_v1"]
    change = by_key["curriculum_f1_change_stability_over_time_v1"]
    motion = by_key["curriculum_f1_motion_position_speed_v1"]

    assert "object" in objects["near_concept_distinctions"][0].lower()
    assert "solidity is not the same as hardness" in states["comparisons"][0].lower()
    assert "cause" in change["near_concept_distinctions"][0].lower()
    assert "relative to a stated reference" in motion["material"]
    assert "force" in " ".join(motion["limits"]).lower()


def test_group9_preparation_is_reviewable_and_non_retaining(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    result = route_request(conn, "curriculum.foundation.prepare_f1_materials_change_motion", {})["result"]
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


def test_group9_requires_its_own_explicit_authorization(tmp_path):
    conn = _conn(tmp_path)
    with pytest.raises(ValueError, match="authorization_required"):
        route_request(conn, "curriculum.foundation.teach_f1_materials_change_motion", {})
    assert group_concept_rows(conn, GROUP_KEY) == []


def test_group9_completes_lifecycle_retains_and_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    authorization = _authorize(conn)
    result = route_request(conn, "curriculum.foundation.teach_f1_materials_change_motion", {})["result"]
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
    assert status["ninth_group"]["retained_count"] == 6
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

    repeated = route_request(conn, "curriculum.foundation.teach_f1_materials_change_motion", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 6
    assert repeated["held_count"] == 0


def test_group9_http_activation_and_preparation_routes_are_available(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    satisfy_group_prerequisites(server.conn, GROUP_KEY)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f1-materials-change-motion",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized this bounded F1 materials-change-motion group from Cocoon.",
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
            "/api/curriculum-foundation/prepare-f1-materials-change-motion",
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
