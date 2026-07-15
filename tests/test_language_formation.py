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
    assert "when the source is unclear, she asks Aleks." in result["candidate_text"]
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

    assert result["version"] == "v7_comprehension_integration"
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
