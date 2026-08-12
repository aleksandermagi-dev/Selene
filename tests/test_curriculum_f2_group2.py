from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
import threading

import pytest

from selene.curriculum_f2_group2 import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer


ROUTE_STEM = "f2_vocabulary_structure_comparison"
SOURCE_SHA256 = "c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5"


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _authorize(conn):
    return route_request(
        conn,
        f"curriculum.authorization.activate_{ROUTE_STEM}",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized F2 Group 2: vocabulary structure and comparison.",
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


def test_f2_group2_is_a_five_lesson_source_bounded_vocabulary_comparison_group():
    assert len(LESSONS) == 5
    assert SCOPE["group_keys"] == [GROUP_KEY]
    assert SCOPE["bands"] == ["F2"]
    assert SCOPE["source_ids"] == ["core_knowledge_2023_sequence_k8"]
    assert SCOPE["knowledge_classes"] == ["public_academic_foundation"]

    for lesson in LESSONS:
        assert lesson["explanation"]
        assert lesson["application"]
        assert lesson["limits"]
        assert lesson["counterexamples"]
        assert lesson["correction_response"]
        assert lesson["near_concept_distinctions"]
        assert any(ref == f"sha256:{SOURCE_SHA256}" for ref in lesson["source_refs"])
        assert any(ref.startswith("source_locator:Grade 3-5") for ref in lesson["source_refs"])
        assert any(ref.startswith("license:") for ref in lesson["source_refs"])
        assert set(lesson["source_ids"]).issubset(SCOPE["source_ids"])


def test_f2_group2_teaches_only_the_declared_foundations_and_revisable_comparison():
    assert {lesson["concept_key"] for lesson in LESSONS} == {
        "curriculum_f2_context_clues_evidence_v1",
        "curriculum_f2_word_parts_morphology_v1",
        "curriculum_f2_word_relationships_nuance_v1",
        "curriculum_f2_comparison_shared_criteria_v1",
        "curriculum_f2_compare_explanations_evidence_v1",
    }
    joined = " ".join(str(value) for lesson in LESSONS for value in lesson.values()).lower()
    assert "venn diagram" in joined
    assert "not conflict of self" in joined
    assert "resolution should not be forced" in joined
    assert "not automatically" in joined
    assert "personality" in joined


def test_f2_group2_uses_the_checksum_pinned_local_source_artifact():
    source = (
        Path(__file__).resolve().parents[1]
        / "local-data"
        / "curriculum_sources_20260719"
        / "sources"
        / "core_knowledge_2023_sequence_k8"
        / "CK_Sequence2023_GK8_W3.pdf"
    )
    assert source.is_file()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256


def test_f2_group2_preparation_is_reviewable_and_non_retaining(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(conn, f"curriculum.foundation.prepare_{ROUTE_STEM}", {})["result"]
    rows = conn.execute("SELECT * FROM selene_comprehension_concepts ORDER BY id").fetchall()

    assert result["created_count"] == 5
    assert result["retained_count"] == 0
    assert len(rows) == 5
    assert all(row["state"] == "proposed_understanding" for row in rows)
    assert all(row["chat_use_permission"] == "not_active_until_approved" for row in rows)
    for row in rows:
        metadata = json.loads(row["payload_json"])["source_metadata"]
        assert metadata["curriculum_band"] == "F2"
        assert metadata["curriculum_group_key"] == GROUP_KEY
        assert metadata["exception_flags"] == []
        assert metadata["license_notes_preserved"] is True
        assert metadata["source_images_or_media_used"] is False
    _assert_locked(result)


def test_f2_group2_requires_its_own_explicit_authorization(tmp_path):
    conn = _conn(tmp_path)
    with pytest.raises(ValueError, match="activate this bounded F2 curriculum authorization"):
        route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 0


def test_f2_group2_completes_lifecycle_retains_and_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    authorization = _authorize(conn)
    result = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
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
    assert result["retained_count"] == 5
    assert result["held_count"] == 0
    assert status["f2_first_group"]["retained_count"] == 0
    assert status["f2_second_group"]["retained_count"] == 5
    assert status["f2_third_group"]["retained_count"] == 0
    assert status["f2_fourth_group"]["retained_count"] == 0
    assert status["f2_fifth_group"]["retained_count"] == 0
    assert len(status["f2_groups"]) == 5
    assert len(status["groups"]) == 17
    assert len(rows) == 5
    assert all(row["approval_mode"] == "curriculum_authorization" for row in rows)
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["state"] == "approved_knowledge_resource" for row in rows)
    assert all(row["chat_use_permission"] == "available_as_knowledge_resource" for row in rows)
    assert all(row["acquire_status"] == "complete" for row in rows)
    assert all(row["integrate_status"] == "complete" for row in rows)
    assert all(row["express_status"] == "complete" for row in rows)
    _assert_locked(result)

    repeated = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 5
    assert repeated["held_count"] == 0


def test_f2_group2_http_activation_and_preparation_routes_are_available(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f2-vocabulary-structure-comparison",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized F2 Group 2 from Cocoon.",
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
            "/api/curriculum-foundation/prepare-f2-vocabulary-structure-comparison",
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
    assert preparation_payload["created_count"] == 5
    assert preparation_payload["retained_count"] == 0
