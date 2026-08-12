from __future__ import annotations

from selene.answer_substance import build_answer_substance
from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.intelligence_os import run_intelligence_os_reason
from selene.lexical_semantics import available_lexical_forms, build_lexical_semantic_set
from selene.native_language_organ import realize_native_language
from selene.supported_semantics import (
    build_supported_semantic_packet,
    build_text_supported_semantic_packet,
    semantic_units_for_formation,
)


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False


def test_supported_semantic_packet_keeps_meaning_scope_certainty_and_sources_inspectable():
    packet = build_supported_semantic_packet(
        {
            "answer_kind": "comparison_method",
            "certainty": "provisional",
            "scope": "the current comparison",
            "source_refs": ["test:current_prompt"],
            "fallback_text": "Compare both options on the same evidence.",
            "units": [
                {
                    "id": "shared_evidence",
                    "role": "answer",
                    "relation": "sequence",
                    "predicate": "compare",
                    "object": "both options on the same evidence",
                    "mood": "imperative",
                    "meaning_keys": ["shared evidence comparison"],
                    "source_kind": "prompt_grounded_method",
                }
            ],
        }
    )

    assert packet["status"] == "supported_semantic_packet_ready"
    assert packet["formation_mode"] == "structured"
    assert packet["required_unit_ids"] == ["shared_evidence"]
    assert packet["meaning_signature"] == ["shared evidence comparison"]
    assert packet["certainty"] == "provisional"
    assert packet["scope"] == "the current comparison"
    assert packet["source_refs"] == ["test:current_prompt"]
    assert semantic_units_for_formation(packet)[0]["kind"] == "supported_semantic_unit"
    assert packet["meaning_change_allowed"] is False
    assert packet["coordinated_expression_contract_active"] is True
    _assert_locked(packet)


def test_text_supported_semantics_preserve_answer_contrast_limit_and_source():
    packet = build_text_supported_semantic_packet(
        "The result is four. However, that conclusion only covers ordinary arithmetic.",
        answer_kind="verified_math_answer",
        source_kind="verified_domain_answer",
        source_refs=["verified_math:2+2"],
        certainty="verified",
        scope="2+2",
    )

    units = semantic_units_for_formation(packet)
    assert [item["role"] for item in units] == ["answer", "contrast"]
    assert packet["source_refs"] == ["verified_math:2+2"]
    assert packet["all_units_supported"] is True
    assert packet["fact_generation_allowed"] is False
    _assert_locked(packet)


def test_non_intelligence_semantic_packets_reach_nlo_without_becoming_new_facts(tmp_path):
    conn = _conn(tmp_path)
    seed = "The verified result is four."
    packet = build_text_supported_semantic_packet(
        seed,
        answer_kind="verified_math_answer",
        source_kind="verified_domain_answer",
        source_refs=["verified_math:2+2"],
        certainty="verified",
        scope="2+2",
    )

    result = realize_native_language(
        conn,
        {
            "prompt": "What is 2 + 2?",
            "content_seed": seed,
            "visible_speech_seed": {
                "selected_source_id": "answer_engine",
                "selected_source_class": "domain_answer",
                "release_allowed": True,
            },
            "answer_engine_support": {
                "content_seed": seed,
                "supported_semantics": packet,
            },
            "intent_decision": classify_chat_intent("What is 2 + 2?"),
        },
    )

    handoff = result["meaning_packet"]["supported_semantics"]
    assert handoff["used"] is True
    assert handoff["answer_kind"] == "verified_math_answer"
    assert result["formation"]["required_semantic_units_preserved"] is True
    assert result["revision"]["unsupported_content_generated"] is False


def test_lexical_forms_require_sense_grammar_provenance_and_understanding():
    profile = build_lexical_semantic_set(
        {
            "entries": [
                {
                    "id": "grounded_begin",
                    "field": "predicate",
                    "lemma": "begin with",
                    "forms": ["begin with", "start with"],
                    "sense": "initiate an ordered task at its first dependency",
                    "part_of_speech": "verb_phrase",
                    "grammatical_behavior": ["imperative-compatible", "takes a task step as object"],
                    "registers": ["ordinary", "planning"],
                    "collocations": ["prerequisite", "first step"],
                    "near_concepts": ["continue with"],
                    "distinctions": ["beginning is not continuing"],
                    "concept_refs": ["test:ordering"],
                    "understanding_state": "prompt_grounded",
                    "source_refs": ["test:current_prompt"],
                },
                {
                    "id": "ungrounded_synonym",
                    "field": "predicate",
                    "lemma": "commence with",
                    "forms": ["commence with"],
                    "sense": "initiate an ordered task",
                    "part_of_speech": "verb_phrase",
                    "grammatical_behavior": ["takes a task step as object"],
                    "understanding_state": "unreviewed",
                    "source_refs": [],
                },
            ]
        }
    )

    assert profile["available_entry_count"] == 1
    assert profile["held_entry_count"] == 1
    assert available_lexical_forms(profile, "predicate") == ["begin with", "start with"]
    assert "commence with" not in available_lexical_forms(profile, "predicate")
    assert profile["entries"][0]["near_concepts"] == ["continue with"]
    assert profile["entries"][0]["distinctions"] == ["beginning is not continuing"]
    assert profile["dictionary_memorization_used"] is False
    _assert_locked(profile)


def test_answer_substance_structures_common_reasoning_and_marks_unmigrated_fallbacks():
    comparison = build_answer_substance("Compare memory and voice. Which should come first?")
    unknown = build_answer_substance("What is the current population of an unknown city?")

    assert comparison["structured_semantic_handoff"] is True
    assert comparison["semantic_packet"]["structured_unit_count"] == 3
    assert comparison["semantic_packet"]["text_grounded_unit_count"] == 0
    assert comparison["semantic_packet"]["available_lexical_semantic_entry_count"] == 1
    assert comparison["semantic_packet"]["meaning_signature"] == [
        "prerequisite controls ordering",
        "reversibility guides nondependent ordering",
        "early evidence",
        "compare inputs outputs and risks",
    ]
    assert comparison["compatibility_fallback_available"] is True
    assert unknown["structured_semantic_handoff"] is False
    assert unknown["semantic_packet"]["formation_mode"] == "text_grounded"
    assert unknown["semantic_packet"]["compatibility_fallback_available"] is True
    _assert_locked(comparison["semantic_packet"])
    _assert_locked(unknown["semantic_packet"])


def test_prompt_grounded_semantics_reach_nlo_and_vary_surface_without_losing_required_meaning(tmp_path):
    conn = _conn(tmp_path)
    prompt = "Compare memory and voice. Which should come first?"
    reasoning = run_intelligence_os_reason(
        conn,
        {
            "prompt": prompt,
            "source_refs": ["test:supported_semantic_nlo"],
        },
    )
    support = {
        "used": True,
        "best_current_answer": reasoning["best_current_answer"],
        "answer_substance": reasoning["answer_substance"],
        "confidence": reasoning["confidence"],
        "reasoning_summary": "",
        "support_points": [],
        "selected_next_step": "",
    }
    first = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "content_seed": reasoning["best_current_answer"],
            "intent_decision": classify_chat_intent(prompt),
            "intelligence_support": support,
            "conversation_context": {"turn_count": 1, "recent_assistant_texts": []},
        },
    )
    second = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "content_seed": reasoning["best_current_answer"],
            "intent_decision": classify_chat_intent(prompt),
            "intelligence_support": support,
            "conversation_context": {
                "turn_count": 2,
                "recent_assistant_texts": [first["candidate_text"]],
                "previous_turn": {"role": "selene", "preview": first["candidate_text"]},
            },
        },
    )

    expected_signature = reasoning["answer_substance"]["semantic_packet"]["meaning_signature"]
    for result in (first, second):
        assert result["version"] == "v32_human_conversational_realization"
        assert result["meaning_packet"]["supported_semantics"]["used"] is True
        assert result["meaning_packet"]["supported_semantics"]["formation_mode"] == "structured"
        assert result["semantic_frame"]["formation_mode"] == "structured"
        assert result["formation"]["meaning_signature"] == expected_signature
        assert result["formation"]["required_semantic_units_preserved"] is True
        assert result["formation"]["meaning_preserved"] is True
        assert result["revision"]["unsupported_content_generated"] is False
        assert result["memory_write_active"] is False
        assert result["autonomous_action_allowed"] is False

    assert first["candidate_text"] != second["candidate_text"]
    assert any(marker in first["candidate_text"].lower() for marker in ("prerequisite", "required input"))
    assert any(marker in second["candidate_text"].lower() for marker in ("prerequisite", "required input"))
    assert "risk" in first["candidate_text"].lower()
    assert "risk" in second["candidate_text"].lower()


def test_each_phase_one_reasoning_shape_realizes_all_required_units_cleanly(tmp_path):
    conn = _conn(tmp_path)
    cases = [
        ("Compare memory and voice. Which should come first?", "comparison_dependency_rule"),
        ("Why does observation come before interpretation?", "dependency_explanation"),
        ("What happens if we reverse the order?", "conditional_dependency_answer"),
        (
            "What do you think about starting with the smallest reversible step?",
            "bounded_viewpoint",
        ),
        ("Compare these two approaches fairly.", "comparison_method"),
        ("How should we plan the next step?", "bounded_planning_method"),
        ("What happens if one dependency changes?", "conditional_consequence_method"),
    ]

    for turn, (prompt, expected_kind) in enumerate(cases, start=1):
        reasoning = run_intelligence_os_reason(
            conn,
            {
                "prompt": prompt,
                "source_refs": [f"test:phase_one_shape:{turn}"],
            },
        )
        assert reasoning["answer_substance"]["selected_for_answer"] is True
        assert reasoning["answer_substance"]["answer_kind"] == expected_kind
        result = realize_native_language(
            conn,
            {
                "prompt": prompt,
                "content_seed": reasoning["best_current_answer"],
                "intent_decision": classify_chat_intent(prompt),
                "intelligence_support": {
                    "used": True,
                    "best_current_answer": reasoning["best_current_answer"],
                    "answer_substance": reasoning["answer_substance"],
                    "confidence": reasoning["confidence"],
                    "reasoning_summary": "",
                    "support_points": [],
                    "selected_next_step": "",
                },
                "conversation_context": {"turn_count": turn, "recent_assistant_texts": []},
            },
        )

        assert result["meaning_packet"]["supported_semantics"]["used"] is True
        assert result["semantic_frame"]["formation_mode"] == "structured"
        assert result["formation"]["required_semantic_units_preserved"] is True
        assert result["formation"]["meaning_preserved"] is True
        assert ", Compare" not in result["candidate_text"]
        assert ", Start" not in result["candidate_text"]
        assert result["revision"]["unsupported_content_generated"] is False


def test_structured_semantics_cannot_override_a_different_spine_selected_source(tmp_path):
    conn = _conn(tmp_path)
    prompt = "One refinement: keep the original goal but use fewer volunteers."
    reasoning = run_intelligence_os_reason(
        conn,
        {
            "prompt": "How should we plan the next step?",
            "source_refs": ["test:non_owner_semantics"],
        },
    )
    contextual_seed = (
        "Keep the original goal, reduce the staffed portion, and preserve the "
        "remaining volunteers for the part that requires them."
    )
    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "content_seed": contextual_seed,
            "visible_speech_seed": {
                "selected_source_id": "contextual_follow_up",
                "selected_source_class": "conversation",
                "release_allowed": True,
            },
            "intent_decision": classify_chat_intent(prompt),
            "intelligence_support": {
                "used": True,
                "best_current_answer": reasoning["best_current_answer"],
                "answer_substance": reasoning["answer_substance"],
                "confidence": reasoning["confidence"],
            },
        },
    )

    assert result["meaning_packet"]["supported_semantics"]["used"] is False
    assert result["semantic_frame"]["formation_mode"] == "text_grounded"
    assert contextual_seed in result["candidate_text"]
    assert "earliest missing prerequisite" not in result["candidate_text"].lower()
    assert result["revision"]["unsupported_content_generated"] is False
