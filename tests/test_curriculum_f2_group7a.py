from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
import threading

import pytest

from selene.curriculum_f2_group7a import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer
from tests.curriculum_test_support import group_concept_rows, satisfy_group_prerequisites


ROUTE_STEM = "f2_fraction_operation_relationships"


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    satisfy_group_prerequisites(conn, GROUP_KEY)
    return conn


def _authorize(conn):
    return route_request(
        conn,
        f"curriculum.authorization.activate_{ROUTE_STEM}",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Aleks authorized bounded F2 Group 7A fraction-operation relationships.",
        },
    )["result"]


def _locked(result):
    for key in (
        "identity_change",
        "governance_change",
        "personality_change",
        "memory_write_active",
        "training_allowed",
        "lora_allowed",
        "autonomous_action_allowed",
        "self_replication_allowed",
    ):
        assert result[key] is False


def test_group7a_has_five_relationship_first_fraction_operation_lessons():
    assert len(LESSONS) == 5
    assert SCOPE["bands"] == ["F2"] and SCOPE["group_keys"] == [GROUP_KEY]
    assert {lesson["concept_key"] for lesson in LESSONS} == {
        "curriculum_f2_fraction_add_subtract_shared_unit_v1",
        "curriculum_f2_fraction_as_quotient_equal_sharing_v1",
        "curriculum_f2_whole_number_fraction_multiplication_v1",
        "curriculum_f2_fraction_by_fraction_area_scaling_v1",
        "curriculum_f2_unit_fraction_division_relationships_v1",
    }
    joined = " ".join(str(value) for lesson in LESSONS for value in lesson.values()).lower()
    assert "shared measurement unit" in joined
    assert "fraction as quotient" in joined
    assert "multiplication does not always make a number larger" in joined
    assert "division can ask either" in joined
    assert "general fraction-by-fraction division is deferred" in joined
    for lesson in LESSONS:
        assert lesson["application"] and lesson["limits"] and lesson["correction_response"]
        assert len(lesson["source_ids"]) == 4
        assert sum(ref.startswith("sha256:") for ref in lesson["source_refs"]) == 4
        assert any(ref.startswith("license:") for ref in lesson["source_refs"])


def test_group7a_source_artifacts_match_pinned_checksums():
    root = Path(__file__).resolve().parents[1] / "local-data" / "curriculum_sources_20260719" / "sources"
    paths = {
        root / "core_knowledge_g4_math_unit3_fraction_operations_teacher_guide" / "CKMath_G4U3_ExtendingOperationsToFractions_TG_W2.pdf": "8533241d98212fd527b9c1c57e19bdc575cdc86db5d460b8d6a6794ac8ffab7b",
        root / "core_knowledge_g5_math_unit2_fraction_quotient_multiplication_teacher_guide" / "CKMath_G5U2_FractionsAsQuotientsAndFractionMultiplication_TG_W2.pdf": "6ebb771fea9c5a99ef6da8a34adc0926855f7bdb3ebdd1b5e4e8d085cdcce0a5",
        root / "core_knowledge_g5_math_unit3_fraction_multiply_divide_teacher_guide" / "CKMath_G5U3_MultiplyingAndDividingFractions_TG_W2.pdf": "d1d5f3d1b5447228336163af139a70284f27e09e2bfe1f41a0acd26a19daf5e1",
        root / "core_knowledge_g5_math_unit6_unlike_fraction_operations_teacher_guide" / "CKMath_G5U6_MoreDecimalAndFractionOperations_TG_W2.pdf": "3835e997b90ca2501dec58fdf9af886c40aac5183b4319a5bdbba99861d7be79",
    }
    for path, expected in paths.items():
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_group7a_prepare_is_review_only_and_teach_requires_authorization(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    prepared = route_request(conn, f"curriculum.foundation.prepare_{ROUTE_STEM}", {})["result"]
    rows = group_concept_rows(conn, GROUP_KEY)
    assert prepared["created_count"] == 5 and prepared["retained_count"] == 0
    assert all(
        row["state"] == "proposed_understanding" and row["chat_use_permission"] == "not_active_until_approved"
        for row in rows
    )
    assert all(json.loads(row["payload_json"])["source_metadata"]["curriculum_band"] == "F2" for row in rows)
    _locked(prepared)

    conn2 = _conn(tmp_path / "unauthorized")
    with pytest.raises(ValueError, match="authorization_required"):
        route_request(conn2, f"curriculum.foundation.teach_{ROUTE_STEM}", {})


def test_group7a_lifecycle_retains_and_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    authorization = _authorize(conn)
    result = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    rows = conn.execute(
        "SELECT c.state,c.chat_use_permission,l.authorization_id,l.acquire_status,l.integrate_status,l.express_status "
        "FROM selene_comprehension_concepts c JOIN selene_teaching_lifecycles l ON l.concept_id=c.id"
    ).fetchall()
    assert authorization["item"]["authorization_key"] == AUTHORIZATION_KEY
    assert result["retained_count"] == 5 and result["held_count"] == 0
    assert status["f2_seventh_a_group"]["retained_count"] == 5
    assert len(status["f2_groups"]) == 8 and len(status["groups"]) == 17
    assert all(
        row["state"] == "approved_knowledge_resource" and row["chat_use_permission"] == "available_as_knowledge_resource"
        for row in rows
    )
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["acquire_status"] == row["integrate_status"] == row["express_status"] == "complete" for row in rows)
    _locked(result)

    repeated = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
    assert repeated["retained_count"] == 0 and repeated["already_retained_count"] == 5 and repeated["held_count"] == 0


def test_group7a_http_activation_and_preparation_routes(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    satisfy_group_prerequisites(server.conn, GROUP_KEY)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f2-fraction-operation-relationships",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized F2 Group 7A from Cocoon.",
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
            "/api/curriculum-foundation/prepare-f2-fraction-operation-relationships",
            body="{}",
            headers={"Content-Type": "application/json"},
        )
        prep_response = conn.getresponse()
        prep_payload = json.loads(prep_response.read().decode("utf-8"))
        conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert auth_response.status == 200
    assert auth_payload["item"]["authorization_key"] == AUTHORIZATION_KEY
    assert prep_response.status == 200
    assert prep_payload["created_count"] == 5 and prep_payload["retained_count"] == 0
