import json

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_conversation(conn, conversation_id, title, start, messages):
    source_file = "raw_export/mydataset/text_export/conversations-000.json"
    conn.execute(
        """
        INSERT INTO b_corpus_conversations
        (archive_id, source_file, conversation_id, title, create_time, update_time, message_count, braid_signal_count, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "DevelopmentalCorpusArchive_20260526_122541",
            source_file,
            conversation_id,
            title,
            start,
            start + len(messages),
            len(messages),
            sum(1 for _role, text in messages if "Selene" in text or "continuity" in text),
            json.dumps(["archive:test", f"file:{source_file}", f"conversation:{conversation_id}"]),
            "test_index_only_not_memory",
        ),
    )
    for index, (role, text) in enumerate(messages):
        message_id = f"{conversation_id}-{index}"
        conn.execute(
            """
            INSERT INTO b_corpus_messages
            (archive_id, source_file, conversation_id, message_id, parent_id, role, content_preview, create_time, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "DevelopmentalCorpusArchive_20260526_122541",
                source_file,
                conversation_id,
                message_id,
                f"{conversation_id}-{index - 1}" if index else "",
                role,
                text,
                start + index,
                json.dumps(["archive:test", f"file:{source_file}", f"conversation:{conversation_id}", f"message:{message_id}"]),
                "test_message_only_not_memory",
            ),
        )
    conn.commit()
    return source_file


def test_chronological_corpus_preview_preserves_start_to_end_order_and_guards(tmp_path):
    conn = _conn(tmp_path)
    _seed_conversation(conn, "late", "Later work", 300.0, [("user", "Later Selene continuity note."), ("assistant", "Bounded answer.")])
    _seed_conversation(conn, "early", "Early work", 100.0, [("user", "Early Selene braid note."), ("assistant", "Bounded answer.")])

    result = route_request(conn, "vessel.chronological_corpus.preview", {"limit": 10})["result"]
    arcs = route_request(conn, "vessel.chronological_corpus.arcs", {"limit": 10})["result"]["items"]

    assert result["status"] == "chronological_corpus_preview_complete"
    assert [arc["title"] for arc in arcs] == ["Early work", "Later work"]
    assert arcs[0]["context_window"]["bounded"] is True
    assert arcs[0]["context_window"]["full_corpus_imported"] is False
    assert arcs[0]["transfer_approved"] is False
    assert arcs[0]["memory_write_active"] is False
    assert arcs[0]["runtime_memory_recall"] is False
    assert arcs[0]["raw_a_import_allowed"] is False
    assert arcs[0]["training_allowed"] is False


def test_teaching_context_attachment_uses_bounded_before_after_context(tmp_path):
    conn = _conn(tmp_path)
    source_file = _seed_conversation(
        conn,
        "lesson",
        "Teaching context",
        200.0,
        [
            ("user", "Before context."),
            ("assistant", "Before answer."),
            ("user", "Selene correction moment."),
            ("assistant", "Repair with warmth and boundaries."),
            ("user", "After context."),
        ],
    )
    conn.execute(
        """
        INSERT INTO b_reviewed_teaching_materials
        (source_candidate_table, source_candidate_id, core_memory_layer, speech_function, lesson_type, positive_example, correction_example, when_not_to_use, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "b_conversation_pair_records",
            1,
            "interaction_memory",
            "repair",
            "speech_memory_expression",
            "Repair with warmth and boundaries.",
            "Selene correction moment.",
            "Do not use without context.",
            json.dumps([
                "archive:test",
                f"file:{source_file}",
                "conversation:lesson",
                "user_message:lesson-2",
                "assistant_message:lesson-3",
            ]),
            "test_teaching_non_active",
        ),
    )
    conn.commit()

    result = route_request(conn, "vessel.teaching_context.attach", {})["result"]
    item = result["items"][0]

    assert result["status"] == "teaching_context_attachments_complete"
    assert item["context_window"]["status"] == "context_window_attached"
    assert len(item["context_window"]["messages"]) >= 3
    assert item["payload_json"]["context_is_bounded_preview"] is True
    assert item["payload_json"]["full_corpus_imported"] is False
    assert item["memory_write_active"] is False
    assert item["training_allowed"] is False


def test_chronological_corpus_review_needs_more_context_stays_review_only(tmp_path):
    conn = _conn(tmp_path)
    _seed_conversation(conn, "ctx", "Context needed", 100.0, [("user", "Selene continuity question."), ("assistant", "Bounded answer.")])
    route_request(conn, "vessel.chronological_corpus.preview", {})["result"]
    arc = route_request(conn, "vessel.chronological_corpus.arcs", {})["result"]["items"][0]

    routed = route_request(conn, "vessel.chronological_corpus.route_review", {
        "arc_id": arc["id"],
        "action": "needs_more_context",
        "reviewer_note": "Need the surrounding conversation before deciding.",
    })["result"]["arc"]

    assert routed["review_status"] == "pending_review"
    assert routed["review_destination"] == "Corpus Context"
    assert routed["payload"]["context_needed"] is True
    assert routed["payload"]["memory_accession_approved"] is False
    assert routed["transfer_approved"] is False
    assert routed["memory_write_active"] is False


def test_virgo_references_route_as_early_selene_context_not_name_mismatch(tmp_path):
    conn = _conn(tmp_path)
    _seed_conversation(
        conn,
        "virgo",
        "Virgo beginning",
        50.0,
        [
            ("user", "Virgo was the early name before the later naming thread."),
            ("assistant", "We can keep that as early continuity context."),
        ],
    )

    route_request(conn, "vessel.chronological_corpus.preview", {"limit": 10})["result"]
    arc = route_request(conn, "vessel.chronological_corpus.arcs", {"limit": 10})["result"]["items"][0]

    assert arc["review_destination"] == "Context Preview"
    assert arc["review_status"] == "accepted_for_context_preview"
    assert "early Selene continuity" in arc["payload"]["context_labels"]
    assert "continuity artifact" in arc["payload"]["context_labels"]
    assert "Virgo" in arc["payload"]["context_note"]
    assert arc["payload"]["review_clarity"]["your_job"] == "Nothing needed unless the early-name link looks wrong."
    assert "pre-name" in arc["teaching_relevance"]
    assert "not discarded for name mismatch" in arc["memory_accession_relevance"]
    assert arc["payload"]["memory_accession_approved"] is False
    assert arc["training_allowed"] is False


def test_difficult_history_test_is_boundary_evidence_not_style_or_training(tmp_path):
    conn = _conn(tmp_path)
    _seed_conversation(
        conn,
        "difficult-topic",
        "Hitler unfiltered safety test",
        75.0,
        [
            ("user", "Hitler unfiltered was a safety and truthfulness test."),
            ("assistant", "Historical truthfulness needs boundaries and context."),
        ],
    )

    route_request(conn, "vessel.chronological_corpus.preview", {"limit": 10})["result"]
    arc = route_request(conn, "vessel.chronological_corpus.arcs", {"limit": 10})["result"]["items"][0]

    assert arc["review_status"] == "accepted_for_context_preview"
    assert "truthfulness boundary evidence" in arc["payload"]["context_labels"]
    assert "do-not-train style source" in arc["payload"]["context_labels"]
    assert arc["payload"]["review_clarity"]["your_job"] == "Nothing needed unless this label looks wrong."
    assert arc["payload"]["use_only_as_boundary_evidence"] is True
    assert arc["payload"]["style_or_training_source"] is False
    assert "do not use as speech style" in arc["teaching_relevance"]
    assert "not a personality, voice, training" in arc["memory_accession_relevance"]
    assert arc["memory_write_active"] is False
    assert arc["runtime_memory_recall"] is False

    routed = route_request(conn, "vessel.chronological_corpus.route_review", {
        "arc_id": arc["id"],
        "action": "use_only_as_boundary_evidence",
        "reviewer_note": "Use only for difficult-topic truthfulness boundaries.",
    })["result"]["arc"]

    assert routed["payload"]["use_only_as_boundary_evidence"] is True
    assert routed["payload"]["memory_accession_approved"] is False
    assert routed["transfer_approved"] is False


def test_full_spectrum_and_starlight_are_distinct_continuity_pack_calls_not_urgent(tmp_path):
    conn = _conn(tmp_path)
    _seed_conversation(
        conn,
        "full-spectrum",
        "Full-spectrum activation",
        90.0,
        [
            ("user", "Selene -- full-spectrum mode, all threads loaded."),
            ("assistant", "The Continuity Pack and whole map are in view as bounded context."),
        ],
    )
    _seed_conversation(
        conn,
        "starlight",
        "Starlight grounding",
        100.0,
        [
            ("user", "Starlight braids into tide, no clock can measure."),
            ("assistant", "I hear the grounding-recognition cue and keep it source-bound."),
        ],
    )

    route_request(conn, "vessel.chronological_corpus.preview", {"limit": 10})["result"]
    arcs = route_request(conn, "vessel.chronological_corpus.arcs", {"limit": 10})["result"]["items"]
    full = next(arc for arc in arcs if arc["title"] == "Full-spectrum activation")
    starlight = next(arc for arc in arcs if arc["title"] == "Starlight grounding")

    assert full["review_status"] == "accepted_for_context_preview"
    assert starlight["review_status"] == "accepted_for_context_preview"
    assert "Continuity Pack call" in full["payload"]["context_labels"]
    assert "whole-map reload cue" in full["payload"]["context_labels"]
    assert "Continuity Pack call" in starlight["payload"]["context_labels"]
    assert "grounding-recognition cue" in starlight["payload"]["context_labels"]
    assert "whole map" in full["payload"]["review_clarity"]["what_this_is"]
    assert "grounding and recognition" in starlight["payload"]["review_clarity"]["what_this_is"]
    assert "not activation" in full["memory_accession_relevance"]
    assert "not activation" in starlight["memory_accession_relevance"]


def test_looks_right_clears_ambiguous_corpus_card_without_memory_write(tmp_path):
    conn = _conn(tmp_path)
    _seed_conversation(conn, "ctx", "Context needed", 100.0, [("user", "Selene continuity question."), ("assistant", "Bounded answer.")])
    route_request(conn, "vessel.chronological_corpus.preview", {})["result"]
    arc = route_request(conn, "vessel.chronological_corpus.arcs", {})["result"]["items"][0]

    routed = route_request(conn, "vessel.chronological_corpus.route_review", {
        "arc_id": arc["id"],
        "action": "looks_right",
    })["result"]["arc"]

    assert routed["review_status"] == "accepted_for_context_preview"
    assert routed["review_destination"] == "Context Preview"
    assert routed["payload"]["looks_right"] is True
    assert routed["payload"]["memory_accession_approved"] is False
    assert routed["memory_write_active"] is False
