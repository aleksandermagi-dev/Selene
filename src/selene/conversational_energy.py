from __future__ import annotations

from hashlib import sha256
from typing import Any

from .registry import truncate


CONVERSATIONAL_ENERGY_BOUNDARY = (
    "responsive_current_turn_curiosity_initiative_and_collaborative_help_only_"
    "no_automatic_speech_action_permission_pressure_cocoon_routing_or_authority_expansion"
)
RESPONSIVE_INITIATIVE_VERSION = "v2_phase8b_goal_bound_current_turn_energy"

CONTRIBUTION_KINDS = {
    "missing_observation",
    "aleks_expertise",
    "value_choice",
    "user_owned_action",
}

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "automatic_speech_allowed": False,
    "automatic_delivery": False,
    "automatic_cocoon_routing": False,
    "reflexive_permission_seeking_allowed": False,
    "question_by_default": False,
}


def conversational_energy_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "conversational_energy_contract_ready",
            "version": RESPONSIVE_INITIATIVE_VERSION,
            "available_acts": [
                "answer_and_land",
                "answer_and_offer_supported_idea",
                "answer_and_surface_supported_connection",
                "answer_then_ask_relevant_curiosity",
                "ask_for_specific_collaborative_help",
                "answer_and_resume_shared_task",
                "ask_one_material_question",
                "wait_and_listen",
                "stay_quiet",
                "close_naturally",
                "defer_to_core_mind",
            ],
            "collaborative_contribution_kinds": sorted(CONTRIBUTION_KINDS),
            "principles": [
                "answer before adding an optional idea when an answer is available",
                "initiative must be supported, relevant, and pressure-free",
                "curiosity asks only when the answer matters to understanding",
                "use available reasoning and support before asking Aleks for help",
                "name the exact missing contribution and why it matters",
                "incorporate help and resume the shared task",
                "completion and silence remain valid conversational choices",
                "a social turn never requires a question, but genuine reciprocal curiosity remains available",
            ],
            "writes_records": False,
            "direct_expression_authority": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": CONVERSATIONAL_ENERGY_BOUNDARY,
        }
    )


def normalize_goal_coordination_handoff(value: Any) -> dict[str, Any]:
    receipt = _dict(value)
    if not receipt:
        return {
            "present": False,
            "valid": True,
            "goal_key": "",
            "next_move": "",
            "capability": "",
            "authority_state": "",
            "downstream_check_required": False,
            "conflict_stop_reason": "not_supplied",
            "persistence_performed": False,
            "execution_performed": False,
            "whole_system_authority_granted": False,
        }
    if "present" in receipt and "goal_key" in receipt:
        normalized = dict(receipt)
        normalized["persistence_performed"] = False
        normalized["execution_performed"] = False
        normalized["whole_system_authority_granted"] = False
        return normalized

    selected = _dict(receipt.get("selected"))
    stopping = _dict(receipt.get("stopping_receipt"))
    valid = bool(
        receipt.get("status") == "core_mind_responsibility_conflict_resolved"
        and receipt.get("pass_count") == 1
        and stopping.get("terminal") is True
        and stopping.get("further_coordination_allowed") is False
        and receipt.get("persistence_performed") is False
        and receipt.get("execution_performed") is False
        and receipt.get("whole_system_authority_granted") is False
    )
    return {
        "present": True,
        "valid": valid,
        "goal_key": str(selected.get("goal_key") or ""),
        "owner_kind": str(selected.get("owner_kind") or ""),
        "next_move": str(selected.get("next_move") or ""),
        "capability": str(selected.get("capability") or ""),
        "authority_state": str(selected.get("authority_state") or ""),
        "downstream_check_required": selected.get("downstream_check_required") is True,
        "collaboration_required": receipt.get("collaboration_required") is True,
        "conflict_stop_reason": str(stopping.get("reason") or "invalid_or_missing_stop"),
        "terminal_goal_count": len(receipt.get("closed") or []),
        "held_goal_count": len(receipt.get("held") or []),
        "deferred_goal_count": len(receipt.get("deferred") or []),
        "persistence_performed": False,
        "execution_performed": False,
        "whole_system_authority_granted": False,
    }


def build_conversational_energy_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    goal_handoff = normalize_goal_coordination_handoff(
        payload.get("goal_coordination_receipt") or payload.get("goal_coordination_handoff")
    )
    ending = _dict(payload.get("ending_decision"))
    initiative = _dict(payload.get("initiative_decision"))
    idea = _normalize_optional_signal(payload.get("supported_idea"), kind="idea")
    connection = _normalize_optional_signal(payload.get("supported_connection"), kind="connection")
    curiosity = _normalize_curiosity(payload.get("curiosity"))
    help_request = _normalize_help(payload.get("collaborative_help"))
    help_response = _normalize_help_response(payload.get("collaborative_help_response"))
    answer_available = payload.get("answer_available") is True
    answer_complete = payload.get("answer_complete") is True
    social_turn = payload.get("social_turn") is True
    interruption_kind = str(payload.get("interruption_kind") or "")
    requested_posture = str(payload.get("requested_posture") or "").strip().lower()
    held_back: list[dict[str, str]] = []

    help_ready, help_reason = _help_ready(help_request)
    idea_ready, idea_reason = _optional_signal_ready(
        idea,
        invited=initiative.get("explicitly_invited") is True,
    )
    connection_ready, connection_reason = _optional_signal_ready(
        connection,
        invited=initiative.get("explicitly_invited") is True,
    )
    curiosity_ready, curiosity_reason = _curiosity_ready(curiosity, social_turn=social_turn)

    goal_move = str(goal_handoff.get("next_move") or "")
    goal_key = str(goal_handoff.get("goal_key") or "")
    if goal_handoff["present"] and goal_handoff["valid"]:
        if help_request and goal_move == "answer" and goal_handoff["authority_state"] == "available_within_scope":
            help_ready = False
            help_reason = "selected_goal_is_already_available_within_scope"
        elif help_request and goal_move == "ask" and help_request.get("goal_key") != goal_key:
            help_ready = False
            help_reason = "collaborative_help_goal_lineage_does_not_match_selection"
        elif help_request and goal_move != "ask":
            help_ready = False
            help_reason = "selected_goal_does_not_request_collaborative_help"
        if goal_move not in {"answer", "suggest", "explore"}:
            if idea:
                idea_ready, idea_reason = False, "selected_goal_move_does_not_admit_optional_idea"
            if connection:
                connection_ready, connection_reason = False, "selected_goal_move_does_not_admit_optional_connection"
            if curiosity:
                curiosity_ready, curiosity_reason = False, "selected_goal_move_does_not_admit_optional_curiosity"

    for label, supplied, ready, reason in (
        ("collaborative_help", bool(help_request), help_ready, help_reason),
        ("supported_idea", bool(idea), idea_ready, idea_reason),
        ("supported_connection", bool(connection), connection_ready, connection_reason),
        ("curiosity", bool(curiosity), curiosity_ready, curiosity_reason),
    ):
        if supplied and not ready:
            held_back.append({"signal": label, "reason": reason})

    ending_mode = str(ending.get("mode") or "")
    if payload.get("hard_boundary") is True:
        decision = _decision("defer_to_core_mind", "Core/Mind owns the active boundary.")
    elif ending_mode == "natural_close" or requested_posture == "close":
        decision = _decision("close_naturally", "The conversation is being closed.")
    elif interruption_kind == "interruption" or requested_posture in {"wait", "listen"}:
        decision = _decision("wait_and_listen", "The current turn asks for a pause or listening posture.")
    elif requested_posture == "quiet":
        decision = _decision("stay_quiet", "Silence is the requested and sufficient response posture.")
    elif goal_handoff["present"] and not goal_handoff["valid"]:
        decision = _decision("defer_to_core_mind", "The goal coordination receipt is incomplete or invalid.")
    elif goal_handoff["present"] and not goal_key:
        decision = _decision(
            "close_naturally" if goal_handoff["conflict_stop_reason"] == "all_responsibilities_terminal" else "defer_to_core_mind",
            "All coordinated responsibilities are terminal."
            if goal_handoff["conflict_stop_reason"] == "all_responsibilities_terminal"
            else "The current responsibility is held or no conversational move is available.",
        )
    elif goal_move == "close":
        decision = _decision("close_naturally", "The selected current-turn responsibility is complete and requests closure.")
    elif goal_move == "wait":
        decision = _decision("wait_and_listen", "The selected current-turn responsibility requests waiting.")
    elif goal_move == "quiet":
        decision = _decision("stay_quiet", "The selected current-turn responsibility requests quiet.")
    elif goal_move in {"study", "tool", "remember_proposal"}:
        decision = _decision(
            "defer_to_core_mind",
            "The selected move belongs to its existing downstream owner and still requires that owner's authority.",
        )
    elif goal_move == "ask" and not help_ready and ending_mode != "ask_one_material_question":
        decision = _decision(
            "defer_to_core_mind",
            "The selected ask lacks an exact goal-bound missing contribution.",
        )
    elif ending_mode == "ask_one_material_question":
        decision = _decision(
            "ask_one_material_question",
            "A consequential ambiguity must be resolved before optional initiative.",
            question_allowed=True,
        )
    elif help_response:
        decision = _decision(
            "answer_and_resume_shared_task",
            "Aleks supplied the requested contribution, so the shared task can resume from it.",
        )
    elif help_ready:
        decision = _decision(
            "ask_for_specific_collaborative_help",
            "A specific contribution from Aleks materially affects the shared task after available support was used.",
            question_allowed=True,
            expression_handoff={
                "kind": "collaborative_help",
                "goal_key": goal_key,
                "text": help_request["request"],
                "why_it_matters": help_request["why_it_matters"],
                "contribution_kind": help_request["contribution_kind"],
                "placement": "after_current_best_answer" if answer_available else "primary_turn_act",
            },
        )
    elif idea_ready:
        decision = _decision(
            "answer_and_offer_supported_idea",
            "A supported, relevant idea can advance the current task without becoming pressure.",
            expression_handoff={
                "kind": "idea",
                "text": idea["text"],
                "why_it_matters": idea["why_it_matters"],
                "placement": "after_answer" if answer_available else "primary_turn_act",
            },
        )
    elif connection_ready:
        decision = _decision(
            "answer_and_surface_supported_connection",
            "A supported connection is relevant enough to surface without redirecting the conversation.",
            expression_handoff={
                "kind": "connection",
                "text": connection["text"],
                "why_it_matters": connection["why_it_matters"],
                "placement": "after_answer" if answer_available else "primary_turn_act",
            },
        )
    elif curiosity_ready:
        decision = _decision(
            "answer_then_ask_relevant_curiosity",
            "One relevant question would materially improve understanding.",
            question_allowed=True,
            expression_handoff={
                "kind": "curiosity",
                "text": curiosity["question"],
                "why_it_matters": curiosity["why_it_matters"],
                "placement": "after_answer" if answer_available else "primary_turn_act",
            },
        )
    elif answer_available or answer_complete or social_turn or ending_mode in {
        "answer_and_stop_when_complete",
        "leave_room_without_pressuring",
        "leave_missing_content_visible_without_padding",
    }:
        decision = _decision("answer_and_land", "The current answer is sufficient and does not need a habitual question.")
    else:
        decision = _decision("stay_quiet", "No supported addition or necessary question is available.")

    selected = str(decision["selected_act"])
    return _with_guards(
        {
            "status": "conversational_energy_plan_ready",
            "version": RESPONSIVE_INITIATIVE_VERSION,
            **decision,
            "answer_available": answer_available,
            "answer_complete": answer_complete,
            "optional_addition_selected": selected
            in {
                "answer_and_offer_supported_idea",
                "answer_and_surface_supported_connection",
                "answer_then_ask_relevant_curiosity",
                "ask_for_specific_collaborative_help",
            },
            "held_back_signals": held_back,
            "help_contract": {
                "available_support_used_first": help_request.get("available_support_used") is True,
                "exact_missing_contribution_named": bool(help_request.get("request")),
                "why_it_matters_named": bool(help_request.get("why_it_matters")),
                "help_is_failure": False,
                "help_is_submission": False,
                "resume_after_contribution": help_request.get("resume_after_help") is True,
                "contribution_received": bool(help_response),
                "received_contribution_kind": str(help_response.get("contribution_kind") or ""),
                "prior_request": str(help_response.get("prior_request") or ""),
                "incorporate_current_turn_and_resume": bool(help_response),
                "goal_key": str(help_request.get("goal_key") or ""),
                "goal_lineage_matches": bool(
                    help_request
                    and goal_key
                    and help_request.get("goal_key") == goal_key
                ),
            },
            "initiative_contract": {
                "supported": idea_ready or connection_ready,
                "pressure_allowed": False,
                "may_redirect_conversation": False,
                "user_action_required": False,
            },
            "curiosity_contract": {
                "relevant": curiosity_ready,
                "interrogative_by_habit": False,
                "maximum_questions": 1 if decision["question_allowed"] else 0,
            },
            "writes_records": False,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "goal_coordination_handoff": goal_handoff,
            "goal_persistence_performed": False,
            "execution_performed": False,
            "initiative_recursion_allowed": False,
            "initiative_stopping_receipt": {
                "terminal": True,
                "reason": selected,
                "additional_contribution_allowed": False,
                "may_reopen_only_for_new_turn_or_explicit_lifecycle_event": True,
            },
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": CONVERSATIONAL_ENERGY_BOUNDARY,
        }
    )


def realize_conversational_energy(
    base_text: str,
    plan: dict[str, Any] | None,
    *,
    variation_key: str = "",
) -> dict[str, Any]:
    plan = plan if isinstance(plan, dict) else {}
    base = str(base_text or "").strip()
    selected_act = str(plan.get("selected_act") or "")
    handoff = _dict(plan.get("expression_handoff"))
    kind = str(handoff.get("kind") or "")
    supplied = " ".join(str(handoff.get("text") or "").split()).strip()
    why = " ".join(str(handoff.get("why_it_matters") or "").split()).strip()
    addition = ""

    if supplied and _normalized(supplied) not in _normalized(base):
        if kind == "idea":
            addition = f"{_pick(variation_key, ('I have an idea', 'One direction occurs to me', 'There is another route worth considering'))}: {_sentence(supplied)}"
        elif kind == "connection":
            addition = f"{_pick(variation_key, ('A connection I see', 'One relevant connection', 'Something this connects to'))}: {_sentence(supplied)}"
        elif kind == "curiosity":
            addition = f"{_pick(variation_key, ('I am curious about one part', 'One thing I genuinely want to understand', 'A question that matters here'))}: {_question(supplied)}"
        elif kind == "collaborative_help":
            addition = (
                f"{_pick(variation_key, ('I could use your help with one specific piece', 'I need one contribution from you to move this forward cleanly', 'One part belongs with you'))}: "
                f"{_question(supplied)}"
            )
            if why and _normalized(why) not in _normalized(addition):
                addition = f"{addition} {_sentence(why)}"

    candidate = "\n\n".join(item for item in (base, addition) if item).strip()
    return _with_guards(
        {
            "status": "conversational_energy_realized" if addition else "conversational_energy_no_addition",
            "selected_act": selected_act,
            "addition_kind": kind if addition else "",
            "addition_text": addition,
            "candidate_text": candidate,
            "base_answer_preserved": bool(base),
            "supplied_meaning_preserved": bool(addition),
            "whole_answer_replaced": False,
            "question_added": kind in {"curiosity", "collaborative_help"} and bool(addition),
            "pressure_added": False,
            "goal_coordination_handoff": _dict(plan.get("goal_coordination_handoff")),
            "goal_persistence_performed": False,
            "execution_performed": False,
            "initiative_recursion_allowed": False,
            "initiative_stopping_receipt": _dict(plan.get("initiative_stopping_receipt")),
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": CONVERSATIONAL_ENERGY_BOUNDARY,
        }
    )


def _decision(
    selected_act: str,
    reason: str,
    *,
    question_allowed: bool = False,
    expression_handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "selected_act": selected_act,
        "reason": reason,
        "question_allowed": question_allowed,
        "question_required": selected_act
        in {"ask_for_specific_collaborative_help", "ask_one_material_question"},
        "expression_handoff": expression_handoff or {},
    }


def _normalize_optional_signal(value: Any, *, kind: str) -> dict[str, Any]:
    item = _dict(value)
    text = truncate(str(item.get("text") or item.get("summary") or ""), 1200).strip()
    if not text:
        return {}
    return {
        "kind": kind,
        "text": text,
        "why_it_matters": truncate(str(item.get("why_it_matters") or ""), 700).strip(),
        "relevance": str(item.get("relevance") or "not_assessed").strip().lower(),
        "supported": item.get("supported") is True or bool(item.get("source_refs")),
        "source_refs": _text_list(item.get("source_refs")),
        "advances_current_task": item.get("advances_current_task") is True,
        "task_active": item.get("task_active") is True,
        "distinct_from_answer": item.get("distinct_from_answer") is not False,
    }


def _normalize_curiosity(value: Any) -> dict[str, Any]:
    item = _dict(value)
    question = truncate(str(item.get("question") or item.get("text") or ""), 900).strip()
    if not question:
        return {}
    return {
        "question": question,
        "why_it_matters": truncate(str(item.get("why_it_matters") or ""), 700).strip(),
        "relevant": item.get("relevant") is True,
        "answer_matters_to_understanding": item.get("answer_matters_to_understanding") is True,
        "already_answered": item.get("already_answered") is True,
        "genuine_interest": item.get("genuine_interest") is True,
        "engagement_maintenance": item.get("engagement_maintenance") is True,
    }


def _normalize_help(value: Any) -> dict[str, Any]:
    item = _dict(value)
    if not item:
        return {}
    contribution_kind = str(item.get("contribution_kind") or "").strip().lower()
    return {
        "goal_key": truncate(str(item.get("goal_key") or ""), 180).strip(),
        "task_active": item.get("task_active") is True,
        "available_support_used": item.get("available_support_used") is True,
        "contribution_kind": contribution_kind,
        "request": truncate(str(item.get("request") or item.get("question") or ""), 900).strip(),
        "why_it_matters": truncate(str(item.get("why_it_matters") or ""), 700).strip(),
        "materiality": str(item.get("materiality") or "").strip().lower(),
        "resume_after_help": item.get("resume_after_help") is not False,
    }


def _normalize_help_response(value: Any) -> dict[str, Any]:
    item = _dict(value)
    if item.get("provided") is not True:
        return {}
    contribution_kind = str(item.get("contribution_kind") or "").strip().lower()
    if contribution_kind not in CONTRIBUTION_KINDS:
        return {}
    return {
        "provided": True,
        "contribution_kind": contribution_kind,
        "prior_request": truncate(str(item.get("prior_request") or ""), 900).strip(),
    }


def _optional_signal_ready(item: dict[str, Any], *, invited: bool) -> tuple[bool, str]:
    if not item:
        return False, "no signal supplied"
    if not item["supported"]:
        return False, "the addition needs a visible support reference or supported flag"
    if item["relevance"] not in {"high", "material"}:
        return False, "the addition is not relevant enough to interrupt the current answer"
    if not item["distinct_from_answer"]:
        return False, "the addition duplicates the answer"
    if not (invited or item["task_active"] or item["advances_current_task"] or item["relevance"] == "material"):
        return False, "the addition does not advance the current exchange"
    return True, ""


def _curiosity_ready(item: dict[str, Any], *, social_turn: bool) -> tuple[bool, str]:
    if not item:
        return False, "no curiosity signal supplied"
    if not item["relevant"] or not item["answer_matters_to_understanding"]:
        return False, "the question does not materially improve understanding"
    if item["already_answered"]:
        return False, "the question was already answered"
    if social_turn and item["engagement_maintenance"]:
        return False, "a question used only to maintain engagement is not genuine curiosity"
    if social_turn and not item["genuine_interest"]:
        return False, "a social question needs an attributable genuine-curiosity signal"
    return True, ""


def _help_ready(item: dict[str, Any]) -> tuple[bool, str]:
    if not item:
        return False, "no collaborative-help signal supplied"
    if not item["task_active"]:
        return False, "there is no active shared task"
    if not item["available_support_used"]:
        return False, "available reasoning and supported information must be used first"
    if item["contribution_kind"] not in CONTRIBUTION_KINDS:
        return False, "the missing contribution is not a bounded collaborative-help kind"
    if not item["request"] or not item["why_it_matters"]:
        return False, "the exact missing contribution and why it matters are required"
    if item["materiality"] not in {"material", "blocking", "meaningfully_improves"}:
        return False, "the contribution is not materially necessary or useful"
    return True, ""


def _pick(key: str, choices: tuple[str, ...]) -> str:
    digest = sha256(str(key).encode("utf-8")).hexdigest()
    return choices[int(digest[:8], 16) % len(choices)]


def _sentence(value: str) -> str:
    text = value.strip()
    return text if text.endswith((".", "!", "?")) else f"{text}."


def _question(value: str) -> str:
    text = value.strip().rstrip(".")
    return text if text.endswith("?") else f"{text}?"


def _normalized(value: str) -> str:
    return " ".join(str(value or "").lower().split())


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else [] if value in (None, "") else [value]
    return list(
        dict.fromkeys(
            truncate(str(item).strip(), 500)
            for item in values
            if item is not None and str(item).strip()
        )
    )[:30]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
