from __future__ import annotations

import hashlib
import http.client
import json
from pathlib import Path
import threading

import pytest

from selene.curriculum_f2_group6 import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.sidecar import SeleneHandler, SeleneServer


ROUTE_STEM = "f2_fractions_numbers_equivalence"


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
            "authorization_basis": "Aleks authorized F2 Group 6 fractions as numbers, equivalence, comparison, and composition.",
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


def test_group6_has_five_source_bounded_magnitude_first_lessons():
    assert len(LESSONS) == 5
    assert SCOPE["bands"] == ["F2"] and SCOPE["group_keys"] == [GROUP_KEY]
    assert {lesson["concept_key"] for lesson in LESSONS} == {
        "curriculum_f2_unit_fraction_equal_whole_v1",
        "curriculum_f2_fraction_number_line_composition_v1",
        "curriculum_f2_fraction_equivalence_magnitude_v1",
        "curriculum_f2_fraction_comparison_strategy_v1",
        "curriculum_f2_fraction_compose_decompose_v1",
    }
    joined = " ".join(str(value) for lesson in LESSONS for value in lesson.values()).lower()
    assert "identify the whole" in joined
    assert "fractions greater than one" in joined
    assert "same magnitude" in joined
    assert "shared unit" in joined
    assert "general algorithms" in joined and "belong to group 7" in joined
    for lesson in LESSONS:
        assert lesson["application"] and lesson["limits"] and lesson["correction_response"]
        assert len(lesson["source_ids"]) == 2
        assert sum(ref.startswith("sha256:") for ref in lesson["source_refs"]) == 2
        assert any(ref.startswith("license:") for ref in lesson["source_refs"])


def test_group6_source_artifacts_match_pinned_checksums():
    root = Path(__file__).resolve().parents[1] / "local-data" / "curriculum_sources_20260719" / "sources"
    paths = {
        root / "core_knowledge_g3_math_unit5_fractions_teacher_guide" / "CKMath_G3U5_FractionsAsNumbers_TG_W2.pdf": "48819bde5ca8585a3370c2b99c3a082b03d968d9b05503cfa598a857c7c4df45",
        root / "core_knowledge_g4_math_unit2_fraction_equivalence_teacher_guide" / "CKMath_G4U2_FractionEquivalenceAndComparison_TG_W2.pdf": "7636a5fe8e12774c426a9b135089c58e5d9f843851664e634ce6414fcdb463c1",
    }
    for path, expected in paths.items():
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def test_group6_prepare_is_review_only_and_teach_requires_authorization(tmp_path):
    conn = _conn(tmp_path)
    prepared = route_request(conn, f"curriculum.foundation.prepare_{ROUTE_STEM}", {})["result"]
    rows = conn.execute("SELECT * FROM selene_comprehension_concepts ORDER BY id").fetchall()
    assert prepared["created_count"] == 5 and prepared["retained_count"] == 0
    assert all(
        row["state"] == "proposed_understanding" and row["chat_use_permission"] == "not_active_until_approved"
        for row in rows
    )
    assert all(json.loads(row["payload_json"])["source_metadata"]["curriculum_band"] == "F2" for row in rows)
    _locked(prepared)

    conn2 = _conn(tmp_path / "unauthorized")
    with pytest.raises(ValueError, match="activate this bounded F2 curriculum authorization"):
        route_request(conn2, f"curriculum.foundation.teach_{ROUTE_STEM}", {})


def test_group6_lifecycle_retains_and_is_idempotent(tmp_path):
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
    assert status["f2_sixth_group"]["retained_count"] == 5
    assert len(status["f2_groups"]) == 6 and len(status["groups"]) == 17
    assert all(
        row["state"] == "approved_knowledge_resource" and row["chat_use_permission"] == "available_as_knowledge_resource"
        for row in rows
    )
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["acquire_status"] == row["integrate_status"] == row["express_status"] == "complete" for row in rows)
    _locked(result)

    repeated = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
    assert repeated["retained_count"] == 0 and repeated["already_retained_count"] == 5 and repeated["held_count"] == 0


def test_group6_http_activation_and_preparation_routes(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(
            "POST",
            "/api/curriculum-authorization/activate-f2-fractions-numbers-equivalence",
            body=json.dumps(
                {
                    "aleks_authorized": True,
                    "authorization_actor": "Aleks",
                    "authorization_basis": "Aleks authorized F2 Group 6 from Cocoon.",
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
            "/api/curriculum-foundation/prepare-f2-fractions-numbers-equivalence",
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
