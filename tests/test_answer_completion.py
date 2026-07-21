from __future__ import annotations

from selene.answer_completion import build_bounded_answer_completion


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
    assert all(item["source_refs"] == ["lesson:garden-pilot"] for item in result["resolutions"])
    assert result["recursion_allowed"] is False
    assert result["provider_call_allowed"] is False
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False


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
    assert "do not have a grounded factual answer" in result["content_seed"]
    assert "without guessing" in result["content_seed"]
    assert result["provider_call_allowed"] is False
    assert result["memory_write_active"] is False
