from __future__ import annotations

import re
from pathlib import Path

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.organ_maturity_ledger import (
    CONNECTION_STATES,
    MATURITY_STATES,
    ORGAN_SPECS,
    organ_maturity_ledger_status,
)


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _item(result, key):
    return next(item for item in result["items"] if item["key"] == key)


def test_maturity_ledger_has_unique_valid_current_scope_entries(tmp_path):
    conn = _conn(tmp_path)

    result = organ_maturity_ledger_status(conn)

    keys = [item["key"] for item in result["items"]]
    assert result["status"] == "organ_maturity_ledger_ready"
    assert result["organ_count"] == len(ORGAN_SPECS) == len(set(keys))
    assert all(item["maturity_state"] in MATURITY_STATES for item in result["items"])
    assert all(item["target_state"] in MATURITY_STATES for item in result["items"])
    assert all(item["connection_state"] in CONNECTION_STATES for item in result["items"])
    assert result["invariants"]["valid_state_vocabulary"] is True
    assert result["invariants"]["no_blueprint_claimed_operational"] is True
    assert result["invariants"]["route_or_table_presence_proves_maturity"] is False
    assert result["invariants"]["configured_record_count_proves_integration"] is False
    conn.close()


def test_maturity_ledger_source_route_and_test_anchors_exist(tmp_path):
    root = Path(__file__).resolve().parents[1]
    router_source = (root / "src" / "selene" / "module_router.py").read_text(encoding="utf-8")
    implemented_routes = set(re.findall(r'route_key == "([^"]+)"', router_source))

    for spec in ORGAN_SPECS:
        assert all((root / "src" / "selene" / source).is_file() for source in spec["source_modules"])
        assert all(route in implemented_routes for route in spec["routes"])

    conn = _conn(tmp_path)
    result = organ_maturity_ledger_status(conn)
    for item in result["items"]:
        assert all((root / test_path).is_file() for test_path in item["evidence_tests"])
        assert item["authority_scope"]
    conn.close()


def test_maturity_ledger_distinguishes_connected_preview_and_blueprint_states(tmp_path):
    conn = _conn(tmp_path)

    result = organ_maturity_ledger_status(conn)

    assert _item(result, "nlo_voice_text")["maturity_state"] == "mature_current_scope"
    assert _item(result, "nlo_voice_text")["health_state"] == (
        "phase_7_creative_discourse_breadth_and_stopping_gate_verified"
    )
    assert _item(result, "memory")["maturity_state"] == "mature_current_scope"
    assert _item(result, "memory")["health_state"] == "phase_2_completion_gate_verified"
    assert _item(result, "conversation_context")["maturity_state"] == "mature_current_scope"
    assert _item(result, "approved_knowledge_retrieval")["maturity_state"] == "mature_current_scope"
    assert _item(result, "study")["maturity_state"] == "mature_current_scope"
    assert _item(result, "study")["maturation_phase"] == 6
    assert _item(result, "study")["configured_metrics"]["curriculum_concept_profiles"] == 0
    assert _item(result, "dream")["maturity_state"] == "mature_current_scope"
    assert _item(result, "associative_intuition")["maturity_state"] == "mature_current_scope"
    assert _item(result, "self_state")["maturity_state"] == "mature_current_scope"
    assert _item(result, "affect_agency")["maturity_state"] == "mature_current_scope"
    assert _item(result, "intelligence_os")["maturity_state"] == "mature_current_scope"
    assert _item(result, "answer_engine")["maturity_state"] == "mature_current_scope"
    assert _item(result, "problem_resolution")["maturity_state"] == "mature_current_scope"
    assert _item(result, "verified_math")["maturity_state"] == "mature_current_scope"
    assert _item(result, "source_research")["maturity_state"] == "mature_current_scope"
    assert _item(result, "local_code")["maturity_state"] == "mature_current_scope"
    assert _item(result, "local_code")["connection_state"] == "ordinary_chat"
    assert _item(result, "goals_initiative")["maturity_state"] == "implemented"
    assert _item(result, "goals_initiative")["connection_state"] == "bounded_route"
    assert _item(result, "goals_initiative")["health_state"] == (
        "phase_8a_typed_goal_and_conflict_receipts_verified"
    )
    assert _item(result, "perception")["maturity_state"] == "review_preview"
    assert _item(result, "audible_voice")["maturity_state"] == "blueprint"
    assert _item(result, "audible_voice")["connection_state"] == "not_connected"
    assert _item(result, "embodiment")["health_state"] == "structural_preflight_only"
    assert "audible_voice" in result["summary"]["blueprint_or_preview_keys"]
    assert "conversation_context" not in result["summary"]["integration_gap_keys"]
    assert "answer_engine" not in result["summary"]["integration_gap_keys"]
    assert result["summary"]["next_phase"] == 8
    conn.close()


def test_maturity_ledger_generates_current_repository_curriculum_counts(tmp_path):
    conn = _conn(tmp_path)

    counts = organ_maturity_ledger_status(conn)["repository_defined_counts"]

    assert counts == {
        "f1_group_count": 17,
        "f1_concept_count": 106,
        "f2_group_count": 8,
        "f2_concept_count": 41,
        "coding_group_count": 1,
        "coding_concept_count": 5,
        "language_group_count": 12,
        "language_capability_count": 73,
        "defined_approved_knowledge_capacity": 225,
    }
    conn.close()


def test_maturity_ledger_reports_counts_without_private_record_content(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO b_approved_memory_references(
          source_candidate_table, source_candidate_id, core_memory_layer,
          title, reference_summary, source_refs, provenance_boundary,
          status, review_status
        ) VALUES ('test_fixture', 1, 'interaction_memory',
                  'PRIVATE TITLE MUST NOT LEAK', 'PRIVATE SUMMARY MUST NOT LEAK',
                  '["PRIVATE SOURCE MUST NOT LEAK"]', 'test',
                  'approved_reference_non_active',
                  'accepted_for_memory_accession')
        """
    )
    conn.commit()

    before = conn.total_changes
    result = organ_maturity_ledger_status(conn)
    after = conn.total_changes
    serialized = str(result)

    assert result["configured_runtime_metrics"]["approved_memory_references"] == 1
    assert _item(result, "memory")["configured_metrics"]["approved_memory_references"] == 1
    assert "PRIVATE TITLE MUST NOT LEAK" not in serialized
    assert "PRIVATE SUMMARY MUST NOT LEAK" not in serialized
    assert "PRIVATE SOURCE MUST NOT LEAK" not in serialized
    assert result["invariants"]["private_content_included"] is False
    assert after == before
    conn.close()


def test_maturity_ledger_router_is_read_only_and_identity_preserving(tmp_path):
    conn = _conn(tmp_path)
    before = conn.total_changes

    routed = route_request(conn, "organ_maturity.ledger.status")

    assert routed["route"] == "organ_maturity.ledger.status"
    assert routed["result"]["status"] == "organ_maturity_ledger_ready"
    assert routed["result"]["writes_state"] is False
    assert routed["result"]["memory_write_active"] is False
    assert routed["result"]["teaching_operation_performed"] is False
    assert routed["result"]["dream_decision_performed"] is False
    assert routed["result"]["identity_change"] is False
    assert routed["result"]["governance_change"] is False
    assert routed["result"]["authority_change"] is False
    assert routed["result"]["autonomous_action_allowed"] is False
    assert conn.total_changes == before
    conn.close()
