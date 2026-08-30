from __future__ import annotations

import json

import pytest

from selene.curriculum_coding_group1 import AUTHORIZATION_KEY, GROUP_KEY, LESSONS, SCOPE
from selene.db import connect, init_db
from selene.local_code_inspection import inspect_local_code, local_code_inspection_status
from selene.module_router import route_request
from tests.curriculum_test_support import group_concept_rows, satisfy_group_prerequisites


ROUTE_STEM = "coding_computational_thinking_code_reading"


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
            "authorization_basis": "Aleks authorized Coding Group 1 computational thinking and bounded code-reading knowledge without execution authority.",
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


def test_coding_group1_has_five_ordered_source_bounded_lessons():
    assert len(LESSONS) == 5
    assert SCOPE["bands"] == ["CODING-1"]
    assert SCOPE["group_keys"] == [GROUP_KEY]
    assert SCOPE["knowledge_classes"] == ["public_academic_foundation"]
    assert "code execution" in SCOPE["authority_boundary"].lower()
    assert {lesson["concept_key"] for lesson in LESSONS} == {
        "coding_problem_decomposition_input_process_output_v1",
        "coding_names_values_binding_and_state_v1",
        "coding_sequence_condition_iteration_trace_v1",
        "coding_function_contract_and_data_flow_v1",
        "coding_static_inspection_observation_inference_runtime_v1",
    }
    for lesson in LESSONS:
        assert lesson["domain"] == "curriculum.coding.computational_thinking_and_code_reading"
        assert lesson["application"] and lesson["counterexamples"] and lesson["correction_response"]
        assert any(ref == "attribution:Python Software Foundation" for ref in lesson["source_refs"])
        assert any(ref == "license:Python-Software-Foundation-License-Version-2" for ref in lesson["source_refs"])
        assert any(ref == "code_examples_license:Zero-Clause-BSD" for ref in lesson["source_refs"])
        assert any(ref.startswith("https://docs.python.org/") for ref in lesson["source_refs"])
        assert "boundary:no_self_modification_self_replication_or_unapproved_code_action" in lesson["source_refs"]


def test_coding_group1_teaches_reasoning_and_reading_not_execution_authority():
    joined = " ".join(str(value) for lesson in LESSONS for value in lesson.values()).lower()
    assert "rebinding changes which object a name refers to" in joined
    assert "reading both sides of an `if`" in joined
    assert "function name as a clue, not evidence" in joined
    assert "runtime verification" in joined
    assert "code was not run" in joined
    assert "no_self_modification_self_replication_or_unapproved_code_action" in joined


def test_coding_group1_prepare_is_review_only_and_teach_requires_explicit_authorization(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    prepared = route_request(conn, f"curriculum.foundation.prepare_{ROUTE_STEM}", {})["result"]
    rows = group_concept_rows(conn, GROUP_KEY)

    assert prepared["created_count"] == 5
    assert prepared["retained_count"] == 0
    assert all(row["state"] == "proposed_understanding" for row in rows)
    assert all(row["chat_use_permission"] == "not_active_until_approved" for row in rows)
    assert all(json.loads(row["payload_json"])["source_metadata"]["curriculum_band"] == "CODING-1" for row in rows)
    _locked(prepared)

    unauthorized = _conn(tmp_path / "unauthorized")
    with pytest.raises(ValueError, match="authorization_required"):
        route_request(unauthorized, f"curriculum.foundation.teach_{ROUTE_STEM}", {})


def test_coding_group1_lifecycle_retains_idempotently_without_memory_or_action_authority(tmp_path):
    conn = _conn(tmp_path)
    memory_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]
    authorization = _authorize(conn)
    result = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
    status = route_request(conn, "curriculum.authorization.status")["result"]
    rows = conn.execute(
        """SELECT c.state,c.chat_use_permission,l.authorization_id,l.acquire_status,l.integrate_status,l.express_status
           FROM selene_comprehension_concepts c
           JOIN selene_teaching_lifecycles l ON l.concept_id=c.id
           WHERE c.domain='curriculum.coding.computational_thinking_and_code_reading'"""
    ).fetchall()

    assert authorization["item"]["authorization_key"] == AUTHORIZATION_KEY
    assert authorization["item"]["scope"]["bands"] == ["CODING-1"]
    assert result["retained_count"] == 5
    assert result["held_count"] == 0
    assert status["coding_first_group"]["retained_count"] == 5
    assert len(status["coding_groups"]) == 1
    assert all(row["state"] == "approved_knowledge_resource" for row in rows)
    assert all(row["chat_use_permission"] == "available_as_knowledge_resource" for row in rows)
    assert all(row["authorization_id"] == authorization["item"]["id"] for row in rows)
    assert all(row["acquire_status"] == row["integrate_status"] == row["express_status"] == "complete" for row in rows)
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_before
    _locked(result)

    repeated = route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})["result"]
    assert repeated["retained_count"] == 0
    assert repeated["already_retained_count"] == 5
    assert repeated["held_count"] == 0


def test_coding_knowledge_does_not_expand_local_code_adapter_authority(tmp_path):
    conn = _conn(tmp_path)
    _authorize(conn)
    route_request(conn, f"curriculum.foundation.teach_{ROUTE_STEM}", {})

    status = local_code_inspection_status()
    inspection = inspect_local_code(
        {
            "prompt": "Inspect total and explain only what the supplied code supports.",
            "code_packets": [
                {
                    "path": "supplied_example.py",
                    "source_ref": "user_supplied:synthetic_code_reading_example",
                    "content": "total = 0\nfor value in [2, 3]:\n    total = total + value\n",
                }
            ],
        }
    )

    assert status["code_execution_allowed"] is False
    assert status["filesystem_write_allowed"] is False
    assert status["directory_scan_allowed"] is False
    assert inspection["inspected"] is True
    assert inspection["reads_only_explicit_sources"] is True
    assert inspection["code_execution_allowed"] is False
    assert inspection["filesystem_write_allowed"] is False
    assert inspection["autonomous_filesystem_authority"] is False
    assert inspection["source_refs"] == ["user_supplied:synthetic_code_reading_example"]
