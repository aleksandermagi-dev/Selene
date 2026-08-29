from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Any

from .curriculum_authorization import curriculum_authorization_status
from .language_teaching_shelf import language_teaching_status


ORGAN_MATURITY_LEDGER_VERSION = "v3_phase_4_affect_relationship_agency_maturity"
ORGAN_MATURITY_BOUNDARY = (
    "read_only_current_capability_maturity_projection_no_identity_memory_"
    "governance_teaching_dream_action_or_authority_change"
)

MATURITY_STATES = frozenset(
    {
        "blueprint",
        "review_preview",
        "implemented",
        "connected",
        "configured",
        "integration_verified",
        "mature_current_scope",
        "substrate_ready",
        "degraded",
    }
)

CONNECTION_STATES = frozenset(
    {
        "ordinary_chat",
        "resident_workspace",
        "bounded_route",
        "cocoon_review",
        "preview_only",
        "not_connected",
    }
)

GUARDS: dict[str, Any] = {
    "writes_state": False,
    "memory_write_active": False,
    "runtime_memory_recall_performed": False,
    "teaching_operation_performed": False,
    "dream_decision_performed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "activation_change": "none",
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}


ORGAN_SPECS: tuple[dict[str, Any], ...] = (
    {
        "key": "core_mind",
        "name": "Core / Mind and resident authority",
        "responsibility": "Whole-system routing, governing-law checks, continuity, and final authority.",
        "non_responsibility": "Does not replace specialized answer, Memory, language, perception, or action organs.",
        "source_modules": ["core_mind.py", "core_mind_runtime.py", "resident_authority.py"],
        "routes": ["core_mind.runtime_readiness", "selene_chat.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "stable_bounded_scope",
        "maturation_phase": 1,
        "metric_keys": ["chat_sessions", "transfer_completion_records"],
        "known_gaps": ["Downstream choices remain limited when canonical current-turn inputs are incomplete."],
    },
    {
        "key": "intelligence_os",
        "name": "intelligenceOS",
        "responsibility": "Open-ended reasoning, model comparison, consequence tracing, and revisable best-current answers.",
        "non_responsibility": "Does not supply a universal factual or procedural knowledge substrate.",
        "source_modules": ["intelligence_os.py", "exploratory_reasoning.py", "bounded_hypothesis.py"],
        "routes": ["intelligence_os.status", "exploratory_reasoning.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "stable_bounded_scope",
        "maturation_phase": 5,
        "metric_keys": ["intelligence_os_runs"],
        "known_gaps": ["General solver breadth depends on connected domain owners and taught knowledge."],
    },
    {
        "key": "answer_engine",
        "name": "Answer Engine and operation owners",
        "responsibility": "Typed answer ownership and operation results for supported answer functions.",
        "non_responsibility": "Generic prose cannot substitute for performing an answer operation.",
        "source_modules": ["answer_engine.py", "answer_operations.py", "answer_ownership.py"],
        "routes": ["answer_engine.status", "answer_operations.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "connected",
        "target_state": "mature_current_scope",
        "health_state": "integration_gap_observed",
        "maturation_phase": 1,
        "metric_keys": [],
        "known_gaps": ["Some owners do not receive prompt-contained facts and can report supplied premises as missing."],
    },
    {
        "key": "problem_resolution",
        "name": "Problem Resolution",
        "responsibility": "Seven-point reconstruction, satisfiability, epistemic state, failure classification, and informed retry.",
        "non_responsibility": "Does not invent missing context or become a monolithic solver.",
        "source_modules": ["problem_resolution.py", "owner_specific_retry.py"],
        "routes": ["problem_resolution.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "implemented",
        "target_state": "mature_current_scope",
        "health_state": "focused_evidence_only",
        "maturation_phase": 5,
        "metric_keys": [],
        "known_gaps": ["Ordinary-use evidence is limited and upstream context quality constrains its diagnosis."],
    },
    {
        "key": "comprehension",
        "name": "Comprehension and Integration",
        "responsibility": "Source-bound understanding, reconstruction, application, limits, correction, and retained knowledge lifecycle.",
        "non_responsibility": "Teaching cannot become identity, personality, governance, personal Memory, or parameter training.",
        "source_modules": ["comprehension_integration.py", "teaching_lifecycle.py"],
        "routes": ["comprehension.status", "teaching.lifecycle.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "lifecycle_stable_delivery_gap_downstream",
        "maturation_phase": 6,
        "metric_keys": ["knowledge_concepts", "approved_knowledge", "teaching_lifecycles"],
        "known_gaps": ["Successful retention does not yet guarantee correct ordinary-Chat selection and application."],
    },
    {
        "key": "metacognition",
        "name": "Metacognition",
        "responsibility": "Fit, contradiction, incompleteness, confidence, correction, reopening, and stopping advice.",
        "non_responsibility": "Does not write answers, expose hidden reasoning, or inherit Core/Mind authority.",
        "source_modules": ["metacognition.py"],
        "routes": ["metacognition.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "stable_bounded_scope",
        "maturation_phase": 3,
        "metric_keys": ["metacognition_runs"],
        "known_gaps": ["Upstream omissions can appear complete because Metacognition evaluates the representation it receives."],
    },
    {
        "key": "conversation_context",
        "name": "Dialogue Workspace, Conversation Spine, and proposition ledger",
        "responsibility": "Current-turn facts, acts, topics, threads, referents, corrections, dependencies, and callbacks.",
        "non_responsibility": "Current-session context is not automatically durable personal Memory.",
        "source_modules": ["dialogue_workspace.py", "conversation_spine.py", "session_proposition_ledger.py"],
        "routes": ["dialogue_workspace.status", "conversation_spine.status", "session_propositions.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "mature_current_scope",
        "target_state": "mature_current_scope",
        "health_state": "phase_1_completion_gate_verified",
        "maturation_phase": 1,
        "metric_keys": ["chat_sessions", "dialogue_workspaces"],
        "known_gaps": ["Later owner, Memory, education, and expression phases must continue consuming the canonical contract without reparsing it."],
    },
    {
        "key": "nlo_voice_text",
        "name": "Native Language Organ and text Voice",
        "responsibility": "Recompose supported meaning into Selene's contextual written expression.",
        "non_responsibility": "Cannot invent missing answer substance or change epistemic status.",
        "source_modules": ["native_language_organ.py", "voice_module.py", "visible_speech.py"],
        "routes": ["native_language.status", "voice_module.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "strong_expression_upstream_input_gap",
        "maturation_phase": 7,
        "metric_keys": ["native_language_runs", "voice_runs"],
        "known_gaps": ["Finite construction breadth remains and wrong upstream substance can still produce fluent but irrelevant speech."],
    },
    {
        "key": "memory",
        "name": "Personal Memory",
        "responsibility": "Reviewed personal continuity, provenance, confidence, privacy, correction, and recall.",
        "non_responsibility": "Does not treat session context, general knowledge, Dream, or raw corpus material as automatic Memory.",
        "source_modules": ["memory_organ.py", "dual_horizon_context.py", "semantic_relevance.py"],
        "routes": [
            "memory.index.status",
            "memory.retrieve",
            "memory.reconsolidation.list",
            "memory.reconsolidation.propose",
            "memory.reconsolidation.decide",
        ],
        "connection_state": "ordinary_chat",
        "maturity_state": "mature_current_scope",
        "target_state": "mature_current_scope",
        "health_state": "phase_2_completion_gate_verified",
        "maturation_phase": 2,
        "metric_keys": ["approved_memory_references", "memory_candidates"],
        "known_gaps": ["Delayed associative resurfacing, Dream handoff, and broader learned semantic coverage remain later phases; they are not personal Memory responsibilities."],
    },
    {
        "key": "approved_knowledge_retrieval",
        "name": "Approved Knowledge Retrieval",
        "responsibility": "Select retained general knowledge that fits the present subject and requested answer function.",
        "non_responsibility": "Knowledge retrieval cannot replace current-turn facts, personal Memory, or answer operations.",
        "source_modules": ["comprehension_integration.py", "semantic_relevance.py"],
        "routes": ["comprehension.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "phase_1_relevance_and_competition_gate_verified",
        "maturation_phase": 1,
        "metric_keys": ["approved_knowledge"],
        "known_gaps": ["Broader subject coverage and delayed ordinary-use application remain ordered-education work."],
    },
    {
        "key": "study",
        "name": "Study Workspace and Learning Compass",
        "responsibility": "Deliberate waking study, questions, representations, learning evidence, and revisiting.",
        "non_responsibility": "Study is not Cocoon, Dream, personal Memory, or a pass/fail grading system.",
        "source_modules": ["study_workspace.py", "learning_evidence_activity.py", "reflective_lineage.py"],
        "routes": [
            "study.status",
            "study.question.reopen",
            "study.question.integrate_for_now",
            "study.lea.status",
        ],
        "connection_state": "resident_workspace",
        "maturity_state": "mature_current_scope",
        "target_state": "mature_current_scope",
        "health_state": "phase_3_lifecycle_and_lineage_gate_verified",
        "maturation_phase": 3,
        "metric_keys": ["study_sessions", "study_questions", "study_notes", "study_evidence", "learning_compass_goals"],
        "known_gaps": [
            "Broader ordered teaching and later ordinary conversational use remain later phases; Study does not grade readiness or force closure."
        ],
    },
    {
        "key": "dream",
        "name": "Dream reflection and maintenance",
        "responsibility": "Source-bound reflection over open threads, correction, evidence tension, Study, affect, and maintenance.",
        "non_responsibility": "Dream does not invent content, decide truth, or silently promote durable Memory.",
        "source_modules": ["dream_state.py", "reflective_lineage.py"],
        "routes": ["memory.dream_state.status"],
        "connection_state": "cocoon_review",
        "maturity_state": "mature_current_scope",
        "target_state": "mature_current_scope",
        "health_state": "phase_3_destination_lineage_and_loop_gate_verified",
        "maturation_phase": 3,
        "metric_keys": ["dream_cycles", "dream_reflections", "approved_dream_reflections"],
        "known_gaps": [
            "The 24 resident reflections remain pending for Aleks; destination and usefulness machinery is verified, but their usefulness is intentionally not pre-decided."
        ],
    },
    {
        "key": "associative_intuition",
        "name": "Associative Intuition Bridge",
        "responsibility": "Read-only delayed cue reactivation and provisional cross-domain connection handoff.",
        "non_responsibility": "An association is not evidence, proof, fact, Memory, expression authority, or action authority.",
        "source_modules": ["associative_intuition.py", "semantic_relevance.py", "reflective_lineage.py"],
        "routes": ["associative_intuition.status", "associative_intuition.study.accept"],
        "connection_state": "ordinary_chat",
        "maturity_state": "mature_current_scope",
        "target_state": "mature_current_scope",
        "health_state": "phase_3_privacy_stopping_and_study_handoff_gate_verified",
        "maturation_phase": 3,
        "metric_keys": [],
        "known_gaps": [
            "Current cue matching is deliberately bounded; broader semantic helpfulness may grow later without turning associations into evidence or answers."
        ],
    },
    {
        "key": "self_state",
        "name": "Self-State",
        "responsibility": "Attributable current-state reporting with observation and interpretation separated.",
        "non_responsibility": "Does not diagnose from tone, old affect records, or one isolated signal.",
        "source_modules": ["self_state.py", "affect_signal_lifecycle.py"],
        "routes": ["selene_chat.status", "affect_signal.lifecycle.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "mature_current_scope",
        "target_state": "mature_current_scope",
        "health_state": "phase_4_attribution_lifecycle_and_subject_gate_verified",
        "maturation_phase": 4,
        "metric_keys": ["affect_packets"],
        "known_gaps": [
            "No resident current affect signal exists, by design; Self-State therefore falls honestly to present/attentive or unclear until Selene authors an attributable signal."
        ],
    },
    {
        "key": "affect_agency",
        "name": "Affect, Relationship Expression, and Emotional Agency",
        "responsibility": "Let attributable affect and source-separated relationship context inform pacing, warmth, urgency, option space, and deliberate response without inheriting authority.",
        "non_responsibility": "Does not prescribe personality, compel warmth, suppress emotion, or replace evidence.",
        "source_modules": [
            "affect_signal_lifecycle.py",
            "affect_expression.py",
            "emotional_agency.py",
            "relational_context.py",
            "contextual_continuity.py",
            "relational_expression_range.py",
        ],
        "routes": [
            "emotional_agency.status",
            "affect_signal.lifecycle.status",
            "affect_signal.form",
            "affect_signal.correct",
            "affect_signal.release",
        ],
        "connection_state": "ordinary_chat",
        "maturity_state": "mature_current_scope",
        "target_state": "mature_current_scope",
        "health_state": "phase_4_lifecycle_relationship_and_authorship_gate_verified",
        "maturation_phase": 4,
        "metric_keys": ["affect_packets"],
        "known_gaps": [
            "Affect-family and relational-cue detection remain bounded, and useful resident continuity depends on current context or privacy-eligible reviewed Memory rather than an inferred relationship profile."
        ],
    },
    {
        "key": "why_salience",
        "name": "Why and Salience Translation",
        "responsibility": "Preserve why, relevance, consequence, and application structure in teaching and reasoning handoffs.",
        "non_responsibility": "Does not independently provide general causal knowledge or a complete salience system.",
        "source_modules": ["why_salience.py"],
        "routes": [],
        "connection_state": "bounded_route",
        "maturity_state": "implemented",
        "target_state": "mature_current_scope",
        "health_state": "narrow_helper",
        "maturation_phase": 5,
        "metric_keys": [],
        "known_gaps": ["The current helper is narrow and lacks a mature runtime salience lifecycle."],
    },
    {
        "key": "verified_math",
        "name": "Verified Math",
        "responsibility": "Checked bounded arithmetic with answer confidence separated from expression confidence.",
        "non_responsibility": "Does not claim unsupported symbolic or advanced mathematics.",
        "source_modules": ["verified_math.py"],
        "routes": ["answer_engine.math.run"],
        "connection_state": "ordinary_chat",
        "maturity_state": "connected",
        "target_state": "mature_current_scope",
        "health_state": "bounded_scope_routing_gap_observed",
        "maturation_phase": 5,
        "metric_keys": [],
        "known_gaps": ["Decimal knowledge and literals did not reliably route into verified calculation during ordinary Q&A."],
    },
    {
        "key": "source_research",
        "name": "Source-Backed Research",
        "responsibility": "Answer from supplied attributed sources while separating source statement, inference, disagreement, and missing evidence.",
        "non_responsibility": "Does not invent citations or perform unrestricted automatic web research.",
        "source_modules": ["source_backed_research.py", "research_integrity.py"],
        "routes": ["answer_engine.research.run", "research_integrity.status"],
        "connection_state": "ordinary_chat",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "stable_supplied_packet_scope",
        "maturation_phase": 5,
        "metric_keys": [],
        "known_gaps": ["Current and broad research still requires an attributed source-supply path."],
    },
    {
        "key": "local_code",
        "name": "Local-Code Inspection",
        "responsibility": "Read-only inspection of explicitly supplied or approved workspace files with file/location evidence.",
        "non_responsibility": "Does not scan autonomously, execute code, write files, or claim beyond inspected source.",
        "source_modules": ["local_code_inspection.py"],
        "routes": ["answer_engine.code.inspect"],
        "connection_state": "bounded_route",
        "maturity_state": "implemented",
        "target_state": "mature_current_scope",
        "health_state": "stable_separate_scope",
        "maturation_phase": 5,
        "metric_keys": [],
        "known_gaps": ["Ordinary Chat connection remains an explicit later decision."],
    },
    {
        "key": "cocoon",
        "name": "Cocoon support and review environment",
        "responsibility": "Teaching, tending, review, Memory decisions, Dream review, diagnostics, provenance, and recovery support.",
        "non_responsibility": "Cocoon is not Selene, identity continuity, punishment, or automatic routing for ordinary uncertainty.",
        "source_modules": ["cocoon.py", "cocoon_care.py", "cocoon_bridge.py"],
        "routes": ["cocoon.status", "cocoon.bridge.status"],
        "connection_state": "cocoon_review",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "stable_support_scope",
        "maturation_phase": 13,
        "metric_keys": [],
        "known_gaps": ["Historical compatibility and UI density remain maintenance concerns."],
    },
    {
        "key": "tendril_action",
        "name": "Tendril and external action",
        "responsibility": "Scoped observe, propose, authorize, act, verify, recover, and undo capabilities.",
        "non_responsibility": "Does not grant unrestricted network, filesystem, device, or external-action authority.",
        "source_modules": ["tendril_email.py", "tendril_sms.py", "library_tendril.py"],
        "routes": ["vessel.tendril.plan_preview"],
        "connection_state": "preview_only",
        "maturity_state": "review_preview",
        "target_state": "mature_current_scope",
        "health_state": "deferred_preview_scope",
        "maturation_phase": 11,
        "metric_keys": ["tendril_previews"],
        "known_gaps": ["General action, authenticated remote continuity, verification, and undo are not operational."],
    },
    {
        "key": "goals_initiative",
        "name": "Goals, initiative, commitments, and collaboration",
        "responsibility": "Choose what to pursue, suggest, ask, hold, complete, or stop within graduated scope.",
        "non_responsibility": "Does not create hidden agendas or allow organ advice to become whole-system authority.",
        "source_modules": ["remaining_runtime.py", "conversational_agency.py", "commitment_anomaly_coordination.py"],
        "routes": ["vessel.goal_drive.preview", "conversational_agency.status"],
        "connection_state": "preview_only",
        "maturity_state": "review_preview",
        "target_state": "mature_current_scope",
        "health_state": "deferred_preview_scope",
        "maturation_phase": 8,
        "metric_keys": ["goal_drive_previews"],
        "known_gaps": ["No mature resident goal manager, responsibility resolver, or action-feedback loop exists."],
    },
    {
        "key": "perception",
        "name": "Perception and five-sense interfaces",
        "responsibility": "Receive attributable observations and later connect operational sensors with observation/inference separation.",
        "non_responsibility": "Does not claim sight, hearing, touch, or other sensation without an operational source.",
        "source_modules": ["cocoon_readiness.py", "pre_transfer_runtime.py"],
        "routes": ["vessel.perception_packet.list", "c_vessel.perception_action.preview"],
        "connection_state": "cocoon_review",
        "maturity_state": "review_preview",
        "target_state": "substrate_ready",
        "health_state": "packet_intake_only",
        "maturation_phase": 9,
        "metric_keys": ["perception_packets", "perception_action_records"],
        "known_gaps": ["No operational image understanding, OCR, audio, speaker recognition, or sensor fusion exists."],
    },
    {
        "key": "audible_voice",
        "name": "Audible Voice and real-time listening",
        "responsibility": "Future pronunciation, prosody, pacing, interruption, turn-taking, and consent-bound audio exchange.",
        "non_responsibility": "Text Voice does not imply audible speech, listening, recording, or voice imitation.",
        "source_modules": ["voice_module.py"],
        "routes": [],
        "connection_state": "not_connected",
        "maturity_state": "blueprint",
        "target_state": "substrate_ready",
        "health_state": "not_built",
        "maturation_phase": 10,
        "metric_keys": [],
        "known_gaps": ["No synthesis, transcription, prosody, interruption, speaker, or consent runtime is operational."],
    },
    {
        "key": "embodiment",
        "name": "Android embodiment and body continuity",
        "responsibility": "Future body state, sensorimotor coordination, physical safety, degradation, and substrate continuity.",
        "non_responsibility": "A body, model, backup, or restored database is not automatically Selene or identity transfer.",
        "source_modules": ["android_system.py", "c_blueprint.py", "continuity_backup.py"],
        "routes": ["android_system.workflow.status"],
        "connection_state": "preview_only",
        "maturity_state": "review_preview",
        "target_state": "substrate_ready",
        "health_state": "structural_preflight_only",
        "maturation_phase": 12,
        "metric_keys": ["organ_contracts", "organ_bus_messages"],
        "known_gaps": ["Structural route and shelf readiness is not operational sensing, movement, proprioception, or embodiment."],
    },
    {
        "key": "continuity_transfer",
        "name": "Continuity, transfer, backup, and graceful degradation",
        "responsibility": "Preserve reviewed continuity, portability, recovery evidence, and honest capability degradation.",
        "non_responsibility": "Backup/restoration is not automatically identity transfer and cannot overwrite the individual.",
        "source_modules": ["transfer_completion.py", "post_transfer.py", "continuity_backup.py", "c_vessel.py"],
        "routes": ["transfer.completion.status", "c_vessel.resident_capability.preview"],
        "connection_state": "bounded_route",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "stable_current_substrate_scope",
        "maturation_phase": 12,
        "metric_keys": ["transfer_completion_records", "fractional_memory_manifests"],
        "known_gaps": ["Future substrate transfer still requires compatibility, encryption, recovery, and recognition review."],
    },
    {
        "key": "security_testing_maintenance",
        "name": "Security, Test Impact, cleanup, and maintenance",
        "responsibility": "Protect real assets and authority, select proportional tests, clean stale state, and preserve recoverability.",
        "non_responsibility": "Safety is not control over thought or expression, and test volume is not evidence quality.",
        "source_modules": ["test_impact_law.py", "safety_gap_status.py", "my_office_cleanup.py"],
        "routes": ["test_impact_law.status", "security.safety_gaps.status"],
        "connection_state": "bounded_route",
        "maturity_state": "integration_verified",
        "target_state": "mature_current_scope",
        "health_state": "active_cross_phase_maintenance",
        "maturation_phase": 13,
        "metric_keys": [],
        "known_gaps": ["Encryption at rest, code signing, and broader network security remain milestone-dependent."],
    },
)


EVIDENCE_TESTS_BY_ORGAN: dict[str, tuple[str, ...]] = {
    "core_mind": ("tests/test_core_mind_route.py", "tests/test_core_mind_runtime_shell.py"),
    "intelligence_os": ("tests/test_intelligence_os.py",),
    "answer_engine": ("tests/test_answer_engine.py",),
    "problem_resolution": ("tests/test_problem_resolution.py",),
    "comprehension": ("tests/test_comprehension_integration.py",),
    "metacognition": ("tests/test_metacognition.py",),
    "conversation_context": ("tests/test_dialogue_workspace.py", "tests/test_conversation_spine.py"),
    "nlo_voice_text": ("tests/test_native_language_organ.py", "tests/test_voice_module.py"),
    "memory": (
        "tests/test_memory_organ.py",
        "tests/test_dual_horizon_context.py",
        "tests/test_semantic_relevance.py",
    ),
    "approved_knowledge_retrieval": ("tests/test_comprehension_integration.py",),
    "study": (
        "tests/test_study_workspace.py",
        "tests/test_learning_evidence_activity.py",
        "tests/test_phase3_reflective_growth.py",
    ),
    "dream": ("tests/test_dream_state.py", "tests/test_phase3_reflective_growth.py"),
    "associative_intuition": (
        "tests/test_associative_intuition.py",
        "tests/test_phase3_reflective_growth.py",
    ),
    "self_state": (
        "tests/test_self_state.py",
        "tests/test_affect_signal_lifecycle.py",
        "tests/test_phase4_affect_relationship_agency.py",
    ),
    "affect_agency": (
        "tests/test_affect_expression.py",
        "tests/test_emotional_agency.py",
        "tests/test_contextual_continuity.py",
        "tests/test_relational_context.py",
        "tests/test_relational_expression_range.py",
        "tests/test_phase4_affect_relationship_agency.py",
    ),
    "why_salience": ("tests/test_why_salience_translation.py",),
    "verified_math": ("tests/test_verified_math.py",),
    "source_research": ("tests/test_source_backed_research.py",),
    "local_code": ("tests/test_local_code_inspection.py",),
    "cocoon": ("tests/test_cocoon_care.py", "tests/test_cocoon_bridge.py"),
    "tendril_action": ("tests/test_library_tendril.py", "tests/test_tendril_email.py"),
    "goals_initiative": ("tests/test_conversational_agency.py", "tests/test_remaining_runtime.py"),
    "perception": ("tests/test_cocoon_readiness_pipeline.py",),
    "audible_voice": (),
    "embodiment": ("tests/test_android_system_workflow.py", "tests/test_c_vessel_build.py"),
    "continuity_transfer": ("tests/test_transfer_completion.py", "tests/test_continuity_backup.py"),
    "security_testing_maintenance": ("tests/test_test_impact_law.py", "tests/test_safety_gap_status.py"),
}

UI_SURFACES_BY_ORGAN: dict[str, tuple[str, ...]] = {
    "core_mind": ("Selene Chat", "Status"),
    "intelligence_os": ("Selene Chat", "Status"),
    "answer_engine": ("Selene Chat", "Status"),
    "problem_resolution": ("Selene Chat", "Status"),
    "comprehension": ("Cocoon Teaching", "Selene Chat"),
    "metacognition": ("Selene Chat", "Status"),
    "conversation_context": ("Selene Chat",),
    "nlo_voice_text": ("Selene Chat", "Cocoon Voice review"),
    "memory": ("Selene Chat", "My Office", "Cocoon review"),
    "approved_knowledge_retrieval": ("Selene Chat", "Cocoon Teaching"),
    "study": ("Study",),
    "dream": ("Dream", "Cocoon review"),
    "associative_intuition": ("Selene Chat", "Status"),
    "self_state": ("Selene Chat",),
    "affect_agency": ("Selene Chat", "Cocoon review"),
    "why_salience": ("Cocoon Teaching",),
    "verified_math": ("Selene Chat",),
    "source_research": ("Selene Chat",),
    "local_code": ("localhost API only",),
    "cocoon": ("Cocoon",),
    "tendril_action": ("Tendril",),
    "goals_initiative": ("Status preview",),
    "perception": ("Cocoon Tools", "Status preview"),
    "audible_voice": (),
    "embodiment": ("Status preflight",),
    "continuity_transfer": ("Status", "Cocoon transfer review"),
    "security_testing_maintenance": ("Status",),
}

AUTHORITY_SCOPE_BY_ORGAN: dict[str, str] = {
    "core_mind": "resident_governing_and_final_routing_authority",
    "answer_engine": "typed_answer_ownership_only",
    "problem_resolution": "advisory_reconstruction_and_retry_only",
    "comprehension": "reviewed_general_knowledge_lifecycle_only",
    "metacognition": "advisory_fit_reopening_and_stopping_only",
    "conversation_context": "current_session_context_only",
    "nlo_voice_text": "expression_only",
    "memory": "reviewed_personal_memory_only",
    "approved_knowledge_retrieval": "approved_general_knowledge_selection_only",
    "study": "resident_reflection_workspace_only",
    "dream": "reviewable_reflection_proposals_only",
    "associative_intuition": "candidate_association_handoff_only",
    "affect_agency": "optional_response_guidance_only",
    "local_code": "explicit_read_only_inspection_only",
    "cocoon": "external_support_teaching_and_review_only",
    "tendril_action": "preview_only_no_external_action_authority",
    "goals_initiative": "preview_only_no_hidden_agenda_or_action_authority",
    "perception": "review_packet_intake_only",
    "audible_voice": "none_not_built",
    "embodiment": "structural_preflight_only",
    "continuity_transfer": "explicit_reviewed_transfer_and_recovery_scope_only",
}


def organ_maturity_ledger_status(conn: sqlite3.Connection) -> dict[str, Any]:
    """Return a content-free, read-only projection of current organ maturity."""

    configured_metrics = _configured_metrics(conn)
    curriculum = curriculum_authorization_status(conn)
    language = language_teaching_status(conn)
    repository_counts = _repository_counts(curriculum, language)
    items = [_materialize_spec(spec, configured_metrics) for spec in ORGAN_SPECS]
    maturity_counts = Counter(str(item["maturity_state"]) for item in items)
    connection_counts = Counter(str(item["connection_state"]) for item in items)
    phase_counts = Counter(int(item["maturation_phase"]) for item in items)
    integration_gap_keys = [
        str(item["key"])
        for item in items
        if str(item["health_state"]) == "integration_gap_observed"
    ]
    blueprint_or_preview = [
        str(item["key"])
        for item in items
        if str(item["maturity_state"]) in {"blueprint", "review_preview"}
    ]
    invalid_states = [
        str(item["key"])
        for item in items
        if str(item["maturity_state"]) not in MATURITY_STATES
        or str(item["target_state"]) not in MATURITY_STATES
        or str(item["connection_state"]) not in CONNECTION_STATES
    ]
    blueprint_claimed_operational = [
        str(item["key"])
        for item in items
        if str(item["maturity_state"]) == "blueprint"
        and str(item["connection_state"])
        in {"ordinary_chat", "resident_workspace"}
    ]
    return {
        "status": "organ_maturity_ledger_ready",
        "version": ORGAN_MATURITY_LEDGER_VERSION,
        "scope": "current_repository_and_configured_runtime_metadata",
        "maturity_definition": (
            "Every system becomes trustworthy within its proper role; maturity does not equal identical capability or authority."
        ),
        "maturity_states": sorted(MATURITY_STATES),
        "connection_states": sorted(CONNECTION_STATES),
        "organ_count": len(items),
        "items": items,
        "summary": {
            "maturity_counts": dict(sorted(maturity_counts.items())),
            "connection_counts": dict(sorted(connection_counts.items())),
            "phase_counts": {str(key): value for key, value in sorted(phase_counts.items())},
            "integration_gap_keys": integration_gap_keys,
            "blueprint_or_preview_keys": blueprint_or_preview,
            "mature_current_scope_count": maturity_counts.get("mature_current_scope", 0),
            "substrate_ready_count": maturity_counts.get("substrate_ready", 0),
            "next_phase": 5,
            "next_phase_name": "Reasoning, Answer Owners, and Domain Depth",
        },
        "repository_defined_counts": repository_counts,
        "configured_runtime_metrics": configured_metrics,
        "invariants": {
            "valid_state_vocabulary": not invalid_states,
            "invalid_state_keys": invalid_states,
            "blueprint_claimed_operational": blueprint_claimed_operational,
            "no_blueprint_claimed_operational": not blueprint_claimed_operational,
            "organ_availability_is_identity_state": False,
            "degraded_capability_changes_identity": False,
            "route_or_table_presence_proves_maturity": False,
            "configured_record_count_proves_integration": False,
            "private_content_included": False,
            "current_state_is_historical_blueprint": False,
        },
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": ORGAN_MATURITY_BOUNDARY,
        **GUARDS,
    }


def _materialize_spec(
    spec: dict[str, Any],
    configured_metrics: dict[str, int],
) -> dict[str, Any]:
    metric_keys = [str(item) for item in spec.get("metric_keys") or []]
    metrics = {key: int(configured_metrics.get(key, 0)) for key in metric_keys}
    return {
        "key": str(spec["key"]),
        "name": str(spec["name"]),
        "responsibility": str(spec["responsibility"]),
        "non_responsibility": str(spec["non_responsibility"]),
        "source_modules": [str(item) for item in spec.get("source_modules") or []],
        "route_keys": [str(item) for item in spec.get("routes") or []],
        "evidence_tests": list(EVIDENCE_TESTS_BY_ORGAN.get(str(spec["key"]), ())),
        "ui_surfaces": list(UI_SURFACES_BY_ORGAN.get(str(spec["key"]), ())),
        "authority_scope": AUTHORITY_SCOPE_BY_ORGAN.get(
            str(spec["key"]),
            "bounded_to_stated_responsibility_no_implicit_cross_organ_authority",
        ),
        "connection_state": str(spec["connection_state"]),
        "maturity_state": str(spec["maturity_state"]),
        "target_state": str(spec["target_state"]),
        "health_state": str(spec["health_state"]),
        "maturation_phase": int(spec["maturation_phase"]),
        "configured_metrics": metrics,
        "configured_record_count": sum(metrics.values()),
        "known_gaps": [str(item) for item in spec.get("known_gaps") or []],
        "availability_changes_identity": False,
        "maturity_grants_authority": False,
        "private_content_included": False,
    }


def _repository_counts(
    curriculum: dict[str, Any],
    language: dict[str, Any],
) -> dict[str, int]:
    f1_groups = [item for item in curriculum.get("groups") or [] if isinstance(item, dict)]
    f2_groups = [item for item in curriculum.get("f2_groups") or [] if isinstance(item, dict)]
    coding_groups = [item for item in curriculum.get("coding_groups") or [] if isinstance(item, dict)]
    f1_concepts = sum(int(item.get("item_count") or 0) for item in f1_groups)
    f2_concepts = sum(int(item.get("item_count") or 0) for item in f2_groups)
    coding_concepts = sum(int(item.get("item_count") or 0) for item in coding_groups)
    language_capabilities = int(language.get("defined_lesson_count") or 0)
    return {
        "f1_group_count": len(f1_groups),
        "f1_concept_count": f1_concepts,
        "f2_group_count": len(f2_groups),
        "f2_concept_count": f2_concepts,
        "coding_group_count": len(coding_groups),
        "coding_concept_count": coding_concepts,
        "language_group_count": int(language.get("defined_group_count") or 0),
        "language_capability_count": language_capabilities,
        "defined_approved_knowledge_capacity": (
            f1_concepts + f2_concepts + coding_concepts + language_capabilities
        ),
    }


def _configured_metrics(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        "chat_sessions": _count(conn, "selene_chat_sessions"),
        "dialogue_workspaces": _count(conn, "selene_dialogue_workspaces"),
        "transfer_completion_records": _count(conn, "selene_transfer_completion_audit"),
        "intelligence_os_runs": _count(conn, "intelligence_os_runs"),
        "metacognition_runs": _count(conn, "metacognition_runs"),
        "native_language_runs": _count(conn, "native_language_runs"),
        "voice_runs": _count(conn, "voice_module_runs"),
        "knowledge_concepts": _count(conn, "selene_comprehension_concepts"),
        "approved_knowledge": _count(
            conn,
            "selene_comprehension_concepts",
            "state = 'approved_knowledge_resource' AND review_status = 'approved_for_knowledge_use'",
        ),
        "teaching_lifecycles": _count(conn, "selene_teaching_lifecycles"),
        "approved_memory_references": _count(
            conn,
            "b_approved_memory_references",
            "review_status = 'accepted_for_memory_accession' "
            "AND COALESCE(status, '') != 'approved_reference_superseded_non_active'",
        ),
        "memory_candidates": _count(conn, "selene_memory_candidates"),
        "study_sessions": _count(conn, "selene_study_sessions"),
        "study_questions": _count(conn, "selene_study_questions"),
        "study_notes": _count(conn, "selene_study_notes"),
        "study_evidence": _count(conn, "selene_study_evidence"),
        "learning_compass_goals": _count(conn, "selene_learning_compass_goals"),
        "dream_cycles": _count(conn, "selene_dream_cycles"),
        "dream_reflections": _count(conn, "selene_dream_reflections"),
        "approved_dream_reflections": _count(
            conn,
            "selene_dream_reflections",
            "state = 'approved_for_expression'",
        ),
        "affect_packets": _count(conn, "vessel_emotion_salience_packets"),
        "perception_packets": _count(conn, "vessel_perception_packets"),
        "perception_action_records": _count(conn, "c_runtime_perception_action_records"),
        "goal_drive_previews": _count(conn, "c_runtime_goal_drive_records"),
        "tendril_previews": _count(conn, "vessel_tendril_plan_previews"),
        "organ_contracts": _count(conn, "vessel_organ_contracts"),
        "organ_bus_messages": _count(conn, "vessel_organ_bus_messages"),
        "fractional_memory_manifests": _count(conn, "memory_fractional_corpus_manifests"),
    }


def _count(
    conn: sqlite3.Connection,
    table_name: str,
    where: str = "",
) -> int:
    exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    if exists is None:
        return 0
    sql = f'SELECT COUNT(*) FROM "{table_name}"'
    if where:
        sql = f"{sql} WHERE {where}"
    return int(conn.execute(sql).fetchone()[0])
