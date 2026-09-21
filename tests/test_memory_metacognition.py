from __future__ import annotations

from copy import deepcopy

from selene.memory_metacognition import appraise_retrieved_memory


def _memory(*, duplicate: bool = False) -> dict:
    item = {
        "id": "approved-reference-20",
        "record_class": "private_corpus_continuity",
        "title": "Moonlight exchange",
        "memory_category": "relational",
        "emotional_texture": "tender affection",
        "confidence": "clear",
        "expression_summary": (
            "Aleks and Selene connected the Selene name with moonlight. "
            "They used Virgo for focused idea-building. "
            "The exchange ended with an affectionate use of hon."
        ),
        "source_refs": ["approved_memory:20"],
        "retrieval_layers": {
            "present_interpretation": {
                "selected_for_current_query": True,
                "selection_reason": "memory_context_matches_current_subject",
                "matched_query_terms": ["hon"],
            }
        },
    }
    return {
        "status": "memory_retrieval_ready",
        "retrieval_mode": "contextual_relevance",
        "memory_context_used": True,
        "memory_confidence": "clear",
        "items": [item, dict(item)] if duplicate else [item],
    }


def test_affectionate_association_shapes_expression_without_dumping_memory() -> None:
    memory = _memory(duplicate=True)
    original = deepcopy(memory)
    result = appraise_retrieved_memory(
        {
            "prompt": "I got it hon! I'll be right back! :) ",
            "memory_retrieval": memory,
            "intent_decision": {"social_turn": True},
            "relational_context": {
                "relational_context_present": True,
                "cue_types": ["affectionate_address", "playful_tone"],
            },
            "contextual_continuity": {
                "callback_decision": {
                    "mode": "silent_interpretive_context",
                    "silent_influence_allowed": True,
                    "surface_callback_allowed": False,
                }
            },
        }
    )

    assert result["status"] == "memory_metacognition_appraisal_ready"
    assert result["raw_retrieval_item_count"] == 2
    assert result["appraised_item_count"] == 1
    assert result["coalesced_duplicate_count"] == 1
    appraisal = result["appraised_items"][0]
    assert appraisal["evidence_role"] == "association_only"
    assert appraisal["expression_scope"] == "influence_without_mention"
    assert appraisal["surface_allowed"] is False
    assert appraisal["surface_text"] == ""
    assert {"tone", "interpretation"} <= set(appraisal["influence_channels"])
    assert result["expression_handoff"]["surface_memory_allowed"] is False
    assert result["expression_handoff"]["raw_retrieval_summary_is_response_text"] is False
    assert result["retrieval_preserved"] is True
    assert result["memory_write_active"] is False
    assert memory == original


def test_explicit_recall_can_surface_only_the_relevant_fragment() -> None:
    memory = _memory()
    memory["retrieval_mode"] = "explicit_recall"
    memory["items"][0]["retrieval_layers"]["present_interpretation"][
        "matched_query_terms"
    ] = ["moonlight"]

    result = appraise_retrieved_memory(
        {
            "prompt": "Do you remember why moonlight mattered?",
            "memory_retrieval": memory,
            "intent_decision": {
                "memory_recall_requested": True,
                "social_turn": False,
            },
            "contextual_continuity": {
                "callback_decision": {
                    "mode": "explicit_recall",
                    "surface_callback_allowed": True,
                    "silent_influence_allowed": False,
                }
            },
        }
    )

    appraisal = result["appraised_items"][0]
    assert appraisal["evidence_role"] == "primary_personal_memory_evidence"
    assert appraisal["surface_allowed"] is True
    assert appraisal["expression_scope"] == "explicit_attributed_recall"
    assert "moonlight" in appraisal["surface_text"].lower()
    assert "Virgo" not in appraisal["surface_text"]
    assert result["expression_handoff"]["surface_memory_allowed"] is True


def test_procedural_memory_can_support_reasoning_without_becoming_universal_fact() -> None:
    memory = _memory()
    item = memory["items"][0]
    item.update(
        {
            "title": "Adapter repair plan",
            "memory_category": "shared_project",
            "emotional_texture": "focused",
            "expression_summary": (
                "The repair plan keeps retrieval unchanged and inserts appraisal before synthesis. "
                "The unrelated packaging note can wait."
            ),
            "retrieval_layers": {
                "present_interpretation": {
                    "selected_for_current_query": True,
                    "selection_reason": "memory_context_matches_current_subject",
                    "matched_query_terms": ["appraisal", "synthesis"],
                }
            },
        }
    )
    result = appraise_retrieved_memory(
        {
            "prompt": "Where does appraisal belong before synthesis?",
            "memory_retrieval": memory,
            "intent_decision": {"social_turn": False},
            "contextual_continuity": {
                "callback_decision": {
                    "mode": "silent_interpretive_context",
                    "silent_influence_allowed": True,
                    "surface_callback_allowed": False,
                }
            },
        }
    )

    appraisal = result["appraised_items"][0]
    assert appraisal["evidence_role"] == "supporting_context"
    assert appraisal["reasoning_context_allowed"] is True
    assert appraisal["surface_allowed"] is False
    assert "packaging" not in appraisal["relevant_fragment"].lower()
    assert appraisal["raw_memory_payload_exposed"] is False


def test_no_selected_memory_is_a_bounded_noop() -> None:
    result = appraise_retrieved_memory(
        {
            "prompt": "Good morning",
            "memory_retrieval": {
                "memory_context_used": False,
                "items": [],
            },
        }
    )

    assert result["status"] == "memory_metacognition_not_needed"
    assert result["active"] is False
    assert result["appraised_items"] == []
    assert result["expression_handoff"]["surface_text"] == ""
