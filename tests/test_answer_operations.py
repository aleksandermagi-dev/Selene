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
    assert status["generic_prose_may_complete_operation"] is False
    assert status["canonical_obligation_reparse_allowed"] is False
    assert status["memory_write_active"] is False
    assert status["identity_change"] is False
    assert status["governance_change"] is False
    assert status["authority_change"] is False
    assert status["expression_authority"] is False


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
