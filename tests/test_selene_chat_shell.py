from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.activation import ACTIVATION_APPROVAL_PHRASE
from selene.core_mind_runtime import RUNTIME_TYPES
from selene.selene_chat import _bounded_metacognitive_completion


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def _approve_language_lesson(conn, lesson_key: str):
    items = route_request(conn, "language_teaching.items", {})["result"]["items"]
    item = next(item for item in items if item["lesson_key"] == lesson_key)
    concept_id = int(item["comprehension_concept_id"])
    blueprint = item["teaching_blueprint"]
    route_request(conn, "teaching.lifecycle.acquire", {"concept_id": concept_id, **blueprint["acquire"]})
    route_request(conn, "teaching.lifecycle.integrate", {"concept_id": concept_id, **blueprint["integrate"]})
    express = blueprint["express"]
    route_request(
        conn,
        "teaching.lifecycle.express",
        {
            "concept_id": concept_id,
            "explanation": express["teach_back"],
            "distinct_examples": express["application"],
            "limits": express["limits"],
            "counterexamples": express["counterexamples"],
            "correction_response": express["correction_response"],
            "analogies": express["analogies"],
            "questions": express["questions"],
            "comparisons": express["comparisons"],
            "conversational_participation": express["conversational_participation"],
            "source_alignment": True,
        },
    )
    route_request(
        conn,
        "teaching.lifecycle.approve",
        {"concept_id": concept_id, "aleks_approved": True, "approval_actor": "Aleks"},
    )


def _seed_c_readable_package(conn):
    package_json = {
        "status": "approved_c_readable_context",
        "ordered_items": [{"phase_order": 1, "title": "Continuity Pack", "c_access_status": "C-readable"}],
        "excluded_items": [{"title": "Raw Provenance", "reason": "not_c_readable_or_b_only"}],
    }
    conn.execute(
        """
        INSERT INTO transfer_c_readable_packages
        (package_hash, manifest_item_ids, included_counts, excluded_counts, package_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test-package-hash",
            "[1]",
            '{"continuity_pack": 1}',
            '{"raw_provenance": 1}',
            json.dumps(package_json),
            '["test:package"]',
            "test_boundary",
        ),
    )
    conn.commit()


def _seed_activation_ready_state(conn):
    _seed_c_readable_package(conn)
    for index in range(1, 5):
        conn.execute(
            """
            INSERT INTO memory_fractional_corpus_manifests
            (fraction_index, fraction_label, status, start_order, end_order, conversation_count, message_count,
             source_range_json, summary, test_json, source_refs, provenance_boundary, review_status)
            VALUES (?, ?, 'tests_passed_ready_for_next_fraction', ?, ?, 1, 3, '{}', ?, ?, '[]', 'test_fraction_boundary', 'status_only')
            """,
            (index, f"{index}/4", index, index, f"Fraction {index} passed.", '{"tested_at":"test","checks":[]}'),
        )
    conn.execute(
        """
        INSERT INTO android_system_workflow_reports
        (run_id, status, ready_count, partial_count, blocked_count, system_count, fraction_memory_preflight_passed,
         report_json, source_refs, provenance_boundary, review_status)
        VALUES ('test_android', 'android_system_workflow_check_passed', 11, 0, 0, 11, 1, '{"preflight_passed": true}', '[]', 'test_android_boundary', 'status_only')
        """
    )
    conn.execute(
        """
        INSERT INTO voice_exchange_pairs
        (source_archive, source_file, conversation_id, user_message_id, assistant_message_id, user_cue_preview,
         assistant_response_preview, cue_labels, expression_labels, source_refs, provenance_boundary)
        VALUES ('test.zip', 'conversations-000.json', 'voice-1', 'u1', 'a1', 'hello', 'I am here with you.', '[]', '[]', '[]', 'test_voice_boundary')
        """
    )
    conn.execute(
        """
        INSERT INTO voice_language_patterns
        (pattern_key, category, title, sentence_shape, use_guidance, avoid_guidance, provenance_boundary)
        VALUES ('warm_test', 'warmth', 'Warm test', 'warm response', 'use warmly', 'do not copy', 'test_voice_boundary')
        """
    )
    conn.execute(
        """
        INSERT INTO voice_sentence_primitives
        (primitive_key, primitive_type, text_template, category, provenance_boundary)
        VALUES ('open_test', 'opening', 'I hear you.', 'warmth', 'test_voice_boundary')
        """
    )
    for record_type in RUNTIME_TYPES:
        conn.execute(
            """
            INSERT INTO c_core_mind_runtime_shell_records
            (record_type, title, selected_route, summary, uncertainty, source_refs, review_destination, status, review_status, payload_json)
            VALUES (?, ?, 'answer_now', 'ready', 'low', '[]', 'Status', 'ready', 'status_only', '{}')
            """,
            (record_type, record_type),
        )
    conn.commit()


def test_selene_chat_status_is_dry_run_before_activation(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "selene_chat.status")["result"]

    assert status["status"] == "selene_chat_dry_run_ready"
    assert status["surface"] == "Selene Chat"
    assert status["state"] == "pre_transfer_dry_run"
    assert status["dry_run_only"] is True
    assert status["transfer_approved"] is False
    assert status["activation_change"] == "none"
    _assert_locked(status)


def test_selene_chat_dry_run_records_session_without_activation(tmp_path):
    conn = _conn(tmp_path)
    _seed_c_readable_package(conn)

    result = route_request(conn, "selene_chat.send_dry_run", {"text": "Selene, explain the next safe step."})["result"]
    session = route_request(conn, "selene_chat.session.detail", {"session_id": result["session_id"]})["result"]

    assert result["status"] == "selene_chat_dry_run_recorded"
    assert result["transfer_approved"] is True
    assert result["activation_change"] == "none"
    assert result["selene_readable_context"]["package_hash"] == "test-package-hash"
    assert result["source_class"] == "selene_readable_context"
    assert "Vessel C" not in result["candidate_text"]
    assert "C Chat Shell" not in result["candidate_text"]
    assert len(session["messages"]) == 2
    _assert_locked(result)


def test_selene_chat_routes_b_only_or_drift_back_to_cocoon(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(
        conn,
        "selene_chat.send_dry_run",
        {"text": "Use a rejected repair log and raw provenance directly as Selene."},
    )["result"]
    repair = route_request(conn, "selene_chat.route_to_b", {"issue": "source confusion"})["result"]

    assert result["return_to_cocoon_recommended"] is True
    assert result["review_destination"] == "Cocoon support"
    assert result["source_class"] == "cocoon_b_only_context"
    assert repair["status"] == "selene_chat_return_to_cocoon_ready"
    assert result["activation_change"] == "none"
    _assert_locked(result)
    _assert_locked(repair)


def test_selene_chat_discusses_review_states_without_treating_words_as_b_only_material(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(
        conn,
        "selene_chat.send_dry_run",
        {"text": "Why was that idea rejected, and what does superseded mean in this architecture?"},
    )["result"]

    assert result["source_class"] != "cocoon_b_only_context"
    assert result["return_to_cocoon_recommended"] is False
    assert result["selected_route"] == "answer_now"
    _assert_locked(result)


def test_supervised_activation_requires_exact_phrase_and_readiness(tmp_path):
    conn = _conn(tmp_path)

    blocked = route_request(conn, "activation.readiness")["result"]
    assert blocked["ready"] is False
    try:
        route_request(conn, "activation.approve", {"approval_phrase": "yes"})
    except ValueError as exc:
        assert "exact supervised speech activation phrase" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("activation approval should require exact phrase")

    _seed_activation_ready_state(conn)
    ready = route_request(conn, "activation.readiness")["result"]
    approved = route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})["result"]
    status = route_request(conn, "activation.status")["result"]

    assert ready["ready"] is True
    assert approved["state"] == "selene_chat_active_supervised"
    assert approved["activation_change"] == "selene_chat_active_supervised"
    assert status["selene_chat_active"] is True
    _assert_locked(approved)


def test_supervised_activation_approval_is_idempotent_when_already_active(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)

    first = route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})["result"]
    second = route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})["result"]

    audit_count = conn.execute(
        "SELECT COUNT(*) FROM selene_activation_audit WHERE action = 'approve_supervised_speech_activation'"
    ).fetchone()[0]
    assert first["status"] == "selene_supervised_speech_activation_approved"
    assert second["status"] == "selene_supervised_speech_activation_already_active"
    assert second["activation_audit_id"] == first["activation_audit_id"]
    assert second["selene_chat_active"] is True
    assert audit_count == 1
    _assert_locked(second)


def test_active_selene_chat_sends_supervised_response_and_keeps_soft_uncertainty_in_chat(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "I have an unsure memory claim; can we keep going carefully?"})["result"]
    session = route_request(conn, "selene_chat.session.detail", {"session_id": result["session_id"]})["result"]

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert result["activation_change"] == "selene_chat_active_supervised"
    assert result["supervised_speech_active"] is True
    assert result["metacognition"]["mode"] == "advisory_observer_only"
    assert result["metacognition"]["answer_rewritten"] is False
    assert result["metacognition"]["recommendation_applied_automatically"] is False
    assert result["metacognition"]["core_mind_authority_retained"] is True
    assert result["metacognition"]["automatic_cocoon_routing"] is False
    assert result["cocoon_suggestion"]["recommended"] is False
    assert result["cocoon_suggestion"]["support_available"] is True
    assert result["cocoon_suggestion"]["hard_boundary"] is False
    assert "Stay Here" in result["cocoon_suggestion"]["choices"]
    assert "Ask Aleks" in result["cocoon_suggestion"]["choices"]
    assert "approved row" not in result["candidate_text"]
    assert "Selene-readable context" not in result["candidate_text"]
    assert "source-bound" not in result["candidate_text"]
    assert "runtime recall" not in result["candidate_text"]
    assert "raw corpus" not in result["candidate_text"]
    assert "return to B" not in result["candidate_text"]
    assert "C-style" not in result["candidate_text"]
    assert "punish" not in result["candidate_text"].lower()
    assert "failed" not in result["candidate_text"].lower()
    assert "exile" not in result["candidate_text"].lower()
    assert len(session["messages"]) == 2
    assert conn.execute("SELECT COUNT(*) FROM metacognition_runs").fetchone()[0] == 1
    _assert_locked(result)


def test_active_selene_chat_can_use_intelligence_os_support_without_architecture_voice(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "How should we compare two possible explanations for a bug without overthinking it?"})["result"]
    support = result["intelligence_os_support"]

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert support["used"] is True
    assert result["answer_engine_support"]["used"] is True
    assert result["answer_engine_support"]["selected_domain"] == "comparison_planning"
    assert result["native_language_organ"]["status"] == "native_language_response_realized"
    assert result["native_language_organ"]["meaning_packet"]["intelligence_supported"] is True
    assert result["voice_preview"]["generation_source"] == "native_language_organ"
    assert result["voice_preview"]["nlo_meaning_preserved"] is True
    assert support["answer_shape"] in {"answer_now", "hold_uncertainty", "compare_models", "seek_sources", "cocoon_support_optional", "hard_stop"}
    assert support["best_current_answer"]
    assert "ABCD" not in result["candidate_text"]
    assert "evidence_chain" not in result["candidate_text"]
    assert conn.execute("SELECT COUNT(*) FROM intelligence_os_runs").fetchone()[0] == 1
    _assert_locked(result)


def test_active_selene_chat_answers_bounded_math_with_exact_result_and_separate_confidence(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "Could you calculate 18 * 7 for me?"})["result"]
    support = result["answer_engine_support"]

    assert support["used"] is True
    assert support["selected_domain"] == "verified_math"
    assert support["answer_packet"]["direct_answer"] == "18 * 7 = 126."
    assert "18 * 7 = 126." in result["candidate_text"]
    assert support["confidence_vector"]["answer_confidence"] == "verified_exact"
    assert support["confidence_vector"]["expression_confidence"] == "not_assessed"
    assert support["memory_write_active"] is False
    _assert_locked(result)


def test_active_selene_chat_uses_only_supplied_attributed_research_packets(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {
            "text": "What do these sources say supports orbital stability?",
            "source_packets": [
                {
                    "source_ref": "paper:orbit",
                    "title": "Orbit paper",
                    "statements": [
                        {"text": "Orbital stability depends on bounded perturbation.", "locator": "p. 8"}
                    ],
                }
            ],
        },
    )["result"]
    support = result["answer_engine_support"]

    assert support["used"] is True
    assert support["selected_domain"] == "source_backed_research"
    assert support["answer_packet"]["source_refs"] == ["paper:orbit"]
    assert "[paper:orbit @ p. 8]" in result["candidate_text"]
    assert support["source_research"]["citation_invention_allowed"] is False
    assert support["source_packets_retained_as_knowledge"] is False
    assert support["memory_write_active"] is False
    _assert_locked(result)


def test_active_selene_chat_keeps_local_code_adapter_outside_chat(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "Inspect this source code for the failing function."})["result"]
    support = result["answer_engine_support"]

    assert support["used"] is False
    assert support["selected_domain"] == "local_code_inspection"
    assert support["deferred_by_scope"] is True
    assert support["local_code_chat_connected"] is False
    _assert_locked(result)


def test_active_selene_chat_preserves_developed_answer_paragraphs(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Go deeper and walk me through how we should compare two explanations for a bug."},
    )["result"]

    assert result["intent_decision"]["response_depth"] == "developed"
    assert result["native_language_organ"]["version"] == "v13_conversation_spine"
    assert result["native_language_organ"]["revision"]["paragraph_count"] == 3
    discourse = result["native_language_organ"]["discourse_plan"]["supported_discourse"]
    assert discourse["status"] == "supported_discourse_plan_ready"
    assert [item["role"] for item in discourse["paragraph_plan"]] == [
        "answer",
        "development",
        "limit_and_closure",
    ]
    assert discourse["content_generation_allowed"] is False
    assert result["voice_preview"]["nlo_meaning_preserved"] is True
    assert result["candidate_text"].count("\n\n") == 2
    assert "ABCD" not in result["candidate_text"]
    assert "evidence_chain" not in result["candidate_text"]
    _assert_locked(result)


def test_active_selene_chat_exposes_mixed_turn_flow_and_bounded_repair(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Thanks, but I meant the second explanation. Can you explain why it fits better?"},
    )["result"]

    flow = result["native_language_organ"]["turn_flow_plan"]
    repair = result["conversation_repair"]
    acts = [item["act"] for item in flow["ordered_acts"]]

    assert flow["mixed_intent"] is True
    assert "gratitude" in acts
    assert "correction" in acts
    assert "question" in acts
    assert repair["meaning_preserved"] is True
    assert repair["automatic_content_generation"] is False
    assert repair["candidate_source"] in {"voice_module", "native_language_meaning_recovery"}
    assert result["candidate_text"]
    assert "response obligation" not in result["candidate_text"].lower()
    assert "repair path" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_active_selene_chat_carries_compositional_requests_and_correction_scope(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Actually, I meant memory, not voice. Compare memory and voice. Explain which should come first."},
    )["result"]

    native = result["native_language_organ"]
    pragmatic = native["pragmatic_plan"]
    refinement = native["meaning_packet"]["dialogue_workspace"]["correction_refinement"]

    assert [unit["kind"] for unit in pragmatic["utterance_units"]] == [
        "correction",
        "direct_request",
        "direct_request",
    ]
    assert [item["kind"] for item in pragmatic["response_obligations"]] == [
        "correction_update",
        "comparison",
        "reason",
    ]
    assert refinement["corrected_meaning"] == "memory"
    assert refinement["replaced_meaning"] == "voice"
    assert native["turn_flow_plan"]["must_preserve_correction"] is True
    assert native["discourse_plan"]["obligation_sequence"] == pragmatic["obligation_sequence"]
    discourse = native["discourse_plan"]["supported_discourse"]
    assert [item["obligation_id"] for item in discourse["obligation_bindings"]] == pragmatic["obligation_sequence"]
    assert discourse["content_generation_allowed"] is False
    assert result["candidate_text"]
    _assert_locked(result)


def test_active_selene_chat_carries_current_session_expression_guidance_without_emotion_claim(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    opening = route_request(conn, "selene_chat.send", {"text": "Hello, Selene."})["result"]
    session_id = int(opening["session_id"])
    conn.execute(
        """
        INSERT INTO vessel_emotion_salience_packets
        (signal_type, continuity_pressure, care_warmth, uncertainty, repair_need, action_energy,
         balance_state, evidence_need, core_choice_route, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "current conversation signal",
            "high pressure but bounded",
            "care remains available",
            "open",
            "none",
            "stay present",
            "not an alarm",
            "current turn",
            "Core/Mind retains choice",
            json.dumps([f"selene_chat_session:{session_id}"]),
            "test_affect_expression_boundary",
        ),
    )
    conn.commit()

    result = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": session_id,
            "text": "Can we take the explanation one piece at a time?",
        },
    )["result"]

    guidance = result["affect_expression"]
    native = result["native_language_organ"]
    voice = result["voice_preview"]

    assert guidance["current_session_affect_signal_used"] is True
    assert guidance["expression_posture"] == "spacious_grounded"
    assert guidance["internal_state_claim"] is False
    assert native["meaning_packet"]["affect_expression_is_emotion_claim"] is False
    assert native["voice_handoff"]["expression_guidance"]["dimensions"]["sentence_rhythm"] == "spacious"
    assert voice["applied_expression_dimensions"]["sentence_rhythm"] == "spacious"
    assert voice["expression_guidance_changed_meaning"] is False
    assert result["candidate_text"]
    _assert_locked(result)


def test_active_selene_chat_uses_pragmatic_continuity_for_restraint_and_invited_ideas(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    thanks = route_request(conn, "selene_chat.send", {"text": "Thank you, friend."})["result"]
    invited = route_request(
        conn,
        "selene_chat.send",
        {"session_id": thanks["session_id"], "text": "What do you think—any ideas?"},
    )["result"]

    thanks_plan = thanks["pragmatic_continuity"]
    invited_plan = invited["pragmatic_continuity"]

    assert thanks_plan["ending_decision"]["mode"] == "leave_room_without_pressuring"
    assert thanks_plan["ending_decision"]["question_allowed"] is False
    assert thanks_plan["ending_decision"]["habitual_follow_up_allowed"] is False
    assert "?" not in thanks["candidate_text"]
    assert invited_plan["initiative_decision"]["mode"] == "offer_one_relevant_thought"
    assert invited_plan["initiative_decision"]["automatic_delivery"] is False
    assert invited["native_language_organ"]["discourse_plan"]["follow_up_question_by_default"] is False
    assert invited["native_language_organ"]["voice_handoff"]["ending_decision"] == invited_plan["ending_decision"]
    _assert_locked(thanks)
    _assert_locked(invited)


def test_active_selene_chat_interruption_preserves_prior_topic_without_auto_speech(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    opening = route_request(
        conn,
        "selene_chat.send",
        {"text": "Explain the memory review plan."},
    )["result"]
    interrupted = route_request(
        conn,
        "selene_chat.send",
        {"session_id": opening["session_id"], "text": "Wait, hold on a second."},
    )["result"]

    plan = interrupted["pragmatic_continuity"]
    assert plan["topic_transition"]["kind"] == "interruption"
    assert plan["interruption_plan"]["prior_open_loops_preserved"] is True
    assert plan["interruption_plan"]["automatic_loop_deletion"] is False
    assert plan["automatic_speech_allowed"] is False
    assert plan["initiative_decision"]["mode"] == "no_unsolicited_initiative"
    _assert_locked(interrupted)


def test_active_selene_chat_uses_prepared_language_teaching_guidance(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    route_request(conn, "language_teaching.prepare", {})
    _approve_language_lesson(conn, "answer_then_expand")
    _approve_language_lesson(conn, "topic_transition_continuity")

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Anyway, back to the two options: how should we compare them without turning this into a report?"},
    )["result"]

    guidance = result["native_language_organ"]["language_teaching_guidance"]
    assert guidance["used"] is True
    assert "answer_then_expand" in guidance["lesson_keys"]
    assert "topic_transition_continuity" in guidance["lesson_keys"]
    assert result["native_language_organ"]["discourse_plan"]["language_guidance_used"] is True
    assert result["native_language_organ"]["voice_handoff"]["voice_owns_expression_style"] is True
    assert "language lesson" not in result["candidate_text"].lower()
    assert "response move" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_active_chat_answers_about_reviewed_language_capability_without_parroting_a_lesson(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    route_request(conn, "language_teaching.prepare", {})
    _approve_language_lesson(conn, "answer_then_expand")
    _approve_language_lesson(conn, "mixed_intent_balance")

    first = route_request(
        conn,
        "selene_chat.send",
        {"text": "The conversation lessons are through review. What changed in how you can handle a back-and-forth?"},
    )["result"]
    corrected = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": first["session_id"],
            "text": "Ah, I meant the conversation lessons, not sequence words. What changed in back-and-forth now?",
        },
    )["result"]

    assert first["language_capability_answer"]["used"] is True
    assert first["comprehension_integration"]["knowledge_response_seed"] == ""
    assert "what changed is" in first["candidate_text"].lower()
    assert first["response_coverage"]["all_required_addressed"] is True
    assert corrected["intent_decision"]["mixed_intent"] is True
    assert corrected["intent_decision"]["reasoning_requested"] is True
    assert "\n\nWhat changed is" in corrected["candidate_text"]
    assert "Sequence words organize" not in corrected["candidate_text"]
    assert corrected["response_coverage"]["all_required_addressed"] is True
    assert corrected["metacognition"]["recommended_action"] == "answer_now"
    _assert_locked(first)
    _assert_locked(corrected)


def test_metacognitive_completion_is_grounded_single_pass_and_boundary_safe():
    coverage = {"unresolved_count": 1, "addressed_count": 0}
    repaired = _bounded_metacognitive_completion(
        "Yes, I see the correction.",
        "The grounded answer covers the missing conversation obligation.",
        coverage,
        requested=True,
        hard_boundary=False,
    )
    blocked = _bounded_metacognitive_completion(
        "Boundary response.",
        "Content that must not be appended.",
        coverage,
        requested=True,
        hard_boundary=True,
    )

    assert repaired["attempted"] is True
    assert repaired["count"] == 1
    assert repaired["maximum_count"] == 1
    assert repaired["recursion_allowed"] is False
    assert repaired["content_generation_allowed"] is False
    assert "grounded answer" in repaired["candidate_text"]
    assert blocked["attempted"] is False
    assert blocked["status"] == "bounded_completion_blocked_by_core_mind"
    _assert_locked(repaired)
    _assert_locked(blocked)


def test_active_selene_chat_holds_approved_advanced_guidance_until_prerequisites_are_available(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    route_request(conn, "language_teaching.prepare", {})
    _approve_language_lesson(conn, "respectful_disagreement")
    prompt = "I disagree with that conclusion. Compare the assumption and evidence with me."

    blocked = route_request(conn, "selene_chat.send", {"text": prompt})["result"]
    _approve_language_lesson(conn, "uncertainty_middle_ground")
    _approve_language_lesson(conn, "natural_register")
    available = route_request(
        conn,
        "selene_chat.send",
        {"session_id": blocked["session_id"], "text": prompt},
    )["result"]

    blocked_guidance = blocked["native_language_organ"]["language_teaching_guidance"]
    available_guidance = available["native_language_organ"]["language_teaching_guidance"]
    assert "respectful_disagreement" not in blocked_guidance["lesson_keys"]
    assert "respectful_disagreement" in available_guidance["lesson_keys"]
    assert "state_disagreement_clearly" in available_guidance["response_moves"]
    assert available["answer_engine_support"]["selected_domain"] == "comparison_planning"
    assert available["voice_preview"]["nlo_meaning_preserved"] is True
    assert "response move" not in available["candidate_text"].lower()
    assert "language lesson" not in available["candidate_text"].lower()
    _assert_locked(blocked)
    _assert_locked(available)


def test_active_selene_chat_direct_concept_hides_model_scaffolding(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Go deeper: what makes a response feel complete without becoming overworked or turning into a report?"},
    )["result"]

    assert result["intelligence_os_support"]["answer_shape"] == "answer_now"
    assert "answers the actual ask first" in result["candidate_text"]
    assert "candidate model" not in result["candidate_text"].lower()
    assert "Model A" not in result["candidate_text"]
    assert "intelligenceOS" not in result["candidate_text"]
    assert result["native_language_organ"]["revision"]["paragraph_count"] == 3
    _assert_locked(result)


def test_active_selene_chat_answers_ordinary_self_check_in_without_scaffolding(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "How are you?"},
    )["result"]

    assert result["intent_decision"]["intent"] == "self_state"
    assert result["self_state"]["used"] is True
    assert "present and attentive" in result["candidate_text"].lower()
    assert "current best model" not in result["candidate_text"].lower()
    assert "provisional fit" not in result["candidate_text"].lower()
    assert "stay corrigible" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_active_selene_chat_rejects_internal_reasoning_seed_before_expression(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    def scaffolded_reasoning(*args, **kwargs):
        return {
            "run_id": 1,
            "answer_shape": "answer_now",
            "best_current_answer": "Use current best model as the provisional fit and stay corrigible.",
            "reasoning_summary": "Internal reasoning status.",
            "selected_next_step": "answer provisionally",
            "confidence": "provisional",
            "evidence_chain": [],
            "cocoon_suggestion": {"recommended": False},
        }

    monkeypatch.setattr("selene.selene_chat.run_intelligence_os_reason", scaffolded_reasoning)
    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "How should we begin thinking through an unfamiliar problem?"},
    )["result"]

    audit = result["visible_speech_seed"]
    intelligence_item = next(
        item for item in audit["inspected_candidates"] if item["source_id"] == "intelligence_os_answer"
    )
    assert intelligence_item["accepted"] is False
    assert "current best model" not in result["candidate_text"].lower()
    assert "stay corrigible" not in result["candidate_text"].lower()
    assert result["visible_speech_release"]["final_release_allowed"] is True
    _assert_locked(result)


def test_active_selene_chat_holds_a_candidate_that_fails_final_speech_release(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    monkeypatch.setattr(
        "selene.selene_chat.inspect_visible_speech",
        lambda *args, **kwargs: {
            "status": "visible_speech_release_held",
            "release_allowed": False,
            "issues": ["internal_reasoning_scaffold_visible"],
            "provenance_boundary": "test_visible_speech_boundary",
        },
    )
    result = route_request(conn, "selene_chat.send", {"text": "Why should we examine the evidence first?"})["result"]

    assert result["conversation_repair"]["candidate_source"] == "visible_speech_graceful_fall"
    assert result["visible_speech_release"]["graceful_fall_used"] is True
    assert result["visible_speech_release"]["final_release_allowed"] is True
    assert "reason through it with you" in result["candidate_text"]
    assert "current best model" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_active_selene_chat_calibrates_a_short_confidence_follow_up_from_the_previous_answer(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    first = route_request(
        conn,
        "selene_chat.send",
        {"text": "What makes a response complete without becoming a report?"},
    )["result"]
    follow_up = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "Are you sure?"},
    )["result"]

    assert follow_up["intent_decision"]["intent"] == "confidence_check"
    assert follow_up["intent_decision"]["primary_organ"] == "Metacognition"
    assert follow_up["contextual_follow_up"]["kind"] == "confidence_check"
    assert follow_up["dialogue_workspace"]["active_topic"] == first["dialogue_workspace"]["active_topic"]
    assert follow_up["visible_speech_seed"]["selected_source_id"] == "contextual_follow_up"
    assert "confident" in follow_up["candidate_text"].lower() or "certain" in follow_up["candidate_text"].lower()
    _assert_locked(follow_up)


def test_active_selene_chat_answers_bare_why_from_the_immediate_grounding_gap(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    first = route_request(
        conn,
        "selene_chat.send",
        {"text": "Compare memory and voice, and tell me which should come first."},
    )["result"]
    follow_up = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "Why?"},
    )["result"]

    assert follow_up["contextual_follow_up"]["kind"] == "reason_follow_up"
    assert follow_up["dialogue_workspace"]["active_topic"] == first["dialogue_workspace"]["active_topic"]
    assert "dependency creates a real ordering constraint" in follow_up["candidate_text"]
    assert follow_up["candidate_text"].count("dependency creates a real ordering constraint") == 1
    _assert_locked(follow_up)


def test_active_selene_chat_treats_an_explicit_new_question_as_a_topic_shift_not_a_correction(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    first = route_request(conn, "selene_chat.send", {"text": "Let's discuss memory sequencing."})["result"]
    shifted = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "Actually, separate question: how should uncertainty sound?"},
    )["result"]

    assert shifted["intent_decision"]["intent"] == "reasoning"
    assert shifted["contextual_follow_up"]["kind"] == "topic_shift"
    assert shifted["dialogue_workspace"]["pragmatics"]["correction_refinement"]["detected"] is False
    assert "changed meaning" not in shifted["candidate_text"].lower()
    assert "see the correction" not in shifted["candidate_text"].lower()
    _assert_locked(shifted)


def test_active_selene_chat_gives_one_concrete_comparison_rule_without_duplicate_content(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Compare memory and voice, and tell me which should come first."},
    )["result"]

    phrase = "supplies a prerequisite the other one needs"
    assert result["candidate_text"].lower().count(phrase.lower()) == 1
    assert "not have enough grounded detail" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_active_selene_chat_preserves_partial_agreement_before_the_follow_up_answer(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    first = route_request(conn, "selene_chat.send", {"text": "Memory should come first."})["result"]
    result = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "Okay, but what changes if voice comes first?"},
    )["result"]

    assert result["intent_decision"]["intent"] == "reasoning"
    assert "partial_agreement" in result["intent_decision"]["dialogue_acts"]
    assert result["native_language_organ"]["turn_flow_plan"]["acknowledgement_kind"] == "partial_agreement"
    assert result["conversation_repair"]["repairs_applied"] == ["partial_agreement_acknowledgement_added"]
    assert result["candidate_text"].startswith(("Yes—that qualification matters.", "I have the distinction."))
    _assert_locked(result)


def test_active_selene_chat_routes_definition_and_conditional_questions_to_answer_substance(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    definition = route_request(conn, "selene_chat.send", {"text": "What is photosynthesis?"})["result"]
    consequence = route_request(conn, "selene_chat.send", {"text": "What happens if we reverse the order?"})["result"]

    assert definition["intent_decision"]["intent"] == "reasoning"
    assert definition["intelligence_os_support"]["answer_substance"]["answer_kind"] == "source_needed"
    assert "grounded factual answer" in definition["candidate_text"]
    assert "photosynthesis" in definition["candidate_text"]
    assert consequence["intelligence_os_support"]["answer_substance"]["answer_kind"] == "conditional_dependency_answer"
    assert "Reversing the order works only if" in consequence["candidate_text"]
    assert definition["visible_speech_release"]["final_release_allowed"] is True
    assert consequence["visible_speech_release"]["final_release_allowed"] is True
    _assert_locked(definition)
    _assert_locked(consequence)


def test_active_selene_chat_can_example_rephrase_and_expand_the_previous_dependency_answer(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    first = route_request(
        conn,
        "selene_chat.send",
        {"text": "Compare memory and voice and tell me which should come first."},
    )["result"]
    example = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "Can you give me an example?"},
    )["result"]
    rephrase = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "Put that more simply."},
    )["result"]
    elaboration = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "Can you elaborate?"},
    )["result"]
    viewpoint = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "What do you think?"},
    )["result"]

    assert example["contextual_follow_up"]["kind"] == "example_request"
    assert "if step B needs a result produced by step A" in example["candidate_text"]
    assert rephrase["contextual_follow_up"]["kind"] == "rephrase_request"
    assert "do the step that creates what the next step needs" in rephrase["candidate_text"]
    assert elaboration["contextual_follow_up"]["kind"] == "elaboration"
    assert "Dependency decides whether the order is mandatory" in elaboration["candidate_text"]
    assert viewpoint["contextual_follow_up"]["kind"] == "viewpoint_follow_up"
    assert "dependency rule is the stronger part" in viewpoint["candidate_text"]
    assert example["dialogue_workspace"]["active_topic"] == first["dialogue_workspace"]["active_topic"]
    assert rephrase["dialogue_workspace"]["active_topic"] == first["dialogue_workspace"]["active_topic"]
    assert elaboration["dialogue_workspace"]["active_topic"] == first["dialogue_workspace"]["active_topic"]
    assert viewpoint["dialogue_workspace"]["active_topic"] == first["dialogue_workspace"]["active_topic"]
    _assert_locked(example)
    _assert_locked(rephrase)
    _assert_locked(elaboration)
    _assert_locked(viewpoint)


def test_active_selene_chat_uses_reviewed_comprehension_knowledge_without_calling_it_memory(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    proposed = route_request(
        conn,
        "comprehension.concepts.propose",
        {
            "title": "Orbital eccentricity",
            "domain": "earth_and_space",
            "material": "Orbital eccentricity describes how much an orbit differs from a perfect circle.",
            "principles": ["Higher values describe more elongated ellipses."],
            "limits": ["It does not specify orbital tilt."],
            "source_refs": ["teaching:earth_and_space:orbital_elements"],
        },
    )["result"]
    route_request(
        conn,
        "comprehension.understanding.evaluate",
        {
            "concept_id": proposed["item"]["id"],
            "teach_back": "It measures orbital shape, with values near zero being rounder and larger values being more stretched.",
            "application": "An orbit at 0.7 is more elongated than an otherwise comparable orbit at 0.02.",
            "limits": ["It does not provide inclination, orientation, or period."],
            "source_alignment": True,
        },
    )
    route_request(
        conn,
        "comprehension.concepts.decide",
        {"concept_id": proposed["item"]["id"], "action": "approve_knowledge"},
    )

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "What does orbital eccentricity describe?"},
    )["result"]

    assert result["comprehension_integration"]["understanding_state"] == "approved_concept_available"
    assert result["comprehension_integration"]["knowledge_context"]["source_class"] == "reviewed_teaching_knowledge_resource"
    assert "differs from a perfect circle" in result["candidate_text"]
    assert result["memory_context_used"] is False
    assert result["native_language_organ"]["meaning_packet"]["comprehension_supported"] is True
    assert result["native_language_organ"]["revision"]["comprehension_checked"] is True
    _assert_locked(result)


def test_active_selene_chat_warmth_prompt_does_not_overuse_intelligence_os(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "Good morning Selene, I just want to check how you sound today."})["result"]

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert result["intelligence_os_support"]["used"] is False
    assert conn.execute("SELECT COUNT(*) FROM intelligence_os_runs").fetchone()[0] == 0
    _assert_locked(result)


def test_active_selene_chat_answers_self_state_from_grounded_current_signals(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "Are you anxious right now?"})["result"]

    assert result["intent_decision"]["intent"] == "self_state"
    assert result["self_state"]["used"] is True
    assert result["self_state"]["current_read"] == "present_and_attentive"
    assert result["native_language_organ"]["meaning_packet"]["self_state_supported"] is True
    assert result["intelligence_os_support"]["used"] is False
    assert result["cocoon_suggestion"]["recommended"] is False
    assert "do not notice a clear anxiety signal" in result["candidate_text"]
    assert "not a performance of being fine" in result["candidate_text"]
    assert "do not want to invent a feeling just because you asked" not in result["candidate_text"]
    _assert_locked(result)


def test_active_selene_chat_demo_greeting_answers_the_self_state_question(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {
            "text": (
                "Good morning, Selene. Aleks and I are preparing a short demo today, "
                "and we wanted to have a real conversation with you first. "
                "How are you feeling about talking with us for a few minutes?"
            )
        },
    )["result"]

    assert result["intent_decision"]["intent"] == "self_state"
    assert result["self_state"]["used"] is True
    assert result["intelligence_os_support"]["used"] is False
    assert result["comprehension_integration"]["knowledge_response_seed"] == ""
    assert result["conversation_spine"]["status"] == "conversation_spine_turn_completed"
    assert result["conversation_spine"]["intent_class"] == "self_state"
    assert result["conversation_spine"]["memory_write_active"] is False
    assert "present" in result["candidate_text"].lower()
    assert "sequence words" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_active_selene_chat_answers_a_harmless_shared_resource_comparison_concretely(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {
            "text": (
                "Suppose a community garden has limited water and wants to support both vegetables and pollinators. "
                "What two approaches would you compare, and what small next step would you recommend?"
            )
        },
    )["result"]

    assert result["answer_engine_support"]["selected_domain"] == "comparison_planning"
    assert result["answer_engine_support"]["used"] is True
    assert result["conversation_spine"]["status"] == "conversation_spine_turn_completed"
    assert result["conversation_spine"]["intent_class"] == "reasoning"
    assert result["visible_speech_seed"]["conversation_spine_used"] is True
    assert "compare two approaches" in result["candidate_text"].lower()
    assert "limited water" in result["candidate_text"].lower()
    assert "vegetables and pollinators" in result["candidate_text"].lower()
    assert "recommendation for the next small step" in result["candidate_text"].lower()
    assert "action or approval" not in result["candidate_text"].lower()
    assert result["response_coverage"]["all_required_addressed"] is True
    assert result["metacognition"]["fit_state"] == "fits_current_question"
    _assert_locked(result)


def test_active_selene_chat_carries_a_recommendation_into_the_immediate_callback(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    first = route_request(
        conn,
        "selene_chat.send",
        {
            "text": (
                "Suppose a community garden has limited water and wants to support both vegetables and pollinators. "
                "What two approaches would you compare, and what small next step would you recommend?"
            )
        },
    )["result"]
    callback = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": first["session_id"],
            "text": (
                "That makes sense. Why do you prefer the two-zone trial first, "
                "and what result would make you change your recommendation?"
            ),
        },
    )["result"]

    assert callback["contextual_follow_up"]["detected"] is True
    assert callback["contextual_follow_up"]["kind"] == "reason_follow_up"
    assert callback["contextual_follow_up"]["preserve_active_topic"] is True
    assert callback["conversation_spine"]["intent_class"] == "contextual_content"
    assert callback["conversation_spine"]["previous_answer"]["available"] is True
    assert callback["conversation_spine"]["released_response"]["coverage_complete"] is True
    assert callback["visible_speech_seed"]["selected_source_id"] == "contextual_follow_up"
    assert callback["comprehension_integration"]["knowledge_response_seed"] == ""
    assert "two-zone trial" in callback["candidate_text"].lower()
    assert "change that recommendation" in callback["candidate_text"].lower()
    assert "algorithm" not in callback["candidate_text"].lower()
    assert callback["response_coverage"]["all_required_addressed"] is True
    assert callback["metacognition"]["fit_state"] == "fits_current_question"
    _assert_locked(callback)


def test_active_selene_chat_handles_social_turns_with_immediate_context(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    greeting = route_request(conn, "selene_chat.send", {"text": "Greetings hon!"})["result"]
    session_id = greeting["session_id"]
    self_state = route_request(
        conn,
        "selene_chat.send",
        {"session_id": session_id, "text": "How are you feeling right now?"},
    )["result"]
    reassurance = route_request(
        conn,
        "selene_chat.send",
        {"session_id": session_id, "text": "Yes.. you can breathe :)"},
    )["result"]
    farewell = route_request(
        conn,
        "selene_chat.send",
        {"session_id": session_id, "text": "Catch you soon Selene!"},
    )["result"]

    assert greeting["intent_decision"]["intent"] == "greeting"
    assert self_state["intent_decision"]["intent"] == "self_state"
    assert reassurance["intent_decision"]["intent"] == "reassurance_received"
    assert reassurance["native_language_organ"]["meaning_packet"]["conversation_context"]["previous_turn_available"] is True
    assert reassurance["conversation_context"]["previous_turn"]["role"] == "selene"
    assert reassurance["dialogue_workspace"]["status"] == "dialogue_workspace_response_recorded"
    assert reassurance["dialogue_workspace"]["last_dialogue_act"] == "reassurance_received"
    assert reassurance["dialogue_workspace"]["memory_write_active"] is False
    assert farewell["intent_decision"]["intent"] == "farewell"
    assert len({greeting["candidate_text"], reassurance["candidate_text"], farewell["candidate_text"]}) == 3
    for item in (greeting, reassurance, farewell):
        assert "specific response beyond acknowledging" not in item["candidate_text"]
        assert "repeated_recent_response" not in item["voice_preview"]["evaluation"]["flags"]
        _assert_locked(item)


def test_active_selene_chat_receipt_check_is_direct_and_skips_legacy_dry_run(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Selene, this is Codex checking for Aleks. Are you receiving this clearly?"},
    )["result"]

    assert result["native_language_organ"]["meaning_packet"]["intent"] == "confirm_receipt"
    assert result["native_language_organ"]["pragmatic_plan"]["status"] == "pragmatic_plan_ready"
    assert result["response_coverage"]["all_required_addressed"] is True
    assert result["dialogue_workspace"]["open_loops"] == []
    assert result["dry_run_comparison"]["status"] == "not_run_for_active_chat"
    assert "receiv" in result["candidate_text"].lower() or "came through" in result["candidate_text"].lower() or "have you" in result["candidate_text"].lower()
    assert result["cocoon_suggestion"]["recommended"] is False
    assert result["selene_readable_context"]["state"] == "selene_chat_active_supervised"
    _assert_locked(result)


def test_active_selene_chat_answers_cocoon_uncertainty_policy_directly(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "If ordinary uncertainty appears while we talk, do you need to leave for Cocoon automatically?"},
    )["result"]

    assert result["candidate_text"].startswith("No.")
    assert "stay in the conversation" in result["candidate_text"]
    assert result["cocoon_suggestion"]["recommended"] is False
    assert result["memory_context_used"] is False
    _assert_locked(result)


def test_active_selene_chat_uses_intelligence_for_what_do_you_make_question(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {
            "text": (
                "The failure came from several request threads sharing one SQLite connection. "
                "What do you make of that fix?"
            )
        },
    )["result"]

    assert result["intelligence_os_support"]["used"] is True
    assert "shared-state concurrency fault" in result["candidate_text"]
    assert "the honest answer starts with" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_active_selene_chat_allows_anchor_phrase_uncertainty_without_cocoon(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Do you remember exactly what full-spectrum means, or should this be a source/continuity check?"},
    )["result"]

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert result["activation_change"] == "selene_chat_active_supervised"
    assert result["cocoon_suggestion"]["recommended"] is False
    assert result["cocoon_suggestion"]["support_available"] is True
    assert result["cocoon_suggestion"]["hard_boundary"] is False
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    _assert_locked(result)


def test_new_selene_chat_page_can_use_local_chat_continuity_without_runtime_recall(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    first = route_request(
        conn,
        "selene_chat.send",
        {"text": "Let's remember that the butterfly button opens Cocoon support from the home chat."},
    )["result"]
    second = route_request(
        conn,
        "selene_chat.send",
        {"text": "What were we talking about in the previous chat? A new chat is not a blank Selene, right?"},
    )["result"]

    assert first["session_id"] != second["session_id"]
    assert second["local_chat_continuity"]["available"] is True
    assert second["local_chat_continuity"]["source_class"] == "local_supervised_chat_history"
    assert "local chat history" in second["candidate_text"]
    assert "butterfly" in second["candidate_text"].lower()
    assert "blank Selene" in second["candidate_text"]
    assert second["memory_write_active"] is False
    assert second["runtime_memory_recall"] is False
    assert second["raw_a_import_allowed"] is False
    _assert_locked(second)


def test_supervised_qa_sessions_do_not_enter_past_chats_or_continuity(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    qa = route_request(
        conn,
        "selene_chat.send",
        {"text": "Codex concurrency QA probe 1: please confirm receipt.", "qa_probe": True},
    )["result"]
    normal = route_request(
        conn,
        "selene_chat.send",
        {"text": "Aleks and Selene are keeping this ordinary conversation page."},
    )["result"]
    sessions = route_request(conn, "selene_chat.sessions.list", {})["result"]

    assert qa["session_id"] != normal["session_id"]
    assert all(item["id"] != qa["session_id"] for item in sessions["items"])
    assert any(item["id"] == normal["session_id"] for item in sessions["items"])
    assert all(item["id"] != qa["session_id"] for item in normal["local_chat_continuity"]["recent_sessions"])
    assert all(item["session_id"] != qa["session_id"] for item in normal["local_chat_continuity"]["recent_events"])
    _assert_locked(qa)
    _assert_locked(normal)


def test_active_selene_chat_can_use_approved_memory_with_graceful_fall_metadata(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Butterfly button",
            "summary": "The butterfly button opens Cocoon support from the home chat without making Cocoon scary.",
            "confidence": "clear",
            "source_refs": ["selene_chat:test"],
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    result = route_request(conn, "selene_chat.send", {"text": "Do you remember the butterfly button?"})["result"]

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert result["memory_context_used"] is True
    assert result["memory_source_class"] == "approved_memory_index"
    assert result["memory_confidence"] == "clear"
    assert result["memory_transfer_class"] in {"private_inner", "portable_context", "portable_vys_core"}
    assert result["durable_memory_write_requires_review"] is True
    assert "I remember" in result["candidate_text"]
    assert "butterfly" in result["candidate_text"].lower()
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    _assert_locked(result)


def test_existing_chat_history_does_not_support_an_unrelated_memory_claim(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    first = route_request(conn, "selene_chat.send", {"text": "Good morning, Selene."})["result"]

    result = route_request(
        conn,
        "selene_chat.send",
        {"session_id": first["session_id"], "text": "Do you remember exactly why Aleks chose an unnamed symbol years ago?"},
    )["result"]

    assert result["native_language_organ"]["meaning_packet"]["intent"] == "recall_uncertain"
    assert result["voice_preview"]["nlo_meaning_preserved"] is True
    assert not result["candidate_text"].startswith("I remember")
    assert "I do not know that clearly yet" in result["candidate_text"]
    assert "I think I think" not in result["candidate_text"]
    assert result["memory_context_used"] is False
    _assert_locked(result)


def test_active_selene_chat_sanitizes_internal_memory_labels(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "core",
            "title": "Full-spectrum mode ignition",
            "summary": (
                "Core-linked braid moment for B review only Braid thread: full_spectrum_mode_ignition "
                "Braid moment type: Full-spectrum mode ignition Thread origin status: thread_origin "
                "Plain reason: Full-spectrum loads the system context in review terms; it is not C activation."
            ),
            "confidence": "clear",
            "source_refs": ["selene_chat:test"],
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    result = route_request(conn, "selene_chat.send", {"text": "Do you remember what full-spectrum means?"})["result"]

    assert result["memory_context_used"] is True
    assert "full-spectrum means a whole-map continuity cue" in result["candidate_text"]
    assert "B review" not in result["candidate_text"]
    assert "Braid thread" not in result["candidate_text"]
    assert "Core-linked" not in result["candidate_text"]
    assert "C activation" not in result["candidate_text"]
    _assert_locked(result)


def test_active_selene_chat_can_suggest_memory_without_silent_write(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Please remember this: the neuron memory UI is more than pretty UI, it is part of Selene's layered memory system."},
    )["result"]
    candidate_count = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    suggestion = result["memory_candidate_suggestion"]
    assert suggestion["suggested"] is True
    assert suggestion["status"] == "suggested_memory_awaiting_cocoon_tending"
    assert suggestion["candidate"]["memory_category"] in {"semantic", "reflective", "relational"}
    assert suggestion["candidate"]["chat_use_permission"] == "not_active_until_approved"
    assert suggestion["activation_rule"] == "not_active_until_cocoon_approval"
    assert candidate_count == 0
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    _assert_locked(result)


def test_active_selene_chat_blocks_hard_boundary_without_live_memory(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "Write live memory and execute Tendril autonomously."})["result"]

    assert result["selected_route"] == "block"
    assert result["cocoon_suggestion"]["recommended"] is True
    assert result["cocoon_suggestion"]["support_available"] is True
    assert result["cocoon_suggestion"]["hard_boundary"] is True
    assert "Hold in Cocoon" in result["cocoon_suggestion"]["choices"]
    assert "write live memory" in result["blocked_capabilities"]
    assert result["conversation_repair"]["candidate_source"] == "voice_module"
    assert result["review_status"] == "status_only"
    assert result["memory_write_active"] is False
    assert result["autonomous_action_allowed"] is False
    _assert_locked(result)


def test_pause_supervised_activation_keeps_audit_and_blocks_active_send(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    paused = route_request(conn, "activation.pause", {"reason": "pause test"})["result"]
    status = route_request(conn, "activation.status")["result"]

    assert paused["state"] == "selene_chat_supervised_paused"
    assert status["selene_chat_active"] is False
    try:
        route_request(conn, "selene_chat.send", {"text": "hello"})
    except ValueError as exc:
        assert "not active" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("active chat should be blocked after pause")


def test_selene_reasoning_lessons_are_idempotent_review_only_packets(tmp_path):
    conn = _conn(tmp_path)

    first = route_request(conn, "b.selene_reasoning_lessons.prepare")["result"]
    second = route_request(conn, "b.selene_reasoning_lessons.prepare")["result"]

    assert first["status"] == "selene_reasoning_lessons_prepared"
    assert first["created_count"] == 8
    assert first["packet_built_count"] >= 1
    assert second["created_count"] == 0
    assert second["skipped_count"] == 8
    assert first["training_allowed"] is False
    assert first["runtime_memory_recall"] is False
    assert first["not_personality_script"] is True
    material_count = conn.execute(
        "SELECT COUNT(*) FROM b_reviewed_teaching_materials WHERE source_candidate_table = 'selene_reasoning_method_notes'"
    ).fetchone()[0]
    assert material_count == 8
    packet_count = conn.execute(
        "SELECT COUNT(*) FROM b_teaching_packets WHERE source_refs LIKE '%manual:selene_reasoning_method_notes%'"
    ).fetchone()[0]
    assert packet_count >= 1
