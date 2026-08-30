from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from selene.curriculum_f2_group4 import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
from selene.db import connect, init_db
from selene.module_router import route_request
from tests.curriculum_test_support import group_concept_rows, satisfy_group_prerequisites


ROUTE_STEM = "f2_multi_digit_arithmetic_operations"


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    satisfy_group_prerequisites(conn, GROUP_KEY)
    return conn


def _authorize(conn):
    return route_request(conn, f"curriculum.authorization.activate_{ROUTE_STEM}", {"aleks_authorized": True, "authorization_actor": "Aleks", "authorization_basis": "Aleks authorized F2 Group 4 multi-digit arithmetic."})["result"]


def _locked(result):
    for key in ("identity_change", "governance_change", "personality_change", "memory_write_active", "training_allowed", "lora_allowed", "autonomous_action_allowed", "self_replication_allowed"):
        assert result[key] is False


def test_group4_has_five_source_bounded_checked_arithmetic_lessons():
    assert len(LESSONS) == 5
    assert SCOPE["bands"] == ["F2"] and SCOPE["group_keys"] == [GROUP_KEY]
    assert {lesson["concept_key"] for lesson in LESSONS} == {
        "curriculum_f2_place_value_decomposition_equivalence_v1",
        "curriculum_f2_multi_digit_addition_regrouping_v1",
        "curriculum_f2_multi_digit_subtraction_regrouping_v1",
        "curriculum_f2_multiplication_decomposition_properties_v1",
        "curriculum_f2_division_quotient_remainder_inverse_v1",
    }
    joined = " ".join(str(value) for lesson in LESSONS for value in lesson.values()).lower()
    assert "do not substitute fluency for understanding" in joined
    assert "divisor × quotient + remainder" in joined
    for lesson in LESSONS:
        assert lesson["application"] and lesson["limits"] and lesson["correction_response"]
        assert any(ref.startswith("sha256:") for ref in lesson["source_refs"])
        assert any(ref.startswith("license:") for ref in lesson["source_refs"])


def test_group4_source_artifacts_match_pinned_checksums():
    root = Path(__file__).resolve().parents[1] / "local-data" / "curriculum_sources_20260719" / "sources"
    expected = {
        root / "core_knowledge_2023_sequence_k8" / "CK_Sequence2023_GK8_W3.pdf": "c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5",
        root / "core_knowledge_g2_math_unit1" / "CKMath_G2U1_AddingSubtractingAndWorkingWithData_Unit_Material_W2.zip": "eae00a4777672b66368780c4ba753c09eff5a18a29afd9bf5cbd55ed915457f7",
        root / "core_knowledge_g2_math_unit8" / "CKMath_G2U8_EqualGroups_Unit_Materials_W2.zip": "029b3123304c1c15676d647fe584700b9171a4c6f62d2070e5aed92f7deb3fd4",
    }
    for path, digest in expected.items():
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_group4_prepare_is_review_only_and_teach_requires_authorization(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    prepared = route_request(conn, f"curriculum.foundation.prepare_{ROUTE_STEM}", {})["result"]
    rows = group_concept_rows(conn, GROUP_KEY)
    assert prepared["created_count"] == 5 and prepared["retained_count"] == 0
    assert all(row["state"] == "proposed_understanding" and row["chat_use_permission"] == "not_active_until_approved" for row in rows)
    assert all(json.loads(row["payload_json"])["source_metadata"]["curriculum_band"] == "F2" for row in rows)
    _locked(prepared)
    conn2 = _conn(tmp_path / "unauthorized")
    with pytest.raises(ValueError, match="authorization_required"):
        route_request(conn2, f"curriculum.foundation.teach_{ROUTE_STEM}", {})


def test_group4_lifecycle_retains_and_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    authorization = _authorize(conn)
    result = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    rows = conn.execute("SELECT c.state,c.chat_use_permission,l.authorization_id,l.acquire_status,l.integrate_status,l.express_status FROM selene_comprehension_concepts c JOIN selene_teaching_lifecycles l ON l.concept_id=c.id").fetchall()
    assert authorization["item"]["authorization_key"] == AUTHORIZATION_KEY
    assert result["retained_count"] == 5 and result["held_count"] == 0
    assert status["f2_fourth_group"]["retained_count"] == 5
    assert status["f2_fifth_group"]["retained_count"] == 0
    assert status["f2_sixth_group"]["retained_count"] == 0
    assert status["f2_seventh_a_group"]["retained_count"] == 0
    assert len(status["f2_groups"]) == 8 and len(status["groups"]) == 17
    assert all(row["state"] == "approved_knowledge_resource" and row["chat_use_permission"] == "available_as_knowledge_resource" for row in rows)
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["acquire_status"] == row["integrate_status"] == row["express_status"] == "complete" for row in rows)
    _locked(result)
    repeated = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
    assert repeated["retained_count"] == 0 and repeated["already_retained_count"] == 5 and repeated["held_count"] == 0
