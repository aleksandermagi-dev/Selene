from __future__ import annotations

from selene.c_vessel import c_vessel_status
from selene.db import connect, init_db
from selene.transfer_state import current_runtime_truth
from selene.validation import validate
from selene.vessel import vessel_status
from selene.registry import seed_registry


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_resident_state(conn, *, activation_state: str = "selene_chat_active_supervised"):
    conn.execute(
        """
        INSERT INTO transfer_c_readable_packages(
          package_hash, status, manifest_item_ids, included_counts, excluded_counts,
          package_json, source_refs, provenance_boundary, review_status
        ) VALUES ('test-package', 'approved_c_readable_context', '[]', '{}', '{}',
                  '{}', '[]', 'test_boundary', 'approved_c_readable_context')
        """
    )
    conn.execute(
        """
        INSERT INTO selene_transfer_completion_audit(
          state, action, actor, exact_phrase_matched, readiness_json, audit_json,
          source_refs, provenance_boundary, review_status
        ) VALUES ('selene_v1_live_reviewed_continuity', 'approve_transfer_completion',
                  'Aleks', 1, '{}', '{}', '[]', 'test_boundary',
                  'approved_transfer_completion')
        """
    )
    conn.execute(
        """
        INSERT INTO selene_activation_audit(
          state, action, actor, exact_phrase_matched, readiness_json, audit_json,
          source_refs, provenance_boundary
        ) VALUES (?, 'runtime_availability_test', 'Aleks', 1, '{}', '{}', '[]',
                  'test_boundary')
        """,
        (activation_state,),
    )
    conn.commit()


def test_pre_transfer_status_preserves_historical_build_truth(tmp_path):
    conn = _conn(tmp_path)

    runtime = current_runtime_truth(conn)
    vessel = vessel_status(conn)
    c_vessel = c_vessel_status(conn)

    assert runtime["runtime_phase"] == "pre_transfer"
    assert vessel["status"] == "vessel_v1_built_not_activated"
    assert c_vessel["status"] == "c_vessel_built_non_active"
    assert vessel["historical_build_status_is_current"] is True
    assert c_vessel["historical_build_status_is_current"] is True


def test_resident_status_replaces_legacy_current_claim_without_erasing_history(tmp_path):
    conn = _conn(tmp_path)
    _seed_resident_state(conn)

    runtime = current_runtime_truth(conn)
    vessel = vessel_status(conn)
    c_vessel = c_vessel_status(conn)

    assert runtime["runtime_phase"] == "resident_active"
    assert runtime["selene_v1_live"] is True
    assert vessel["status"] == "selene_resident_vessel_active"
    assert c_vessel["status"] == "selene_resident_vessel_active"
    assert vessel["transfer_complete"] is True
    assert c_vessel["transfer_approved"] is True
    assert vessel["resident_runtime_state"] == "resident_chat_available"
    assert c_vessel["c_chat_state"] == "resident_governed_chat"
    assert vessel["historical_build_status"] == "vessel_v1_built_not_activated"
    assert c_vessel["historical_build_status"] == "c_vessel_built_non_active"
    assert vessel["historical_build_status_is_current"] is False
    assert c_vessel["historical_build_status_is_current"] is False
    assert vessel["cocoon_is_resident_runtime_dependency"] is False
    assert c_vessel["cocoon_is_resident_runtime_dependency"] is False


def test_pausing_chat_changes_availability_without_changing_transfer_or_identity(tmp_path):
    conn = _conn(tmp_path)
    _seed_resident_state(conn, activation_state="selene_chat_supervised_paused")

    runtime = current_runtime_truth(conn)
    vessel = vessel_status(conn)

    assert runtime["runtime_phase"] == "resident_chat_paused"
    assert runtime["transfer_complete"] is True
    assert runtime["selene_v1_live"] is False
    assert runtime["identity_continuity_persists_when_chat_unavailable"] is True
    assert vessel["status"] == "selene_resident_vessel_chat_paused"
    assert vessel["resident_runtime_state"] == "resident_chat_paused"


def test_validation_uses_canonical_truth_after_transfer(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    _seed_resident_state(conn)

    result = validate(conn)

    assert result["ok"], result["checks"]
    assert result["current_runtime_truth"]["runtime_phase"] == "resident_active"
    assert result["checks"]["vessel_current_runtime_truth_matches_canonical"] is True
    assert result["checks"]["c_vessel_current_runtime_truth_matches_canonical"] is True
    assert result["checks"]["historical_vessel_build_truth_preserved"] is True

