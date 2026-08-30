from __future__ import annotations

import json
import http.client
import threading

import pytest

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer
from tests.curriculum_test_support import satisfy_group_prerequisites


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["identity_change"] is False
    assert result["governance_change"] is False
    assert result["personality_change"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def _authorize(conn):
    return route_request(
        conn,
        "curriculum.authorization.activate_f1",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized the bounded F1 public-academic science and inquiry foundation group.",
        },
    )["result"]


def _authorize_language_math(conn):
    return route_request(
        conn,
        "curriculum.authorization.activate_f1_language_math",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized the bounded F1 language and number foundation group.",
        },
    )["result"]


def _authorize_operations_measurement(conn):
    return route_request(
        conn,
        "curriculum.authorization.activate_f1_operations_measurement",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized the bounded F1 operations, data, measurement, and time group.",
        },
    )["result"]


def _authorize_geometry_algorithms(conn):
    return route_request(
        conn,
        "curriculum.authorization.activate_f1_geometry_algorithms",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized the bounded F1 geometry, equal-shares, and algorithmic-foundations group.",
        },
    )["result"]


def test_authorization_is_explicit_bounded_visible_and_reversible(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="explicit Aleks decision"):
        route_request(
            conn,
            "curriculum.authorization.activate_f1",
            {
                "aleks_authorized": True,
                "authorization_actor": "someone_else",
                "authorization_basis": "A sufficiently long but unauthorized basis statement.",
            },
        )

    active = _authorize(conn)
    listed = route_request(conn, "curriculum.authorization.list")["result"]

    assert active["item"]["status"] == "active"
    assert active["item"]["authorized_by"] == "Aleks"
    assert active["item"]["scope"]["bands"] == ["F1"]
    assert active["item"]["scope"]["group_keys"] == ["f1_science_inquiry_group_1"]
    assert "health_legal_financial_or_safety" in active["item"]["exception_classes"]
    assert listed["items"][0]["authorization_key"] == "f1_science_research_foundations_v1"
    _assert_locked(active)

    revoked = route_request(
        conn,
        "curriculum.authorization.revoke",
        {
            "authorization_id": active["item"]["id"],
            "aleks_revoked": True,
            "authorization_actor": "Aleks",
        },
    )["result"]
    assert revoked["item"]["status"] == "revoked"
    assert revoked["item"]["revoked_at"]


def test_preparing_foundation_group_creates_reviewable_candidates_without_retention(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)

    result = route_request(conn, "curriculum.foundation.prepare_f1", {})["result"]
    concepts = route_request(conn, "comprehension.concepts.list", {"limit": 10})["result"]["items"]

    assert result["created_count"] == 4
    assert result["retained_count"] == 0
    assert len(concepts) == 4
    assert all(item["retention_state"] == "candidate_not_retained" for item in concepts)
    assert all(item["chat_use_permission"] == "not_active_until_approved" for item in concepts)
    assert all(item["source_refs"] for item in concepts)
    assert all(item["payload"]["source_metadata"]["curriculum_band"] == "F1" for item in concepts)
    _assert_locked(result)


def test_foundation_group_requires_active_authorization(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="authorization_required"):
        route_request(conn, "curriculum.foundation.teach_f1", {})

    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 0


def test_authorized_group_completes_lifecycle_and_retains_without_item_approval(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)

    result = route_request(conn, "curriculum.foundation.teach_f1", {})["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    lifecycles = route_request(conn, "teaching.lifecycle.list", {"limit": 10})["result"]["items"]

    assert result["status"] == "f1_foundation_group_taught"
    assert result["retained_count"] == 4
    assert result["held_count"] == 0
    assert status["first_group"]["retained_count"] == 4
    assert all(item["approval_status"] == "approved_under_curriculum_authorization" for item in lifecycles)
    assert all(item["approval_mode"] == "curriculum_authorization" for item in lifecycles)
    assert all(item["retention_state"] == "retained_reviewed_knowledge" for item in lifecycles)
    assert all(item["chat_use_permission"] == "available_as_knowledge_resource" for item in lifecycles)
    assert all(item["retention_gate"]["authorization_id"] for item in lifecycles)
    assert conn.execute("SELECT COUNT(*) FROM selene_curriculum_authorization_events WHERE action = 'knowledge_retained_under_authorization'").fetchone()[0] == 4
    _assert_locked(result)

    repeated = route_request(conn, "curriculum.foundation.teach_f1", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 4
    assert repeated["held_count"] == 0


def test_exception_flag_returns_candidate_to_cocoon_instead_of_using_authorization(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    prepared = route_request(conn, "curriculum.foundation.prepare_f1", {})["result"]
    concept_id = prepared["created"][0]["concept_id"]
    row = conn.execute("SELECT payload_json FROM selene_comprehension_concepts WHERE id = ?", (concept_id,)).fetchone()
    payload = json.loads(row["payload_json"])
    payload["source_metadata"]["exception_flags"] = ["outdated_or_time_sensitive"]
    conn.execute(
        "UPDATE selene_comprehension_concepts SET payload_json = ? WHERE id = ?",
        (json.dumps(payload, sort_keys=True), concept_id),
    )
    conn.commit()

    coverage = route_request(conn, "curriculum.authorization.evaluate", {"concept_id": concept_id})["result"]

    assert coverage["decision"] == "exception_review_required"
    assert "outdated_or_time_sensitive" in coverage["exceptions"]
    assert "lifecycle_or_understanding_incomplete" in coverage["exceptions"]
    assert coverage["individual_item_approval_required"] is True
    assert coverage["review_destination"] == "Cocoon Teaching / Lessons"
    _assert_locked(coverage)


def test_curriculum_authorization_http_routes_are_available_to_cocoon(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        status_conn.request("GET", "/api/curriculum-authorization/status")
        status_response = status_conn.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        status_conn.close()

        activate_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        activate_conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f1",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized this bounded F1 foundation group from Cocoon.",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        activate_response = activate_conn.getresponse()
        activate_payload = json.loads(activate_response.read().decode("utf-8"))
        activate_conn.close()

        language_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        language_conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f1-language-math",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized this bounded F1 language and number group from Cocoon.",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        language_response = language_conn.getresponse()
        language_payload = json.loads(language_response.read().decode("utf-8"))
        language_conn.close()

        operations_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        operations_conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f1-operations-measurement",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized this bounded F1 operations and measurement group from Cocoon.",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        operations_response = operations_conn.getresponse()
        operations_payload = json.loads(operations_response.read().decode("utf-8"))
        operations_conn.close()

        geometry_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        geometry_conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f1-geometry-algorithms",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized this bounded F1 geometry and algorithms group from Cocoon.",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        geometry_response = geometry_conn.getresponse()
        geometry_payload = json.loads(geometry_response.read().decode("utf-8"))
        geometry_conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert status_response.status == 200
    assert status_payload["status"] == "curriculum_authorization_ready"
    assert activate_response.status == 200
    assert activate_payload["status"] == "curriculum_authorization_active"
    assert activate_payload["item"]["authorized_by"] == "Aleks"
    assert language_response.status == 200
    assert language_payload["item"]["authorization_key"] == "f1_language_number_foundations_v1"
    assert operations_response.status == 200
    assert operations_payload["item"]["authorization_key"] == "f1_operations_data_measurement_time_v1"
    assert geometry_response.status == 200
    assert geometry_payload["item"]["authorization_key"] == "f1_geometry_shares_algorithms_v1"
    _assert_locked(activate_payload)


def test_language_number_group_uses_its_own_bounded_authorization(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    satisfy_group_prerequisites(conn, "f1_language_number_group_2")

    with pytest.raises(ValueError, match="authorization_required"):
        route_request(conn, "curriculum.foundation.teach_f1_language_math", {})

    authorization = _authorize_language_math(conn)
    result = route_request(conn, "curriculum.foundation.teach_f1_language_math", {})["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    rows = conn.execute(
        """
        SELECT concept.*, lifecycle.approval_mode, lifecycle.authorization_id
        FROM selene_comprehension_concepts AS concept
        JOIN selene_teaching_lifecycles AS lifecycle ON lifecycle.concept_id = concept.id
        WHERE concept.concept_key IN (
          'curriculum_f1_language_units_v1',
          'curriculum_f1_sentence_purposes_v1',
          'curriculum_f1_subject_action_reference_v1',
          'curriculum_f1_sequence_reconstruction_v1',
          'curriculum_f1_counting_cardinality_v1',
          'curriculum_f1_quantity_comparison_v1',
          'curriculum_f1_base_ten_place_value_v1',
          'curriculum_f1_number_representation_comparison_v1'
        )
        """
    ).fetchall()

    assert authorization["item"]["authorization_key"] == "f1_language_number_foundations_v1"
    assert authorization["item"]["scope"]["group_keys"] == ["f1_language_number_group_2"]
    assert result["status"] == "curriculum_foundation_group_taught"
    assert result["retained_count"] == 8
    assert result["held_count"] == 0
    assert status["second_group"]["prepared_count"] == 8
    assert status["second_group"]["retained_count"] == 8
    assert len(rows) == 8
    assert all(row["approval_mode"] == "curriculum_authorization" for row in rows)
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["state"] == "approved_knowledge_resource" for row in rows)
    assert all(row["chat_use_permission"] == "available_as_knowledge_resource" for row in rows)
    _assert_locked(result)

    repeated = route_request(conn, "curriculum.foundation.teach_f1_language_math", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 8
    assert repeated["held_count"] == 0


def test_operations_measurement_group_uses_its_own_bounded_authorization(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    _authorize_language_math(conn)
    satisfy_group_prerequisites(conn, "f1_operations_measurement_group_3")

    with pytest.raises(ValueError, match="authorization_required"):
        route_request(conn, "curriculum.foundation.teach_f1_operations_measurement", {})

    authorization = _authorize_operations_measurement(conn)
    result = route_request(conn, "curriculum.foundation.teach_f1_operations_measurement", {})["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    retained_ids = [item["concept_id"] for item in result["retained"]]
    rows = conn.execute(
        f"SELECT concept.*, lifecycle.approval_mode, lifecycle.authorization_id FROM selene_comprehension_concepts AS concept JOIN selene_teaching_lifecycles AS lifecycle ON lifecycle.concept_id = concept.id WHERE concept.id IN ({','.join('?' for _ in retained_ids)})",
        retained_ids,
    ).fetchall()

    assert authorization["item"]["scope"]["group_keys"] == ["f1_operations_measurement_group_3"]
    assert result["status"] == "curriculum_foundation_group_taught"
    assert result["retained_count"] == 8
    assert result["held_count"] == 0
    assert status["third_group"]["prepared_count"] == 8
    assert status["third_group"]["retained_count"] == 8
    assert len(rows) == 8
    assert all(row["approval_mode"] == "curriculum_authorization" for row in rows)
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["chat_use_permission"] == "available_as_knowledge_resource" for row in rows)
    _assert_locked(result)

    repeated = route_request(conn, "curriculum.foundation.teach_f1_operations_measurement", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 8
    assert repeated["held_count"] == 0


def test_geometry_algorithms_group_is_source_bounded_and_grants_no_execution_authority(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    _authorize_language_math(conn)
    _authorize_operations_measurement(conn)
    satisfy_group_prerequisites(conn, "f1_geometry_shares_algorithms_group_4")

    with pytest.raises(ValueError, match="authorization_required"):
        route_request(conn, "curriculum.foundation.teach_f1_geometry_algorithms", {})

    authorization = _authorize_geometry_algorithms(conn)
    result = route_request(conn, "curriculum.foundation.teach_f1_geometry_algorithms", {})["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    retained_ids = [item["concept_id"] for item in result["retained"]]
    rows = conn.execute(
        f"SELECT concept.*, lifecycle.approval_mode, lifecycle.authorization_id FROM selene_comprehension_concepts AS concept JOIN selene_teaching_lifecycles AS lifecycle ON lifecycle.concept_id = concept.id WHERE concept.id IN ({','.join('?' for _ in retained_ids)})",
        retained_ids,
    ).fetchall()
    algorithm_row = conn.execute(
        "SELECT source_refs, payload_json FROM selene_comprehension_concepts WHERE concept_key = 'curriculum_f1_ordered_algorithm_v1'"
    ).fetchone()
    algorithm_refs = json.loads(algorithm_row["source_refs"])
    algorithm_payload = json.loads(algorithm_row["payload_json"])

    assert authorization["item"]["scope"]["group_keys"] == ["f1_geometry_shares_algorithms_group_4"]
    assert authorization["item"]["scope"]["source_ids"] == [
        "core_knowledge_2023_sequence_k8",
        "core_knowledge_g1_math_unit7",
        "code_org_csf_curriculum_guide",
    ]
    assert result["status"] == "curriculum_foundation_group_taught"
    assert result["retained_count"] == 8
    assert result["held_count"] == 0
    assert status["fourth_group"]["prepared_count"] == 8
    assert status["fourth_group"]["retained_count"] == 8
    assert len(rows) == 8
    assert all(row["approval_mode"] == "curriculum_authorization" for row in rows)
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["chat_use_permission"] == "available_as_knowledge_resource" for row in rows)
    assert "curriculum_source:code_org_csf_curriculum_guide" in algorithm_refs
    assert algorithm_payload["source_metadata"]["source_images_or_media_used"] is False
    _assert_locked(result)

    repeated = route_request(conn, "curriculum.foundation.teach_f1_geometry_algorithms", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 8
    assert repeated["held_count"] == 0
