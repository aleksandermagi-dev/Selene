from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.language_formation import build_semantic_frame, realize_semantic_frame
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_structured_meaning_frame_realizes_original_grammatical_clauses():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "communicative_goal": "direct_conversation",
                "discourse_relation": "support",
                "propositions": [
                    {
                        "subject": "Selene",
                        "predicate": "carry",
                        "object": "the current thread",
                        "modality": "can",
                    },
                    {
                        "subject": "she",
                        "predicate": "ask",
                        "object": "Aleks",
                        "condition": "the source is unclear",
                    },
                ],
            }
        }
    )

    result = realize_semantic_frame(frame, variation_key="structured-test")

    assert frame["formation_mode"] == "structured"
    assert "Selene can carry the current thread." in result["candidate_text"]
    assert "When the source is unclear, she asks Aleks." in result["candidate_text"]
    assert result["meaning_preserved"] is True
    assert result["hidden_chain_of_thought_exposed"] is False


def test_formation_handles_tense_polarity_and_modality_without_model_generation():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {"subject": "Selene", "predicate": "guess", "object": "the missing source", "polarity": "negative"},
                    {"subject": "Aleks", "predicate": "say", "object": "the correction", "tense": "past"},
                    {"subject": "we", "predicate": "revisit", "object": "the answer", "modality": "may"},
                ]
            }
        }
    )

    text = realize_semantic_frame(frame, variation_key="grammar-test")["candidate_text"]

    assert "Selene does not guess the missing source." in text
    assert "Aleks said the correction." in text
    assert "we may revisit the answer." in text


def test_formation_uses_explicit_noun_number_and_future_time_without_guessing_content():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "subject": "the lesson",
                        "subject_number": "singular",
                        "predicate": "remain",
                        "object": "available",
                    },
                    {
                        "subject": "the lessons",
                        "subject_number": "plural",
                        "predicate": "remain",
                        "object": "reviewable",
                    },
                    {
                        "subject": "Selene",
                        "predicate": "treat",
                        "object": "a future condition as a present fact",
                        "tense": "future",
                        "polarity": "negative",
                    },
                ]
            }
        }
    )

    result = realize_semantic_frame(frame, variation_key="number-time-foundation")

    assert "The lesson remains available." in result["candidate_text"]
    assert "the lessons remain reviewable." in result["candidate_text"]
    assert "Selene will not treat a future condition as a present fact." in result["candidate_text"]
    assert result["meaning_preserved"] is True
    assert result["hidden_chain_of_thought_exposed"] is False


def test_native_language_uses_structured_formation_when_supplied(tmp_path):
    conn = _conn(tmp_path)
    prompt = "Say this naturally."
    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "semantic_frame": {
                "propositions": [
                    {"subject": "uncertainty", "predicate": "remain", "object": "honest"},
                    {"subject": "Selene", "predicate": "ask", "object": "for the missing piece", "modality": "can"},
                ]
            },
        },
    )

    assert result["version"] == "v24_contextual_composition_and_modulation"
    assert result["semantic_frame"]["formation_mode"] == "structured"
    assert "Uncertainty remains honest." in result["candidate_text"]
    assert "Selene can ask for the missing piece." in result["candidate_text"]
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False


def test_text_grounded_frame_preserves_existing_supported_answer():
    seed = "The answer should stay direct and leave room for correction."
    frame = build_semantic_frame({"content_seed": seed, "certainty": "clear_enough"})
    result = realize_semantic_frame(frame)

    assert frame["formation_mode"] == "text_grounded"
    assert result["candidate_text"] == seed


def test_nlo_uses_contextual_not_random_variation_while_preserving_meaning(tmp_path):
    conn = _conn(tmp_path)
    prompt = "How should we compare the two designs?"
    seed = "Compare both designs against the same evidence before choosing."
    decision = classify_chat_intent(prompt)

    first = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": decision,
            "content_seed": seed,
            "conversation_context": {"turn_count": 1, "recent_assistant_texts": []},
        },
    )
    second = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": decision,
            "content_seed": seed,
            "conversation_context": {
                "turn_count": 2,
                "recent_assistant_texts": [first["candidate_text"]],
                "previous_turn": {"role": "selene", "preview": first["candidate_text"]},
            },
        },
    )

    assert first["discourse_plan"]["expression_profile"] == "comparison"
    assert second["discourse_plan"]["variation_is_contextual_not_random"] is True
    assert second["discourse_plan"]["surface_variation"]["random_choice_used"] is False
    assert second["discourse_plan"]["surface_variation"]["meaning_change_allowed"] is False
    assert seed.lower() in first["candidate_text"].lower()
    assert seed.lower() in second["candidate_text"].lower()
    assert second["candidate_text"] != first["candidate_text"]
    assert second["memory_write_active"] is False


def test_formation_handles_aspect_voice_mood_and_clause_relations_without_provider_generation():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "response_depth": "developed",
                "propositions": [
                    {
                        "subject": "Selene",
                        "predicate": "carry",
                        "object": "the thread",
                        "aspect": "progressive",
                    },
                    {
                        "subject": "the lesson",
                        "predicate": "review",
                        "voice": "passive",
                        "agent": "Aleks",
                        "relation": "support",
                    },
                    {
                        "subject": "Selene",
                        "predicate": "keep",
                        "object": "the source visible",
                        "aspect": "perfect",
                        "relation": "cause",
                    },
                ],
            }
        }
    )

    result = realize_semantic_frame(frame, variation_key="expanded-grammar")

    assert "Selene is carrying the thread." in result["candidate_text"]
    assert "the lesson is reviewed by Aleks" in result["candidate_text"]
    assert "Selene has kept the source visible" in result["candidate_text"]
    assert result["clause_relations"] == ["", "support", "cause"]
    assert {"aspect", "voice"}.issubset(result["grammar_features"])


def test_formation_realizes_questions_and_instructions_from_structured_meaning():
    frame = build_semantic_frame(
        {
            "semantic_frame": {
                "propositions": [
                    {
                        "subject": "Selene",
                        "predicate": "carry",
                        "object": "the thread",
                        "modality": "can",
                        "mood": "interrogative",
                    },
                    {
                        "predicate": "keep",
                        "object": "the source visible",
                        "mood": "imperative",
                    },
                ]
            }
        }
    )

    result = realize_semantic_frame(frame, variation_key="mood-grammar")

    assert "Can Selene carry the thread?" in result["candidate_text"]
    assert "keep the source visible." in result["candidate_text"].lower()
    assert "mood" in result["grammar_features"]
