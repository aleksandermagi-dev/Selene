from __future__ import annotations

from selene.answer_completion import build_bounded_answer_completion
from selene.supported_semantics import build_supported_semantic_packet


def _obligations():
    return [
        {
            "id": "choice",
            "kind": "choice_or_priority",
            "source_text": "Which garden design should we choose first?",
            "coverage_terms": ["garden", "design", "choose", "first"],
            "required": True,
        },
        {
            "id": "reason",
            "kind": "reason",
            "source_text": "Why should we choose that garden design?",
            "coverage_terms": ["choose", "garden", "design"],
            "required": True,
        },
        {
            "id": "limit",
            "kind": "limitation",
            "source_text": "What limitation applies to the garden design?",
            "coverage_terms": ["limitation", "garden", "design"],
            "required": True,
        },
    ]


def test_one_bounded_pass_supplies_missing_supported_obligations_without_authority_change():
    result = build_bounded_answer_completion(
        {
            "prompt": "Which garden design should we choose, why, and what is its limitation?",
            "content_seed": "Choose the reversible garden design first.",
            "response_obligations": _obligations(),
            "knowledge_items": [
                {
                    "id": 7,
                    "title": "Reversible garden pilot",
                    "central_claim": "Choose the reversible garden design first.",
                    "principles": ["A reversible garden pilot supplies evidence before a larger commitment"],
                    "limits": ["the garden design is limited when water availability is unknown"],
                    "source_refs": ["lesson:garden-pilot"],
                }
            ],
        }
    )

    assert result["accepted"] is True
    assert result["count"] == result["limit"] == 1
    assert result["initial_coverage"]["addressed_count"] == 1
    assert result["final_coverage"]["all_required_addressed"] is True
    assert "The reason is that" in result["content_seed"]
    assert "A limitation is that" in result["content_seed"]
    assert {item["obligation_id"] for item in result["resolutions"]} == {"reason", "limit"}
    assert {
        obligation_id
        for unit in result["supported_semantics"]["units"]
        for obligation_id in unit["obligation_ids"]
    } == {"reason", "limit"}
    assert all(item["source_refs"] == ["lesson:garden-pilot"] for item in result["resolutions"])
    assert result["recursion_allowed"] is False
    assert result["provider_call_allowed"] is False
    assert result["memory_write_active"] is False


def test_supported_paraphrase_prevents_redundant_completion():
    obligation = {
        "id": "reason",
        "kind": "reason",
        "source_text": "Why should we start with the reversible garden design?",
        "coverage_terms": ["start", "reversible", "garden", "design"],
        "required": True,
    }
    packet = build_supported_semantic_packet(
        {
            "answer_kind": "approved_reason",
            "units": [
                {
                    "id": "reason-unit",
                    "role": "support",
                    "text": "A small reversible trial lets us learn before committing.",
                    "obligation_ids": ["reason"],
                    "source_kind": "approved_knowledge",
                    "source_refs": ["lesson:garden-pilot"],
                }
            ],
        }
    )

    result = build_bounded_answer_completion(
        {
            "prompt": obligation["source_text"],
            "content_seed": "A small reversible trial lets us learn before committing.",
            "response_obligations": [obligation],
            "supported_semantics": packet,
        }
    )

    assert result["attempted"] is False
    assert result["accepted"] is False
    assert result["initial_coverage"]["all_required_addressed"] is True
    assert result["content_seed"] == "A small reversible trial lets us learn before committing."


def test_unsupported_yes_or_no_names_missing_ground_without_topic_scaffold():
    obligation = {
        "id": "yes-no",
        "kind": "yes_or_no",
        "source_text": "Did the greenhouse stay above freezing on Tuesday?",
        "coverage_terms": ["greenhouse", "freezing", "tuesday"],
        "required": True,
    }

    result = build_bounded_answer_completion(
        {
            "prompt": obligation["source_text"],
            "content_seed": "",
            "response_obligations": [obligation],
        }
    )

    assert result["accepted"] is True
    assert result["final_coverage"]["all_required_addressed"] is True
    assert result["resolutions"][0]["missing_ground"] == "evidence that distinguishes yes from no"
    assert "reliable yes or no" in result["content_seed"]
    assert not result["content_seed"].startswith("On ")
    assert result["supported_semantics"]["units"][0]["obligation_ids"] == ["yes-no"]


def test_correction_only_gap_does_not_trigger_empty_completion_pass():
    result = build_bounded_answer_completion(
        {
            "prompt": "Actually, I meant the smaller garden.",
            "content_seed": "",
            "response_obligations": [
                {
                    "id": "correction",
                    "kind": "correction_update",
                    "source_text": "Actually, I meant the smaller garden.",
                    "coverage_terms": ["smaller", "garden"],
                    "required": True,
                }
            ],
        }
    )

    assert result["attempted"] is False
    assert result["accepted"] is False
    assert result["status"] == "bounded_answer_completion_no_supported_addition"
    assert result["count"] == 0
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False


def test_one_pass_completion_uses_the_exact_missing_obligation_and_session_fact():
    result = build_bounded_answer_completion(
        {
            "prompt": "What were the porch dimensions and how many chairs did I say?",
            "content_seed": "The porch details are still in this session.",
            "response_obligations": [
                {
                    "id": "details",
                    "kind": "direct_question",
                    "source_text": "What were the porch dimensions and how many chairs did I say?",
                    "coverage_terms": ["porch", "dimensions", "chairs"],
                    "required": True,
                }
            ],
            "conversation_spine": {
                "relevant_session_facts": [
                    {"kind": "dimensions", "text": "The porch dimensions are six feet by eight feet."},
                    {"kind": "count", "text": "There are two chairs."},
                ]
            },
        }
    )

    assert result["attempted"] is True
    assert result["accepted"] is True
    assert result["newly_addressed_obligation_ids"] == ["details"]
    assert "six feet by eight feet" in result["content_seed"]
    assert "two chairs" in result["content_seed"]
    assert result["resolutions"][0]["resolution"] == "current_session_fact"
    assert result["count"] == 1
    assert result["recursion_allowed"] is False


def test_unsupported_part_is_named_instead_of_invented():
    obligation = {
        "id": "temperature",
        "kind": "direct_question",
        "source_text": "What was the greenhouse temperature on Tuesday?",
        "coverage_terms": ["greenhouse", "temperature", "tuesday"],
        "required": True,
    }
    result = build_bounded_answer_completion(
        {
            "prompt": obligation["source_text"],
            "content_seed": "",
            "response_obligations": [obligation],
            "knowledge_items": [],
            "observations": [],
        }
    )

    assert result["attempted"] is True
    assert result["unsupported_resolution_count"] == 1
    assert result["resolutions"][0]["resolution"] == "explicit_unsupported_part"
    assert result["resolutions"][0]["visible_fragment"] in result["content_seed"]
    assert "do not have a grounded factual answer" in result["content_seed"]
    assert "without guessing" in result["content_seed"]
    assert result["provider_call_allowed"] is False
    assert result["memory_write_active"] is False
