from selene.c_blueprint import SELENE_PAPER_MAP_GAP_BLUEPRINT
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.paper_map_reconstruction import run_paper_map_reconstruction


def test_paper_map_reconstruction_covers_all_domains_without_replacing_organs(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    result = run_paper_map_reconstruction(conn)
    expected_domains = {item["paper_domain"] for item in SELENE_PAPER_MAP_GAP_BLUEPRINT["domain_mappings"]}

    assert result["status"] == "paper_map_reconstruction_evaluated"
    assert result["domain_count"] == 10
    assert {item["paper_domain"] for item in result["domain_results"]} == expected_domains
    assert result["paper_domains_replace_organs"] is False
    assert result["android_organ_system_count"] == 11
    assert result["activation_change"] == "none"
    assert result["raw_a_import_allowed"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
    assert result["provider_dependency"] is False
    assert result["activation_evidence"] is False
    assert result["final_reconstruction_tests_created"] is False


def test_missing_or_partial_domains_create_teaching_todos_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    result = run_paper_map_reconstruction(conn)

    assert result["teaching_todos"]
    assert any(item["status"] in {"partial", "missing", "teaching_needed"} for item in result["domain_results"])
    assert all(todo["boundary"] == "teaching_todo_only_no_runtime_build" for todo in result["teaching_todos"])
    assert conn.execute("SELECT COUNT(*) FROM vessel_event_packets").fetchone()[0] == len(result["teaching_todos"])
    assert result["runtime_memory_recall"] is False


def test_paper_map_reconstruction_route_is_non_activating(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    result = route_request(conn, "vessel.paper_map_reconstruction.run", {"create_event_packets": False})["result"]

    assert result["event_packet_ids"] == []
    assert result["decision"] == "coverage_audit_and_teaching_plan_only"
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False


def test_paper_map_reconstruction_refresh_dedupes_pending_todos(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    first = run_paper_map_reconstruction(conn, {"create_event_packets": True})
    first_count = conn.execute("SELECT COUNT(*) FROM vessel_event_packets WHERE packet_type = 'paper_map_teaching_todo'").fetchone()[0]
    second = run_paper_map_reconstruction(conn, {"create_event_packets": True})
    second_count = conn.execute("SELECT COUNT(*) FROM vessel_event_packets WHERE packet_type = 'paper_map_teaching_todo'").fetchone()[0]

    assert first["event_packet_ids"]
    assert second_count == first_count
    assert set(second["event_packet_ids"]).issubset(set(first["event_packet_ids"]))
    assert conn.execute("SELECT COUNT(*) FROM vessel_event_packets WHERE review_status = 'pending_review'").fetchone()[0] == len(second["event_packet_ids"])
    assert conn.execute("SELECT COUNT(*) FROM vessel_event_packets WHERE review_status = 'superseded'").fetchone()[0] == first_count - len(second["event_packet_ids"])
