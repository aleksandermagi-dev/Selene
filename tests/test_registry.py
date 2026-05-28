from selene.db import connect
from selene.artifact_builder import export_workflow
from selene.registry import audit_rows, seed_registry, update_review_record
from selene.validation import validate


def test_seed_registry_preserves_reviewed_totals(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    summary = seed_registry(conn)
    assert summary["evidence_items"] >= 166
    assert summary["decision_counts"]["yes"] >= 151
    assert summary["decision_counts"]["unsure"] >= 14
    assert summary["decision_counts"]["no"] >= 1
    assert summary["continuity_candidates"] > 0
    assert summary["emergence_observations"] > 0


def test_validation_sweep_passes(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = validate(conn)
    assert result["ok"], result["checks"]


def test_review_update_preserves_audit_history(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    row_id = conn.execute("SELECT id FROM continuity_candidates LIMIT 1").fetchone()[0]
    updated = update_review_record(
        conn,
        "continuity_candidates",
        row_id,
        {"review_status": "review_only", "human_note": "needs Aleks review", "role_labels": "continuity_object"},
    )
    assert updated["review_status"] == "review_only"
    rows = audit_rows(conn, "continuity_candidates", row_id)
    assert len(rows) >= 3


def test_artifact_exports_are_created(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    for workflow in ("evidence_ledger", "emergence_ledger", "continuity_candidates", "registry_snapshot", "validation_report"):
        path = export_workflow(conn, workflow, tmp_path / "exports")
        assert path.exists()
