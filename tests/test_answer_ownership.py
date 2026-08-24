from __future__ import annotations

from selene.answer_ownership import enrich_obligation_ownership, research_domain_requested


def _owned(text: str, *, kind: str = "direct_question", intent: dict | None = None) -> dict:
    return enrich_obligation_ownership(
        {
            "id": "answer",
            "kind": kind,
            "source_text": text,
            "coverage_terms": [],
            "required": True,
        },
        intent_decision=intent,
    )


def _assert_locked(result: dict) -> None:
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def test_paper_object_does_not_select_research_but_publication_context_does():
    assert research_domain_requested("How can I make a paper pinwheel spin?") is False
    assert research_domain_requested("Summarize this research paper and cite its authors.") is True


def test_self_state_and_preference_keep_their_current_answer_owners():
    state = _owned(
        "How are you feeling about the repair?",
        kind="self_state_check_in",
        intent={"intent": "self_state", "self_state_requested": True},
    )
    preference = _owned("What would you like to explore next?")

    assert state["answer_act"] == "current_self_state_report"
    assert state["responsible_owner"] == "self_state"
    assert state["external_evidence_required"] is False
    assert state["completion_policy"] == "preserve_current_owner"
    assert preference["answer_act"] == "current_authored_preference"
    assert preference["responsible_owner"] == "ordinary_conversation_path"
    assert preference["requested_response_functions"] == ["preference"]
    _assert_locked(state)
    _assert_locked(preference)


def test_reasoning_operations_are_owned_by_the_organs_that_perform_them():
    prediction = _owned("What do you predict will happen next?")
    hypothesis = _owned("What is your best current hypothesis for this pattern?")
    comparison = _owned("Compare the two designs.", kind="comparison")
    action = _owned("What is the smallest safe inspection we can do?")

    assert (prediction["responsible_owner"], prediction["answer_act"]) == (
        "intelligence_os",
        "prompt_grounded_prediction",
    )
    assert hypothesis["requested_response_functions"] == ["hypothesis"]
    assert comparison["answer_domain"] == "comparison_planning"
    assert action["requested_response_functions"] == ["method", "action_scope"]
    assert all(item["external_evidence_required"] is False for item in (prediction, hypothesis, comparison, action))


def test_external_fact_and_attributed_research_remain_evidence_owned():
    fact = _owned("What is photosynthesis?")
    research = _owned("What did the published paper conclude?")

    assert fact["responsible_owner"] == "comprehension_integration"
    assert fact["external_evidence_required"] is True
    assert research["responsible_owner"] == "answer_engine"
    assert research["answer_domain"] == "source_backed_research"
    assert research["external_evidence_required"] is True
