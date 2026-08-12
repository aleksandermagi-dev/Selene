from selene.epistemic_composition import (
    compose_epistemic_answer,
    epistemic_composition_status,
)


def _assert_locked(result):
    assert result["memory_write_active"] is False
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


def _obligation(identifier, kind, text):
    return {
        "id": identifier,
        "kind": kind,
        "source_text": text,
        "required": True,
    }


def test_status_preserves_known_parts_and_open_ended_exploration():
    result = epistemic_composition_status()

    assert result["known_part_may_survive_unknown_neighbor"] is True
    assert result["unknown_part_may_not_downgrade_supported_part"] is True
    assert result["prediction_requires_future_fact"] is False
    assert result["hypothesis_requires_prior_proof"] is False
    _assert_locked(result)


def test_known_prediction_and_missing_parts_remain_separate_and_ordered():
    obligations = [
        _obligation("known", "reason", "Why do day and night happen?"),
        _obligation("prediction", "prediction", "Predict whether tomorrow will be warmer."),
        _obligation("exact", "requested_output", "Give tomorrow's exact sunrise time."),
    ]
    result = compose_epistemic_answer(
        {
            "prompt": (
                "Why do day and night happen, what is your prediction for tomorrow's "
                "temperature, and what is the exact sunrise time?"
            ),
            "content_seed": "Earth's rotation produces the day-and-night cycle.",
            "response_obligations": obligations,
            "source_id": "approved_comprehension",
            "source_class": "approved_knowledge",
            "part_candidates": [
                {
                    "obligation_id": "known",
                    "epistemic_state": "supported_answer",
                    "text": "Earth's rotation produces the day-and-night cycle.",
                    "addressed": True,
                    "source_class": "approved_knowledge",
                    "source_refs": ["lesson:earth-rotation"],
                },
                {
                    "obligation_id": "prediction",
                    "epistemic_state": "bounded_prediction",
                    "text": "My current prediction is that warmer conditions are possible if the same air mass remains.",
                    "addressed": True,
                    "source_class": "reasoning_answer",
                },
                {
                    "obligation_id": "exact",
                    "epistemic_state": "missing_ground",
                    "text": "I still need the date, location, and current astronomical data for the exact sunrise time.",
                    "unsupported": True,
                    "missing_ground": "date, location, and current astronomical data",
                },
            ],
        }
    )

    assert result["composition_order"] == ["known", "prediction", "exact"]
    assert [item["epistemic_state"] for item in result["parts"]] == [
        "supported_answer",
        "bounded_prediction",
        "missing_ground",
    ]
    assert result["dominant_state"] == "partial_answer"
    assert result["known_part_preserved_with_missing_part"] is True
    assert result["unknown_part_downgraded_supported_part"] is False
    assert result["supported_part_count"] == 2
    assert result["missing_part_count"] == 1
    assert "Earth's rotation" in result["content_seed"]
    assert "My current prediction" in result["content_seed"]
    assert "I still need the date" in result["content_seed"]
    assert result["release_ready"] is True
    _assert_locked(result)


def test_inference_and_hypothesis_are_not_upgraded_to_known_fact():
    result = compose_epistemic_answer(
        {
            "prompt": "What can we infer, and what hypothesis might explain the vibration?",
            "content_seed": "The vibration changed after the mount was tightened.",
            "response_obligations": [
                _obligation("inference", "reason", "What can we infer from the change?"),
                _obligation("hypothesis", "hypothesis", "What hypothesis might explain the vibration?"),
            ],
            "source_id": "intelligence_os_answer",
            "source_class": "reasoning_answer",
            "part_candidates": [
                {
                    "obligation_id": "inference",
                    "epistemic_state": "supported_inference",
                    "text": "The timing supports an inference that the mount is relevant.",
                    "addressed": True,
                },
                {
                    "obligation_id": "hypothesis",
                    "epistemic_state": "open_hypothesis",
                    "text": "A working hypothesis is that looseness in the mount amplified the vibration.",
                    "addressed": True,
                },
            ],
        }
    )

    assert result["mixed_epistemic_answer"] is True
    assert result["epistemic_states_present"] == ["supported_inference", "open_hypothesis"]
    assert result["unlabeled_exploratory_part_count"] == 0
    assert all(item["epistemic_state"] != "supported_answer" for item in result["parts"])
    _assert_locked(result)


def test_unlabeled_prediction_is_held_as_not_release_ready_without_erasing_it():
    result = compose_epistemic_answer(
        {
            "prompt": "What do you predict next?",
            "content_seed": "The temperature rises next.",
            "response_obligations": [
                _obligation("prediction", "prediction", "What do you predict next?")
            ],
            "part_candidates": [
                {
                    "obligation_id": "prediction",
                    "epistemic_state": "bounded_prediction",
                    "text": "The temperature rises next.",
                    "addressed": True,
                }
            ],
        }
    )

    assert result["parts"][0]["epistemic_state"] == "bounded_prediction"
    assert result["parts"][0]["visible_label_required"] is True
    assert result["parts"][0]["visible_label_present"] is False
    assert result["release_ready"] is False
    assert result["content_seed"] == "The temperature rises next."
    _assert_locked(result)


def test_selected_exploratory_answer_remains_one_complete_typed_part():
    seed = (
        "The evidence is genuinely split here. That conflict stays unresolved "
        "until a matched observation distinguishes the positions."
    )
    result = compose_epistemic_answer(
        {
            "prompt": "The sources conflict. What can we conclude?",
            "content_seed": seed,
            "response_obligations": [
                _obligation("conclusion", "direct_question", "What can we conclude?")
            ],
            "answer_completion": {
                "resolutions": [
                    {
                        "obligation_id": "conclusion",
                        "visible_fragment": "Unrelated missing-ground scaffolding.",
                        "unsupported": True,
                    }
                ]
            },
            "exploratory_reasoning": {
                "selected_for_answer": True,
                "response_kind": "data_conflict",
                "source_refs": ["source:a", "source:b"],
            },
            "source_id": "exploratory_reasoning",
            "source_class": "reasoning_answer",
        }
    )

    assert result["content_seed"] == seed
    assert result["part_count"] == 1
    assert result["missing_part_count"] == 0
    assert result["dominant_state"] == "supported_inference"
    assert result["parts"][0]["certainty"] == "unresolved_claim_level_conflict"
    assert result["exploratory_reasoning_primary_part_preserved"] is True
    assert result["release_ready"] is True
    _assert_locked(result)
