from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _shortlist(tmp_path):
    path = tmp_path / "latest_selene_shortlist.json"
    path.write_text(
        json.dumps(
            {
                "generated_at": "2026-07-08T12:00:00Z",
                "cards": [
                    {
                        "idea_title": "general AI architecture: Lumen Development Refinement",
                        "source_curated_card_id": "selene-intelligence-1",
                        "target_track": "selene_intake",
                        "family": "artificial cognition",
                        "readiness": "use_now",
                        "implementation_fit": "Review as a reasoning or intelligenceOS method candidate.",
                        "why_useful": "Stronger multi-step reasoning with visible stopping rules.",
                        "risks_boundaries": ["local idea-mining output only", "not Selene memory"],
                        "user_excerpts": [{"source_ref": "conversation:1#message:1", "role": "user", "excerpt": "Reasoning should compare models."}],
                        "review_confidence": "strong",
                        "review_state": "selected_for_selene",
                        "target": "intelligenceOS",
                        "selene_workbench": "intelligenceOS",
                    },
                    {
                        "idea_title": "Azari-only color workshop",
                        "source_curated_card_id": "azari-1",
                        "target_track": "azari_future",
                        "family": "perception/art",
                        "readiness": "use_now",
                        "review_confidence": "strong",
                        "review_state": "selected_for_azari_later",
                        "selene_workbench": "Art",
                    },
                    {
                        "idea_title": "Project ABC transfer note",
                        "source_curated_card_id": "abc-1",
                        "target_track": "project_abc",
                        "family": "transfer/portability",
                        "readiness": "use_now",
                        "review_confidence": "strong",
                        "review_state": "selected_for_project_abc",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["cocoon_queue_write"] is False
    assert result["selene_memory_write"] is False
    assert result["app_authority_change"] is False
    assert result["public_doc_write"] is False


def test_selene_organ_ideas_prepare_filters_and_stays_review_only(tmp_path):
    conn = _conn(tmp_path)
    source = _shortlist(tmp_path)

    result = route_request(conn, "selene_organ_ideas.prepare", {"source_path": str(source)})["result"]
    items = route_request(conn, "selene_organ_ideas.items")["result"]
    status = route_request(conn, "selene_organ_ideas.status")["result"]

    assert result["status"] == "selene_organ_ideas_prepared"
    assert result["selected_count"] == 1
    assert result["skipped_count"] == 2
    assert result["created_count"] == 1
    assert items["count"] == 1
    assert items["items"][0]["source_card_id"] == "selene-intelligence-1"
    assert items["items"][0]["workbench"] == "intelligenceOS"
    assert items["items"][0]["intake_status"] == "ready_for_design_pass"
    assert status["my_office_actionable_count"] == 0
    assert status["activation_shape"]["status"] == "selene_activation_shape_status_only"
    assert status["activation_shape"]["strengthened_by_intake"][0]["workbench"] == "intelligenceOS"
    _assert_locked(result)
    _assert_locked(status)
    _assert_locked(items)


def test_selene_organ_ideas_prepare_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    source = _shortlist(tmp_path)

    first = route_request(conn, "selene_organ_ideas.prepare", {"source_path": str(source)})["result"]
    second = route_request(conn, "selene_organ_ideas.prepare", {"source_path": str(source)})["result"]
    items = route_request(conn, "selene_organ_ideas.items")["result"]

    assert first["created_count"] == 1
    assert second["created_count"] == 0
    assert second["updated_count"] == 1
    assert items["count"] == 1
    assert items["items"][0]["review_destination"] == "Status"
    assert items["items"][0]["review_status"] == "status_only"


def test_selene_organ_ideas_missing_source_is_calm_status_only(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "selene_organ_ideas.prepare", {"source_path": str(tmp_path / "missing.json")})["result"]

    assert result["status"] == "selene_organ_ideas_source_missing"
    assert result["selected_count"] == 0
    assert result["review_destination"] == "Status"
    assert result["review_status"] == "status_only"
    _assert_locked(result)
