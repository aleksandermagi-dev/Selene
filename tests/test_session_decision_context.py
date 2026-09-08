from __future__ import annotations

from selene.session_decision_context import build_session_decision_context


def _events(*turns: str) -> list[dict[str, str]]:
    return [{"role": "user", "preview": text} for text in turns]


def _assert_bounded(result: dict) -> None:
    assert result["writes_state"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["retained_knowledge_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def test_visible_options_become_one_revisable_current_session_decision() -> None:
    prompt = (
        "Suppose we have three plans: one fast but fragile, one slow but reliable, "
        "and one balanced. Compare them and recommend one."
    )
    result = build_session_decision_context(
        {"session_id": 7, "prompt": prompt, "conversation_events": _events(prompt)}
    )

    assert result["available"] is True
    assert result["mode"] == "comparison_and_choice"
    assert len(result["options"]) == 3
    assert result["recommendation"]["option_label"] == "balanced plan"
    assert result["supported_operations"] == ["comparison", "choice"]
    assert "fast but fragile plan" in result["response_seed"]
    assert "slow but reliable plan" in result["response_seed"]
    assert "balanced plan" in result["response_seed"]
    _assert_bounded(result)


def test_changed_priority_revises_the_choice_without_losing_the_options() -> None:
    opening = (
        "Suppose we have three plans: one fast but fragile, one slow but reliable, "
        "and one balanced. Compare them and recommend one."
    )
    update = "Actually, the deadline moved closer, but reliability still matters most. What changes?"
    result = build_session_decision_context(
        {
            "session_id": 8,
            "prompt": update,
            "conversation_events": _events(opening, update),
        }
    )

    assert result["mode"] == "revision"
    assert result["recommendation"]["option_label"] == "slow but reliable plan"
    assert result["constraint_updates"] == ["the deadline moved closer"]
    assert "reliability remains the controlling priority" in result["response_seed"]
    assert "Actually" not in result["response_seed"]
    _assert_bounded(result)


def test_hypothetical_evidence_updates_the_scenario_but_not_later_observed_state() -> None:
    opening = (
        "Suppose we have three plans: one fast but fragile, one slow but reliable, "
        "and one balanced. Compare them and recommend one."
    )
    priority = "The deadline moved closer, but reliability still matters most. What changes?"
    hypothetical = "If evidence later showed the balanced plan fails twice as often, what would you update?"
    hypothetical_result = build_session_decision_context(
        {
            "session_id": 9,
            "prompt": hypothetical,
            "conversation_events": _events(opening, priority, hypothetical),
        }
    )

    assert hypothetical_result["active_evidence_updates"][0]["hypothetical"] is True
    assert hypothetical_result["response_seed"].startswith("If that evidence held")

    prediction = "My best guess is that the reliable plan wins. What is your best prediction from what we have?"
    later_result = build_session_decision_context(
        {
            "session_id": 9,
            "prompt": prediction,
            "conversation_events": _events(opening, priority, hypothetical, prediction),
        }
    )

    assert later_result["active_evidence_updates"] == []
    assert "latest reported evidence" not in later_result["response_seed"]
    assert "reliability being the current priority" in later_result["response_seed"]
    assert later_result["operation_fields"]["prediction"]["revision_conditions"] == [
        "the premises or results changed"
    ]
    _assert_bounded(later_result)


def test_natural_whether_choice_uses_general_option_grammar() -> None:
    prompt = "I'm deciding whether to sketch indoors or walk by the river. Which sounds better?"
    result = build_session_decision_context(
        {"session_id": 41, "prompt": prompt, "conversation_events": _events(prompt)}
    )

    assert result["available"] is True
    assert result["mode"] == "choice"
    assert [item["label"] for item in result["options"]] == [
        "sketch indoors",
        "walk by the river",
    ]
    assert "choose sketch indoors" in result["response_seed"]
    assert "the sketch indoors" not in result["response_seed"]
    _assert_bounded(result)


def test_would_you_rather_paraphrase_uses_the_same_decision_owner() -> None:
    prompt = "Would you rather assemble the shelf now or read beside the window?"
    result = build_session_decision_context(
        {"session_id": 42, "prompt": prompt, "conversation_events": _events(prompt)}
    )

    assert result["available"] is True
    assert result["mode"] == "choice"
    assert [item["label"] for item in result["options"]] == [
        "assemble the shelf now",
        "read beside the window",
    ]
    _assert_bounded(result)
