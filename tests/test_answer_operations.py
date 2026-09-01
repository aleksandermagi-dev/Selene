from selene.answer_operations import (
    answer_operations_status,
    build_answer_operation_packet,
)
from selene.answer_substance import build_answer_substance


def _spine(*obligations: dict, **single_obligation: object) -> dict:
    if single_obligation:
        obligations = (single_obligation,)
    canonical = [
        {
            "id": f"obligation-{index + 1}",
            "required": True,
            "responsible_owner": "intelligence_os",
            "requested_response_functions": [],
            **obligation,
        }
        for index, obligation in enumerate(obligations)
    ]
    return {
        "open_obligations": canonical,
        "obligation_ledger": {
            "obligations": canonical,
            "downstream_reparse_allowed": False,
        },
    }


def _intelligence(prompt: str) -> dict:
    substance = build_answer_substance(prompt)
    substance["selected_for_answer"] = True
    return {
        "used": True,
        "answer_substance": substance,
        "source_refs": ["test:current_prompt"],
    }


def test_status_declares_typed_non_authoritative_operation_contracts() -> None:
    status = answer_operations_status()

    assert status["status"] == "answer_operation_coordination_ready"
    assert "prediction" in status["supported_operations"]
    assert "counterfactual" in status["supported_operations"]
    assert "planning" in status["supported_operations"]
    assert "creative_expression" in status["supported_operations"]
    assert "FICTIONAL_INVENTION" in status["epistemic_states"]
    assert "NO_FICTION_RELEASED" in status["epistemic_states"]
    assert status["generic_prose_may_complete_operation"] is False
    assert status["canonical_obligation_reparse_allowed"] is False
    assert status["memory_write_active"] is False
    assert status["identity_change"] is False
    assert status["governance_change"] is False
    assert status["authority_change"] is False
    assert status["expression_authority"] is False


def test_creative_operation_carries_brief_source_fiction_lineage_and_stop_receipts() -> None:
    prompt = "Write a short tense dialogue between Ilya and Noor in three sentences."
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["creative_expression"],
                source_text=prompt,
            ),
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    assert packet["status"] == "answer_operations_complete"
    result = packet["results"][0]
    fields = result["fields"]
    assert result["operation"] == "creative_expression"
    assert result["epistemic_state"] == "FICTIONAL_INVENTION"
    assert fields["creative_brief"]["content_owner"] == "answer_substance"
    assert fields["creative_brief"]["content_generation_allowed_in_nlo"] is False
    assert fields["fiction_status"] == "explicit_fictional_invention"
    assert fields["source_style_separation"]["status"] == "released"
    assert fields["revision_lineage"]["relation"] == "root_invention"
    assert fields["stopping_receipt"]["recursion_allowed"] is False
    assert fields["fact_claimed"] is False
    assert fields["memory_candidate_created"] is False
    assert "prompt_grounded_creative_contract" in result["source_role_receipt"]["roles"]
    assert result["terminal_receipt"]["further_attempt_authorized"] is False


def test_creative_hold_is_typed_as_no_fiction_released() -> None:
    prompt = "Write a scene in the style of Virginia Woolf about a train platform."
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["creative_expression"],
                source_text=prompt,
            ),
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["epistemic_state"] == "NO_FICTION_RELEASED"
    assert result["fields"]["fiction_status"] == "no_fiction_released"
    assert result["fields"]["source_style_separation"]["status"] == (
        "unsupported_style_imitation_held"
    )


def test_method_owner_returns_typed_steps_or_precise_fields() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["method"],
                source_text="How should we plan this?",
                responsible_owner="ordinary_conversation_path",
            ),
            "intelligence_os_support": _intelligence("How should we plan this?"),
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["operation"] == "method"
    assert result["fields"]["steps"]
    assert result["fields"]["basis"]
    assert result["fields"]["limitations"]
    assert result["generic_prose_used_as_completion"] is False


def test_comparison_candidates_do_not_repeat_the_parent_source_text() -> None:
    source = "Compare paper and thin card for a pinwheel"
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["comparison"],
                source_text=source,
                parent_source_text=source,
                responsible_owner="answer_engine",
            ),
            "answer_engine_support": {
                "adapter_executed": True,
                "answer_packet": {
                    "domain": "comparison_planning",
                    "direct_answer": "Paper bends more easily, while thin card holds its shape longer.",
                    "source_refs": ["test:visible_options"],
                },
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["candidates"] == ["paper", "thin card for a pinwheel"]


def test_comparison_candidates_can_come_from_the_current_domain_answer() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["comparison"],
                source_text="Compare their tradeoffs.",
                responsible_owner="answer_engine",
            ),
            "answer_engine_support": {
                "adapter_executed": True,
                "answer_packet": {
                    "domain": "comparison_planning",
                    "direct_answer": (
                        "In a shared-schedule design, the groups alternate rooms. "
                        "In a parallel-zone design, both groups run at once."
                    ),
                    "source_refs": ["test:current_prompt"],
                },
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["candidates"] == [
        "shared-schedule design",
        "parallel-zone design",
    ]


def test_comparison_candidate_parser_removes_follow_up_question_grammar() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["comparison"],
                source_text=(
                    "What difference between consistency and fairness were we "
                    "preserving there?"
                ),
                responsible_owner="intelligence_os",
            ),
            "intelligence_os_support": {
                "used": True,
                "answer_substance": {
                    "selected_for_answer": True,
                    "answer_kind": "accessibility_fairness_application",
                    "answer": (
                        "Consistency applies the same treatment. Fairness considers "
                        "relevant needs and equal participation."
                    ),
                    "support_basis": "current_prompt_and_previous_answer",
                    "semantic_packet": {
                        "units": [
                            {"text": "Consistency applies the same treatment."},
                            {
                                "text": (
                                    "Fairness considers relevant needs and equal "
                                    "participation."
                                )
                            },
                        ]
                    },
                },
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["candidates"] == ["consistency", "fairness"]


def test_current_domain_explanation_outranks_an_older_contextual_answer() -> None:
    explanation = (
        "An exact answer can be correct for one case; understanding also includes "
        "why it works and how to apply it to a different case."
    )
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["reason"],
                source_text="Explain why an exact answer is not the same as understanding.",
                responsible_owner="answer_engine",
            ),
            "answer_engine_support": {
                "adapter_executed": True,
                "answer_packet": {
                    "domain": "coordinated_multi_domain",
                    "direct_answer": f"18 * 7 = 126. {explanation}",
                    "source_refs": ["verified_math:test", "reasoning:test"],
                    "supported_semantics": {
                        "units": [
                            {"text": "18 * 7 = 126."},
                            {"text": explanation},
                        ]
                    },
                },
            },
            "contextual_follow_up": {
                "kind": "reason_follow_up",
                "response_seed": "An older discussion supplied a different reason.",
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["expression_source_id"] == "answer_engine"
    assert result["fields"]["conclusion"] == explanation
    assert "older discussion" not in result["expression_seed"].lower()


def test_authored_preference_is_current_and_not_a_factual_gap() -> None:
    prompt = "What would you like to get into?"
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["preference"],
                source_text=prompt,
                responsible_owner="ordinary_conversation_path",
            ),
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["authored_preference"]
    assert result["fields"]["basis"] == "current_authored_preference"
    assert result["fields"]["current_only"] is True
    assert result["expression_source_id"] == "intelligence_os_answer"


def test_structured_prediction_preserves_basis_assumptions_and_revision() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["prediction"],
                source_text="What would we expect next?",
            ),
            "exploratory_reasoning": {
                "prediction": {
                    "available": True,
                    "statement": "The flicker should recur when the lamp shares the same power path.",
                    "basis_evidence_ids": ["visible-observation-1"],
                    "conditions": ["the wiring state remains comparable"],
                    "assumptions": ["the observed association is relevant"],
                    "what_would_change": ["the flicker recurs with the lamp disconnected"],
                },
                "response_seed": "My current prediction is that the flicker should recur when the lamp shares the same power path.",
                "source_refs": ["current_conversation:visible_observation"],
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["basis"] == ["visible-observation-1"]
    assert result["fields"]["assumptions"]
    assert result["fields"]["revision_conditions"]
    assert result["fields"]["predicted_change"].startswith("The flicker")


def test_structured_hypothesis_preserves_alternatives_and_discriminating_check() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["hypothesis"],
                source_text="What is your best current hypothesis?",
            ),
            "exploratory_reasoning": {
                "hypothesis": {
                    "available": True,
                    "statement": "The lamp may be affecting the shared power path.",
                    "basis_evidence_ids": ["visible-observation-1"],
                    "assumptions": ["the timing is not coincidental"],
                    "alternatives": ["the display cable is loose"],
                    "discriminating_observations": [
                        "repeat the comparison with the lamp disconnected"
                    ],
                    "what_would_change": [
                        "the flicker continues under the same comparison"
                    ],
                },
                "response_seed": "My current hypothesis is that the lamp may be affecting the shared power path.",
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["hypothesis"].startswith("The lamp")
    assert result["fields"]["alternatives"]
    assert result["fields"]["discriminating_checks"]
    assert result["fields"]["revision_conditions"]


def test_structured_counterfactual_restores_actual_state_and_stays_candidate() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["counterfactual"],
                source_text="What if release happened before validation?",
            ),
            "exploratory_reasoning": {
                "counterfactual": {
                    "available": True,
                    "changed_premise": "release happened before validation",
                    "preserved_premises": ["the same acceptance rule remained"],
                    "consequence": "the release would lack the validation result",
                    "basis_evidence_ids": ["current-sequence"],
                    "limits": ["only this dependency is changed"],
                    "actual_state": "validation currently precedes release",
                    "actual_state_restored": True,
                    "what_would_change": ["another verifier supplied the result"],
                },
                "response_seed": "Counterfactually, release would lack the validation result.",
                "source_refs": ["current_conversation:visible_observation"],
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["actual_state_restored"] is True
    assert result["epistemic_state"] == "CANDIDATE_UNVERIFIED"
    assert result["source_role_receipt"]["expression_may_strengthen_status"] is False
    assert result["terminal_receipt"]["automatic_retention"] is False


def test_phase_five_synthetic_mixed_reasoning_walkthrough_is_disposable() -> None:
    prompt = (
        "Given this synthetic tray test, predict the next result, consider what "
        "would change if the divider moved first, and plan one bounded recheck."
    )
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                {
                    "requested_response_functions": ["prediction"],
                    "source_text": prompt,
                },
                {
                    "requested_response_functions": ["counterfactual"],
                    "source_text": prompt,
                },
                {
                    "requested_response_functions": ["planning"],
                    "source_text": prompt,
                    "responsible_owner": "answer_engine",
                },
            ),
            "exploratory_reasoning": {
                "prediction": {
                    "available": True,
                    "statement": "The token will remain in the left tray on the next unchanged run.",
                    "basis_evidence_ids": ["synthetic:tray-observation-1"],
                    "conditions": ["the divider and tray angle remain unchanged"],
                    "assumptions": ["the first observation was representative"],
                    "alternatives": ["the token crosses because of an unnoticed tilt"],
                    "what_would_change": ["an unchanged repeat places the token in the right tray"],
                },
                "counterfactual": {
                    "available": True,
                    "changed_premise": "the divider moved before the token was released",
                    "preserved_premises": ["the same tray and token were used"],
                    "consequence": "the earlier observation would not determine the new path",
                    "basis_evidence_ids": ["synthetic:tray-observation-1"],
                    "limits": ["only divider timing is changed"],
                    "actual_state": "the divider did not move before the observed release",
                    "actual_state_restored": True,
                    "what_would_change": ["a controlled divider-timing comparison was observed"],
                },
                "response_seed": "The synthetic tray result remains provisional.",
                "source_refs": ["synthetic:tray-observation-1"],
            },
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    assert packet["status"] == "answer_operations_complete"
    assert packet["operation_count"] == packet["completed_count"] == 3
    assert packet["expression_handoff"]["composition_required"] is True
    by_operation = {item["operation"]: item for item in packet["results"]}
    assert set(by_operation) == {"prediction", "counterfactual", "planning"}
    assert by_operation["prediction"]["epistemic_state"] == "CANDIDATE_UNVERIFIED"
    assert by_operation["counterfactual"]["fields"]["actual_state_restored"] is True
    assert "stop" in by_operation["planning"]["fields"]["stopping_condition"].lower()
    assert all(
        item["terminal_receipt"]["automatic_retention"] is False
        for item in packet["results"]
    )


def test_concrete_resource_plan_has_task_specific_dependencies_fallback_and_stop() -> None:
    prompt = (
        "I have twenty minutes, tea, and a notebook. Help me plan one small thing."
    )
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["planning"],
                source_text=prompt,
                responsible_owner="answer_engine",
            ),
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["operation"] == "planning"
    assert result["fields"]["steps"]
    assert result["fields"]["dependencies"]
    assert result["fields"]["constraints"]
    assert result["fields"]["fallback"]
    assert "stop" in result["fields"]["stopping_condition"].lower()
    assert result["terminal_receipt"]["further_attempt_authorized"] is False


def test_causal_explanation_has_conclusion_mechanism_and_basis() -> None:
    prompt = "Why should fractions come before calculus?"
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["reason"],
                source_text=prompt,
            ),
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["conclusion"]
    assert result["fields"]["mechanism_or_reason"]
    assert result["fields"]["basis"]


def test_structured_comparison_returns_candidates_findings_and_basis() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["comparison"],
                source_text="Compare the porch and the walk.",
                responsible_owner="answer_engine",
            ),
            "exploratory_reasoning": {
                "comparison": {
                    "available": True,
                    "left": "porch",
                    "right": "walk",
                    "dimensions": ["reversibility", "movement"],
                    "venn": {
                        "shared": ["both are available this afternoon"],
                        "only_left": ["stays near home"],
                        "only_right": ["provides movement"],
                        "unresolved": ["weather"],
                    },
                    "source_refs": ["current_conversation:visible_options"],
                },
                "response_seed": "Both are available; the porch stays near home, while the walk provides movement.",
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["candidates"] == ["porch", "walk"]
    assert result["fields"]["findings"]["shared"]
    assert result["fields"]["comparison_basis"]


def test_prompt_grounded_choice_has_selection_criteria_and_revision_condition() -> None:
    prompt = (
        "It is a quiet afternoon. Choose between reading on the porch and taking a walk, "
        "then tell me why."
    )
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["choice"],
                source_text=prompt,
                responsible_owner="ordinary_conversation_path",
            ),
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["selected_option"]
    assert result["fields"]["criteria"]
    assert result["fields"]["revision_conditions"]


def test_disagreement_evaluates_the_claim_without_turning_conflict_into_identity() -> None:
    prompt = "I think calculus should come before fractions. Do you disagree?"
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["disagreement", "claim_evaluation"],
                source_text=prompt,
            ),
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert result["fields"]["stance"] == "disagreement"
    assert result["fields"]["claim_evaluated"] == prompt
    assert result["fields"]["premises"]
    assert result["identity_change"] is False


def test_current_session_summary_requires_real_points_and_preserves_scope() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["session_summary"],
                source_text="Can you summarize where we landed?",
                responsible_owner="ordinary_conversation_path",
            ),
            "current_session_summary": {
                "points": [
                    "We compared the porch and the walk.",
                    "The porch remained the easier reversible choice.",
                ],
                "response_seed": "We compared the porch and the walk, then kept the porch as the easier reversible choice.",
                "source_refs": ["conversation_spine:current_session_summary"],
            },
        }
    )

    result = packet["results"][0]
    assert result["status"] == "completed"
    assert len(result["fields"]["points"]) == 2
    assert result["fields"]["source_scope"] == "current_session_only"


def test_generic_comparison_method_does_not_impersonate_completed_comparison() -> None:
    prompt = "Compare the options."
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["comparison"],
                source_text=prompt,
                responsible_owner="answer_engine",
            ),
            "intelligence_os_support": _intelligence(prompt),
        }
    )

    result = packet["results"][0]
    assert result["status"] == "missing_input"
    assert "two supported candidates" in result["missing_input"]
    assert result["generic_prose_used_as_completion"] is False
    assert packet["generic_prose_accepted_as_completion"] is False


def test_missing_report_cannot_request_current_turn_inputs_already_supplied() -> None:
    obligation = {
        "id": "obligation-1",
        "required": True,
        "responsible_owner": "answer_engine",
        "requested_response_functions": ["comparison"],
        "source_text": "Compare paper and thin card.",
    }
    spine = _spine(obligation)
    spine["current_turn_fact_ledger"] = {"fact_count": 3}
    spine["current_turn_owner_inputs"] = [
        {
            "obligation_id": "obligation-1",
            "fact_count": 3,
            "fact_ids": ["paper", "card", "durability"],
            "supplied_field_names": ["options", "criteria"],
            "supplied_fields": {
                "options": ["paper", "thin card"],
                "criteria": ["durability"],
            },
            "current_turn_precedence": True,
        }
    ]

    packet = build_answer_operation_packet({"conversation_spine": spine})
    result = packet["results"][0]

    assert result["status"] == "missing_input"
    assert "two supported candidates" not in result["missing_input"]
    assert "shared comparison basis" not in result["missing_input"]
    assert "no additional user input identified" in result["missing_input"]
    assert result["current_turn_input_receipt"]["accounted_before_result"] is True
    assert result["already_supplied_current_turn_fields"] == ["options", "criteria"]
    assert packet["current_turn_fact_ledger_used"] is True
    assert packet["all_operation_inputs_accounted_for"] is True


def test_correction_and_closure_are_typed_without_changing_identity_or_authority() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                {
                    "requested_response_functions": ["correction", "reopening"],
                    "source_text": "I meant the cool evening, not the warm one.",
                    "responsible_owner": "ordinary_conversation_path",
                },
                {
                    "requested_response_functions": ["closure"],
                    "source_text": "Talk later.",
                    "responsible_owner": "ordinary_conversation_path",
                },
            ),
            "epistemic_revision_plan": {
                "detected": True,
                "revised_claim": "the evening is cool",
                "target": "the drink recommendation",
            },
        }
    )

    correction, closure = packet["results"]
    assert correction["status"] == "completed"
    assert correction["fields"]["recompute_required"] is True
    assert correction["fields"]["affected_result"] == "the drink recommendation"
    assert closure["status"] == "completed"
    assert closure["fields"]["closure_intent"]
    assert packet["identity_change"] is False
    assert packet["authority_change"] is False


def test_source_wording_is_not_reparsed_into_an_operation() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                source_text="Predict what happens next, please.",
                requested_response_functions=[],
            ),
            "exploratory_reasoning": {
                "prediction": {
                    "available": True,
                    "statement": "This text should not create an operation by itself.",
                    "basis_evidence_ids": ["test-evidence"],
                    "what_would_change": ["a canonical prediction obligation"],
                }
            },
        }
    )

    assert packet["operation_count"] == 0
    assert packet["status"] == "answer_operations_not_material"


def test_hard_boundary_holds_operation_without_executing_it() -> None:
    packet = build_answer_operation_packet(
        {
            "conversation_spine": _spine(
                requested_response_functions=["method"],
                source_text="How should this proceed?",
            ),
            "intelligence_os_support": _intelligence("How should this proceed?"),
            "hard_boundary": True,
        }
    )

    result = packet["results"][0]
    assert result["status"] == "unsupported"
    assert result["fields"] == {}
    assert packet["autonomous_action_allowed"] is False
