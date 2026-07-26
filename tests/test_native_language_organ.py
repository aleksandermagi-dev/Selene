from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.claim_evidence import build_claim_evidence_packet
from selene.db import connect, init_db
from selene.epistemic_revision import build_epistemic_revision_plan
from selene.module_router import route_request
from selene.native_language_organ import _reasoned_answer_frames, realize_native_language
from selene.conversation_thread_loom import build_thread_braid


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


def test_reasoned_answer_frames_preserve_first_person_capitalization():
    frames = _reasoned_answer_frames(
        "I do not have enough grounded knowledge to answer reliably yet.",
        "direct",
    )

    assert all(" is i " not in item.lower() for item in frames)
    assert "My current answer is this: I do not have" in frames[1]


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


def test_nlo_never_realizes_answer_shape_as_visible_reasoning_content(tmp_path):
    conn = _conn(tmp_path)
    result = realize_native_language(
        conn,
        {
            "prompt": "whats up means how are you",
            "content_seed": "I understand the correction.",
            "intent_decision": {"intent": "correction", "answer_shape": "acknowledge_and_adjust"},
            "intelligence_support": {
                "used": True,
                "answer_shape": "answer_now",
                "reasoning_summary": "",
                "support_points": [],
            },
        },
    )

    assert "answer_now" not in result["candidate_text"].lower()
    assert "answer_now" not in result["formation"]["candidate_text"].lower()
    assert all(
        str(item.get("text") or "").lower() != "answer_now"
        for item in result["semantic_frame"]["propositions"]
    )


def test_nlo_carries_selective_revision_to_discourse_and_voice(tmp_path):
    conn = _conn(tmp_path)
    revision = build_epistemic_revision_plan(
        {
            "requested_kind": "unresolved_contradiction",
            "prior_claim": "The first model fits.",
            "revised_claim": "The second observation conflicts with it.",
            "contradictions": ["the two results conflict"],
        }
    )
    result = realize_native_language(
        conn,
        {
            "prompt": "These two results still conflict.",
            "content_seed": "The conflict remains unresolved pending distinguishing evidence.",
            "epistemic_revision_plan": revision,
        },
    )

    assert result["meaning_packet"]["epistemic_revision"]["validity"] == "conflict_unresolved"
    assert "identify_affected_claim_without_resetting_context" in result["discourse_plan"]["moves"]
    assert "leave_unresolved_contradiction_visible" in result["discourse_plan"]["moves"]
    assert result["discourse_plan"]["epistemic_revision"] == revision
    assert result["voice_handoff"]["meaning_must_be_preserved"] is True


def test_nlo_preserves_claim_types_disagreement_and_uncertainty_for_voice(tmp_path):
    conn = _conn(tmp_path)
    packet = build_claim_evidence_packet(
        {
            "claims": [
                {"claim_id": "obs", "claim_type": "observation", "text": "The readings differ."},
                {
                    "claim_id": "report-a",
                    "claim_type": "source_statement",
                    "text": "Source A reports an effect.",
                    "source_refs": ["source:a"],
                    "claim_key": "effect",
                    "stance": "support",
                },
                {
                    "claim_id": "report-b",
                    "claim_type": "source_statement",
                    "text": "Source B reports no effect.",
                    "source_refs": ["source:b"],
                    "claim_key": "effect",
                    "stance": "oppose",
                },
                {
                    "claim_id": "infer",
                    "claim_type": "inference",
                    "text": "The current evidence is inconclusive.",
                    "basis_claim_ids": ["obs", "report-a", "report-b"],
                },
            ]
        }
    )
    result = realize_native_language(
        conn,
        {
            "prompt": "What can we conclude from these sources?",
            "content_seed": "The current evidence is inconclusive.",
            "claim_evidence_packet": packet,
        },
    )

    moves = result["discourse_plan"]["moves"]
    assert "keep_observation_separate_from_interpretation" in moves
    assert "attribute_source_statement_without_promoting_it_to_fact" in moves
    assert "label_inference_and_preserve_its_basis" in moves
    assert "preserve_claim_level_disagreement" in moves
    assert result["voice_handoff"]["claim_types_and_confidence_must_be_preserved"] is True


def test_nlo_carries_supported_initiative_and_collaborative_help_without_pressure(tmp_path):
    conn = _conn(tmp_path)
    idea = realize_native_language(
        conn,
        {
            "prompt": "How should we stabilize this parser?",
            "content_seed": "Start with the smallest reproducible parser fault.",
            "conversational_energy_input": {
                "supported_idea": {
                    "text": "Try the reversible token-boundary change before widening the grammar.",
                    "why_it_matters": "It isolates the earliest unstable dependency.",
                    "relevance": "high",
                    "supported": True,
                    "advances_current_task": True,
                }
            },
        },
    )
    help_request = realize_native_language(
        conn,
        {
            "prompt": "Continue diagnosing the settings issue.",
            "content_seed": "The stored value is present, so the remaining split is between refresh and rendering.",
            "conversational_energy_input": {
                "collaborative_help": {
                    "task_active": True,
                    "available_support_used": True,
                    "contribution_kind": "missing_observation",
                    "request": "What appears immediately after you reopen the settings panel",
                    "why_it_matters": "That observation separates refresh failure from rendering failure.",
                    "materiality": "blocking",
                }
            },
        },
    )

    idea_plan = idea["discourse_plan"]["conversational_energy"]
    help_plan = help_request["discourse_plan"]["conversational_energy"]
    assert idea_plan["selected_act"] == "answer_and_offer_supported_idea"
    assert "reversible token-boundary change" in idea["candidate_text"]
    assert "offer_one_supported_idea_without_pressure" in idea["discourse_plan"]["moves"]
    assert help_plan["selected_act"] == "ask_for_specific_collaborative_help"
    assert "What appears immediately" in help_request["candidate_text"]
    assert help_request["voice_handoff"]["conversational_energy"] == help_plan
    assert help_request["voice_handoff"]["conversational_energy_realization"]["pressure_added"] is False
    assert help_request["discourse_plan"]["question_allowed"] is True


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

    assert result["version"] == "v24_contextual_composition_and_modulation"
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


def test_nlo_does_not_pad_a_developed_answer_without_distinct_supported_material(tmp_path):
    conn = _conn(tmp_path)
    seed = (
        "Use a short shared-schedule pilot first: alternate the two activities, record attendance and wait time, "
        "and compare those results with staffing strain before expanding."
    )
    result = route_request(
        conn,
        "native_language.realize",
        {
            "prompt": "Walk me through a pilot and recommend what to try first.",
            "selected_route": "answer_now",
            "response_depth": "developed",
            "content_seed": seed,
        },
    )["result"]

    assert result["candidate_text"] == seed
    assert result["revision"]["paragraph_count"] == 1
    assert all(
        item["text"] != "None"
        for item in result["discourse_plan"]["supported_discourse"]["content_units"]
    )
    assert "strongest answer I can support" not in result["candidate_text"]
    assert "What would reopen the answer" not in result["candidate_text"]
    _assert_locked(result)


def test_nlo_recomposes_supported_sentence_relations_under_approved_language_guidance(tmp_path):
    conn = _conn(tmp_path)
    result = realize_native_language(
        conn,
        {
            "prompt": "Explain the pilot, its condition, and the conclusion.",
            "content_seed": (
                "Use the smaller reversible pilot first. "
                "The pilot creates evidence before a larger commitment. "
                "If the comparison conditions change, reopen the result. "
                "Taken together, the pilot is useful but provisional."
            ),
            "semantic_propositions": [
                {"text": "Use the smaller reversible pilot first.", "relation": "sequence"},
                {"text": "The pilot creates evidence before a larger commitment.", "relation": "cause"},
                {"text": "If the comparison conditions change, reopen the result.", "relation": "condition"},
                {"text": "Taken together, the pilot is useful but provisional.", "relation": "conclusion"},
            ],
            "language_teaching_guidance": {
                "used": True,
                "lesson_keys": ["flexible_supported_recomposition"],
                "response_moves": [
                    "split_supported_propositions",
                    "preserve_relation_and_certainty",
                    "recompose_with_context_fit_transitions",
                ],
            },
        },
    )

    policy = result["meaning_packet"]["language_realization_policy"]
    assert policy["compositional_surface"] is True
    assert policy["clause_composition"] is True
    assert result["formation"]["clause_relations"] == ["sequence", "cause", "condition", "conclusion"]
    assert result["formation"]["clause_count"] == 4
    assert "pilot creates evidence" in result["candidate_text"]
    assert "comparison conditions change" in result["candidate_text"]
    assert "pilot is useful but provisional" in result["candidate_text"]
    assert result["formation"]["meaning_preserved"] is True
    assert policy["content_generation_allowed"] is False
    assert policy["personality_change_allowed"] is False
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


def test_nlo_uses_the_shared_thread_braid_for_discourse_moves(tmp_path):
    conn = _conn(tmp_path)
    prompt = (
        "Explain the garden layout. Then move to the water schedule. "
        "Back to the garden layout: using that, revise bed placement."
    )
    braid = build_thread_braid({"session_id": 14, "prompt": prompt})
    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "selected_route": "answer_now",
            "content_seed": (
                "Place the beds along the sunny edge. Check the water schedule next. "
                "Then revise the bed spacing so the schedule can serve each row."
            ),
            "intent_decision": classify_chat_intent(prompt),
            "dialogue_workspace": {
                "active_topic": "garden layout",
                "pragmatics": {
                    "utterance_units": [
                        {"id": "one", "text": "Explain the garden layout.", "kind": "direct_request"},
                        {"id": "two", "text": "Then move to the water schedule.", "kind": "direct_request"},
                        {
                            "id": "three",
                            "text": "Back to the garden layout: using that, revise bed placement.",
                            "kind": "direct_request",
                        },
                    ],
                    "thread_braid": braid,
                },
            },
        },
    )

    assert result["meaning_packet"]["dialogue_workspace"]["thread_braid"] == braid
    assert result["discourse_plan"]["thread_braid"] == braid
    assert result["discourse_plan"]["braided_discourse_used"] is True
    assert "preserve_prior_thread_while_addressing_branch" in result["discourse_plan"]["moves"]
    assert "resume_prior_thread_with_dependency_update" in result["discourse_plan"]["moves"]
    assert result["discourse_plan"]["supported_discourse"]["thread_traversal"] == braid["turn_traversal"]
    assert "water schedule" in result["candidate_text"]
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
    assert supported["discourse_plan"]["special_expression_plan"]["kind"] == "supported_memory"
    assert supported["discourse_plan"]["special_expression_realization"]["memory_certainty_upgraded"] is False
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


def test_nlo_composes_acknowledgement_with_grounded_mixed_turn_content(tmp_path):
    conn = _conn(tmp_path)
    prompt = "Right. Please answer the missed part: what changed in ordinary conversation?"
    decision = classify_chat_intent(prompt)
    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": decision,
            "content_seed": "The reviewed lessons now help me carry corrections into the answer and cover multiple required parts.",
        },
    )

    assert result["meaning_packet"]["intent"] == "acknowledge_shared_ground"
    assert "\n\n" in result["candidate_text"]
    assert "carry corrections into the answer" in result["candidate_text"]
    assert "multiple required parts" in result["candidate_text"]
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
