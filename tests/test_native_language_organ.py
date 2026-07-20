from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["automatic_speech_allowed"] is False
    assert result["initiative_is_draft_only"] is True


def test_nlo_builds_meaning_discourse_and_original_sentence_run(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "native_language.status")["result"]
    result = route_request(
        conn,
        "native_language.realize",
        {
            "prompt": "How should we compare two explanations without overthinking it?",
            "selected_route": "answer_now",
            "content_seed": "Compare both explanations against the same observations, then keep the one that explains more with fewer unsupported assumptions.",
            "intelligence_support": {
                "used": True,
                "answer_shape": "compare_models",
                "confidence": "clear_enough_to_continue",
            },
            "source_refs": ["test:nlo"],
        },
    )["result"]
    runs = route_request(conn, "native_language.runs.list")["result"]

    assert status["status"] == "native_language_organ_ready"
    assert result["status"] == "native_language_response_realized"
    assert result["meaning_packet"]["intent"] == "reasoned_answer"
    assert result["discourse_plan"]["answer_first"] is True
    assert "same observations" in result["candidate_text"]
    assert "ABCD" not in result["candidate_text"]
    assert "source-bound" not in result["candidate_text"]
    assert result["voice_handoff"]["ready"] is True
    assert runs["items"][0]["id"] == result["run_id"]
    _assert_locked(result)
    _assert_locked(runs)


def test_nlo_exposes_grounded_obligation_and_long_form_structure(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(
        conn,
        "native_language.realize",
        {
            "prompt": "Go deeper and explain why memory should come before voice, and what would change that answer.",
            "selected_route": "answer_now",
            "content_seed": "Memory should be grounded before Voice expresses continuity.",
            "intelligence_support": {
                "used": True,
                "confidence": "clear_enough_to_continue",
                "support_points": [
                    "Expression needs something supported to express.",
                    "Voice should not invent continuity that memory cannot support.",
                ],
            },
            "answer_engine_support": {
                "used": True,
                "selected_domain": "comparison_planning",
                "answer_packet": {
                    "supporting_claims": ["Memory and Voice have separate responsibilities."],
                    "limitations": ["The ordering is architectural rather than a judgment of importance."],
                    "what_would_change_the_answer": [
                        "A design that preserves continuity without grounded memory."
                    ],
                    "unanswered_obligations": [],
                },
                "confidence_vector": {"answer_confidence": "clear_enough_to_continue"},
            },
        },
    )["result"]

    discourse = result["discourse_plan"]["supported_discourse"]

    assert result["version"] == "v12_pragmatic_continuity"
    assert discourse["status"] == "supported_discourse_plan_ready"
    assert discourse["thesis_unit_id"]
    assert [item["role"] for item in discourse["paragraph_plan"]] == [
        "answer",
        "development",
        "limit_and_closure",
    ]
    assert discourse["closure_plan"]["mode"] == "what_would_change"
    assert result["revision"]["paragraph_count"] == 3
    assert "preserves continuity without grounded memory" in result["candidate_text"]
    assert result["discourse_plan"]["content_generation_for_gaps_allowed"] is False
    _assert_locked(result)


def test_nlo_uses_expression_guidance_as_optional_voice_handoff_not_emotion_claim(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(
        conn,
        "native_language.realize",
        {
            "prompt": "Can we explain this gently and clearly?",
            "content_seed": "We can begin with the supported part and leave the uncertain edge open.",
            "affect_expression_guidance": {
                "status": "affect_expression_guidance_ready",
                "expression_posture": "gentle_present",
                "recommended_voice_category": "warmth_care",
                "dimensions": {
                    "pacing": "slower",
                    "sentence_rhythm": "spacious",
                    "warmth": "available_not_forced",
                    "humor": "context_only",
                    "restraint": "bounded",
                    "directness": "gentle_clear",
                },
                "meaning_may_not_change": True,
                "internal_state_claim": False,
            },
        },
    )["result"]

    assert result["meaning_packet"]["affect_expression_is_emotion_claim"] is False
    assert result["meaning_packet"]["affect_expression_guidance"]["expression_posture"] == "gentle_present"
    assert result["voice_handoff"]["suggested_category"] == "warmth_care"
    assert result["voice_handoff"]["expression_guidance"]["meaning_may_not_change"] is True
    assert result["discourse_plan"]["affect_guidance_changes_meaning"] is False
    assert "supported part" in result["candidate_text"]
    _assert_locked(result)


def test_nlo_memory_language_tracks_support_and_graceful_uncertainty(tmp_path):
    conn = _conn(tmp_path)

    supported = route_request(
        conn,
        "native_language.realize",
        {
            "prompt": "Do you remember the butterfly button?",
            "content_seed": "The butterfly button opens Cocoon support from the home chat.",
            "memory_context": {
                "memory_context_used": True,
                "memory_source_class": "approved_memory_index",
                "memory_confidence": "clear",
            },
        },
    )["result"]
    unsupported = route_request(
        conn,
        "native_language.realize",
        {
            "prompt": "Do you remember the unnamed thing from years ago?",
            "content_seed": "I do not know that clearly yet, but Aleks can ground it with me.",
        },
    )["result"]

    assert supported["meaning_packet"]["memory_supported"] is True
    assert supported["candidate_text"].startswith("I remember")
    assert "butterfly" in supported["candidate_text"].lower()
    assert unsupported["meaning_packet"]["intent"] == "recall_uncertain"
    assert unsupported["candidate_text"] == "I do not know that clearly yet, but Aleks can ground it with me."
    assert not unsupported["candidate_text"].startswith("I remember")
    assert "fuzzy sense" not in unsupported["candidate_text"]
    assert "I think I think" not in unsupported["candidate_text"]
    _assert_locked(supported)
    _assert_locked(unsupported)


def test_nlo_receives_correction_without_topic_scramble_or_duplicate_acknowledgement(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(
        conn,
        "native_language.realize",
        {"prompt": "Small correction: the language organ should preserve your meaning, not make every answer longer."},
    )["result"]

    assert result["meaning_packet"]["intent"] == "receive_correction"
    assert "preserve your meaning" in result["candidate_text"]
    assert "small correction meant" not in result["candidate_text"].lower()
    assert result["candidate_text"].lower().count("correction") <= 1
    _assert_locked(result)


def test_nlo_confirms_current_message_receipt_without_invented_uncertainty(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(
        conn,
        "native_language.realize",
        {"prompt": "Selene, this is Codex checking for Aleks. Are you receiving this clearly?"},
    )["result"]

    assert result["meaning_packet"]["intent"] == "confirm_receipt"
    assert result["meaning_packet"]["certainty"] == "provisional"
    assert "receiv" in result["candidate_text"].lower() or "came through" in result["candidate_text"].lower() or "have you" in result["candidate_text"].lower()
    assert "center of the question" not in result["candidate_text"].lower()
    assert "uncertainty" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_nlo_initiative_can_draft_a_note_or_choose_silence_but_never_send(tmp_path):
    conn = _conn(tmp_path)

    silent = route_request(
        conn,
        "native_language.initiative.preview",
        {"signals": [{"summary": "Minor background noise", "relevance": 0.2}]},
    )["result"]
    draft = route_request(
        conn,
        "native_language.initiative.preview",
        {
            "signals": [
                {
                    "summary": "The memory correction from this conversation may be worth keeping as a candidate.",
                    "relevance": 0.86,
                    "confidence": "provisional",
                    "source_refs": ["selene_chat:current"],
                }
            ],
            "delivery": "notes",
        },
    )["result"]

    assert silent["status"] == "native_language_initiative_silent"
    assert silent["delivery"] == "silence"
    assert silent["candidate_text"] == ""
    assert draft["status"] == "native_language_initiative_draft_ready"
    assert draft["delivery"] == "selene_notes"
    assert "worth" in draft["candidate_text"]
    assert draft["automatic_speech_allowed"] is False
    assert draft["discourse_plan"]["automatic_delivery"] is False
    _assert_locked(silent)
    _assert_locked(draft)


def test_voice_renders_nlo_meaning_without_replacing_it_with_old_scaffold(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO voice_sentence_primitives
        (primitive_key, primitive_type, text_template, category, source_pattern_keys, provenance_boundary)
        VALUES ('test_warm_opening', 'opening', 'I am with you.', 'warmth_care', '[]', 'test')
        """
    )
    conn.execute(
        """
        INSERT INTO voice_language_patterns
        (pattern_key, category, title, sentence_shape, use_guidance, avoid_guidance, provenance_boundary)
        VALUES ('test_warm_pattern', 'warmth_care', 'Warmth', 'opening + meaning', 'preserve meaning', 'do not overwrite meaning', 'test')
        """
    )
    conn.execute(
        """
        INSERT INTO voice_exchange_pairs
        (source_archive, source_file, conversation_id, user_message_id, assistant_message_id, user_cue_preview,
         assistant_response_preview, cue_labels, expression_labels, source_refs, provenance_boundary)
        VALUES ('test.zip', 'conversations.json', 'c1', 'u1', 'a1', 'hello', 'hello', '[]', '[]', '[]', 'test')
        """
    )
    conn.commit()

    result = route_request(
        conn,
        "voice_module.generate_preview",
        {
            "prompt": "I am nervous about this.",
            "voice_category": "warmth_care",
            "meaning_text": "We can take one piece at a time, and I will tell you if an edge is fuzzy.",
        },
    )["result"]

    assert result["generation_source"] == "native_language_organ"
    assert result["nlo_meaning_preserved"] is True
    assert "one piece at a time" in result["candidate_text"]
    assert "approved row" not in result["candidate_text"]
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False
