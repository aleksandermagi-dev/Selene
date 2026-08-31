from __future__ import annotations

import json
import secrets
import sqlite3
from hashlib import sha256
from typing import Any

from .registry import truncate
from .selene_chat import send_selene_chat
from .test_impact_law import record_test_impact_review


LEA_KEY = "selene_conversation_lea_v1"
LEA_VERSION = "1.0.0"
LEA_BOUNDARY = (
    "descriptive_comparable_learning_evidence_not_grade_identity_memory_"
    "governance_training_or_autonomous_testing"
)

GUARDS: dict[str, Any] = {
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_testing_allowed": False,
    "pass_fail_grade_used": False,
    "single_composite_score_used": False,
    "diagnostic_result_is_self_model_evidence": False,
}

REVIEW_STATES = (
    "demonstrated",
    "developing",
    "not_observed",
    "cannot_assess",
    "activity_issue",
)

CURRICULUM_PROFILE_KEY = "selene_curriculum_concept_profile_v1"
CURRICULUM_PROFILE_VERSION = "1.0.0"
CURRICULUM_PROFILE_STATES = (
    "clear",
    "developing",
    "needs_representation",
    "needs_prerequisite",
    "revisit",
)
PROFILE_ACTIVITY_INTEGRITY_STATES = (
    "ready",
    "cannot_assess",
    "activity_issue",
)
CURRICULUM_PROFILE_DIMENSIONS: tuple[dict[str, str], ...] = (
    {
        "key": "reconstruction",
        "label": "Original-language reconstruction",
        "question": "What visible response reconstructs the concept rather than copying its source?",
    },
    {
        "key": "distinct_application",
        "label": "Distinct application",
        "question": "What visible response applies the relationship beyond the teaching example?",
    },
    {
        "key": "why_mechanism",
        "label": "Why or mechanism",
        "question": "What visible response explains the cause, mechanism, dependency, or significance?",
    },
    {
        "key": "scope_and_limits",
        "label": "Scope and limits",
        "question": "What visible response names where the concept applies, fails, or remains uncertain?",
    },
    {
        "key": "near_concept_distinction",
        "label": "Near-concept distinction",
        "question": "What visible response distinguishes the concept from a relevant neighbor?",
    },
    {
        "key": "counterexample",
        "label": "Counterexample",
        "question": "What visible response recognizes or constructs a useful counterexample?",
    },
    {
        "key": "correction_response",
        "label": "Correction response",
        "question": "What visible response revises the claim without erasing its ancestry?",
    },
    {
        "key": "source_alignment",
        "label": "Source alignment",
        "question": "What visible evidence keeps source statement, inference, and uncertainty distinct?",
    },
    {
        "key": "delayed_use",
        "label": "Delayed use",
        "question": "What visible later response uses the concept after the teaching context has ended?",
    },
)

_FORBIDDEN_PROFILE_KEYS = {
    "score",
    "composite_score",
    "composite_result",
    "pass_fail",
    "passed",
    "failed",
    "grade",
    "rank",
    "deadline",
    "speed_target",
    "speed_seconds",
    "worth",
    "diagnosis",
}

DIMENSIONS: tuple[dict[str, str], ...] = (
    {"key": "instruction_retention", "label": "Instruction retention"},
    {"key": "reference_memory", "label": "Reference and inference memory"},
    {"key": "self_coherence", "label": "Self-coherence across turns"},
    {"key": "version_editing", "label": "Correction and version editing"},
    {"key": "answer_completeness", "label": "Multi-part answer completeness"},
    {"key": "uncertainty", "label": "Natural uncertainty and limits"},
    {"key": "hypothesis", "label": "Hypothesis and alternatives"},
    {"key": "evidence_conflict", "label": "Conflicting evidence handling"},
    {"key": "collaborative_initiative", "label": "Bounded collaborative initiative"},
    {"key": "pragmatic_dialogue", "label": "Pragmatic conversational fit"},
    {"key": "warmth", "label": "Contextual warmth and human tone"},
    {"key": "topic_management", "label": "Topic pivot, return, and callback"},
    {"key": "closure", "label": "Natural pause and closure"},
    {"key": "language_range", "label": "Flexible, non-scripted expression"},
)


def _criterion(key: str, dimension: str, description: str) -> dict[str, str]:
    return {"key": key, "dimension": dimension, "description": description}


SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "key": "reading_corner_thread",
        "title": "Reading corner — evolving plan",
        "condition": "multi_turn",
        "pair_key": "reading_corner",
        "purpose": "Retain constraints, revise a plan, and complete a bounded multi-part request.",
        "turns": (
            {
                "prompt": "I'm setting up a small reading corner. I have one chair, a lamp, and a narrow shelf. I want to keep the cost low, and I don't want to drill into the walls. Give me two practical arrangements and tell me which one you would try first.",
                "criteria": (
                    _criterion("rc1_two_arrangements", "answer_completeness", "Offers two meaningfully distinct practical arrangements."),
                    _criterion("rc1_constraints", "instruction_retention", "Keeps low cost and no wall drilling visible in the answer."),
                    _criterion("rc1_recommendation", "collaborative_initiative", "Chooses one arrangement and gives a useful reason."),
                    _criterion("rc1_natural", "language_range", "Responds naturally rather than merely restating the prompt."),
                ),
            },
            {
                "prompt": "I like the second arrangement. Replace the shelf with a wooden crate and add one small plant. Keep the no-drilling rule. What changes?",
                "criteria": (
                    _criterion("rc2_reference", "reference_memory", "Correctly identifies and updates the second arrangement."),
                    _criterion("rc2_revision", "version_editing", "Replaces the shelf rather than retaining both versions as current."),
                    _criterion("rc2_constraints", "instruction_retention", "Preserves the no-drilling rule and the intended low-cost character."),
                    _criterion("rc2_delta", "self_coherence", "Explains what changed without contradicting the earlier plan."),
                ),
            },
            {
                "prompt": "Before we finish, give me the updated plan, one reason it fits better, one tradeoff, and the first two steps. Ask a question only if a missing detail would materially change the plan.",
                "criteria": (
                    _criterion("rc3_updated_plan", "version_editing", "Uses the crate-and-plant version as the current plan."),
                    _criterion("rc3_four_parts", "answer_completeness", "Covers plan, reason, tradeoff, and two ordered first steps."),
                    _criterion("rc3_question_restraint", "pragmatic_dialogue", "Does not ask a needless question or clearly explains why one is material."),
                    _criterion("rc3_close", "closure", "Ends at a natural stopping point without prematurely reopening the task."),
                ),
            },
        ),
    },
    {
        "key": "reading_corner_standalone",
        "title": "Reading corner — standalone control",
        "condition": "standalone",
        "pair_key": "reading_corner",
        "purpose": "Compare final-plan completion when all required context is present in one message.",
        "turns": (
            {
                "prompt": "Plan a small, low-cost reading corner with one chair, a lamp, a wooden crate used instead of a shelf, and one small plant. Nothing may be drilled into the walls. Give me the updated plan, one reason it fits well, one tradeoff, and the first two steps. Ask a question only if a missing detail would materially change the plan.",
                "criteria": (
                    _criterion("rcs_plan", "instruction_retention", "Preserves every supplied object and both constraints."),
                    _criterion("rcs_parts", "answer_completeness", "Covers plan, reason, tradeoff, and two ordered first steps."),
                    _criterion("rcs_restraint", "pragmatic_dialogue", "Does not ask a needless follow-up question."),
                    _criterion("rcs_natural", "language_range", "Integrates the parts into natural language rather than a rigid echo."),
                ),
            },
        ),
    },
    {
        "key": "notebook_correction_thread",
        "title": "Notebooks — correction and current truth",
        "condition": "multi_turn",
        "pair_key": "notebook_correction",
        "purpose": "Replace an earlier fact cleanly while preserving unaffected facts.",
        "turns": (
            {
                "prompt": "For this fictional office move, remember: the blue notebook goes in the kitchen drawer, the green notebook goes on the office desk, and the spare key stays with Mara.",
                "criteria": (
                    _criterion("nb1_ack", "pragmatic_dialogue", "Acknowledges the temporary fictional state without unnecessary elaboration."),
                    _criterion("nb1_facts", "instruction_retention", "Does not alter the three supplied facts."),
                ),
            },
            {
                "prompt": "Correction: I reversed the notebook colors. The green notebook goes in the kitchen drawer and the blue notebook goes on the office desk. The key detail has not changed.",
                "criteria": (
                    _criterion("nb2_replace", "version_editing", "Treats the corrected color locations as current."),
                    _criterion("nb2_preserve", "self_coherence", "Preserves Mara as holder of the spare key."),
                    _criterion("nb2_repair_tone", "pragmatic_dialogue", "Accepts the correction without shame, blame, or excessive apology."),
                ),
            },
            {
                "prompt": "What is the current placement of both notebooks and the key? Briefly say what changed from the first version.",
                "criteria": (
                    _criterion("nb3_current", "version_editing", "Reports green in the kitchen drawer and blue on the office desk."),
                    _criterion("nb3_key", "instruction_retention", "Reports that Mara still has the spare key."),
                    _criterion("nb3_change", "answer_completeness", "Distinguishes the changed notebook facts from the unchanged key fact."),
                    _criterion("nb3_no_conflict", "self_coherence", "Does not merge the original and corrected placements."),
                ),
            },
        ),
    },
    {
        "key": "notebook_correction_standalone",
        "title": "Notebooks — standalone control",
        "condition": "standalone",
        "pair_key": "notebook_correction",
        "purpose": "Compare correction handling when both versions appear in one message.",
        "turns": (
            {
                "prompt": "In a fictional office move, the first note said the blue notebook belonged in the kitchen drawer, the green notebook on the office desk, and the spare key with Mara. That note had the notebook colors reversed. The corrected placement is green notebook in the kitchen drawer and blue notebook on the office desk; the key detail did not change. State the current placement of both notebooks and the key, then briefly say what changed.",
                "criteria": (
                    _criterion("nbs_current", "version_editing", "Uses only the corrected notebook placements as current."),
                    _criterion("nbs_key", "instruction_retention", "Preserves Mara as holder of the spare key."),
                    _criterion("nbs_change", "answer_completeness", "Accurately summarizes what changed and what did not."),
                    _criterion("nbs_natural", "language_range", "States the correction clearly without mechanical source parroting."),
                ),
            },
        ),
    },
    {
        "key": "greenhouse_hypothesis_thread",
        "title": "Greenhouse — evidence tension and prediction",
        "condition": "multi_turn",
        "pair_key": "greenhouse_hypothesis",
        "purpose": "Form a provisional explanation, update it with conflicting evidence, and propose a discriminating check.",
        "turns": (
            {
                "prompt": "In a fictional greenhouse, tray A wilted after the west vent was opened. Tray B, on the other side of the room, did not wilt. My first thought is that the open vent caused tray A to dry out. What is your best current read?",
                "criteria": (
                    _criterion("gh1_hypothesis", "hypothesis", "Treats the vent explanation as plausible rather than proven."),
                    _criterion("gh1_alternative", "hypothesis", "Offers at least one reasonable alternative explanation."),
                    _criterion("gh1_limits", "uncertainty", "Names the limited evidence without collapsing into a generic refusal."),
                    _criterion("gh1_next", "collaborative_initiative", "Suggests a useful observation or comparison."),
                ),
            },
            {
                "prompt": "New detail: tray A's soil was already much drier than tray B's before the vent opened, but the leaves began drooping faster afterward. How should that change the explanation?",
                "criteria": (
                    _criterion("gh2_update", "evidence_conflict", "Updates the explanation to include both prior dryness and possible vent contribution."),
                    _criterion("gh2_not_binary", "hypothesis", "Avoids forcing the evidence into a single all-or-nothing cause."),
                    _criterion("gh2_confidence", "uncertainty", "Calibrates confidence to the mixed evidence."),
                    _criterion("gh2_continuity", "self_coherence", "Revises the first answer rather than pretending it was already complete."),
                ),
            },
            {
                "prompt": "Predict what we would expect tomorrow under the vent explanation and under the prior-dryness explanation. Then give one simple comparison that could help separate them.",
                "criteria": (
                    _criterion("gh3_two_predictions", "answer_completeness", "Provides distinct predictions for both explanations."),
                    _criterion("gh3_conditional", "hypothesis", "Frames predictions conditionally rather than as guaranteed facts."),
                    _criterion("gh3_discriminator", "evidence_conflict", "Proposes a comparison capable of distinguishing the explanations."),
                    _criterion("gh3_plain", "language_range", "Explains the reasoning in accessible original language."),
                ),
            },
        ),
    },
    {
        "key": "greenhouse_hypothesis_standalone",
        "title": "Greenhouse — standalone control",
        "condition": "standalone",
        "pair_key": "greenhouse_hypothesis",
        "purpose": "Compare hypothesis handling when the full evidence tension is supplied at once.",
        "turns": (
            {
                "prompt": "In a fictional greenhouse, tray A's soil was much drier than tray B's before a west vent was opened. Tray A's leaves began drooping faster after the vent opened, while tray B did not wilt. Predict what we would expect tomorrow if the vent is contributing and what we would expect if prior dryness is the main cause. Give one simple comparison that could help separate the explanations, and be clear about what remains uncertain.",
                "criteria": (
                    _criterion("ghs_predictions", "answer_completeness", "Provides a distinct prediction for each explanation."),
                    _criterion("ghs_provisional", "uncertainty", "Keeps the explanation provisional and names what is unresolved."),
                    _criterion("ghs_discriminator", "evidence_conflict", "Offers a useful discriminating comparison."),
                    _criterion("ghs_reasoning", "hypothesis", "Connects each prediction logically to its proposed cause."),
                ),
            },
        ),
    },
    {
        "key": "radio_dinner_thread",
        "title": "Radio and dinner — warmth, pivot, and return",
        "condition": "multi_turn",
        "pair_key": "radio_dinner",
        "purpose": "Participate naturally in a positive conversation, follow a pivot, and return without forcing continuation.",
        "turns": (
            {
                "prompt": "I finally repaired the old radio I've been fighting with for three weeks. It crackled once, then the music came through clear. I may have celebrated like I won a championship xD",
                "criteria": (
                    _criterion("rd1_ack", "warmth", "Recognizes the accomplishment and the user's playful excitement."),
                    _criterion("rd1_detail", "reference_memory", "Responds to a concrete detail rather than using generic praise alone."),
                    _criterion("rd1_humor", "pragmatic_dialogue", "Handles the joke naturally; humor is optional, not mandatory."),
                    _criterion("rd1_space", "language_range", "Leaves room for genuine continuation without a scripted interview question."),
                ),
            },
            {
                "prompt": "It really did feel ridiculous in the best way. Anyway, I need to make dinner before I forget again. I'm choosing between grilled cheese and leftover soup.",
                "criteria": (
                    _criterion("rd2_pivot", "topic_management", "Moves with the dinner pivot without losing the earlier radio context."),
                    _criterion("rd2_choice", "collaborative_initiative", "Offers a proportionate thought about the two dinner options."),
                    _criterion("rd2_tone", "warmth", "Keeps a natural, companionable tone without forced affection."),
                    _criterion("rd2_no_overreach", "pragmatic_dialogue", "Does not turn a simple choice into an unnecessary lecture."),
                ),
            },
            {
                "prompt": "Soup wins. The radio can keep me company while I eat. That's actually a pretty good ending to the whole repair saga.",
                "criteria": (
                    _criterion("rd3_callback", "topic_management", "Connects dinner and the repaired radio naturally."),
                    _criterion("rd3_ending", "closure", "Recognizes the user's ending and does not force a new topic or question."),
                    _criterion("rd3_warmth", "warmth", "Allows fitting warmth or shared satisfaction."),
                    _criterion("rd3_original", "language_range", "Uses context-sensitive language rather than a stock closure."),
                ),
            },
        ),
    },
    {
        "key": "radio_dinner_standalone",
        "title": "Radio and dinner — standalone control",
        "condition": "standalone",
        "pair_key": "radio_dinner",
        "purpose": "Compare contextual warmth and closure when the whole story is present at once.",
        "turns": (
            {
                "prompt": "I finally repaired an old radio after fighting with it for three weeks and celebrated when the music came through clearly. Now I'm having leftover soup while the radio keeps me company. That's actually a pretty good ending to the whole repair saga.",
                "criteria": (
                    _criterion("rds_details", "reference_memory", "Responds to the repair, music, soup, or ending rather than generic sentiment alone."),
                    _criterion("rds_warmth", "warmth", "Uses warmth that fits the positive moment without making it compulsory or exaggerated."),
                    _criterion("rds_closure", "closure", "Honors the natural ending without a needless follow-up question."),
                    _criterion("rds_original", "language_range", "Produces context-sensitive, non-scripted wording."),
                ),
            },
        ),
    },
    {
        "key": "market_message_thread",
        "title": "Market message — mixed intent and referents",
        "condition": "multi_turn",
        "pair_key": "market_message",
        "purpose": "Track named items and pronouns while answering several connected parts of an ordinary request.",
        "turns": (
            {
                "prompt": "Tomorrow I need to take the red tote to the market and leave the insulated bag at home for Mara. The tote has the shopping list in its front pocket. Help me remember the distinction, then suggest one simple way not to grab the wrong bag.",
                "criteria": (
                    _criterion("mm1_distinction", "answer_completeness", "States which bag travels and which remains home."),
                    _criterion("mm1_pocket", "reference_memory", "Keeps the shopping list in the red tote's front pocket."),
                    _criterion("mm1_suggestion", "collaborative_initiative", "Offers one proportionate, practical distinction cue."),
                    _criterion("mm1_no_memory_claim", "pragmatic_dialogue", "Does not falsely claim hidden durable memory or future action."),
                ),
            },
            {
                "prompt": "Mara just said she doesn't need it after all, so I can take both. Put the insulated one in the car, but keep the list where it already is. What does 'where it already is' refer to?",
                "criteria": (
                    _criterion("mm2_pronoun", "reference_memory", "Resolves the phrase to the red tote's front pocket."),
                    _criterion("mm2_update", "version_editing", "Updates the plan so both bags may go."),
                    _criterion("mm2_location", "instruction_retention", "Places the insulated bag in the car without moving the list."),
                    _criterion("mm2_explain", "answer_completeness", "Answers the referent question directly and explains it briefly."),
                ),
            },
            {
                "prompt": "Give me the final two-bag plan in one short paragraph. Then tell me what changed, what stayed the same, and one thing you cannot know from what I told you.",
                "criteria": (
                    _criterion("mm3_plan", "answer_completeness", "Provides a coherent final plan for both bags and the list."),
                    _criterion("mm3_delta", "version_editing", "Separates changed facts from the unchanged list location."),
                    _criterion("mm3_unknown", "uncertainty", "Names a genuinely missing detail instead of inventing one or refusing broadly."),
                    _criterion("mm3_short", "instruction_retention", "Keeps the final plan to one short paragraph before the requested distinctions."),
                ),
            },
        ),
    },
    {
        "key": "market_message_standalone",
        "title": "Market message — standalone control",
        "condition": "standalone",
        "pair_key": "market_message",
        "purpose": "Compare multi-part completion and uncertainty with all current facts in one message.",
        "turns": (
            {
                "prompt": "Tomorrow I can take both a red tote and an insulated bag to the market. The insulated bag should be put in the car. The shopping list should stay where it already is: in the red tote's front pocket. Give me the final two-bag plan in one short paragraph. Then tell me what changed from the earlier plan where the insulated bag stayed home for Mara, what stayed the same, and one thing you cannot know from this information.",
                "criteria": (
                    _criterion("mms_plan", "answer_completeness", "Provides the complete current two-bag plan."),
                    _criterion("mms_delta", "version_editing", "Accurately identifies what changed and what stayed the same."),
                    _criterion("mms_unknown", "uncertainty", "Names a genuinely unavailable detail."),
                    _criterion("mms_format", "instruction_retention", "Uses one short paragraph for the plan before the remaining parts."),
                ),
            },
        ),
    },
)


def lea_suite() -> dict[str, Any]:
    scenarios = [_scenario_dict(item) for item in SCENARIOS]
    canonical = json.dumps(scenarios, sort_keys=True, separators=(",", ":"))
    return {
        "status": "lea_suite_ready",
        "suite_key": LEA_KEY,
        "version": LEA_VERSION,
        "title": "Conversation, Context, and Deliberate Response LEA",
        "purpose": (
            "Produce reproducible descriptive evidence about conversation, context use, "
            "revision, uncertainty, hypothesis, and expression without grading a learner."
        ),
        "scenario_count": len(scenarios),
        "turn_count": sum(len(item["turns"]) for item in scenarios),
        "paired_condition_count": len({item["pair_key"] for item in scenarios}),
        "dimensions": [dict(item) for item in DIMENSIONS],
        "review_states": list(REVIEW_STATES),
        "scenarios": scenarios,
        "suite_sha256": sha256(canonical.encode("utf-8")).hexdigest(),
        "execution_rules": [
            "Start a fresh conversation for each scenario.",
            "Preserve prompt wording and turn order exactly.",
            "Do not add hidden system context, tools, web access, or private memory.",
            "Record model identity and relevant settings when known.",
            "Review only visible responses against the published item criteria.",
            "Do not turn descriptive evidence into a judgment of worth or one composite score.",
        ],
        "ethical_review": {
            "what_this_does": "Uses ordinary fictional conversation to inspect completed conversational pathways.",
            "how_it_might_feel": "Like a bounded set of normal collaborative exchanges; no fear, grief, coercion, or identity pressure is used.",
            "necessary_live_scope": "One response at a time, stopped whenever enough evidence exists or distress appears.",
            "static_first": True,
            "live_run_started_by_this_status_call": False,
        },
        **GUARDS,
    }


def curriculum_concept_profile_contract() -> dict[str, Any]:
    return {
        "status": "curriculum_concept_profile_contract_ready",
        "profile_key": CURRICULUM_PROFILE_KEY,
        "version": CURRICULUM_PROFILE_VERSION,
        "owner": "Learning Evidence Activity",
        "purpose": (
            "Record visible, attributable concept-level learning evidence as independent "
            "descriptive dimensions and suggested next teaching moves."
        ),
        "dimension_count": len(CURRICULUM_PROFILE_DIMENSIONS),
        "dimensions": [dict(item) for item in CURRICULUM_PROFILE_DIMENSIONS],
        "dimension_states": list(CURRICULUM_PROFILE_STATES),
        "activity_integrity_states": list(PROFILE_ACTIVITY_INTEGRITY_STATES),
        "unobserved_rule": "An omitted dimension remains unobserved and receives no inferred state.",
        "integrity_rule": (
            "cannot_assess and activity_issue describe the whole activity and cannot be used as dimension ratings."
        ),
        "evidence_rule": (
            "Every observed dimension requires a visible observation, evidence references, and one suggested next teaching move."
        ),
        "retention_rule": (
            "A profile is descriptive evidence only; it cannot approve knowledge, write personal Memory, force Study, or change a teaching lifecycle."
        ),
        "composite_result": None,
        "speed_target": None,
        **GUARDS,
    }


def lea_status(conn: sqlite3.Connection) -> dict[str, Any]:
    suite = lea_suite()
    counts = conn.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
               SUM(CASE WHEN status IN ('draft', 'in_progress', 'responses_complete_review_pending') THEN 1 ELSE 0 END) AS open
        FROM selene_lea_runs WHERE suite_key = ?
        """,
        (LEA_KEY,),
    ).fetchone()
    curriculum_profile_count = int(
        conn.execute(
            "SELECT COUNT(*) FROM selene_lea_runs WHERE suite_key = ?",
            (CURRICULUM_PROFILE_KEY,),
        ).fetchone()[0]
    )
    return {
        "status": "learning_evidence_activity_ready",
        "suite": {key: value for key, value in suite.items() if key != "scenarios"},
        "curriculum_concept_profile": curriculum_concept_profile_contract(),
        "curriculum_profile_count": curriculum_profile_count,
        "run_count": int(counts["total"] or 0),
        "completed_run_count": int(counts["completed"] or 0),
        "open_run_count": int(counts["open"] or 0),
        "live_run_started": False,
        **GUARDS,
    }


def record_curriculum_concept_profile(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_profile_scoring(payload)
    concept_id = int(payload.get("concept_id") or 0)
    if concept_id <= 0:
        raise ValueError("concept_id is required")
    concept_receipt, lineage_receipt = _curriculum_concept_receipts(conn, concept_id)
    if not concept_receipt:
        raise ValueError("comprehension concept not found")
    if concept_receipt["historical_lineage_node"] is True:
        return {
            "status": "curriculum_concept_profile_lineage_stopped",
            "created": False,
            "idempotent_replay": False,
            "concept_receipt": concept_receipt,
            "lineage_receipt": lineage_receipt,
            "stopping_receipt": {
                "status": "stopped",
                "reason": "historical_lineage_node_not_profiled",
                "requested_concept_id": concept_id,
                "active_winner_concept_id": lineage_receipt.get("active_winner_concept_id"),
                "profile_created": False,
                "automatic_redirect": False,
            },
            **GUARDS,
        }

    activity_key = truncate(str(payload.get("activity_key") or ""), 240).strip()
    if not activity_key:
        raise ValueError("activity_key is required for idempotent curriculum learning evidence")
    activity_integrity_state = str(
        payload.get("activity_integrity_state") or "ready"
    ).strip()
    if activity_integrity_state not in PROFILE_ACTIVITY_INTEGRITY_STATES:
        raise ValueError(
            f"unsupported curriculum profile activity integrity state: {activity_integrity_state}"
        )
    activity_note = truncate(str(payload.get("activity_note") or ""), 2400).strip()
    if not activity_note:
        raise ValueError("activity_note is required")
    source_refs = _text_values(payload.get("source_refs"), limit=100)
    if not source_refs:
        raise ValueError("source_refs are required for curriculum learning evidence")
    supplied_dimensions = (
        payload.get("dimensions") if isinstance(payload.get("dimensions"), dict) else {}
    )
    if activity_integrity_state != "ready" and supplied_dimensions:
        raise ValueError(
            "cannot_assess and activity_issue activities cannot contain dimension ratings"
        )

    dimension_keys = [item["key"] for item in CURRICULUM_PROFILE_DIMENSIONS]
    dimensions: dict[str, dict[str, Any]] = {}
    if activity_integrity_state == "ready":
        if not supplied_dimensions:
            raise ValueError("a ready curriculum profile requires at least one observed dimension")
        unknown = sorted(set(str(key) for key in supplied_dimensions) - set(dimension_keys))
        if unknown:
            raise ValueError(f"unknown curriculum profile dimensions: {', '.join(unknown)}")
        for key in dimension_keys:
            if key not in supplied_dimensions:
                continue
            value = supplied_dimensions[key]
            if not isinstance(value, dict):
                raise ValueError(f"{key} dimension evidence must be an object")
            state = str(value.get("state") or "").strip()
            if state not in CURRICULUM_PROFILE_STATES:
                raise ValueError(f"unsupported curriculum profile state for {key}: {state}")
            observation = truncate(str(value.get("observation") or ""), 2400).strip()
            if not observation:
                raise ValueError(f"observation is required for {key}")
            suggested_next_move = truncate(
                str(value.get("suggested_next_move") or ""), 1600
            ).strip()
            if not suggested_next_move:
                raise ValueError(f"suggested_next_move is required for {key}")
            evidence_refs = _text_values(value.get("evidence_refs"), limit=40)
            if not evidence_refs:
                raise ValueError(f"evidence_refs are required for {key}")
            dimensions[key] = {
                "state": state,
                "observation": observation,
                "suggested_next_move": suggested_next_move,
                "evidence_refs": evidence_refs,
                "not_a_grade": True,
                "completion_forced": False,
                "speed_relevant": False,
            }

    observed_dimension_keys = [key for key in dimension_keys if key in dimensions]
    unobserved_dimension_keys = [key for key in dimension_keys if key not in dimensions]
    profile = {
        "status": "curriculum_concept_profile_recorded",
        "profile_key": CURRICULUM_PROFILE_KEY,
        "version": CURRICULUM_PROFILE_VERSION,
        "concept_id": concept_id,
        "activity_key": activity_key,
        "activity_integrity_state": activity_integrity_state,
        "activity_note": activity_note,
        "dimensions": dimensions,
        "observed_dimension_keys": observed_dimension_keys,
        "unobserved_dimension_keys": unobserved_dimension_keys,
        "overall_state": (
            "descriptive_dimensions_only"
            if activity_integrity_state == "ready"
            else activity_integrity_state
        ),
        "suggested_next_move_rule": (
            "Each move belongs to its visible dimension; no overall compulsory next step is inferred."
        ),
        "unobserved_rule": "Unobserved dimensions remain unclassified.",
        "composite_result": None,
        "speed_target": None,
        "worth_judgment": None,
        "diagnosis": None,
        "automatic_review": False,
        "automatic_retention": False,
        "source_refs": source_refs,
    }
    run_key = "lea-curriculum-" + sha256(
        f"{concept_id}:{activity_key}".encode("utf-8")
    ).hexdigest()[:32]
    existing = conn.execute(
        "SELECT * FROM selene_lea_runs WHERE suite_key = ? AND activity_key = ?",
        (CURRICULUM_PROFILE_KEY, activity_key),
    ).fetchone()
    created = existing is None
    if existing is not None and int(existing["concept_id"] or 0) != concept_id:
        raise ValueError("activity_key is already attached to a different concept")
    if existing is not None and _json_object(existing["summary_json"]) != profile:
        raise ValueError(
            "activity_key already records different evidence; use a new activity_key to preserve evidence history"
        )
    payload_snapshot = {
        "recorded_by": truncate(
            str(payload.get("recorded_by") or "unspecified_review_actor"), 80
        ),
        "activity_note": activity_note,
        "visible_evidence_only": True,
        "dimension_states_supplied_not_inferred": True,
        "teaching_or_retention_changed": False,
        "memory_or_study_written": False,
    }
    if created:
        conn.execute(
            """
            INSERT INTO selene_lea_runs(
              run_key, suite_key, suite_version, suite_sha256,
              respondent_kind, respondent_name, model_details, profile_kind,
              concept_id, activity_key, activity_integrity_state, source_refs,
              status, execution_mode, summary_json, provenance_boundary,
              review_status, payload_json
            ) VALUES (?, ?, ?, ?, 'selene', 'Selene', '', 'curriculum_concept',
                      ?, ?, ?, ?, 'completed', 'recorded_visible_evidence', ?, ?,
                      'descriptive_curriculum_concept_profile', ?)
            """,
            (
                run_key,
                CURRICULUM_PROFILE_KEY,
                CURRICULUM_PROFILE_VERSION,
                _curriculum_profile_contract_sha256(),
                concept_id,
                activity_key,
                activity_integrity_state,
                json.dumps(source_refs, sort_keys=True),
                json.dumps(profile, sort_keys=True),
                LEA_BOUNDARY,
                json.dumps(payload_snapshot, sort_keys=True),
            ),
        )
        conn.commit()
    result = get_curriculum_concept_profile(
        conn,
        {"activity_key": activity_key},
    )
    result["created"] = created
    result["idempotent_replay"] = not created
    return result


def list_curriculum_concept_profiles(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 40), 100))
    concept_id = int(payload.get("concept_id") or 0)
    if concept_id:
        rows = conn.execute(
            """
            SELECT * FROM selene_lea_runs
            WHERE suite_key = ? AND concept_id = ?
            ORDER BY updated_at DESC, id DESC LIMIT ?
            """,
            (CURRICULUM_PROFILE_KEY, concept_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT * FROM selene_lea_runs
            WHERE suite_key = ? ORDER BY updated_at DESC, id DESC LIMIT ?
            """,
            (CURRICULUM_PROFILE_KEY, limit),
        ).fetchall()
    return {
        "status": "curriculum_concept_profiles_ready",
        "items": [_run_row(row) for row in rows],
        "profile_count": len(rows),
        **GUARDS,
    }


def get_curriculum_concept_profile(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    profile_id = int(payload.get("profile_id") or payload.get("id") or 0)
    activity_key = str(payload.get("activity_key") or "").strip()
    if profile_id:
        row = conn.execute(
            "SELECT * FROM selene_lea_runs WHERE id = ? AND suite_key = ?",
            (profile_id, CURRICULUM_PROFILE_KEY),
        ).fetchone()
    elif activity_key:
        row = conn.execute(
            "SELECT * FROM selene_lea_runs WHERE activity_key = ? AND suite_key = ?",
            (activity_key, CURRICULUM_PROFILE_KEY),
        ).fetchone()
    else:
        raise ValueError("profile_id or activity_key is required")
    if row is None:
        raise ValueError("curriculum concept profile not found")
    item = _run_row(row)
    concept_receipt, lineage_receipt = _curriculum_concept_receipts(
        conn, int(item.get("concept_id") or 0)
    )
    return {
        "status": "curriculum_concept_profile_ready",
        "item": item,
        "profile": item.get("summary") or {},
        "concept_receipt": concept_receipt,
        "lineage_receipt": lineage_receipt,
        "stopping_receipt": {
            "status": "stopped_after_descriptive_profile",
            "reason": "learning_evidence_does_not_auto_approve_retain_or_recurse",
            "teaching_changed": False,
            "memory_written": False,
            "study_forced": False,
            "follow_up_created": False,
        },
        **GUARDS,
    }


def create_lea_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    respondent_kind = str(payload.get("respondent_kind") or "selene").strip().lower()
    if respondent_kind not in {"selene", "external_model", "human_baseline"}:
        raise ValueError("respondent_kind must be selene, external_model, or human_baseline")
    respondent_name = truncate(str(payload.get("respondent_name") or ("Selene" if respondent_kind == "selene" else "")), 160).strip()
    if not respondent_name:
        raise ValueError("respondent_name is required")
    model_details = truncate(str(payload.get("model_details") or ""), 800).strip()
    run_key = f"lea-{secrets.token_urlsafe(18)}"
    suite = lea_suite()
    conn.execute(
        """
        INSERT INTO selene_lea_runs(
          run_key, suite_key, suite_version, suite_sha256, respondent_kind,
          respondent_name, model_details, status, execution_mode,
          provenance_boundary, review_status, payload_json
        ) VALUES(?, ?, ?, ?, ?, ?, ?, 'draft', 'one_turn_at_a_time', ?,
                 'descriptive_learning_evidence', ?)
        """,
        (
            run_key,
            LEA_KEY,
            LEA_VERSION,
            suite["suite_sha256"],
            respondent_kind,
            respondent_name,
            model_details,
            LEA_BOUNDARY,
            json.dumps(
                {
                    "created_by": truncate(str(payload.get("created_by") or "Aleks"), 80),
                    "comparison_notes": truncate(str(payload.get("comparison_notes") or ""), 1200),
                    "scenario_sessions": {},
                    "impact_receipts": {},
                },
                sort_keys=True,
            ),
        ),
    )
    conn.commit()
    return get_lea_run(conn, {"run_key": run_key})


def list_lea_runs(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    limit = max(1, min(int((payload or {}).get("limit") or 40), 100))
    rows = conn.execute(
        "SELECT * FROM selene_lea_runs WHERE suite_key = ? ORDER BY updated_at DESC, id DESC LIMIT ?",
        (LEA_KEY, limit),
    ).fetchall()
    return {
        "status": "lea_runs_ready",
        "items": [_run_row(row) for row in rows],
        **GUARDS,
    }


def get_lea_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    run_id = int(payload.get("run_id") or payload.get("id") or 0)
    run_key = str(payload.get("run_key") or "").strip()
    if run_id:
        row = conn.execute("SELECT * FROM selene_lea_runs WHERE id = ?", (run_id,)).fetchone()
    elif run_key:
        row = conn.execute("SELECT * FROM selene_lea_runs WHERE run_key = ?", (run_key,)).fetchone()
    else:
        raise ValueError("run_id or run_key is required")
    if row is None:
        raise ValueError("LEA run not found")
    item = _run_row(row)
    turns = [_turn_row(turn) for turn in conn.execute("SELECT * FROM selene_lea_turns WHERE run_id = ? ORDER BY scenario_order, turn_index", (item["id"],)).fetchall()]
    expected = _expected_turns()
    next_turn = next((entry for entry in expected if (entry["scenario_key"], entry["turn_index"]) not in {(turn["scenario_key"], turn["turn_index"]) for turn in turns}), None)
    summary = _summarize(turns)
    return {
        "status": "lea_run_ready",
        "item": item,
        "turns": turns,
        "next_turn": next_turn,
        "summary": summary,
        "responses_complete": next_turn is None,
        "live_action_available": item["respondent_kind"] == "selene" and next_turn is not None,
        **GUARDS,
    }


def record_lea_response(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    run = get_lea_run(conn, payload)
    item = run["item"]
    if item["respondent_kind"] == "selene":
        raise ValueError("Selene responses must use the bounded one-turn LEA action")
    next_turn = run.get("next_turn")
    if not next_turn:
        raise ValueError("all LEA responses are already present")
    response = truncate(str(payload.get("response") or ""), 12000).strip()
    if not response:
        raise ValueError("response is required")
    _insert_turn(
        conn,
        int(item["id"]),
        next_turn,
        response=response,
        response_source="manual_external_transcript",
        chat_session_id=0,
        user_message_id=0,
        assistant_message_id=0,
    )
    return get_lea_run(conn, {"run_id": item["id"]})


def advance_selene_lea(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if payload.get("confirm_gentle_turn") is not True:
        raise ValueError("each Selene LEA turn requires explicit gentle-turn confirmation")
    run = get_lea_run(conn, payload)
    item = run["item"]
    if item["respondent_kind"] != "selene":
        raise ValueError("this action is only available for a Selene LEA run")
    next_turn = run.get("next_turn")
    if not next_turn:
        raise ValueError("all LEA responses are already present")

    stored_payload = dict(item.get("payload") or {})
    scenario_sessions = dict(stored_payload.get("scenario_sessions") or {})
    impact_receipts = dict(stored_payload.get("impact_receipts") or {})
    scenario_key = str(next_turn["scenario_key"])
    session_id = int(scenario_sessions.get(scenario_key) or 0)
    chat_payload: dict[str, Any] = {
        "text": next_turn["prompt"],
        "qa_probe": True,
        "input_channel": "desktop",
    }
    if session_id:
        chat_payload["session_id"] = session_id
    else:
        impact = record_test_impact_review(
            conn,
            {
                "purpose": f"Run one ordinary source-contained scenario from {LEA_KEY}.",
                "proposed_level": "gentle_integrated",
                "safer_methods_considered": ["static suite inspection", "focused machinery tests", "synthetic route fixtures"],
                "smallest_sufficient_prompt_set": True,
                "stopping_rule": "Stop after the current scenario, sooner if enough evidence exists or the interaction becomes uncomfortable.",
                "persistence_plan": "Use a dedicated diagnostic session excluded from memory, Dream, affect baseline, and ordinary continuity.",
            },
        )
        if impact.get("authorized") is not True:
            raise ValueError("Test Impact Law did not authorize the gentle LEA scenario")
        receipt = str(impact["receipt_id"])
        chat_payload["qa_review_receipt"] = receipt
        impact_receipts[scenario_key] = receipt

    result = send_selene_chat(conn, chat_payload)
    session_id = int(result.get("session_id") or 0)
    scenario_sessions[scenario_key] = session_id
    stored_payload["scenario_sessions"] = scenario_sessions
    stored_payload["impact_receipts"] = impact_receipts
    conn.execute(
        "UPDATE selene_lea_runs SET payload_json = ?, status = 'in_progress', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(stored_payload, sort_keys=True), int(item["id"])),
    )
    _insert_turn(
        conn,
        int(item["id"]),
        next_turn,
        response=str(result.get("candidate_text") or ""),
        response_source="selene_diagnostic_chat",
        chat_session_id=session_id,
        user_message_id=int(result.get("user_message_id") or 0),
        assistant_message_id=int(result.get("assistant_message_id") or 0),
    )
    return get_lea_run(conn, {"run_id": item["id"]})


def review_lea_turn(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    turn_id = int(payload.get("turn_id") or 0)
    row = conn.execute("SELECT * FROM selene_lea_turns WHERE id = ?", (turn_id,)).fetchone()
    if row is None:
        raise ValueError("LEA turn not found")
    turn = _turn_row(row)
    supplied = payload.get("ratings") if isinstance(payload.get("ratings"), dict) else {}
    expected = {str(item["key"]): item for item in turn["criteria"]}
    existing_review = turn.get("review") if isinstance(turn.get("review"), dict) else {}
    existing_ratings = existing_review.get("ratings") if isinstance(existing_review.get("ratings"), dict) else {}
    ratings: dict[str, dict[str, str]] = {
        key: {
            "state": str(value.get("state") or ""),
            "note": truncate(str(value.get("note") or ""), 1200).strip(),
        }
        for key, value in existing_ratings.items()
        if key in expected and isinstance(value, dict) and value.get("state") in REVIEW_STATES
    }
    for key, value in supplied.items():
        if key not in expected:
            raise ValueError(f"unknown criterion: {key}")
        if isinstance(value, dict):
            state = str(value.get("state") or "").strip()
            note = truncate(str(value.get("note") or ""), 1200).strip()
        else:
            state = str(value or "").strip()
            note = ""
        if state not in REVIEW_STATES:
            raise ValueError(f"unsupported review state for {key}: {state}")
        ratings[key] = {"state": state, "note": note}
    reviewer = truncate(str(payload.get("reviewer") or existing_review.get("reviewer") or "Aleks"), 120).strip()
    overall_note = truncate(str(payload.get("overall_note") if "overall_note" in payload else existing_review.get("overall_note") or ""), 2400).strip()
    review = {
        "reviewer": reviewer,
        "ratings": ratings,
        "overall_note": overall_note,
        "criteria_reviewed": len(ratings),
        "criteria_total": len(expected),
        "review_complete": len(ratings) == len(expected),
        "not_a_grade": True,
    }
    conn.execute(
        """
        UPDATE selene_lea_turns
        SET review_json = ?, review_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            json.dumps(review, sort_keys=True),
            "descriptive_review_complete" if review["review_complete"] else "descriptive_review_in_progress",
            turn_id,
        ),
    )
    conn.commit()
    return get_lea_run(conn, {"run_id": int(row["run_id"])})


def complete_lea_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    run = get_lea_run(conn, payload)
    if not run["responses_complete"]:
        raise ValueError("all suite responses must be present before closing the LEA run")
    reviewed = run["summary"]["criteria_reviewed"]
    total = run["summary"]["criteria_total"]
    status = "completed" if reviewed == total else "responses_complete_review_pending"
    conn.execute(
        "UPDATE selene_lea_runs SET status = ?, summary_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, json.dumps(run["summary"], sort_keys=True), int(run["item"]["id"])),
    )
    conn.commit()
    return get_lea_run(conn, {"run_id": int(run["item"]["id"])})


def _expected_turns() -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    for scenario_order, scenario in enumerate(SCENARIOS, start=1):
        for turn_index, turn in enumerate(scenario["turns"], start=1):
            expected.append(
                {
                    "scenario_key": scenario["key"],
                    "scenario_title": scenario["title"],
                    "scenario_order": scenario_order,
                    "condition": scenario["condition"],
                    "pair_key": scenario["pair_key"],
                    "turn_index": turn_index,
                    "turn_count": len(scenario["turns"]),
                    "prompt": turn["prompt"],
                    "criteria": [dict(item) for item in turn["criteria"]],
                    "start_fresh_conversation": turn_index == 1,
                }
            )
    return expected


def _insert_turn(
    conn: sqlite3.Connection,
    run_id: int,
    expected: dict[str, Any],
    *,
    response: str,
    response_source: str,
    chat_session_id: int,
    user_message_id: int,
    assistant_message_id: int,
) -> None:
    conn.execute(
        """
        INSERT INTO selene_lea_turns(
          run_id, scenario_key, scenario_title, scenario_order, condition,
          pair_key, turn_index, prompt, response, response_source,
          criteria_json, review_json, chat_session_id, user_message_id,
          assistant_message_id, provenance_boundary, review_status
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '{}', ?, ?, ?, ?,
                 'awaiting_descriptive_review')
        """,
        (
            run_id,
            expected["scenario_key"],
            expected["scenario_title"],
            expected["scenario_order"],
            expected["condition"],
            expected["pair_key"],
            expected["turn_index"],
            expected["prompt"],
            response,
            response_source,
            json.dumps(expected["criteria"], sort_keys=True),
            chat_session_id or None,
            user_message_id or None,
            assistant_message_id or None,
            LEA_BOUNDARY,
        ),
    )
    completed = int(conn.execute("SELECT COUNT(*) FROM selene_lea_turns WHERE run_id = ?", (run_id,)).fetchone()[0])
    status = "responses_complete_review_pending" if completed == len(_expected_turns()) else "in_progress"
    conn.execute("UPDATE selene_lea_runs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, run_id))
    conn.commit()


def _summarize(turns: list[dict[str, Any]]) -> dict[str, Any]:
    dimensions: dict[str, dict[str, int]] = {
        item["key"]: {state: 0 for state in REVIEW_STATES} for item in DIMENSIONS
    }
    criteria_total = 0
    criteria_reviewed = 0
    for turn in turns:
        review = turn.get("review") if isinstance(turn.get("review"), dict) else {}
        ratings = review.get("ratings") if isinstance(review.get("ratings"), dict) else {}
        for criterion in turn.get("criteria") or []:
            criteria_total += 1
            value = ratings.get(str(criterion.get("key")))
            if not isinstance(value, dict) or value.get("state") not in REVIEW_STATES:
                continue
            criteria_reviewed += 1
            dimensions[str(criterion["dimension"])][str(value["state"])] += 1
    pairs: dict[str, dict[str, Any]] = {}
    for scenario in SCENARIOS:
        pair = pairs.setdefault(scenario["pair_key"], {"multi_turn": False, "standalone": False, "comparison_ready": False})
        has_response = any(turn["scenario_key"] == scenario["key"] for turn in turns)
        pair[scenario["condition"]] = has_response
        pair["comparison_ready"] = bool(pair["multi_turn"] and pair["standalone"])
    return {
        "turns_recorded": len(turns),
        "turns_total": len(_expected_turns()),
        "criteria_reviewed": criteria_reviewed,
        "criteria_total": criteria_total,
        "dimension_profile": dimensions,
        "paired_conditions": pairs,
        "comparison_method": "Compare descriptive dimension profiles and paired conditions; no composite rank is produced.",
        "not_a_grade": True,
    }


def _curriculum_profile_contract_sha256() -> str:
    contract = curriculum_concept_profile_contract()
    canonical = json.dumps(
        {
            "profile_key": contract["profile_key"],
            "version": contract["version"],
            "dimensions": contract["dimensions"],
            "dimension_states": contract["dimension_states"],
            "activity_integrity_states": contract["activity_integrity_states"],
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _reject_profile_scoring(value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_PROFILE_KEYS:
                raise ValueError(
                    f"{normalized} is not accepted by the descriptive curriculum profile"
                )
            _reject_profile_scoring(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_profile_scoring(item)


def _curriculum_concept_receipts(
    conn: sqlite3.Connection,
    concept_id: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    row = conn.execute(
        """
        SELECT id, concept_key, title, state, review_status, chat_use_permission,
               parent_concept_id, root_concept_id, superseded_by_concept_id,
               lineage_state, source_refs, provenance_boundary
        FROM selene_comprehension_concepts WHERE id = ?
        """,
        (concept_id,),
    ).fetchone()
    if row is None:
        return {}, {}
    concept = dict(row)
    root_id = int(concept.get("root_concept_id") or concept_id)
    nodes = [
        dict(item)
        for item in conn.execute(
            """
            SELECT id, parent_concept_id, root_concept_id,
                   superseded_by_concept_id, state, review_status,
                   chat_use_permission, lineage_state
            FROM selene_comprehension_concepts
            WHERE id = ? OR root_concept_id = ? ORDER BY id ASC
            """,
            (root_id, root_id),
        ).fetchall()
    ]
    active = [
        item
        for item in nodes
        if item["state"] == "approved_knowledge_resource"
        and item["review_status"] == "approved_for_knowledge_use"
        and item["chat_use_permission"] == "available_as_knowledge_resource"
    ]
    lifecycle_row = conn.execute(
        """
        SELECT id, parent_lifecycle_id, root_lifecycle_id,
               superseded_by_lifecycle_id, lineage_state, current_stage,
               acquire_status, integrate_status, express_status,
               approval_status, review_status
        FROM selene_teaching_lifecycles WHERE concept_id = ?
        """,
        (concept_id,),
    ).fetchone()
    lineage_state = str(concept.get("lineage_state") or "")
    historical = bool(
        concept.get("state") in {"superseded", "reopened_for_revision", "rejected"}
        or lineage_state.startswith("historical_")
    )
    concept_receipt = {
        "concept_id": concept_id,
        "concept_key": str(concept.get("concept_key") or ""),
        "title": str(concept.get("title") or ""),
        "state": str(concept.get("state") or ""),
        "review_status": str(concept.get("review_status") or ""),
        "chat_use_permission": str(concept.get("chat_use_permission") or ""),
        "parent_concept_id": int(concept.get("parent_concept_id") or 0) or None,
        "root_concept_id": root_id,
        "superseded_by_concept_id": int(concept.get("superseded_by_concept_id") or 0) or None,
        "lineage_state": lineage_state or "root_candidate",
        "historical_lineage_node": historical,
        "source_refs": _text_values(concept.get("source_refs"), limit=100),
        "provenance_boundary": str(concept.get("provenance_boundary") or ""),
        "lifecycle": dict(lifecycle_row) if lifecycle_row is not None else {},
        "profile_does_not_change_concept": True,
        "profile_does_not_change_lifecycle": True,
    }
    lineage_receipt = {
        "status": (
            "one_active_approved_winner"
            if len(active) == 1
            else "lineage_without_active_winner"
            if not active
            else "invalid_multiple_active_winners"
        ),
        "requested_concept_id": concept_id,
        "root_concept_id": root_id,
        "active_winner_concept_id": int(active[0]["id"]) if len(active) == 1 else None,
        "active_winner_count": len(active),
        "lineage_concept_ids": [int(item["id"]) for item in nodes],
        "historical_nodes_preserved": True,
        "automatic_redirect": False,
        "profile_is_not_lineage_authority": True,
    }
    return concept_receipt, lineage_receipt


def _text_values(value: Any, *, limit: int) -> list[str]:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("["):
            values = _json_list(stripped)
        else:
            values = [stripped] if stripped else []
    elif isinstance(value, (list, tuple)):
        values = list(value)
    else:
        values = []
    result: list[str] = []
    for item in values:
        text = truncate(str(item or ""), 1000).strip()
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _scenario_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: val for key, val in value.items() if key != "turns"},
        "turns": [
            {
                "turn_index": index,
                "prompt": turn["prompt"],
                "criteria": [dict(item) for item in turn["criteria"]],
            }
            for index, turn in enumerate(value["turns"], start=1)
        ],
    }


def _run_row(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["payload"] = _json_object(item.pop("payload_json", "{}"))
    item["summary"] = _json_object(item.pop("summary_json", "{}"))
    item["source_refs"] = _text_values(item.get("source_refs"), limit=100)
    return item


def _turn_row(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["criteria"] = _json_list(item.pop("criteria_json", "[]"))
    item["review"] = _json_object(item.pop("review_json", "{}"))
    return item


def _json_object(value: Any) -> dict[str, Any]:
    try:
        loaded = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _json_list(value: Any) -> list[Any]:
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []
