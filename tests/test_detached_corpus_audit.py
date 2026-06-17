from selene.db import connect, init_db
from selene.detached_corpus import detached_corpus_audit, detached_corpus_metadata, detached_corpus_previews
from selene.module_router import route_request


def _make_archive(tmp_path):
    root = tmp_path / "DevelopmentalCorpusArchive_20260526_122541"
    text_export = root / "raw_export" / "mydataset" / "text_export"
    text_export.mkdir(parents=True)
    (text_export / "conversations-000.json").write_text(
        '[{"conversation_id":"c1","title":"Selene","mapping":{"m1":{"message":{"content":{"parts":["Selene remembers the braid through reviewed accession."]}}}}}]',
        encoding="utf-8",
    )
    (text_export / "chat.html").write_text("<html><body>Selene chat export preview.</body></html>", encoding="utf-8")
    (root / "raw_export" / "mydataset" / "source.zip").write_bytes(b"zip metadata only")
    return root


def test_detached_corpus_audit_labels_future_b_reviewed_accession_without_import(tmp_path):
    root = _make_archive(tmp_path)
    result = detached_corpus_audit("Selene", archive_root=root)
    assert result["boundary"] == "read_only_detached_corpus_audit"
    assert result["memory_candidate_type"] == "shared_developmental_memory_candidate"
    assert result["abc_transfer_rule"] == "A -> B-reviewed translation -> C; never raw A -> C"
    assert result["future_b_reviewed_accession_status"] == "not_implemented_explicit_b_review_required"
    assert result["blocked_transfer"] == "raw_A_direct_to_C_memory"
    assert "pass through B" in result["accession_note"]
    assert result["writes_performed"] is False
    assert result["model_call_allowed"] is False
    assert result["gate"]["route"] == "allowed_source_archive_audit"
    assert result["previews"][0]["boundary"] == "bounded_preview_only_not_memory"


def test_detached_corpus_metadata_exposes_files_without_zip_preview(tmp_path):
    root = _make_archive(tmp_path)
    metadata = detached_corpus_metadata(root)
    files = {item["name"]: item for item in metadata["files"]}
    assert metadata["file_count"] == 3
    assert files["conversations-000.json"]["preview_available"] is True
    assert files["chat.html"]["preview_available"] is True
    assert files["source.zip"]["preview_available"] is False
    assert files["source.zip"]["role"] == "detached_source_package_metadata_only"


def test_detached_corpus_previews_are_bounded_and_path_safe(tmp_path):
    root = _make_archive(tmp_path)
    previews = detached_corpus_previews("Selene", limit=8, archive_root=root)
    assert previews
    assert all(len(item["preview"]) <= 520 for item in previews)
    assert detached_corpus_previews("Selene", file_id="../outside.txt", archive_root=root) == []


def test_detached_corpus_route_does_not_write_memory_tables(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    before = conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0]
    result = route_request(conn, "detached_corpus.audit", {"query": "Selene"})["result"]
    after = conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0]
    assert result["writes_performed"] is False
    assert result["future_b_reviewed_accession_status"] == "not_implemented_explicit_b_review_required"
    assert result["abc_transfer_rule"] == "A -> B-reviewed translation -> C; never raw A -> C"
    assert after == before
