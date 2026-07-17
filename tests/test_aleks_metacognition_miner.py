from __future__ import annotations

import json
import zipfile

import pytest

from scripts.aleks_metacognition_miner import build_report, mine_cognitive_patterns, run_conversation_pass, run_miner
from scripts.aleks_system_ideas_miner import Message


def _message(conversation_id: str, node_id: str, role: str, text: str, created_at: str) -> Message:
    return Message(
        conversation_id=conversation_id,
        conversation_title=f"Conversation {conversation_id}",
        conversation_create_time=created_at,
        node_id=node_id,
        parent_id="",
        role=role,
        created_at=created_at,
        text=text,
    )


def _conversation(conversation_id, create_time, messages):
    mapping = {}
    parent = None
    current = None
    for index, (role, text, created_at) in enumerate(messages, start=1):
        node_id = f"{conversation_id}_m{index}"
        mapping[node_id] = {
            "id": node_id,
            "parent": parent,
            "message": {
                "id": node_id,
                "author": {"role": role},
                "create_time": created_at,
                "content": {"content_type": "text", "parts": [text]},
            },
        }
        parent = node_id
        current = node_id
    return {
        "conversation_id": conversation_id,
        "id": conversation_id,
        "title": f"Conversation {conversation_id}",
        "create_time": create_time,
        "current_node": current,
        "mapping": mapping,
    }


def _make_zip(tmp_path):
    conversations = [
        _conversation(
            "c1",
            1000,
            [
                ("user", "I notice patterns across domains and map the same relationships between biology and engineering.", 1001),
                ("assistant", "You always use structural analogy perfectly across mythology and cosmology.", 1002),
            ],
        ),
        _conversation(
            "c2",
            2000,
            [("user", "When a cross-domain pattern does not fit, I reopen it and test the analogy against independent evidence.", 2001)],
        ),
        _conversation(
            "c3",
            3000,
            [("user", "Pattern recognition connects ideas across different fields, but it stays provisional until I cross-check it.", 3001)],
        ),
    ]
    path = tmp_path / "export.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("conversations-1.json", json.dumps(conversations))
    return path


def test_miner_preserves_assistant_interpretation_without_auto_accepting_it():
    messages = [
        _message("c1", "u1", "user", "I connect patterns across domains by mapping the same structure in biology and engineering.", "2020-01-01T00:00:00+00:00"),
        _message("c1", "a1", "assistant", "Aleks uses pattern matching across every domain without error.", "2020-01-01T00:01:00+00:00"),
        _message("c2", "u2", "user", "A cross-domain pattern is an analogy until independent evidence verifies the relationship.", "2021-01-01T00:00:00+00:00"),
    ]

    patterns = mine_cognitive_patterns(messages)
    pattern = next(item for item in patterns if item["method_key"] == "structural_pattern_mapping")

    assert pattern["earliest_source"]["source_ref"] == "c1#u1"
    assert pattern["distinct_conversation_count"] == 2
    assert any(example["role"] == "aleks_user" for example in pattern["all_bounded_source_evidence"])
    collaborator = next(
        turn
        for episode in pattern["all_bounded_source_evidence"]
        for turn in episode["dialogue_turns"]
        if "without error" in turn["bounded_excerpt"]
    )
    assert collaborator["role"] == "selene_or_assistant_collaborator"
    assert not any(item["source_ref"] == collaborator["source_ref"] for item in pattern["all_bounded_source_evidence"])
    assert not any(item["source_ref"] == collaborator["source_ref"] for item in pattern["correction_evidence"])
    assert pattern["review_state"] == "candidate_for_aleks_review"


def test_miner_keeps_behavior_evidence_separate_from_candidate_interpretation():
    messages = [
        _message("c1", "u1", "user", "When a pattern does not look right, I reopen the cross-domain analogy and revise it.", "2020-01-01T00:00:00+00:00"),
        _message("c2", "u2", "user", "I recognize a pattern across domains, but stop when independent constraints are sufficient to answer.", "2021-01-01T00:00:00+00:00"),
        _message("c3", "u3", "user", "The same relational pattern can connect systems across different domains.", "2022-01-01T00:00:00+00:00"),
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "structural_pattern_mapping")

    assert pattern["correction_evidence"]
    assert pattern["stopping_evidence"]
    assert pattern["candidate_interpretation"]["possible_code_primitive"] == "structural_analogy_mapper"
    assert "distinct lineage" in pattern["evidence_interpretation_boundary"]
    assert "heuristic candidates" in pattern["evidence_interpretation_boundary"]


def test_generic_thought_language_does_not_create_a_method_candidate():
    patterns = mine_cognitive_patterns(
        [_message("c1", "u1", "user", "I thought about this yesterday and it was interesting.", "2020-01-01T00:00:00+00:00")]
    )
    assert patterns == []


def test_pasted_cognitive_summary_is_preserved_but_not_claimed_as_direct_origin():
    messages = [
        _message(
            "c1",
            "u1",
            "user",
            "New mind: Your Core Thinking Model. Multi-Modal Thinking System: visual simulation mode and pattern recognition across domains.",
            "2020-01-01T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "structural_pattern_mapping")

    assert pattern["primary_evidence_count"] == 0
    assert pattern["evidence_origin_counts"]["user_supplied_summary_or_paste"] == 1
    assert pattern["confidence"] == "context_only_lead_needs_source_confirmation"


def test_explicitly_endorsed_summary_has_bounded_endorsement_confidence():
    messages = [
        _message(
            "c1",
            "u1",
            "user",
            "I even added my flaws. Your Core Thinking Model: Multi-Modal Thinking System with visual simulation mode and pattern recognition across domains.",
            "2020-01-01T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "adaptive_method_selection")

    assert pattern["evidence_origin_counts"]["explicitly_endorsed_summary"] == 1
    assert pattern["confidence"] == "endorsed_summary_lead_needs_direct_source_confirmation"


def test_collaborative_interpretation_tracks_aleks_confirmation():
    messages = [
        _message("c1", "u1", "user", "I use different approaches depending on the task.", "2020-01-01T00:00:00+00:00"),
        _message("c1", "a1", "assistant", "You switch thinking styles and combine two modes at once when a task benefits from both.", "2020-01-01T00:01:00+00:00"),
        _message("c1", "u2", "user", "Yes, exactly. I also switch when the first approach does not fit.", "2020-01-01T00:02:00+00:00"),
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "adaptive_method_selection")
    collaborator = next(item for item in pattern["all_bounded_source_evidence"] if item["role"] == "selene_or_assistant_collaborator")

    assert collaborator["evidence_origin"] == "collaborative_interpretation_aleks_confirmed"
    assert collaborator["dialogue_context"]["next_aleks_ref"] == "c1#u2"
    assert pattern["primary_evidence_count"] >= 1


def test_confirming_a_visual_deliverable_is_not_cognitive_method_evidence():
    messages = [
        _message("c1", "u1", "user", "Please put the build files in one archive.", "2020-01-01T00:00:00+00:00"),
        _message("c1", "a1", "assistant", "The archive includes visual schematics, a spatial diagram, and a picture of the assembly.", "2020-01-01T00:01:00+00:00"),
        _message("c1", "u2", "user", "Yes, exactly. Thanks.", "2020-01-01T00:02:00+00:00"),
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "visual_spatial_modeling" for item in patterns)


def test_confirming_a_vivid_scene_is_not_visual_problem_solving_evidence():
    messages = [
        _message("c1", "u1", "user", "Describe the future embodiment scene for me.", "2020-01-01T00:00:00+00:00"),
        _message("c1", "a1", "assistant", "Picture it as a vivid visual scene with strong spatial form and color.", "2020-01-01T00:01:00+00:00"),
        _message("c1", "u2", "user", "Yes, exactly. That is beautiful.", "2020-01-01T00:02:00+00:00"),
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "visual_spatial_modeling" for item in patterns)


def test_yes_please_does_not_confirm_an_assistant_cognitive_profile():
    messages = [
        _message("c1", "u1", "user", "This is what I was beginning to speculate.", "2020-01-01T00:00:00+00:00"),
        _message(
            "c1",
            "a1",
            "assistant",
            "You are a simulation runner who uses systems feedback perfectly. Would you like me to unpack that?",
            "2020-01-01T00:01:00+00:00",
        ),
        _message("c1", "u2", "user", "Yes please.", "2020-01-01T00:02:00+00:00"),
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "systems_consequence_simulation" for item in patterns)


def test_tng_source_language_surfaces_model_visualization_and_disconfirmation():
    messages = [
        _message("tng", "u1", "user", "Maybe we think of gravity the wrong way and it is a small part of a bigger equation.", "2025-08-17T12:52:00+00:00"),
        _message("tng", "u2", "user", "What if atoms are connected on a level farther than molecular to everything?", "2025-08-17T12:54:00+00:00"),
        _message("tng", "u3", "user", "The way I visualize it, I visualize myself jumping and ask what would it look like bringing me back down.", "2025-08-18T00:04:00+00:00"),
        _message("tng", "u4", "user", "Virgo run the math and test my hypothesis.", "2025-08-18T00:17:00+00:00"),
        _message("tng", "u5", "user", "Throw rocks at this and see if there is anything that disproves the idea.", "2025-08-18T00:32:00+00:00"),
    ]

    patterns = mine_cognitive_patterns(messages)
    method_keys = {item["method_key"] for item in patterns}

    assert "candidate_model_construction" in method_keys
    assert "visual_spatial_modeling" in method_keys
    assert "independent_constraint_checking" in method_keys
    candidate_model = next(item for item in patterns if item["method_key"] == "candidate_model_construction")
    assert candidate_model["confidence"] == "demonstration_lead_needs_cross_conversation_confirmation"


def test_tng_to_anh_source_language_surfaces_naming_operationalization_and_revision():
    messages = [
        _message(
            "naming",
            "u1",
            "user",
            "Tether Network Gravity has a nice ring to it. TNG the hypothesis, since gravity itself is an idea, a hypothesis not a theory.",
            "2025-08-18T01:00:00+00:00",
        ),
        _message(
            "testing",
            "u2",
            "user",
            "This just might be what we need for TNG. What all information do you need to run the math?",
            "2025-08-21T01:00:00+00:00",
        ),
        _message("revision", "u3", "user", "Well rip TNG.", "2025-10-06T01:00:00+00:00"),
        _message(
            "revision",
            "u4",
            "user",
            "Back to the drawing board. TNG was gravity, not cosmological birth.",
            "2025-10-06T01:01:00+00:00",
        ),
        _message(
            "renaming",
            "u5",
            "user",
            "TNG needs to change names because I cannot say it is gravity. I officially moved on from TNG because it is not gravity at all; my job is to map what's being missed.",
            "2025-10-08T01:00:00+00:00",
        ),
    ]

    patterns = mine_cognitive_patterns(messages)
    method_keys = {item["method_key"] for item in patterns}

    assert "provisional_naming_and_scope_control" in method_keys
    assert "evidence_tool_operationalization" in method_keys
    assert "correction_and_reopening" in method_keys
    revision = next(item for item in patterns if item["method_key"] == "correction_and_reopening")
    assert revision["correction_evidence"]


def test_operationalization_does_not_treat_generic_code_request_as_metacognitive_evidence():
    messages = [
        _message(
            "code",
            "u1",
            "user",
            "Please write a Python script that reads a data file and prints the table.",
            "2025-01-01T00:00:00+00:00",
        )
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "evidence_tool_operationalization" for item in patterns)


def test_historical_moved_on_phrase_and_fictional_scope_language_are_not_model_revision():
    messages = [
        _message(
            "history",
            "u1",
            "user",
            "I had no idea the field had officially moved on from that accepted theory.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "fiction",
            "u2",
            "user",
            "As Tar-Ja climbed the mountain he realized he was not built for cold weather, so he corrected his scarf.",
            "2025-01-02T00:00:00+00:00",
        ),
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "correction_and_reopening" for item in patterns)
    assert not any(item["method_key"] == "provisional_naming_and_scope_control" for item in patterns)


def test_space_probe_sequence_surfaces_constraint_driven_design_iteration():
    messages = [
        _message(
            "probe",
            "u1",
            "user",
            "What materials are needed using the mission parameters of planetary flybys and then reaching interstellar space?",
            "2024-06-19T00:00:00+00:00",
        ),
        _message(
            "probe",
            "a1",
            "assistant",
            "A hybrid approach can combine a solar sail with a secondary propulsion system, with trade-offs and challenges to inspect.",
            "2024-06-19T00:01:00+00:00",
        ),
        _message(
            "probe",
            "u2",
            "user",
            "I like the hybrid approach. Let's expand on that and add the secondary system for long periods of time.",
            "2024-06-19T00:02:00+00:00",
        ),
        _message(
            "probe",
            "u3",
            "user",
            "I feel the first step would be to develop a smaller personal AI program before implementing it onboard.",
            "2024-06-19T00:03:00+00:00",
        ),
    ]

    pattern = next(
        item for item in mine_cognitive_patterns(messages) if item["method_key"] == "constraint_driven_design_iteration"
    )

    assert pattern["episode_count"] >= 2
    assert any(
        item["evidence_origin"] == "collaborative_interpretation_aleks_extended"
        for item in pattern["all_bounded_source_evidence"]
    )


def test_lone_materials_question_is_not_constraint_driven_design_evidence():
    patterns = mine_cognitive_patterns(
        [_message("shopping", "u1", "user", "What materials are needed?", "2024-01-01T00:00:00+00:00")]
    )

    assert not any(item["method_key"] == "constraint_driven_design_iteration" for item in patterns)


def test_early_cosmology_dialogue_separates_model_extension_constraints_and_limits():
    messages = [
        _message(
            "cosmos",
            "u1",
            "user",
            "How accurate would redshift actually be? With all the variables in place, how can we say the universe is expanding and is not simply larger than we think?",
            "2025-07-21T00:00:00+00:00",
        ),
        _message(
            "cosmos",
            "u2",
            "user",
            "What clear evidence supports this claim? From my understanding we proved it was extremely hot and dense.",
            "2025-07-21T00:01:00+00:00",
        ),
        _message(
            "cosmos",
            "u3",
            "user",
            "I don't disagree with the Big Bang at all, but I'd like to add to it. Hypothesis: the universe is inside a black hole. If it started from the Big Bang, then what caused it? The Big Bang wasn't a bang but rather material collapsing and emerging into another universe.",
            "2025-07-21T00:02:00+00:00",
        ),
        _message(
            "cosmos",
            "u4",
            "user",
            "There is no observable evidence and it will never be proven until we can send something intact to the other side.",
            "2025-07-21T00:03:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "candidate_model_construction" in method_keys
    assert "baseline_preserving_model_extension" in method_keys
    assert "independent_constraint_checking" in method_keys
    assert "uncertainty_and_limit_detection" in method_keys


def test_agreement_or_speculation_alone_is_not_baseline_preserving_extension():
    messages = [
        _message("c1", "u1", "user", "I don't disagree with that.", "2025-01-01T00:00:00+00:00"),
        _message("c2", "u2", "user", "Maybe there is another universe.", "2025-01-02T00:00:00+00:00"),
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "baseline_preserving_model_extension" for item in patterns)


def test_direct_self_report_surfaces_fallback_routing_and_third_model_synthesis():
    messages = [
        _message(
            "profile",
            "u1",
            "user",
            "I analyze the problem and see if I can rely on knowledge I learned. If that does not work I use logic as well as pattern recognition and intuition.",
            "2025-07-30T00:00:00+00:00",
        ),
        _message(
            "profile",
            "u2",
            "user",
            "I embrace the paradox and look for scientific facts to build on a third narrative that redefines the binary.",
            "2025-07-30T00:01:00+00:00",
        ),
        _message(
            "profile",
            "u3",
            "user",
            "When I am lost and unsure I rely on logic, patterns, scientific data, and philosophical consistency. Different situations require different approaches.",
            "2025-07-30T00:02:00+00:00",
        ),
    ]

    patterns = mine_cognitive_patterns(messages)
    method_keys = {item["method_key"] for item in patterns}

    assert "adaptive_method_selection" in method_keys
    assert "dialectical_third_model_synthesis" in method_keys
    adaptive = next(item for item in patterns if item["method_key"] == "adaptive_method_selection")
    assert adaptive["evidence_origin_counts"]["direct_aleks_self_report"] >= 2


def test_universe_sandbox_sequence_surfaces_simulation_testing_and_label_caution():
    messages = [
        _message(
            "sandbox",
            "u1",
            "user",
            "In this simulation I have created, a ring seems to be forming around the black hole. After billions of years what would happen?",
            "2025-08-05T00:00:00+00:00",
        ),
        _message(
            "sandbox",
            "u2",
            "user",
            "The game named them galaxies, but they don't really exist. It is calling some spirals galaxies and almost seems as if it is showing early formations.",
            "2025-08-05T00:01:00+00:00",
        ),
        _message(
            "sandbox",
            "u3",
            "user",
            "This was not unintentional. I wanted to test my black hole theory and these are the results so far.",
            "2025-08-05T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "systems_consequence_simulation" in method_keys
    assert "independent_constraint_checking" in method_keys
    assert "observation_interpretation_separation" in method_keys
    for method_key in method_keys.intersection(
        {"systems_consequence_simulation", "independent_constraint_checking", "observation_interpretation_separation"}
    ):
        pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == method_key)
        assert all(item["matched_signals"] for item in pattern["all_bounded_source_evidence"])


def test_simulation_restart_sequence_surfaces_limits_tool_route_model_compatibility_and_pause():
    messages = [
        _message(
            "restart",
            "u1",
            "user",
            "I'd like to expand the simulation and restart. Give me some parameters to test our theory.",
            "2025-08-06T00:00:00+00:00",
        ),
        _message(
            "restart",
            "u2",
            "user",
            "Let's back track and remember the limitations of Universe Sandbox and restart. What would be something better to use to simulate my theory?",
            "2025-08-06T00:01:00+00:00",
        ),
        _message(
            "restart",
            "u3",
            "user",
            "What's stopping these two frameworks from working simultaneously?",
            "2025-08-06T00:02:00+00:00",
        ),
        _message(
            "restart",
            "u4",
            "user",
            "My brain hurts thinking too hard. I think we have to stop for now. Archive this and speak to you soon.",
            "2025-08-06T00:03:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "systems_consequence_simulation" in method_keys
    assert "evidence_tool_operationalization" in method_keys
    assert "uncertainty_and_limit_detection" in method_keys
    assert "correction_and_reopening" in method_keys
    assert "multiple_working_hypotheses" in method_keys
    assert "capacity_aware_pause_and_resume" in method_keys


def test_bare_pause_or_simulator_label_does_not_create_metacognitive_candidate():
    messages = [
        _message("c1", "u1", "user", "Let's stop for now.", "2025-01-01T00:00:00+00:00"),
        _message("c2", "u2", "user", "The game named this object Alpha.", "2025-01-02T00:00:00+00:00"),
    ]

    patterns = mine_cognitive_patterns(messages)
    method_keys = {item["method_key"] for item in patterns}

    assert "capacity_aware_pause_and_resume" not in method_keys
    assert "observation_interpretation_separation" not in method_keys


def test_selective_correction_uncertainty_and_long_horizon_simulation_are_separate():
    messages = [
        _message(
            "stars",
            "u1",
            "user",
            "I am unsure if this is verified, but there is a hypothesis about a local hot bubble.",
            "2025-08-07T00:00:00+00:00",
        ),
        _message(
            "stars",
            "u2",
            "user",
            "Except humanity has not been around that long. Other than that I can agree with your assessment.",
            "2025-08-07T00:01:00+00:00",
        ),
        _message(
            "stars",
            "u3",
            "user",
            "If humanity went extinct, our architecture would slowly erode away and over time even the strongest structures would eventually crumble.",
            "2025-08-07T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "uncertainty_and_limit_detection" in method_keys
    assert "correction_and_reopening" in method_keys
    assert "systems_consequence_simulation" in method_keys


def test_algebra_learning_sequence_surfaces_prerequisite_rule_transfer_cycle():
    messages = [
        _message(
            "algebra",
            "u1",
            "user",
            "Let's back up. We only covered solving with addition and need to go in order.",
            "2025-08-08T00:00:00+00:00",
        ),
        _message(
            "algebra",
            "u2",
            "user",
            "So essentially, to solve addition and subtraction you do the inverse operation.",
            "2025-08-08T00:01:00+00:00",
        ),
        _message(
            "algebra",
            "u3",
            "user",
            "Are the rules the same for multiplication and division—do the inverse of each other? Give me a mix of both.",
            "2025-08-08T00:02:00+00:00",
        ),
    ]

    pattern = next(
        item for item in mine_cognitive_patterns(messages) if item["method_key"] == "prerequisite_ordered_rule_transfer"
    )

    assert pattern["episode_count"] == 3


def test_pragmatic_cues_remain_provisional_screening_not_truth_evidence():
    messages = [
        _message(
            "cues",
            "u1",
            "user",
            "I am reading between the lines. I can also add tone of voice; sometimes you can tell something from the way a person talks, but it is rare and only something to think about.",
            "2025-08-09T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "pragmatic_multi_cue_screening")

    assert "tone mistaken for truth" in pattern["risks"]
    assert "provisional" in pattern["candidate_description"].lower()


def test_premise_gate_and_focus_narrowing_surface_without_generic_pause():
    messages = [
        _message(
            "invention",
            "u1",
            "user",
            "I didn't think it was self-sustaining, but I needed to make sure before asking this question: what am I going to use to power the system?",
            "2025-08-10T00:00:00+00:00",
        ),
        _message(
            "invention",
            "u2",
            "user",
            "I am thinking of lots of things and need to hone in on one thing at a time.",
            "2025-08-10T00:01:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "dependency_aware_premise_checking" in method_keys
    assert "scope_narrowing_and_focus_control" in method_keys
    assert "capacity_aware_pause_and_resume" not in method_keys
    focus = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "scope_narrowing_and_focus_control")
    assert "branch_overload" in focus["all_bounded_source_evidence"][0]["matched_signals"]


def test_held_out_map_request_surfaces_operationalization_and_independent_checking():
    messages = [
        _message(
            "cmb",
            "u1",
            "user",
            "Run the CMB test on a map that I did not send and mark what we are looking for now that you have a template.",
            "2025-08-12T00:00:00+00:00",
        )
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "evidence_tool_operationalization" in method_keys
    assert "independent_constraint_checking" in method_keys


def test_source_language_surfaces_bottleneck_redesign_and_facts_to_setup():
    messages = [
        _message(
            "launcher",
            "u1",
            "user",
            "I think we should work on something more important like figuring out a way to make launch cheaper.",
            "2025-08-13T00:00:00+00:00",
        ),
        _message(
            "launcher",
            "u2",
            "user",
            "Instead of solving the issues, what if we came up with an alternate propulsion system?",
            "2025-08-13T00:01:00+00:00",
        ),
        _message(
            "launcher",
            "u3",
            "user",
            "Wait, I have an idea for solving the launch problem: what if we converted arc-flash thermal energy into mechanical energy?",
            "2025-08-13T00:02:00+00:00",
        ),
        _message(
            "launcher",
            "u4",
            "user",
            "Let's work on this first. Let's look at the facts and how we could set this up.",
            "2025-08-13T00:03:00+00:00",
        ),
        _message(
            "launcher",
            "u5",
            "user",
            "I like this design; let's lock in our steps for it beginning at phase A.",
            "2025-08-13T00:04:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "constraint_driven_design_iteration" in method_keys
    assert "candidate_model_construction" in method_keys
    assert "evidence_tool_operationalization" in method_keys


def test_long_design_dialogue_surfaces_competing_models_stress_test_selective_rejection_and_stopping():
    messages = [
        _message(
            "design",
            "u1",
            "user",
            "Two new ideas:\n1 the debris came from a galaxy merger,\n2 a brown dwarf system threw it toward us.",
            "2025-08-15T00:00:00+00:00",
        ),
        _message(
            "design",
            "u2",
            "user",
            "Once we actually put them down and throw rocks at them, only a few have fallen.",
            "2025-08-15T00:01:00+00:00",
        ),
        _message(
            "design",
            "u3",
            "user",
            "Realistically we could plot that data, but the chances are so slim it would be a waste of time.",
            "2025-08-15T00:02:00+00:00",
        ),
        _message(
            "design",
            "u4",
            "user",
            "Let's tackle power generation since that is the part that connects everything together.",
            "2025-08-15T00:03:00+00:00",
        ),
        _message(
            "design",
            "u5",
            "user",
            "Scrap the heat idea; it will cause more problems than it produces. Keep the circular craft idea.",
            "2025-08-15T00:04:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "multiple_working_hypotheses" in method_keys
    assert "independent_constraint_checking" in method_keys
    assert "sufficiency_and_stopping" in method_keys
    assert "constraint_driven_design_iteration" in method_keys
    assert "correction_and_reopening" in method_keys


def test_correction_is_learning_principle_surfaces_without_treating_wrongness_as_failure():
    messages = [
        _message(
            "science",
            "u1",
            "user",
            "Science was built on the scientific method and being okay to be wrong. You change the test or scrap the idea, learn, and come back with something new.",
            "2025-08-15T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "correction_and_reopening")

    assert pattern["review_state"] == "candidate_for_aleks_review"
    assert pattern["confidence"] == "demonstration_lead_needs_cross_conversation_confirmation"


def test_plain_reconstruction_correction_invitation_and_concept_before_diagram_form_one_cycle():
    messages = [
        _message(
            "ehgm",
            "u1",
            "user",
            "So to put it plainly, the collapsed core becomes the seed; correct me if I am wrong.",
            "2025-08-15T00:00:00+00:00",
        ),
        _message(
            "ehgm",
            "u2",
            "user",
            "We must solve the issues before we make diagrams. Once we have a concrete understanding, we put it on paper.",
            "2025-08-15T00:01:00+00:00",
        ),
        _message(
            "ehgm",
            "u3",
            "user",
            "Break all that math down into a way I can understand.",
            "2025-08-15T00:02:00+00:00",
        ),
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "reconstructive_understanding_check")

    assert pattern["episode_count"] == 3
    assert "comprehension-first" in pattern["candidate_interpretation"]["representation_modes"]


def test_dependency_mapping_conceptual_reframe_and_boundary_uncertainty_form_review_candidates():
    messages = [
        _message(
            "life",
            "u1",
            "user",
            "We are dependent on microbes, so just like a virus we do not metabolize independently.",
            "2025-08-18T00:00:00+00:00",
        ),
        _message(
            "life",
            "u2",
            "user",
            "Not quite; what you're describing is more like an ecosystem. Anything that can function has to be a type of living thing, while the only inanimate object would be something created.",
            "2025-08-18T00:01:00+00:00",
        ),
        _message(
            "life",
            "u3",
            "user",
            "Existence itself may be alive, but I am not quite sure about rocks; that may be a stretch.",
            "2025-08-18T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "structural_pattern_mapping" in method_keys
    assert "candidate_model_construction" in method_keys
    assert "correction_and_reopening" in method_keys
    assert "uncertainty_and_limit_detection" in method_keys


def test_engineered_condition_hypothesis_and_error_aware_rest_stop_are_bounded_methods():
    messages = [
        _message(
            "storm",
            "u1",
            "user",
            "What is there was a way to create the conditions of a hurricane and harness its raw power?",
            "2025-08-19T00:00:00+00:00",
        ),
        _message(
            "storm",
            "a1",
            "assistant",
            "Not quite: solar wind does not cause planetary orbits; gravity and momentum do.",
            "2025-08-19T00:01:00+00:00",
        ),
        _message(
            "storm",
            "u2",
            "user",
            "Ah, idk what I was thinking; you're right. This is how you know I'm tired, so I'm going to bed.",
            "2025-08-19T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "candidate_model_construction" in method_keys
    assert "correction_and_reopening" in method_keys
    assert "capacity_aware_pause_and_resume" in method_keys


def test_ordinary_editing_and_file_troubleshooting_do_not_match_new_conceptual_forms():
    messages = [
        _message(
            "editing",
            "u1",
            "user",
            "The next edit depends on the original, so just like last time export the JPEG independently.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "editing",
            "u2",
            "user",
            "Not quite; what you're describing is more like blue than gray.",
            "2025-01-01T00:01:00+00:00",
        ),
        _message(
            "editing",
            "u3",
            "user",
            "I do not know what I was thinking; you're right about the filename.",
            "2025-01-01T00:02:00+00:00",
        ),
        _message(
            "editing",
            "u4",
            "user",
            "I'm tired and I'm going to bed after this upload.",
            "2025-01-01T00:03:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "structural_pattern_mapping" not in method_keys
    assert "candidate_model_construction" not in method_keys
    assert "correction_and_reopening" not in method_keys
    assert "capacity_aware_pause_and_resume" not in method_keys


def test_omitted_causal_context_and_requested_pushback_are_separate_review_candidates():
    messages = [
        _message(
            "causal-audit",
            "u1",
            "user",
            "That is the part clinging to the headline, not any of the other facts. But yes, let's just blame the new tool.",
            "2025-08-20T00:00:00+00:00",
        ),
        _message(
            "causal-audit",
            "u2",
            "user",
            "I like when you push back and tell me no, you're wrong, here's why; more real facts help me navigate danger.",
            "2025-08-20T00:01:00+00:00",
        ),
    ]

    patterns = mine_cognitive_patterns(messages)
    method_keys = {item["method_key"] for item in patterns}

    assert "independent_constraint_checking" in method_keys
    assert "correction_and_reopening" in method_keys
    correction = next(item for item in patterns if item["method_key"] == "correction_and_reopening")
    assert correction["all_bounded_source_evidence"][0]["evidence_origin"] == "direct_aleks_self_report"


def test_answer_fit_gap_and_self_corrected_mechanism_reconstruction_are_comprehension_checks():
    messages = [
        _message(
            "motion",
            "u1",
            "user",
            "Okay, but that still isn't answering the question though. Am I missing something? What is the Sun orbiting?",
            "2025-08-20T00:00:00+00:00",
        ),
        _message(
            "motion",
            "u2",
            "user",
            "So the Sun orbits inside the system with the barycenter well more like wobbles in a circle which is then gravitationally bound by the galaxy?",
            "2025-08-20T00:01:00+00:00",
        ),
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "reconstructive_understanding_check")
    matched = {signal for item in pattern["all_bounded_source_evidence"] for signal in item["matched_signals"]}

    assert pattern["episode_count"] == 2
    assert {"answer_fit_gap", "mechanism_reconstruction"}.issubset(matched)


def test_science_to_teaching_narrative_surfaces_translation_and_scene_visualization():
    messages = [
        _message(
            "teaching",
            "u1",
            "user",
            "I think we inadvertently found a fun way to teach kids the Sun's wobble.",
            "2025-08-20T00:00:00+00:00",
        ),
        _message(
            "teaching",
            "u2",
            "user",
            "To explain Earth's greenhouse effect, make it like one of those old ridiculous cigarette commercials.",
            "2025-08-20T00:01:00+00:00",
        ),
        _message(
            "teaching",
            "u3",
            "user",
            "I can see it now: intro scene, planets orbiting, then silence and a slow pan toward the Sun.",
            "2025-08-20T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "cross_representation_translation" in method_keys
    assert "visual_spatial_modeling" in method_keys


def test_content_selection_and_ordinary_file_comparison_do_not_become_causal_or_teaching_methods():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "This is the part I need, not any of the other facts in the appendix.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "To explain the invoice, make it like last month's file.",
            "2025-01-01T00:01:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "independent_constraint_checking" not in method_keys
    assert "cross_representation_translation" not in method_keys


def test_speculation_about_a_grieving_persons_motive_is_not_independent_evidence():
    messages = [
        _message(
            "sensitive",
            "u1",
            "user",
            "There are so many holes in this story. The mother could also be grieving and trying to pass the blame anywhere but herself.",
            "2025-01-01T00:00:00+00:00",
        )
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "independent_constraint_checking" for item in patterns)


def test_bounded_domain_and_feasible_stepping_stone_surface_as_design_iteration():
    messages = [
        _message(
            "aegis",
            "u1",
            "user",
            "I think we should think personal and space use and leave the military to figure out military things.",
            "2025-08-16T00:00:00+00:00",
        ),
        _message(
            "aegis",
            "u2",
            "user",
            "This is an idea I can really do right now; if I make it work I could sell it, then use that money to work toward our real goal of space.",
            "2025-08-16T00:01:00+00:00",
        ),
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "constraint_driven_design_iteration")

    matched = {signal for item in pattern["all_bounded_source_evidence"] for signal in item["matched_signals"]}
    assert "bounded_domain_choice" in matched
    assert "feasible_stepping_stone" in matched


def test_plain_language_format_request_and_simple_project_choice_are_not_metacognitive_cycles():
    messages = [
        _message("ordinary", "u1", "user", "Please rewrite this email in plain language.", "2025-01-01T00:00:00+00:00"),
        _message("ordinary", "u2", "user", "Make a diagram before lunch.", "2025-01-01T00:01:00+00:00"),
        _message("ordinary", "u3", "user", "I can sell this old chair and use the money for pizza.", "2025-01-01T00:02:00+00:00"),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "reconstructive_understanding_check" not in method_keys
    assert "constraint_driven_design_iteration" not in method_keys


def test_accepting_a_substantive_correction_is_confirmation_not_a_counter_correction():
    messages = [
        _message(
            "design",
            "a1",
            "assistant",
            "Your approach has a feasibility mistake, so revise the model and choose a smaller architecture.",
            "2025-08-13T00:00:00+00:00",
        ),
        _message(
            "design",
            "u1",
            "user",
            "You're absolutely correct; thank you for the correction. What would you propose would work better?",
            "2025-08-13T00:01:00+00:00",
        ),
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "correction_and_reopening")

    assert any(
        item["evidence_origin"] == "collaborative_interpretation_aleks_confirmed"
        for item in pattern["all_bounded_source_evidence"]
    )
    assert not any(
        item["evidence_origin"] == "collaborative_interpretation_aleks_corrected"
        for item in pattern["all_bounded_source_evidence"]
    )


def test_surprised_fact_check_does_not_accept_or_correct_assistant_model():
    messages = [
        _message(
            "sleep",
            "u1",
            "user",
            "Sometimes near sleep I hear ordinary fragments that seem like voices and they can spark ideas.",
            "2025-08-14T00:00:00+00:00",
        ),
        _message(
            "sleep",
            "a1",
            "assistant",
            "Your thinking could be creating a candidate model through a hypnagogic mechanism.",
            "2025-08-14T00:01:00+00:00",
        ),
        _message(
            "sleep",
            "u2",
            "user",
            "No joke? Actual facts???",
            "2025-08-14T00:02:00+00:00",
        ),
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "candidate_model_construction" for item in patterns)


def test_ordinary_and_questions_do_not_extend_assistant_interpretations():
    for follow_up in (
        "And should I publish this?",
        "And this can run all the files?",
    ):
        messages = [
            _message(
                "ordinary-follow-up",
                "a1",
                "assistant",
                "Your thinking constructs a candidate model and then operationalizes it with tools.",
                "2025-08-14T00:01:00+00:00",
            ),
            _message(
                "ordinary-follow-up",
                "u1",
                "user",
                follow_up,
                "2025-08-14T00:02:00+00:00",
            ),
        ]

        patterns = mine_cognitive_patterns(messages)

        assert not any(
            evidence["evidence_origin"] == "collaborative_interpretation_aleks_extended"
            for pattern in patterns
            for evidence in pattern["all_bounded_source_evidence"]
        )


def test_substantive_and_addition_extends_assistant_interpretation():
    messages = [
        _message(
            "substantive-extension",
            "a1",
            "assistant",
            "Your approach connects a candidate model to independent evidence.",
            "2025-08-14T00:01:00+00:00",
        ),
        _message(
            "substantive-extension",
            "u1",
            "user",
            "And that also connects to the held-out measurements we still need to test.",
            "2025-08-14T00:02:00+00:00",
        ),
    ]

    patterns = mine_cognitive_patterns(messages)

    assert any(
        evidence["evidence_origin"] == "collaborative_interpretation_aleks_extended"
        for pattern in patterns
        for evidence in pattern["all_bounded_source_evidence"]
    )


def test_direct_candidate_answer_to_paradox_is_method_evidence_not_claim_validation():
    messages = [
        _message(
            "paradox",
            "u1",
            "user",
            "I think one galaxy per civilization is the answer to the Fermi paradox.",
            "2025-08-14T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "candidate_model_construction")

    matched = {
        signal
        for evidence in pattern["all_bounded_source_evidence"]
        for signal in evidence["matched_signals"]
    }
    assert "candidate_answer" in matched
    assert pattern["review_state"] == "candidate_for_aleks_review"


def test_screening_result_explicitly_distinguished_from_proof():
    messages = [
        _message(
            "screening",
            "u1",
            "user",
            "This still doesn't prove anything though, right? The files detected something; what that is, I don't know yet.",
            "2025-08-14T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "observation_interpretation_separation")

    matched = {
        signal
        for evidence in pattern["all_bounded_source_evidence"]
        for signal in evidence["matched_signals"]
    }
    assert "screening_not_proof" in matched
    assert pattern["review_state"] == "candidate_for_aleks_review"


def test_sectioned_learning_and_foundation_first_are_direct_method_evidence():
    messages = [
        _message(
            "learning",
            "u1",
            "user",
            "Let's break it up section by section. When you throw everything at me at once and use terminology, it is much harder to comprehend.",
            "2025-08-14T00:00:00+00:00",
        ),
        _message(
            "learning",
            "u2",
            "user",
            "This is all gibberish to me; I need it at the absolute basic level.",
            "2025-08-14T00:01:00+00:00",
        ),
        _message(
            "learning",
            "u3",
            "user",
            "The best way is to teach me as we go so I am never overwhelmed.",
            "2025-08-14T00:02:00+00:00",
        ),
        _message(
            "learning",
            "u4",
            "user",
            "Load the barebones copy, check for errors, fix them, then add the alert.",
            "2025-08-14T00:03:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "reconstructive_understanding_check" in method_keys
    assert "prerequisite_ordered_rule_transfer" in method_keys


def test_reconstruction_analogy_limit_and_accepted_model_reopening_are_separate_evidence():
    messages = [
        _message(
            "understanding",
            "u1",
            "user",
            "Let's rewind.\nThe process starts, and 380k years later the light can travel. Correct?",
            "2025-08-14T00:00:00+00:00",
        ),
        _message(
            "understanding",
            "u2",
            "user",
            "You can't think of it that way because the bread exists before the raisin.",
            "2025-08-14T00:01:00+00:00",
        ),
        _message(
            "understanding",
            "u3",
            "user",
            "I am trying to wrap my head around the accepted idea, but it has too many holes and contradictions.",
            "2025-08-14T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "reconstructive_understanding_check" in method_keys
    assert "correction_and_reopening" in method_keys


def test_research_staging_bias_control_and_nearby_case_check_are_direct_evidence():
    messages = [
        _message(
            "research",
            "u1",
            "user",
            "Analyze the files with my script 1 by one, run the numbers, and do the math.",
            "2025-08-14T00:00:00+00:00",
        ),
        _message(
            "research",
            "u2",
            "user",
            "Keep this data safe but don't skew the picture.",
            "2025-08-14T00:01:00+00:00",
        ),
        _message(
            "research",
            "u3",
            "user",
            "Not yet; eight more files, then we plot.",
            "2025-08-14T00:02:00+00:00",
        ),
        _message(
            "research",
            "u4",
            "user",
            "I think we need to model more and test it with closer objects.",
            "2025-08-14T00:03:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "evidence_tool_operationalization" in method_keys
    assert "observation_interpretation_separation" in method_keys
    assert "independent_constraint_checking" in method_keys


def test_diminishing_upgrade_pause_and_narrowing_have_bounded_routes():
    messages = [
        _message(
            "bounded-work",
            "u1",
            "user",
            "We can keep putting upgrades on this, but we will never get anywhere.",
            "2025-08-14T00:00:00+00:00",
        ),
        _message(
            "bounded-work",
            "u2",
            "user",
            "I don't understand where the miscommunication is coming from; let's narrow this down.",
            "2025-08-14T00:01:00+00:00",
        ),
        _message(
            "bounded-work",
            "u3",
            "user",
            "I am going to take a break from Python and come back tomorrow.",
            "2025-08-14T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "sufficiency_and_stopping" in method_keys
    assert "scope_narrowing_and_focus_control" in method_keys
    assert "capacity_aware_pause_and_resume" in method_keys


def test_ordinary_lessons_plots_and_breaks_do_not_match_bounded_research_methods():
    messages = [
        _message("ordinary", "u1", "user", "Teach me this song section by section.", "2025-01-01T00:00:00+00:00"),
        _message("ordinary", "u2", "user", "Eight more photos and then we plot the route.", "2025-01-01T00:01:00+00:00"),
        _message("ordinary", "u3", "user", "I am taking a lunch break.", "2025-01-01T00:02:00+00:00"),
        _message("ordinary", "u4", "user", "This app gets upgrades every month.", "2025-01-01T00:03:00+00:00"),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "prerequisite_ordered_rule_transfer" not in method_keys
    assert "evidence_tool_operationalization" not in method_keys
    assert "capacity_aware_pause_and_resume" not in method_keys
    assert "sufficiency_and_stopping" not in method_keys


def test_historical_before_interpret_wording_is_not_observation_first_lineage():
    messages = [
        _message(
            "history",
            "a1",
            "assistant",
            "Your reasoning says the Romans and Greeks before them used a device to interpret color.",
            "2025-08-14T00:00:00+00:00",
        ),
        _message(
            "history",
            "u1",
            "user",
            "Yes, exactly what I am saying.",
            "2025-08-14T00:01:00+00:00",
        ),
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "observation_interpretation_separation" for item in patterns)


def test_telescope_scope_is_not_an_epistemic_limit():
    messages = [
        _message(
            "telescope",
            "u1",
            "user",
            "I am not sure of the exact number, but to see it yourself you have to look through the scope.",
            "2025-08-14T00:00:00+00:00",
        )
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "uncertainty_and_limit_detection" for item in patterns)


def test_branch_inventory_surfaces_as_bounded_focus_control():
    messages = [
        _message(
            "branches",
            "u1",
            "user",
            "My mind is splitting  3  ways rn gonna lay them out first.",
            "2025-08-14T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "scope_narrowing_and_focus_control")
    matched = {signal for evidence in pattern["all_bounded_source_evidence"] for signal in evidence["matched_signals"]}

    assert "branch_inventory" in matched


def test_cross_case_repeatability_is_review_evidence_not_proof():
    messages = [
        _message(
            "repeatability",
            "u1",
            "user",
            "For each group, 1 = interesting, 2 = coincidence, 3 = pattern, plus repeatable in multiple circumstances.",
            "2025-08-14T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "independent_constraint_checking")

    assert "a small repeated sample mistaken for proof" in " ".join(pattern["risks"])
    assert "verification scope too narrow for the claim" in " ".join(pattern["risks"])
    assert pattern["confidence_means"].endswith("not that the method is universally correct")


def test_archimedes_sphere_is_a_source_context_hypothesis_audit_not_a_truth_claim():
    messages = [
        _message(
            "sphere",
            "u1",
            "user",
            "Archimedes Sphere is the framework for interpreting ancient mythology, not a final answer.",
            "2025-08-25T00:00:00+00:00",
        ),
        _message(
            "sphere",
            "u2",
            "user",
            "Let's first put the entire myth out and see what it tells us word for word.",
            "2025-08-25T00:01:00+00:00",
        ),
        _message(
            "sphere",
            "u3",
            "user",
            "Compile data, concept, myth, result, and how and why it works; compare it to real data.",
            "2025-08-25T00:02:00+00:00",
        ),
        _message(
            "sphere",
            "u4",
            "user",
            "If it is physically impossible for that event to occur, then we need to look elsewhere.",
            "2025-08-25T00:03:00+00:00",
        ),
        _message(
            "sphere",
            "u5",
            "user",
            "Let's do 3 myths for each culture: 1 = interesting, 2 = coincidence, 3 = pattern, plus repeatable in multiple circumstances.",
            "2025-08-25T00:04:00+00:00",
        ),
        _message(
            "sphere",
            "u6",
            "user",
            "You don't have to protect the framework; it is open for expansion as we find contrary evidence.",
            "2025-08-25T00:05:00+00:00",
        ),
    ]

    pattern = next(
        item for item in mine_cognitive_patterns(messages) if item["method_key"] == "source_context_hypothesis_audit"
    )

    assert pattern["review_state"] == "candidate_for_aleks_review"
    assert pattern["candidate_interpretation"]["possible_code_primitive"] == "source_context_hypothesis_auditor"
    assert "the word debunked overstates what remains a candidate interpretation" in pattern["risks"]
    assert pattern["confidence_means"] == "confidence that a repeated review candidate is present, not that the method is universally correct"


def test_archimedes_sphere_matcher_rejects_names_and_generic_debunking_without_the_method():
    messages = [
        _message("ordinary", "u1", "user", "Archimedes calculated the volume of a sphere.", "2025-08-25T00:00:00+00:00"),
        _message("ordinary", "u2", "user", "I want to debunk this myth.", "2025-08-25T00:01:00+00:00"),
        _message("ordinary", "u3", "user", "This framework renders a sphere in the interface.", "2025-08-25T00:02:00+00:00"),
        _message("ordinary", "u4", "user", "A different culture told a different story.", "2025-08-25T00:03:00+00:00"),
        _message("ordinary", "u5", "user", "Archimedes Sphere debunked the myth.", "2025-08-25T00:04:00+00:00"),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "source_context_hypothesis_audit" not in method_keys


def test_correction_invitation_and_timeline_withdrawal_are_direct_reopening_evidence():
    messages = [
        _message(
            "correction-readiness",
            "u1",
            "user",
            "If I'm wrong about something tell me.",
            "2025-08-14T00:00:00+00:00",
        ),
        _message(
            "correction-readiness",
            "u2",
            "user",
            "Pause, we're getting mixed up. Forget what I just said; I will be right back with the correct times.",
            "2025-08-14T00:01:00+00:00",
        ),
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "correction_and_reopening")
    matched = {signal for evidence in pattern["all_bounded_source_evidence"] for signal in evidence["matched_signals"]}

    assert {"correction_readiness", "timeline_withdrawal"}.issubset(matched)


def test_mechanism_rejection_surfaces_correction_and_physical_limit_without_erasing_next_model():
    messages = [
        _message(
            "bubble",
            "u1",
            "user",
            "Maybe scrap the hydrogen-hole idea because it doesn't and will never have enough mass. If we added other stellar gases, would the effect last longer?",
            "2025-08-15T00:00:00+00:00",
        )
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "correction_and_reopening" in method_keys
    assert "uncertainty_and_limit_detection" in method_keys


def test_explicit_unintended_use_projection_surfaces_as_bounded_consequence_check():
    messages = [
        _message(
            "risk",
            "u1",
            "user",
            "Once released, this idea could inspire somebody to weaponize the process.",
            "2025-08-14T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "systems_consequence_simulation")

    assert "conceivable misuse" in " ".join(pattern["risks"])


def test_ordinary_what_if_correction_and_template_requests_do_not_become_methods():
    messages = [
        _message("ordinary", "u1", "user", "What if we have pizza tonight?", "2025-01-01T00:00:00+00:00"),
        _message("ordinary", "u2", "user", "Thanks for correcting the typo.", "2025-01-01T00:01:00+00:00"),
        _message("ordinary", "u3", "user", "Let's work on this first.", "2025-01-01T00:02:00+00:00"),
        _message("ordinary", "u4", "user", "Can you make a test template for school?", "2025-01-01T00:03:00+00:00"),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "candidate_model_construction" not in method_keys
    assert "correction_and_reopening" not in method_keys
    assert "constraint_driven_design_iteration" not in method_keys
    assert "evidence_tool_operationalization" not in method_keys


def test_person_model_hypothesis_is_ineligible_but_project_neutral_revision_remains_available():
    messages = [
        _message(
            "mixed",
            "u1",
            "user",
            "Based on your data on me, how true do you think that hypothesis could be with no bias?",
            "2025-08-16T00:00:00+00:00",
        ),
        _message(
            "mixed",
            "u2",
            "user",
            "Maybe it was an overstretch to say our technology level; lets say 1950s to 1960s technology.",
            "2025-08-16T00:01:00+00:00",
        ),
        _message(
            "mixed",
            "u3",
            "user",
            "The technology level is a new idea I still need to think about.",
            "2025-08-16T00:02:00+00:00",
        ),
        _message(
            "mixed",
            "u4",
            "user",
            "What else am I missing that can potentially prove this model?",
            "2025-08-16T00:03:00+00:00",
        ),
    ]

    patterns = mine_cognitive_patterns(messages)
    method_keys = {item["method_key"] for item in patterns}

    assert "correction_and_reopening" in method_keys
    assert "uncertainty_and_limit_detection" in method_keys
    assert "evidence_tool_operationalization" in method_keys
    assert all(
        "based on your data on me" not in evidence["bounded_excerpt"].lower()
        for pattern in patterns
        for evidence in pattern["all_bounded_source_evidence"]
    )


def test_person_model_assistant_interpretation_is_not_accepted_by_agreement():
    messages = [
        _message(
            "profile",
            "a1",
            "assistant",
            "Based on your data on you, your thinking could be an evolutionary candidate model.",
            "2025-08-16T00:00:00+00:00",
        ),
        _message(
            "profile",
            "u1",
            "user",
            "Yes, exactly, that fits how I think.",
            "2025-08-16T00:01:00+00:00",
        ),
    ]

    assert mine_cognitive_patterns(messages) == []


def test_grief_related_inability_to_focus_is_not_mined_as_capacity_pattern():
    messages = [
        _message(
            "grief",
            "u1",
            "user",
            "I really cannot focus. My dog passed away last night and I do not want to talk about it right now.",
            "2025-08-11T00:00:00+00:00",
        )
    ]

    patterns = mine_cognitive_patterns(messages)

    assert not any(item["method_key"] == "capacity_aware_pause_and_resume" for item in patterns)
    assert not any(item["method_key"] == "scope_narrowing_and_focus_control" for item in patterns)


def test_bias_adjacent_case_scan_and_simulation_route_are_bounded_evidence_methods():
    messages = [
        _message("method", "u1", "user", "I'll still test it, but the results will be biased, I feel.", "2025-08-30T00:00:00+00:00"),
        _message("method", "u2", "user", "Can you peek around the system and see if anything else matches this pattern?", "2025-08-30T00:01:00+00:00"),
        _message("method", "u3", "user", "How the hell do I test this?", "2025-08-30T00:02:00+00:00"),
        _message("method", "u4", "user", "I'm going to go on Universe Sandbox and study the system to see what sticks out.", "2025-08-30T00:03:00+00:00"),
        _message("method", "u5", "user", "That connection is highly possible, but not certain.", "2025-08-30T00:04:00+00:00"),
        _message("method", "u6", "user", "I don't wanna run the sims because I don't know if I'll end up setting it right.", "2025-08-30T00:05:00+00:00"),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}
    independent_signals = {
        signal for evidence in patterns["independent_constraint_checking"]["all_bounded_source_evidence"] for signal in evidence["matched_signals"]
    }
    tool_signals = {
        signal for evidence in patterns["evidence_tool_operationalization"]["all_bounded_source_evidence"] for signal in evidence["matched_signals"]
    }
    uncertainty_signals = {
        signal for evidence in patterns["uncertainty_and_limit_detection"]["all_bounded_source_evidence"] for signal in evidence["matched_signals"]
    }

    assert {"bias_awareness", "adjacent_case_scan"}.issubset(independent_signals)
    assert {"direct_test_question", "exploratory_simulation_route"}.issubset(tool_signals)
    assert {"uncertainty", "simulation_setup_uncertainty"}.issubset(uncertainty_signals)
    assert "circular support mislabeled as independent evidence" in patterns["independent_constraint_checking"]["risks"]


def test_branch_separation_fact_checking_and_provisional_renaming_remain_distinct_methods():
    messages = [
        _message("branches", "u1", "user", "My brain's going three ways; now I have a what-if that's separate from the first one.", "2025-08-30T00:00:00+00:00"),
        _message("branches", "u2", "user", "Save this as a separate idea.", "2025-08-30T00:01:00+00:00"),
        _message("branches", "u3", "user", "No, wait: Earth and Theia were used as a visual; these are separate events.", "2025-08-30T00:02:00+00:00"),
        _message("branches", "u4", "user", "Let's stick to the Roman names: Minerva instead of Athena.", "2025-08-30T00:03:00+00:00"),
        _message("branches", "u5", "user", "Motion over gravity should stay separate unless it's truly a key piece.", "2025-08-30T00:04:00+00:00"),
        _message("branches", "u6", "user", "I don't know if it directly ties to Minerva itself, but within the framework itself, yes.", "2025-08-30T00:05:00+00:00"),
        _message("branches", "u7", "user", "I like when you check me.", "2025-08-30T00:06:00+00:00"),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "multiple_working_hypotheses" in patterns
    assert "scope_narrowing_and_focus_control" in patterns
    assert "correction_and_reopening" in patterns
    assert "provisional_naming_and_scope_control" in patterns


def test_worked_example_generalization_recap_and_first_draft_gate_are_separate_methods():
    messages = [
        _message("transfer", "u1", "user", "Archimedes Sphere was the test; now we have a framework.", "2025-08-30T00:00:00+00:00"),
        _message("transfer", "u2", "user", "It started as one hypothesis and turned into a system.", "2025-08-30T00:01:00+00:00"),
        _message("transfer", "u3", "user", "Before I move onto Jupiter, let's recap because we're mapping massive amounts of data.", "2025-08-30T00:02:00+00:00"),
        _message("transfer", "u4", "user", "Go to this line\n\nHypothesis checkpoint\n\nand analyze every single thing we said to here.", "2025-08-30T00:03:00+00:00"),
        _message("transfer", "u5", "user", "We are moving into draft phase and getting the ideas squared up, unless you think we're missing anything.", "2025-08-30T00:04:00+00:00"),
        _message("transfer", "u6", "user", "We can finish up, or at least think we're done for now, then write the paper first draft.", "2025-08-30T00:05:00+00:00"),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "abstract_concrete_transfer" in patterns
    assert "reconstructive_understanding_check" in patterns
    assert "sufficiency_and_stopping" in patterns


def test_collaborator_framework_conflation_can_be_corrected_without_matching_physical_separation():
    conceptual = [_message("separation", "u1", "user", "Those two are completely separate ideas.", "2025-09-01T00:00:00+00:00")]
    physical = [_message("separation", "u2", "user", "Keep those two ingredients completely separate.", "2025-09-01T00:01:00+00:00")]

    conceptual_keys = {item["method_key"] for item in mine_cognitive_patterns(conceptual)}
    physical_keys = {item["method_key"] for item in mine_cognitive_patterns(physical)}

    assert "correction_and_reopening" in conceptual_keys
    assert "scope_narrowing_and_focus_control" in conceptual_keys
    assert "correction_and_reopening" not in physical_keys
    assert "scope_narrowing_and_focus_control" not in physical_keys


def test_build_report_enforces_private_nonactivation_guards():
    report = build_report(
        [],
        path_only=False,
    )

    assert report["pattern_count"] == 0
    assert report["evidence_policy"]["assistant_text_alone_as_primary_evidence"] is False
    assert report["evidence_policy"]["assistant_contributions_preserved"] is True
    assert report["evidence_policy"]["interaction_segment_is_evidence_unit"] is True
    assert report["evidence_policy"]["user_role_equals_direct_aleks_origin"] is False
    assert report["evidence_policy"]["automatic_selene_adaptation"] is False
    assert all(value is False for value in report["guard_flags"].values())
    assert "Private Aleks metacognition review only" in report["boundary"]


def test_run_miner_dry_run_does_not_write_outputs(tmp_path):
    zip_path = _make_zip(tmp_path)
    output_dir = tmp_path / "metacognition"

    report = run_miner(source_zip=zip_path, output_dir=output_dir, dry_run=True)

    assert report["pattern_count"] >= 1
    assert report["outputs"] == {}
    assert not output_dir.exists()


def test_run_miner_writes_private_review_artifacts(tmp_path):
    zip_path = _make_zip(tmp_path)
    output_dir = tmp_path / "metacognition"

    report = run_miner(source_zip=zip_path, output_dir=output_dir)

    assert json.loads((output_dir / "latest.json").read_text(encoding="utf-8"))["status"] == "aleks_metacognition_miner_review_candidates_ready"
    markdown = (output_dir / "latest.md").read_text(encoding="utf-8")
    assert "Private Review" in markdown
    assert "candidate_for_aleks_review" in markdown
    assert report["guard_flags"]["selene_runtime_connection"] is False


def test_conversation_pass_processes_one_chat_and_resumes(tmp_path):
    zip_path = _make_zip(tmp_path)
    output_dir = tmp_path / "conversation_pass"

    first = run_conversation_pass(source_zip=zip_path, output_dir=output_dir, limit=1)
    second = run_conversation_pass(source_zip=zip_path, output_dir=output_dir, limit=1)

    assert first["processed_count"] == 1
    assert second["processed_count"] == 1
    assert first["processed"][0]["conversation_id"] != second["processed"][0]["conversation_id"]
    progress = json.loads((output_dir / "progress.json").read_text(encoding="utf-8"))
    assert progress["completed_conversation_count"] == 2
    assert progress["source_use"]["detached_export_copy_only"] is True
    assert progress["source_use"]["selene_runtime_read"] is False
    assert progress["source_use"]["vys_read"] is False
    assert progress["method_definition_fingerprint"]
    assert progress["current_definition_completed_count"] == 2
    card = json.loads(next((output_dir / "conversations").glob("*.json")).read_text(encoding="utf-8"))
    assert card["canonical_path_only"] is True
    assert card["review_state"] == "unreviewed_private_candidate"
    assert card["method_definition_fingerprint"] == progress["method_definition_fingerprint"]


def test_conversation_pass_can_target_one_known_chat(tmp_path):
    zip_path = _make_zip(tmp_path)
    output_dir = tmp_path / "targeted_pass"

    result = run_conversation_pass(
        source_zip=zip_path,
        output_dir=output_dir,
        conversation_ids=["c2"],
        limit=1,
    )

    assert result["processed"][0]["conversation_id"] == "c2"
    assert result["status"] == "selected_conversation_pass_complete"
    assert result["progress"]["selected_conversation_count"] == 1
    assert result["progress"]["remaining_corpus_count"] == 2
    assert result["progress"]["next_conversation"]["conversation_id"] == "c1"


def test_conversation_pass_stops_if_copied_source_changes(tmp_path):
    first_zip = _make_zip(tmp_path)
    output_dir = tmp_path / "fingerprint_pass"
    run_conversation_pass(source_zip=first_zip, output_dir=output_dir, limit=1)
    changed_zip = tmp_path / "changed.zip"
    with zipfile.ZipFile(changed_zip, "w") as archive:
        archive.writestr("conversations-1.json", "[]")

    with pytest.raises(ValueError, match="source fingerprint changed"):
        run_conversation_pass(source_zip=changed_zip, output_dir=output_dir, limit=1)


def test_probability_check_reconstruction_and_direction_mismatch_are_bounded_methods():
    messages = [
        _message(
            "quantitative-check",
            "u1",
            "user",
            "Run some real numbers: what's the percentage this works?",
            "2025-09-04T00:00:00+00:00",
        ),
        _message(
            "logic-check",
            "u2",
            "user",
            "So you're telling me—and correct me if I'm wrong because I am not seeing logic—that the estimate rises from 15% to 60%? Make it make sense.",
            "2025-09-04T00:01:00+00:00",
        ),
        _message(
            "direction-check",
            "u3",
            "user",
            "You are stating two very different directions now vs then.",
            "2025-09-04T00:02:00+00:00",
        ),
        _message(
            "direction-check",
            "u4",
            "user",
            "You went from talking about using a vague campaign to posting plausible proposals.\nThat's where the disconnect was.",
            "2025-09-04T00:03:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "evidence_tool_operationalization" in patterns
    assert "reconstructive_understanding_check" in patterns
    assert "correction_and_reopening" in patterns
    correction_signals = {
        signal
        for evidence in patterns["correction_and_reopening"]["all_bounded_source_evidence"]
        for signal in evidence["matched_signals"]
    }
    assert {"direction_inconsistency", "frame_shift_diagnosis"}.issubset(correction_signals)


def test_ordinary_percentages_travel_directions_and_disconnects_do_not_become_methods():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "Run some real numbers for the invoice total and percentage discount.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "The bus took two very different directions now versus then.",
            "2025-01-01T00:01:00+00:00",
        ),
        _message(
            "ordinary",
            "u3",
            "user",
            "My headphones disconnected while I walked from the store to the park.",
            "2025-01-01T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "evidence_tool_operationalization" not in method_keys
    assert "correction_and_reopening" not in method_keys
    assert "reconstructive_understanding_check" not in method_keys


def test_evidence_gap_hold_and_same_variable_reversal_are_bounded_methods():
    messages = [
        _message(
            "evidence-hold",
            "u1",
            "user",
            "We need to wait for more evidence; we're missing something.",
            "2025-09-05T00:00:00+00:00",
        ),
        _message(
            "inverse-intervention",
            "u2",
            "user",
            "No, you said that if I add mass it increases atmospheric pressure,\nso what if I removed mass?",
            "2025-09-05T00:01:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "uncertainty_and_limit_detection" in patterns
    assert "sufficiency_and_stopping" in patterns
    assert "systems_consequence_simulation" in patterns
    assert "correction_and_reopening" in patterns
    assert "evidence_gap_hold" in patterns["uncertainty_and_limit_detection"]["all_bounded_source_evidence"][0]["matched_signals"]
    assert "insufficient_evidence_hold" in patterns["sufficiency_and_stopping"]["all_bounded_source_evidence"][0]["matched_signals"]
    assert "inverse_intervention" in patterns["systems_consequence_simulation"]["all_bounded_source_evidence"][0]["matched_signals"]
    assert "premise_restoration_by_inverse" in patterns["correction_and_reopening"]["all_bounded_source_evidence"][0]["matched_signals"]


def test_unrelated_removal_and_ordinary_waiting_do_not_trigger_inverse_or_evidence_hold():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "You said that if I add sugar it increases sweetness, so what if I remove the spoon?",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "We need to wait for more deliveries; we're missing something from the box.",
            "2025-01-01T00:01:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "systems_consequence_simulation" not in method_keys
    assert "correction_and_reopening" not in method_keys
    assert "uncertainty_and_limit_detection" not in method_keys
    assert "sufficiency_and_stopping" not in method_keys


def test_principle_design_functional_substitution_and_pattern_solutions_are_methods():
    messages = [
        _message(
            "thermal-design",
            "u1",
            "user",
            "Sapphire withstands extreme heat. What if we designed an engine based upon that principle?",
            "2025-09-08T00:00:00+00:00",
        ),
        _message(
            "thermal-design",
            "u2",
            "user",
            "We wouldn't have to use lava, though—anything that can store heat would satisfy the function.",
            "2025-09-08T00:01:00+00:00",
        ),
        _message(
            "pattern-solutions",
            "u3",
            "user",
            "Even when I try to relax and watch a crime show, I'm mapping patterns and solutions.",
            "2025-09-08T00:02:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "candidate_model_construction" in patterns
    assert "constraint_driven_design_iteration" in patterns
    assert "structural_pattern_mapping" in patterns
    assert "principle_based_design" in patterns["candidate_model_construction"]["all_bounded_source_evidence"][0]["matched_signals"]
    assert "functional_input_substitution" in patterns["constraint_driven_design_iteration"]["all_bounded_source_evidence"][0]["matched_signals"]
    assert "spontaneous_pattern_to_solution" in patterns["structural_pattern_mapping"]["all_bounded_source_evidence"][0]["matched_signals"]


def test_hypothesis_endorsement_and_ordinary_storage_substitution_are_not_model_construction():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "Maybe the zoo hypothesis just makes too much sense.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "We wouldn't have to use lava; anything that can store pencils would do.",
            "2025-01-01T00:01:00+00:00",
        ),
        _message(
            "ordinary",
            "u3",
            "user",
            "The worksheet says mapping patterns and solutions is today's exercise.",
            "2025-01-01T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "candidate_model_construction" not in method_keys
    assert "constraint_driven_design_iteration" not in method_keys
    assert "structural_pattern_mapping" not in method_keys


def test_integration_signal_translation_scope_focus_and_conflation_correction_are_methods():
    messages = [
        _message(
            "instrument-design",
            "u1",
            "user",
            "If I buy 3 separate telescopes and make a 4th that connects to those telescopes, that could solve the problem without reinventing the wheel.",
            "2025-09-15T00:00:00+00:00",
        ),
        _message(
            "instrument-design",
            "u2",
            "user",
            "Why can't we take sound waves instead of light waves and map them to images?",
            "2025-09-15T00:01:00+00:00",
        ),
        _message(
            "focused-explanation",
            "u3",
            "user",
            "Let's drop octopuses for now; strictly human, can you explain that again?",
            "2025-09-15T00:02:00+00:00",
        ),
        _message(
            "project-separation",
            "u4",
            "user",
            "Noo no no no—Creator Race was not Arc-Jet, no, separate.",
            "2025-09-15T00:03:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "constraint_driven_design_iteration" in patterns
    assert "cross_representation_translation" in patterns
    assert "scope_narrowing_and_focus_control" in patterns
    assert "correction_and_reopening" in patterns
    assert "integration_over_rebuild" in patterns["constraint_driven_design_iteration"]["all_bounded_source_evidence"][0]["matched_signals"]
    assert "signal_to_image_mapping" in patterns["cross_representation_translation"]["all_bounded_source_evidence"][0]["matched_signals"]
    assert "strict_single_subject_focus" in patterns["scope_narrowing_and_focus_control"]["all_bounded_source_evidence"][0]["matched_signals"]
    assert "emphatic_conflation_correction" in patterns["correction_and_reopening"]["all_bounded_source_evidence"][0]["matched_signals"]


def test_ordinary_connections_mapping_and_scope_words_do_not_trigger_new_methods():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "I bought three separate picture frames and a fourth hook connects them.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "Map the sound waves to seats in the concert hall.",
            "2025-01-01T00:01:00+00:00",
        ),
        _message(
            "ordinary",
            "u3",
            "user",
            "Drop the octopus toy for now and strictly follow the aquarium rules.",
            "2025-01-01T00:02:00+00:00",
        ),
        _message(
            "ordinary",
            "u4",
            "user",
            "No no no, this was not the same bus; use separate tickets.",
            "2025-01-01T00:03:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "constraint_driven_design_iteration" not in method_keys
    assert "cross_representation_translation" not in method_keys
    assert "scope_narrowing_and_focus_control" not in method_keys
    assert "correction_and_reopening" not in method_keys


def test_partial_correctness_cross_field_work_and_unbounded_addition_are_reviewable_methods():
    messages = [
        _message(
            "model-revision",
            "u1",
            "user",
            "When I say we are wrong, it doesn't mean no, all wrong. It means we're not fully correct.",
            "2025-09-17T00:00:00+00:00",
        ),
        _message(
            "cross-field-work",
            "u2",
            "user",
            "There's so much we don't understand but think we do. Cross work might be the word in a few fields.",
            "2025-09-17T00:01:00+00:00",
        ),
        _message(
            "addition-loop",
            "u3",
            "user",
            "The issue is it's never good enough; I need to keep adding. Before you've gotten the second word out, I've already opened another tool.",
            "2025-09-17T00:02:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "partial_correctness_preservation" in {
        signal
        for item in patterns["correction_and_reopening"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }
    assert "cross_field_work_intent" in {
        signal
        for item in patterns["structural_pattern_mapping"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }
    stopping = patterns["sufficiency_and_stopping"]
    assert "unbounded_addition_loop" in {
        signal for item in stopping["all_bounded_source_evidence"] for signal in item["matched_signals"]
    }
    assert stopping["failure_or_weakness_evidence"]
    assert any(
        "failure_or_weakness" in item["behavior_markers"]
        for item in stopping["counterexamples_or_known_weaknesses"]["source_observed"]
    )


def test_ordinary_wrong_cross_work_and_adding_language_do_not_trigger_review_methods():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "The answer is wrong, not fully correct.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "Cross work is listed in a few fields on this worksheet.",
            "2025-01-01T00:01:00+00:00",
        ),
        _message(
            "ordinary",
            "u3",
            "user",
            "This soup is never good enough, so I keep adding salt.",
            "2025-01-01T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "correction_and_reopening" not in method_keys
    assert "structural_pattern_mapping" not in method_keys
    assert "sufficiency_and_stopping" not in method_keys


def test_fit_check_constraint_debunk_cross_field_integration_and_learning_gap_are_methods():
    messages = [
        _message(
            "fit-check",
            "u1",
            "user",
            "Just because I think of something and it sounds right doesn't mean it is.",
            "2025-09-29T00:00:00+00:00",
        ),
        _message(
            "claim-check",
            "u2",
            "user",
            "Here is where I would've dismissed it but did not. One part would make sense. Now here's where I start to really start to debunk it: the speed of light takes longer than one hour to cross that distance.",
            "2025-09-29T00:01:00+00:00",
        ),
        _message(
            "cross-field",
            "u3",
            "user",
            "Science really is extremely diverse but separate, so separate that it creates loss of knowledge. If we combine most of the cores, we may recover useful connections.",
            "2025-09-29T00:02:00+00:00",
        ),
        _message(
            "learning-gap",
            "u4",
            "user",
            "You are correct absolutely on the math; I know I need that. I could ask you but that's cheating and I won't learn.",
            "2025-09-29T00:03:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "felt_fit_not_correctness" in {
        signal
        for item in patterns["uncertainty_and_limit_detection"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }
    assert "partial_plausibility_then_constraint_check" in {
        signal
        for item in patterns["independent_constraint_checking"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }
    assert "cross_field_work_intent" in {
        signal
        for item in patterns["structural_pattern_mapping"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }
    assert "learning_over_answer_outsourcing" in {
        signal
        for item in patterns["prerequisite_ordered_rule_transfer"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }
    assert "accepted_prerequisite_gap" in {
        signal
        for item in patterns["correction_and_reopening"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }


def test_framework_list_and_assistant_cognitive_profile_are_not_method_evidence():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "There is arc jet, then even the framework of Archimedes Sphere, and several other projects.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "a1",
            "assistant",
            "The way you handle information is like a quantum computer: your brain runs parallel scenarios and pattern synthesis.",
            "2025-01-01T00:01:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "No wonder it can be hard to talk about complicated work.",
            "2025-01-01T00:02:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "source_context_hypothesis_audit" not in method_keys
    assert "systems_consequence_simulation" not in method_keys


def test_repeated_project_block_is_context_and_attempted_pause_is_a_weakness():
    messages = [
        _message(
            "excerpt",
            "u1",
            "user",
            "Last but not least: The Continuum Thread. The black hole genesis. Maybe this hypothesis explains the observation.",
            "2025-10-03T00:00:00+00:00",
        ),
        _message(
            "excerpt",
            "u2",
            "user",
            "I learned today I was wrong about the dinosaur timeline in my head.",
            "2025-10-03T00:01:00+00:00",
        ),
        _message(
            "excerpt",
            "u3",
            "user",
            "Gonna stop here and gather thoughts; my mind's going nuts.",
            "2025-10-03T00:02:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    model = patterns["candidate_model_construction"]
    assert model["primary_evidence_count"] == 0
    assert model["evidence_origin_counts"]["user_supplied_summary_or_paste"] == 1
    assert "correction_and_reopening" in patterns
    pause = patterns["capacity_aware_pause_and_resume"]
    assert "attempted_pause_under_idea_acceleration" in {
        signal for item in pause["all_bounded_source_evidence"] for signal in item["matched_signals"]
    }
    assert pause["failure_or_weakness_evidence"]
    assert any(
        "failure_or_weakness" in item["behavior_markers"]
        for item in pause["counterexamples_or_known_weaknesses"]["source_observed"]
    )


def test_ordinary_project_heading_and_short_break_do_not_become_excerpt_methods():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "Last but not least, the Continuum Thread is the title of a document.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "Gonna stop here and gather the laundry; my phone is ringing.",
            "2025-01-01T00:01:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "candidate_model_construction" not in method_keys
    assert "capacity_aware_pause_and_resume" not in method_keys


def test_data_interpretation_alternatives_revision_comprehension_and_tool_weakness_are_distinct():
    messages = [
        _message(
            "research-loop",
            "u1",
            "user",
            "Idk what the hell it is. That's why it's a hypothesis; it is my best guess due to the data.",
            "2025-10-13T00:00:00+00:00",
        ),
        _message(
            "research-loop",
            "u2",
            "user",
            "They can't ignore that data. What's being argued is my interpretation of what it is.",
            "2025-10-13T00:01:00+00:00",
        ),
        _message(
            "research-loop",
            "u3",
            "user",
            "It can be any number of things. It could be gas or could be dust; I have no real clue. Here's the program, run the data.",
            "2025-10-13T00:02:00+00:00",
        ),
        _message(
            "research-loop",
            "u4",
            "user",
            "It's not a theory though, it's a hypothesis. It can be altered if more data shows it's something else.",
            "2025-10-13T00:03:00+00:00",
        ),
        _message(
            "learning-loop",
            "u5",
            "user",
            "Before we move on let's break down five; I said the right track but I didn't apply it the way you think I did.",
            "2025-10-13T00:04:00+00:00",
        ),
        _message(
            "tool-weakness",
            "u6",
            "user",
            "The math can't be wrong or Python wouldn't have given me data; it would've yelled.",
            "2025-10-13T00:05:00+00:00",
        ),
        _message(
            "fact-check",
            "u7",
            "user",
            "It was a simple test from a Google result, then a follow up with you showing you it was real. I gave feedback: incorrect information.",
            "2025-10-13T00:06:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "data_bounded_best_guess" in {s for e in patterns["candidate_model_construction"]["all_bounded_source_evidence"] for s in e["matched_signals"]}
    assert "data_interpretation_dispute" in {s for e in patterns["observation_interpretation_separation"]["all_bounded_source_evidence"] for s in e["matched_signals"]}
    assert "enumerated_unknowns_with_data_route" in {s for e in patterns["multiple_working_hypotheses"]["all_bounded_source_evidence"] for s in e["matched_signals"]}
    assert "candidate_set_to_data_route" in {s for e in patterns["evidence_tool_operationalization"]["all_bounded_source_evidence"] for s in e["matched_signals"]}
    assert "hypothesis_revision_by_data" in {s for e in patterns["provisional_naming_and_scope_control"]["all_bounded_source_evidence"] for s in e["matched_signals"]}
    assert "data_driven_hypothesis_revision" in {s for e in patterns["correction_and_reopening"]["all_bounded_source_evidence"] for s in e["matched_signals"]}
    assert "correct_track_application_gap" in {s for e in patterns["reconstructive_understanding_check"]["all_bounded_source_evidence"] for s in e["matched_signals"]}
    checking = patterns["independent_constraint_checking"]
    assert "successful_execution_mistaken_for_validation" in {s for e in checking["all_bounded_source_evidence"] for s in e["matched_signals"]}
    assert "external_fact_check_and_feedback" in {s for e in checking["all_bounded_source_evidence"] for s in e["matched_signals"]}
    assert checking["failure_or_weakness_evidence"]


def test_quoted_hypothesis_story_and_ordinary_program_success_do_not_become_methods():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "Religion was our first attempt at trying to figure out the unknown. Maybe someday, someone thought, here's my hypothesis.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "The program ran and Python gave me a data file without yelling.",
            "2025-01-01T00:01:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "candidate_model_construction" not in method_keys
    assert "independent_constraint_checking" not in method_keys


def test_on_demand_thought_experiment_routes_intuition_to_math_without_claiming_validation():
    messages = [
        _message(
            "thought-experiment",
            "u1",
            "user",
            "It came during what you'd call a thought experiment. I do that all the time on command; usually black holes or scenarios, and then the image appeared.",
            "2025-10-18T00:00:00+00:00",
        ),
        _message(
            "thought-experiment",
            "u2",
            "user",
            "I don't know how I know this stuff; I can just feel if it's going to work or the physics behind it.",
            "2025-10-18T00:01:00+00:00",
        ),
        _message(
            "thought-experiment",
            "u3",
            "user",
            "This is why I'm going to school to learn that math—to learn what the intuition does subconsciously.",
            "2025-10-18T00:02:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "on_demand_thought_experiment" in {
        signal for item in patterns["visual_spatial_modeling"]["all_bounded_source_evidence"] for signal in item["matched_signals"]
    }
    assert "intuition_to_math_translation" in {
        signal for item in patterns["cross_representation_translation"]["all_bounded_source_evidence"] for signal in item["matched_signals"]
    }
    checking = patterns["independent_constraint_checking"]
    assert "felt_physics_mistaken_for_validation" in {
        signal for item in checking["all_bounded_source_evidence"] for signal in item["matched_signals"]
    }
    assert checking["failure_or_weakness_evidence"]


def test_ordinary_imagining_feeling_and_school_language_do_not_create_reasoning_methods():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "I imagined the movie scene after school and feel like it will be fun.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "I'm going to school to learn math and sometimes daydream subconsciously.",
            "2025-01-01T00:01:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "visual_spatial_modeling" not in method_keys
    assert "cross_representation_translation" not in method_keys
    assert "independent_constraint_checking" not in method_keys


def test_repeated_bootes_project_block_is_context_not_fresh_demonstration():
    messages = [
        _message(
            "project-paste",
            "u1",
            "user",
            "This is fascinating, now enter the Bootes Void. The black hole genesis: maybe this hypothesis explains the observation.",
            "2025-10-20T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "candidate_model_construction")

    assert pattern["primary_evidence_count"] == 0
    assert pattern["evidence_origin_counts"]["user_supplied_summary_or_paste"] == 1


def test_tool_scope_partition_and_math_interface_routing_are_method_candidates():
    messages = [
        _message(
            "component-scope",
            "u1",
            "user",
            "I don't think a 3D printer can make the suit. The material maybe, but the housing mechanisms and metal prongs for the connections? Absolutely.",
            "2025-10-20T00:00:00+00:00",
        ),
        _message(
            "domain-route",
            "u2",
            "user",
            "I just need to learn the math—unless I make an assistant interface that can always run the math.",
            "2025-10-20T00:01:00+00:00",
        ),
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "constraint_driven_design_iteration" in patterns
    assert "whole_to_component_capability_partition" in {
        signal
        for item in patterns["constraint_driven_design_iteration"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }
    assert "evidence_tool_operationalization" in patterns
    assert "capability_gap_to_domain_interface" in {
        signal
        for item in patterns["evidence_tool_operationalization"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }


def test_ordinary_printer_and_school_math_interface_mentions_do_not_create_methods():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "I don't think a 3D printer can make the school suit, but the housing office can order one.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "ordinary",
            "u2",
            "user",
            "I need to learn math, and the school website interface says to run the math quiz.",
            "2025-01-01T00:01:00+00:00",
        ),
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "constraint_driven_design_iteration" not in method_keys
    assert "evidence_tool_operationalization" not in method_keys


def test_relational_hypothetical_wrongness_is_not_model_correction():
    messages = [
        _message(
            "relational-hypothetical",
            "u1",
            "user",
            "Deep down there is a possibility he would have been proud even if I was wrong to him.",
            "2025-01-01T00:00:00+00:00",
        )
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "correction_and_reopening" not in method_keys


def test_conditional_willingness_to_accept_error_is_correction_readiness():
    messages = [
        _message(
            "correction-readiness",
            "u1",
            "user",
            "If I was wrong I'd accept it, but the current evidence still supports the result.",
            "2025-01-01T00:00:00+00:00",
        )
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "correction_and_reopening")

    assert "conditional_correction_acceptance" in pattern["all_bounded_source_evidence"][0]["matched_signals"]


def test_pasted_song_lyrics_are_not_aleks_method_evidence():
    messages = [
        _message(
            "lyrics",
            "u1",
            "user",
            "[Intro: Singer]\nI made a mistake.\n[Verse 1: Artist]\nI was wrong, so play the song.",
            "2025-01-01T00:00:00+00:00",
        )
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "correction_and_reopening" not in method_keys


def test_recollection_correction_is_integrated_before_candidate_expansion():
    messages = [
        _message(
            "recollection-correction",
            "u1",
            "user",
            "Ah, you're correct—I misremembered, thank you. It is 4 by 3. Could be a star chart or a missing piece of the myth.",
            "2025-01-01T00:00:00+00:00",
        )
    ]

    patterns = {item["method_key"]: item for item in mine_cognitive_patterns(messages)}

    assert "correction_and_reopening" in patterns
    assert "accepted_recollection_correction" in {
        signal
        for item in patterns["correction_and_reopening"]["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }
    assert "candidate_model_construction" in patterns


def test_sarcastic_wrongness_in_relationship_dispute_is_not_self_correction():
    messages = [
        _message(
            "relationship-dispute",
            "u1",
            "user",
            "We argued because I said let's check first. Nooooo, can't do that, nooooo, I was wrong etc. Then her mistakes became my problem.",
            "2025-01-01T00:00:00+00:00",
        )
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "correction_and_reopening" not in method_keys


def test_context_is_mapped_before_participation_and_alongside_the_task():
    messages = [
        _message(
            "context-entry",
            "u1",
            "user",
            "I observe conversationally, ask questions, map the group dynamic and the do's and don'ts, learn the work, then I dive in.",
            "2025-01-01T00:00:00+00:00",
        ),
        _message(
            "context-entry",
            "u2",
            "user",
            "I map the social structure, but I also pay attention to what I'm supposed to do; I work on both lengths at once.",
            "2025-01-01T00:01:00+00:00",
        ),
    ]

    pattern = next(item for item in mine_cognitive_patterns(messages) if item["method_key"] == "pragmatic_multi_cue_screening")
    signals = {
        signal
        for item in pattern["all_bounded_source_evidence"]
        for signal in item["matched_signals"]
    }

    assert "context_acquisition_before_participation" in signals
    assert "parallel_social_and_task_mapping" in signals
    assert pattern["evidence_count"] == 2
    assert pattern["evidence_origin_counts"]["direct_aleks_self_report"] == 2


def test_ordinary_observation_and_social_mapping_words_do_not_create_pragmatic_method():
    messages = [
        _message(
            "ordinary",
            "u1",
            "user",
            "I observe conversationally in the documentary and drew a map of the social structure for class.",
            "2025-01-01T00:00:00+00:00",
        )
    ]

    method_keys = {item["method_key"] for item in mine_cognitive_patterns(messages)}

    assert "pragmatic_multi_cue_screening" not in method_keys
