from scripts.real_corpus_checkpoint import run_checkpoint


def test_real_corpus_checkpoint_writes_repeatable_report(tmp_path):
    report = run_checkpoint(tmp_path / "selene.sqlite3", tmp_path / "exports", limit=5, refresh_braid=False)

    assert report["status"] == "real_corpus_checkpoint_complete"
    assert report["limit"] == 5
    assert report["tracer"]["status"] == "not_run"
    assert report["activation_change"] == "none"
    assert report["memory_write_active"] is False
    assert report["training_allowed"] is False
    assert (tmp_path / "exports" / "review_desk_current.md").exists()
    assert "real_corpus_checkpoint_" in report["checkpoint_path"]
