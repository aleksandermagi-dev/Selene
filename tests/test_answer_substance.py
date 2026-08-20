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


def test_visible_resources_and_time_form_a_bounded_plan_without_external_facts():
    result = build_answer_substance(
        "I have coffee, a sketchbook, and fifteen minutes. "
        "Suggest a simple way to use the time."
    )

    assert result["answer_kind"] == "bounded_resource_plan"
    assert "fifteen minutes" in result["answer"]
    assert "coffee" in result["answer"]
    assert "sketchbook" in result["answer"]
    assert result["structured_semantic_handoff"] is True
    assert result["external_fact_claimed"] is False


def test_competing_hypotheses_get_one_discriminating_check_and_revision_condition():
    result = build_answer_substance(
        "My working guess is a loose drawer runner, but the frame could be warped. "
        "What should I check first, and what evidence would change your answer?"
    )

    assert result["answer_kind"] == "hypothesis_discrimination"
    assert "smallest safe, reversible observation" in result["answer"]
    assert "loose drawer runner" in result["answer"]
    assert "frame being warped" in result["answer"]
    assert "shift toward" in result["answer"]
    assert result["external_fact_claimed"] is False


def test_useful_guess_remains_distinct_from_verified_knowledge():
    result = build_answer_substance(
        "Could you ever make a guess when the answer is not known yet?"
    )

    assert result["answer_kind"] == "bounded_guess_policy"
    assert result["answer"].startswith("Yes.")
    assert "what would make me revise it" in result["answer"]
    assert "separate from something verified" in result["answer"]


def test_low_stakes_choice_answers_directly_from_the_visible_preference():
    result = build_answer_substance(
        "I'm planning a quiet afternoon. Could you help me choose between reading on the porch "
        "and taking a short walk, then give me one reason for your choice?"
    )

    assert result["answer_kind"] == "grounded_low_stakes_choice"
    assert result["answer"].startswith("I would choose reading on the porch.")
    assert "quiet afternoon" in result["answer"]
    assert result["source_required_for_factual_claim"] is False


def test_open_topic_invitation_is_conversational_initiative_not_fact_lookup():
    result = build_answer_substance("What would you like to get into?")

    assert result["answer_kind"] == "open_conversational_topic_preference"
    assert result["answer"].startswith("I'd like to hear")
    assert "building, wondering about, or simply enjoying" in result["answer"]
    assert result["source_required_for_factual_claim"] is False
    assert result["external_fact_claimed"] is False


def test_visible_rain_uncertainty_revises_the_everyday_choice_provisionally():
    result = build_answer_substance(
        "Small change: it may rain soon, but we haven't checked. How does that change your answer?",
        [
            {
                "observation": (
                    "Could you help me choose between reading on the porch and taking a short walk?"
                )
            }
        ],
    )

    assert result["answer_kind"] == "grounded_everyday_choice_revision"
    assert "toward reading on the porch, provisionally" in result["answer"]
    assert "sky or forecast could change" in result["answer"]
    assert result["support_basis"] == "current_prompt_and_recent_conversation"


def test_reversible_everyday_choice_uses_recent_visible_options():
    result = build_answer_substance(
        "Back to the porch and walk: which option keeps the plan easiest to change?",
        [{"observation": "We were choosing between reading on the porch and taking a short walk."}],
    )

    assert result["answer_kind"] == "grounded_reversible_everyday_choice"
    assert result["answer"].startswith("Reading on the porch")
    assert "switch to the walk" in result["answer"]


def test_conflicting_reports_do_not_become_a_false_current_fact():
    result = build_answer_substance(
        "I have two reports: one says the porch is dry and one says it is wet. "
        "What can we honestly conclude?"
    )

    assert result["answer_kind"] == "grounded_conflicting_reports"
    assert "reports conflict" in result["answer"]
    assert "not whether the porch is dry or wet right now" in result["answer"]
    assert "look at the porch directly" in result["answer"]


def test_new_evidence_reopens_only_the_prior_conclusion():
    result = build_answer_substance(
        "Now I notice the drawer still catches after the runner is tightened. "
        "Does that change your answer?",
        [
            {
                "observation": (
                    "My working guess is a loose drawer runner, but the frame could be warped. "
                    "What should I check first?"
                )
            }
        ],
    )

    assert result["answer_kind"] == "evidence_revision"
    assert "would not defend the earlier guess unchanged" in result["answer"]
    assert "observations that still fit remain useful" in result["answer"]
    assert result["support_basis"] == "current_prompt_and_recent_conversation"
    assert result["memory_write_active"] is False


def test_changed_time_constraint_scales_prior_plan_without_discarding_its_aim():
    result = build_answer_substance(
        "We only have five minutes now. Does the plan still hold?",
        [
            {
                "observation": (
                    "I have tea, a notebook, and twenty minutes. "
                    "Recommend a simple way to use the time."
                )
            }
        ],
    )

    assert result["answer_kind"] == "constraint_revised_plan"
    assert "aim still holds" in result["answer"]
    assert "twenty minutes to only have five minutes" not in result["answer"]
    assert "five minutes" in result["answer"]
    assert "one quick note" in result["answer"]


def test_follow_up_can_request_reason_then_a_bounded_number_of_steps():
    result = build_answer_substance(
        "Give me the reason first, then the two smallest steps.",
        [
            {
                "observation": (
                    "I have cocoa, a journal, and twelve minutes. "
                    "What could I do with them?"
                )
            }
        ],
    )

    assert result["answer_kind"] == "contextual_answer_development"
    assert result["answer"].startswith("Reason first:")
    assert "Step 1:" in result["answer"]
    assert "Step 2:" in result["answer"]
    assert "Step 3:" not in result["answer"]
    assert result["structured_semantic_handoff"] is True


def test_visible_shelf_properties_own_the_comparison_before_generic_method():
    result = build_answer_substance(
        "The bins are sorted. Shelf A is wide but wobbly. Shelf B is narrower but sturdy. "
        "Acknowledge the bins, compare the shelves, and tell me where to place the heavy tools."
    )

    assert result["answer_kind"] == "grounded_visible_option_comparison"
    assert result["answer"].startswith("The bins are already sorted.")
    assert "Shelf B is the better place for the heavier items" in result["answer"]
    assert "shelf a is wide but wobbly" in result["answer"].lower()
    assert result["support_basis"] == "current_prompt_and_recent_conversation"
    assert result["source_required_for_factual_claim"] is False


def test_visible_option_revision_uses_latest_session_description():
    result = build_answer_substance(
        "Back to the shelves: what changed and what stayed the same?",
        [
            {"observation": "Shelf A is wide but wobbly. Shelf B is narrow but sturdy."},
            {"observation": "Correction: shelf A is wide and steady now."},
        ],
    )

    assert result["answer_kind"] == "grounded_visible_option_revision"
    assert "changed from wide but wobbly to wide and steady now" in result["answer"].lower()
    assert "other option's last supplied description stayed unchanged" in result["answer"].lower()
