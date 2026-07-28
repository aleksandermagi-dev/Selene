from __future__ import annotations

from selene.answer_substance import build_answer_substance


def test_fluency_without_distinct_application_reopens_understanding():
    result = build_answer_substance(
        "If Selene can repeat an idea fluently but cannot use it in a new example, what should we do next?"
    )

    assert result["answer_kind"] == "reopen_fluency_without_transfer"
    assert "familiarity, not transferable understanding" in result["answer"]
    assert "check reconstruction and application again" in result["answer"]
    assert result["external_fact_claimed"] is False


def test_exact_answer_is_distinguished_from_transferable_understanding():
    result = build_answer_substance(
        "Explain why getting one exact answer is not the same as understanding."
    )

    assert result["answer_kind"] == "exactness_understanding_distinction"
    assert "correct for one case" in result["answer"]
    assert "apply it to a different case" in result["answer"]
    assert result["external_fact_claimed"] is False


def test_shared_capacity_prompt_gets_two_concrete_designs_and_a_pilot():
    result = build_answer_substance(
        "A neighborhood learning festival has limited rooms and volunteers, but it wants to offer both "
        "hands-on science activities and quiet reading discussions for children and adults. "
        "Walk me through two workable designs, compare their tradeoffs, and recommend one small pilot we could try first."
    )

    assert result["answer_kind"] == "bounded_shared_capacity_design"
    assert "shared-schedule design" in result["answer"]
    assert "parallel-zone design" in result["answer"]
    assert "pilot one short shared-schedule block" in result["answer"]
    assert result["external_fact_claimed"] is False


def test_measurement_comparison_answers_choice_limitation_and_report():
    result = build_answer_substance(
        "Compare attendance alone versus attendance plus wait time and participant feedback. "
        "Which is more useful, what is its limitation, and what would you report?"
    )

    assert result["answer_kind"] == "bounded_measurement_comparison"
    assert "more useful than attendance alone" in result["answer"]
    assert "Its limitation" in result["answer"]
    assert "I would report attendance for each offering" in result["answer"]
    assert result["external_fact_claimed"] is False


def test_comparison_with_ordering_returns_a_dependency_rule_before_missing_detail():
    result = build_answer_substance("Compare memory and voice. Which should come first?")

    assert result["answer_kind"] == "comparison_dependency_rule"
    assert "supplies a prerequisite" in result["answer"]
    assert "reversible step" in result["answer"]
    assert result["missing_variable"] == "what each option consumes, produces, and risks"
    assert result["external_fact_claimed"] is False


def test_why_before_question_explains_dependency_and_names_reversal_condition():
    result = build_answer_substance("Why does observation come before interpretation?")

    assert result["answer_kind"] == "dependency_explanation"
    assert "preserves the input" in result["answer"]
    assert "order should reverse" in result["answer"]
    assert result["source_required_for_factual_claim"] is False


def test_unknown_subject_gets_a_material_scope_question_without_inventing_facts():
    result = build_answer_substance("Do you know about black holes?")

    assert result["answer_kind"] == "bounded_knowledge_gap"
    assert "grounded knowledge about black holes" in result["answer"]
    assert "what it is, how it works, or why it matters" in result["answer"]
    assert result["source_required_for_factual_claim"] is True
    assert result["external_fact_claimed"] is False


def test_reversed_order_question_returns_a_conditional_dependency_answer():
    result = build_answer_substance("What happens if we reverse the order?")

    assert result["answer_kind"] == "conditional_dependency_answer"
    assert "depend on an output" in result["answer"]
    assert "If that dependency exists" in result["answer"]
    assert result["external_fact_claimed"] is False


def test_viewpoint_request_about_reversible_action_is_not_treated_as_fact_lookup():
    result = build_answer_substance("What do you think about starting with the smallest reversible step?")

    assert result["answer_kind"] == "bounded_viewpoint"
    assert "sound default when uncertainty is high" in result["answer"]
    assert "should not override a known prerequisite" in result["answer"]
    assert result["source_required_for_factual_claim"] is False


def test_limited_resource_comparison_answers_both_options_and_recommends_a_small_next_step():
    result = build_answer_substance(
        "Suppose a community garden has limited water and wants to support both vegetables and pollinators. "
        "What two approaches would you compare, and what small next step would you recommend?"
    )

    assert result["answer_kind"] == "bounded_shared_resource_comparison"
    assert "compare two approaches" in result["answer"]
    assert "limited water" in result["answer"]
    assert "vegetables and pollinators" in result["answer"]
    assert "recommendation for the next small step" in result["answer"]
    assert result["external_fact_claimed"] is False
