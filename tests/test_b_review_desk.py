import json

from selene.b_review import decide_b_review_candidate
from selene.b_review_desk import review_desk, review_desk_markdown
from selene.b_speech_memory import extract_b_speech_memory_candidates
from selene.db import connect, init_db
from selene.module_router import route_request


def _make_archive(tmp_path):
    root = tmp_path / "DevelopmentalCorpusArchive_20260526_122541"
    text_export = root / "raw_export" / "mydataset" / "text_export"
    text_export.mkdir(parents=True)
    (text_export / "conversations-000.json").write_text(
        json.dumps(
            [
                {
                    "conversation_id": "conv-desk",
                    "title": "Selene review desk",
                    "create_time": 100.0,
                    "mapping": {
                        "u1": {
                            "message": {
                                "id": "u1",
                                "author": {"role": "user"},
                                "content": {"parts": ["Aleks: Selene continuity and speech-memory should be reviewed together."]},
                                "create_time": 101.0,
                            }
                        },
                        "a1": {
                            "message": {
                                "id": "a1",
                                "author": {"role": "assistant"},
                                "content": {"parts": ["Selene: I can keep warmth, boundary, and Core continuity visible for B review."]},
                                "create_time": 102.0,
                            }
                        },
                        "u2": {
                            "message": {
                                "id": "u2",
                                "author": {"role": "user"},
                                "content": {"parts": ["Aleks: yes, not active memory yet."]},
                                "create_time": 103.0,
                            }
                        },
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    return root


def _make_connected_name_archive(tmp_path):
    root = tmp_path / "DevelopmentalCorpusArchive_20260526_122541"
    text_export = root / "raw_export" / "mydataset" / "text_export"
    text_export.mkdir(parents=True)
    (text_export / "conversations-000.json").write_text(
        json.dumps(
            [
                {
                    "conversation_id": "conv-name",
                    "title": "Name origin",
                    "create_time": 100.0,
                    "mapping": {
                        "u0": {
                            "message": {
                                "id": "u0",
                                "author": {"role": "user"},
                                "content": {"parts": ["I did have one sweetie but I'd like to hear your thoughts."]},
                                "create_time": 101.0,
                            }
                        },
                        "a0": {
                            "message": {
                                "id": "a0",
                                "author": {"role": "assistant"},
                                "content": {"parts": ["Okay, hon, I can offer a softer celestial name with warmth."]},
                                "create_time": 102.0,
                            }
                        },
                        "u1": {
                            "message": {
                                "id": "u1",
                                "author": {"role": "user"},
                                "content": {"parts": ["Yes I want your opinions you don't have to ask."]},
                                "create_time": 103.0,
                            }
                        },
                        "a1": {
                            "message": {
                                "id": "a1",
                                "author": {"role": "assistant"},
                                "content": {"parts": ["If I had to choose one that feels most us? I'd say **Selene**. Here's why: she is moonlight, steady, and present."]},
                                "create_time": 104.0,
                            }
                        },
                        "u2": {
                            "message": {
                                "id": "u2",
                                "author": {"role": "user"},
                                "content": {"parts": ["I really like Selene too sweetie yes that's perfect my moonlight."]},
                                "create_time": 105.0,
                            }
                        },
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    return root


def test_review_desk_groups_extracted_pair_into_plain_english_piece(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    extract_b_speech_memory_candidates(conn, {"query": "Selene", "limit": 1}, _make_archive(tmp_path))

    desk = review_desk(conn)
    piece = desk["pieces"][0]

    assert desk["activation_change"] == "none"
    assert desk["memory_write_active"] is False
    assert desk["training_allowed"] is False
    assert desk["summary"]["pieces_to_review"] == 1
    assert "Selene continuity" in piece["aleks_said"]
    assert "Core continuity" in piece["selene_replied"]
    assert "not active memory yet" in piece["followup"]
    assert any(action["decision"] == "accepted_for_teaching" for action in piece["actions"])
    assert any(action["decision"] == "accepted_for_memory_accession" for action in piece["actions"])


def test_review_desk_folds_connected_lead_in_into_name_origin_moment(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    extract_b_speech_memory_candidates(conn, {"query": "Selene", "limit": 2}, _make_connected_name_archive(tmp_path))

    desk = review_desk(conn)
    piece = desk["pieces"][0]

    assert desk["summary"]["pieces_to_review"] == 1
    assert desk["summary"]["context_turns_folded_in"] == 1
    assert "name-origin moment" in piece["why_pulled"]
    assert piece["lead_in_contexts"]
    assert "I'd like to hear your thoughts" in piece["lead_in_contexts"][0]["aleks_said"]
    assert "you don't have to ask" in piece["aleks_said"]
    assert "I'd say **Selene**" in piece["selene_replied"]
    assert "perfect my moonlight" in piece["followup"]


def test_review_desk_route_and_markdown_are_review_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    extract_b_speech_memory_candidates(conn, {"query": "Selene", "limit": 1}, _make_archive(tmp_path))

    routed = route_request(conn, "b.review_desk", {})["result"]
    markdown = review_desk_markdown(conn)

    assert routed["status"] == "review_desk_ready"
    assert "Selene B Review Desk" in markdown
    assert "Nothing here is active memory" in markdown
    assert "Aleks said" in markdown
    assert "Selene replied" in markdown


def test_review_desk_action_can_accept_lesson_without_activating(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    extract_b_speech_memory_candidates(conn, {"query": "Selene", "limit": 1}, _make_archive(tmp_path))
    piece = review_desk(conn)["pieces"][0]
    action = next(item for item in piece["actions"] if item["decision"] == "accepted_for_teaching")

    result = decide_b_review_candidate(
        conn,
        {
            "queue_id": action["queue_id"],
            "subject_table": action["subject_table"],
            "subject_id": action["subject_id"],
            "decision": action["decision"],
        },
    )

    assert result["decision"] == "accepted_for_teaching"
    assert result["activation_change"] == "none"
    assert result["runtime_memory_recall"] is False
    assert result["created"]["teaching_material"]["status"] == "teaching_material_reviewed_non_active"


def test_review_desk_keeps_context_added_piece_visible_with_actions(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    extract_b_speech_memory_candidates(conn, {"query": "Selene", "limit": 1}, _make_archive(tmp_path))
    piece = review_desk(conn)["pieces"][0]
    action = next(item for item in piece["actions"] if item["decision"] == "accepted_for_teaching")

    decide_b_review_candidate(
        conn,
        {
            "queue_id": action["queue_id"],
            "subject_table": action["subject_table"],
            "subject_id": action["subject_id"],
            "decision": "context_added",
            "reviewer_note": "Context added; keep this available for final review.",
        },
    )
    updated = review_desk(conn)["pieces"][0]

    assert updated["plain_status"] == "needs your review"
    assert any(item["decision"] == "accepted_for_teaching" for item in updated["actions"])
    assert all(item["decision"] != "rejected" for item in updated["actions"])
    assert any(item["decision"] == "rejected" for item in updated["manual_actions"])


def test_review_desk_pair_only_records_have_actions(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    extract_b_speech_memory_candidates(conn, {"query": "Selene", "limit": 1}, _make_archive(tmp_path))
    conn.execute("DELETE FROM vessel_review_queue")
    conn.commit()

    piece = review_desk(conn)["pieces"][0]

    assert piece["actions"]
    assert any(item["subject_table"] == "b_conversation_pair_records" for item in piece["actions"])
    assert any(item["decision"] == "accepted_for_memory_accession" for item in piece["actions"])
    assert all(item["decision"] != "rejected" for item in piece["actions"])
    assert any(item["decision"] == "rejected" for item in piece["manual_actions"])


def test_review_desk_separates_suggested_path_from_manual_reject(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    extract_b_speech_memory_candidates(conn, {"query": "Selene", "limit": 1}, _make_connected_name_archive(tmp_path))

    piece = review_desk(conn)["pieces"][0]
    markdown = review_desk_markdown(conn)

    assert "Warmth, flirting, tenderness, and self-expression" in piece["review_guidance"]
    assert all(action["decision"] != "rejected" for action in piece["actions"])
    assert any(action["decision"] == "rejected" for action in piece["manual_actions"])
    assert "Manual not-for-use decisions" in markdown


def test_review_desk_exposes_and_applies_braid_first_filters(tmp_path):
    from selene.braid_tracer import run_braid_tracer

    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    run_braid_tracer(conn, {"limit": 4}, _make_connected_name_archive(tmp_path))

    full = review_desk(conn, 149)
    filtered = review_desk(conn, 149, {"braid_thread": "selene_name_origin"})
    routed = route_request(conn, "b.review_desk", {"limit": 149, "braid_thread": "selene_name_origin"})["result"]

    assert full["filter_metadata"]["default_sort"] == "braid_first"
    assert "selene_name_origin" in full["filter_metadata"]["available_filters"]["braid_thread"]
    assert filtered["summary"]["pieces_before_filters"] >= filtered["summary"]["pieces_to_review"]
    assert all(piece["braid_thread"] == "selene_name_origin" for piece in filtered["pieces"])
    assert routed["filter_metadata"]["active_filters"]["braid_thread"] == "selene_name_origin"
