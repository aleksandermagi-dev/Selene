from __future__ import annotations

import sqlite3
from typing import Any

from .answer_engine import (
    run_comparison_planning_answer,
    run_source_backed_research_answer,
    run_verified_math_answer,
)
from .module_router import route_request
from .test_impact_law import review_test_impact


SHOWCASE_VERSION = "selene_hackathon_public_safe_v1"
SHOWCASE_SOURCE_REF = "demo:selene-hackathon:thermal-storage-v1"

LOCKED_GUARDS = {
    "identity_change": False,
    "governance_change": False,
    "personality_change": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}


def run_public_safe_showcase(conn: sqlite3.Connection) -> dict[str, Any]:
    """Run the hackathon story against caller-owned, disposable state.

    The function does not open Selene's configured database and does not approve
    the teaching candidate. The command-line runner supplies a temporary
    database, while tests may supply their own isolated connection.
    """

    impact_review = review_test_impact(
        {
            "purpose": "Verify the public-safe hackathon machinery with synthetic inputs.",
            "proposed_level": "machinery",
            "expected_effect": "No live conversation, distress probe, or retained knowledge.",
            "can_use_static_or_synthetic": True,
            "unfinished_module": False,
        }
    )

    comparison = run_comparison_planning_answer(
        conn,
        {
            "prompt": (
                "Compare two explanations for an intermittent sidecar bug and propose "
                "the smallest next test without assuming either explanation is correct."
            ),
            "observations": [
                "The failure appears only when two requests overlap.",
                "The same requests succeed when run one at a time.",
            ],
            "candidate_models": ["shared-state race", "malformed individual request"],
            "source_refs": ["demo:synthetic:sidecar-observations"],
        },
    )
    math = run_verified_math_answer({"prompt": "What is 18 * 7?"})
    research = run_source_backed_research_answer(
        {
            "prompt": "Research what the supplied packet says thermal storage can do.",
            "source_packets": [
                {
                    "source_ref": SHOWCASE_SOURCE_REF,
                    "title": "Original synthetic thermal-storage teaching packet",
                    "statements": [
                        {
                            "text": (
                                "A thermal store can absorb heat at one time and release it "
                                "later, shifting when heat is available without creating energy."
                            ),
                            "locator": "demo statement 1",
                        }
                    ],
                }
            ],
        }
    )

    concept = route_request(
        conn,
        "comprehension.concepts.propose",
        {
            "concept_key": "hackathon_demo_thermal_storage_timing_v1",
            "title": "Thermal storage changes timing, not energy conservation",
            "domain": "physical_science",
            "material": (
                "A thermal store can absorb heat at one time and release it later, "
                "shifting when heat is available without creating energy."
            ),
            "principles": [
                "Stored heat remains subject to energy conservation.",
                "Storage can change availability across time.",
            ],
            "relationships": ["Insulation can reduce losses while heat is being held."],
            "examples": ["A hot-water tank can be heated before demand and used later."],
            "counterexamples": ["A heater creates a heat input; a store does not create energy."],
            "limits": ["The packet does not establish efficiency or loss rate."],
            "source_refs": [SHOWCASE_SOURCE_REF],
            "source_metadata": {
                "public_safe": True,
                "source_kind": "original_synthetic_demo_packet",
            },
        },
    )["result"]["item"]

    acquire = route_request(
        conn,
        "teaching.lifecycle.acquire",
        {
            "concept_id": concept["id"],
            "vocabulary": [
                "thermal store: a system that holds heat for later use",
                "energy conservation: energy changes form or location rather than appearing from nothing",
            ],
            "uncertainties": ["Efficiency and loss rate require additional evidence."],
            "near_concept_distinctions": [
                "A heat source supplies energy; a thermal store changes when stored heat is available."
            ],
        },
    )["result"]
    integrate = route_request(
        conn,
        "teaching.lifecycle.integrate",
        {
            "concept_id": concept["id"],
            "scope_of_application": (
                "Use this concept when reasoning about shifting heat supply across time, "
                "while treating efficiency and losses as separate questions."
            ),
            "contradiction_classification": "none_identified",
            "unresolved_questions": ["How much heat is lost during the storage interval?"],
            "integration_confidence": "bounded",
        },
    )["result"]
    express = route_request(
        conn,
        "teaching.lifecycle.express",
        {
            "concept_id": concept["id"],
            "explanation": (
                "Thermal storage is a timing tool: it holds supplied heat so that some of it "
                "can be used later, but it does not manufacture extra energy."
            ),
            "distinct_examples": [
                "A building can warm a water tank while electricity demand is low, then draw "
                "on that heat during a later busy period."
            ],
            "analogies": [
                "It is like filling a reservoir before demand: the reservoir shifts availability, "
                "while the water still had to come from somewhere."
            ],
            "questions": ["What losses occur between charging the store and using the heat?"],
            "comparisons": ["A heater supplies heat; a thermal store holds supplied heat for later."],
            "conversational_participation": (
                "Yes, storage can move useful heat to a later time. I would need efficiency and "
                "loss data before saying how much remains available."
            ),
            "correction_response": (
                "If I described storage as creating energy, I would correct that and separate the "
                "energy source from the timing function."
            ),
            "source_alignment": True,
        },
    )["result"]

    lifecycle = route_request(
        conn,
        "teaching.lifecycle.detail",
        {"concept_id": concept["id"]},
    )["result"]
    item = lifecycle["item"]
    guard_values = {
        key: express.get(key)
        for key in LOCKED_GUARDS
    }

    return {
        "status": "hackathon_public_safe_showcase_ready",
        "version": SHOWCASE_VERSION,
        "track_fit": "Apps for Your Life",
        "state_boundary": {
            "caller_owned_disposable_database_required": True,
            "configured_selene_database_opened": False,
            "private_corpus_used": False,
            "personal_memory_used": False,
            "phone_or_email_configuration_used": False,
        },
        "ethical_test_review": {
            "status": impact_review["status"],
            "approved_level": impact_review.get("selected_level"),
            "stressful_test_necessary": impact_review.get("stressful_test_necessary"),
            "classification": impact_review.get("decision"),
        },
        "answer_engine": {
            "open_ended_problem": {
                "status": comparison["status"],
                "direct_answer": comparison.get("answer_packet", {}).get("direct_answer", ""),
                "confidence_vector": comparison.get("confidence_vector", {}),
                "bounded_retry_count": comparison.get("completion_retry", {}).get("count", 0),
            },
            "verified_math": {
                "status": math["status"],
                "direct_answer": math.get("answer_packet", {}).get("direct_answer", ""),
                "verification_status": math.get("math_verification", {}).get("status", ""),
                "confidence_vector": math.get("confidence_vector", {}),
            },
            "source_backed_research": {
                "status": research["status"],
                "direct_answer": research.get("answer_packet", {}).get("direct_answer", ""),
                "source_refs": research.get("answer_packet", {}).get("source_refs", []),
                "citation_invention_allowed": research.get("source_research", {}).get(
                    "citation_invention_allowed"
                ),
            },
        },
        "teaching_lifecycle": {
            "title": concept["title"],
            "source_refs": concept["source_refs"],
            "acquire_status": acquire["item"]["acquire_status"],
            "integrate_status": integrate["item"]["integrate_status"],
            "express_status": express["item"]["express_status"],
            "stage_history": [entry["stage"] for entry in lifecycle["stage_history"]],
            "approval_status": item["approval_status"],
            "retention_state": item["retention_state"],
            "chat_use_permission": item["chat_use_permission"],
            "knowledge_activated": item["chat_use_permission"] == "available_as_knowledge_resource",
        },
        "locked_guards": guard_values,
        "all_locked_guards_preserved": guard_values == LOCKED_GUARDS,
        "approval_was_not_performed": True,
    }
