from __future__ import annotations

from hashlib import sha256
from typing import Any

from .registry import truncate


CONTRIBUTION_VERSION = "v1_attributable_responsive_contribution_selection"
CONTRIBUTION_BOUNDARY = (
    "current_requested_conversation_turn_contribution_selection_only_no_out_of_turn_"
    "speech_fact_creation_memory_identity_governance_authority_or_action_change"
)

CONTRIBUTION_KINDS = {
    "observation",
    "connection",
    "idea",
    "hypothesis",
    "curiosity",
    "callback",
    "next_step",
}

PRIVATE_SOURCE_PREFIXES = (
    "raw_corpus:",
    "private_corpus:",
    "corpus_message:",
    "aleks_miner:",
    "aleks_metacognition_miner:",
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "raw_corpus_access_allowed": False,
    "private_corpus_wording_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "out_of_turn_automatic_speech_allowed": False,
    "automatic_cocoon_routing": False,
    "hidden_chain_of_thought_exposed": False,
}


def conversational_contribution_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "conversational_contribution_engine_ready",
            "version": CONTRIBUTION_VERSION,
            "contribution_kinds": sorted(CONTRIBUTION_KINDS),
            "principles": [
                "a relevant contribution may be offered without waiting for a permission phrase",
                "the direct answer keeps priority when one is owed",
                "every contribution must have attributable current-turn or approved support",
                "at most one optional contribution is selected for a response",
                "recently expressed meaning is not repeated merely to keep talking",
                "completion, listening, silence, and natural closure remain valid",
                "a contribution does not grant filesystem, network, memory, or action authority",
            ],
            "responsive_contribution_allowed": True,
            "explicit_invitation_required": False,
            "out_of_turn_initiative_allowed": False,
            "creates_facts": False,
            "creates_reasoning": False,
            "selects_attributable_upstream_meaning": True,
            "maximum_optional_contributions": 1,
            "writes_records": False,
            "review_status": "status_only",
            "visible_summary_only": True,
            "provenance_boundary": CONTRIBUTION_BOUNDARY,
        }
    )


def build_conversational_contribution_packet(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    content_seed = _text(payload.get("content_seed"), 3600)
    recent_texts = _text_list(payload.get("recent_assistant_texts"), 1800, 12)
    hard_boundary = payload.get("hard_boundary") is True
    requested_posture = str(payload.get("requested_posture") or "").strip().lower()
    interruption_kind = str(payload.get("interruption_kind") or "").strip().lower()
    explicitly_invited = payload.get("explicitly_invited") is True
    social_turn = payload.get("social_turn") is True
    answer_available = bool(content_seed) or payload.get("answer_available") is True
    selected_source_id = str(payload.get("selected_source_id") or "")

    candidates: list[dict[str, Any]] = []
    held: list[dict[str, str]] = []

    for raw in payload.get("upstream_candidates") or []:
        if not isinstance(raw, dict):
            continue
        candidate, reason = _explicit_candidate(raw)
        if candidate:
            candidates.append(candidate)
        else:
            held.append(
                {
                    "origin": "explicit_upstream_candidate",
                    "text": _text(raw.get("text") or raw.get("question"), 160),
                    "reason": reason,
                }
            )

    candidates.extend(
        _structural_candidates(
            _dict(payload.get("structural_discovery")),
            selected_source_id=selected_source_id,
        )
    )
    candidates.extend(
        _knowledge_relationship_candidates(_dict(payload.get("comprehension_context")))
    )
    candidates.extend(_claim_candidates(_dict(payload.get("claim_evidence_packet"))))
    candidates.extend(_callback_candidates(_dict(payload.get("conversation_context"))))
    candidates = _deduplicate(candidates)

    eligible: list[dict[str, Any]] = []
    for candidate in candidates:
        reason = _ineligible_reason(
            candidate,
            content_seed=content_seed,
            recent_texts=recent_texts,
            explicitly_invited=explicitly_invited,
        )
        if reason:
            held.append(
                {
                    "origin": str(candidate.get("origin") or "unknown"),
                    "text": _text(candidate.get("text"), 160),
                    "reason": reason,
                }
            )
        else:
            eligible.append(candidate)

    room_blocker = ""
    if hard_boundary:
        room_blocker = "hard_boundary_precedes_optional_contribution"
    elif requested_posture in {"close", "quiet", "wait", "listen"}:
        room_blocker = "requested_posture_leaves_no_contribution_room"
    elif interruption_kind == "interruption":
        room_blocker = "interruption_requires_listening_before_optional_contribution"

    selected = (
        _select_candidate(
            eligible,
            explicitly_invited=explicitly_invited,
            social_turn=social_turn,
            answer_available=answer_available,
        )
        if not room_blocker
        else {}
    )
    if room_blocker:
        held.extend(
            {
                "origin": str(item.get("origin") or "unknown"),
                "text": _text(item.get("text"), 160),
                "reason": room_blocker,
            }
            for item in eligible
        )

    return _with_guards(
        {
            "status": (
                "conversational_contribution_selected"
                if selected
                else "conversational_contribution_observed_no_selection"
            ),
            "version": CONTRIBUTION_VERSION,
            "responsive_turn": True,
            "responsive_contribution_allowed": True,
            "explicit_invitation_required": False,
            "explicitly_invited": explicitly_invited,
            "answer_available": answer_available,
            "social_turn": social_turn,
            "candidate_count": len(candidates),
            "eligible_count": len(eligible),
            "available_candidates": candidates,
            "held_back_candidates": held,
            "selected_contribution": selected,
            "selected_kind": str(selected.get("kind") or ""),
            "selection_count": 1 if selected else 0,
            "maximum_optional_contributions": 1,
            "conversational_room_blocker": room_blocker,
            "energy_handoff": _energy_handoff(selected),
            "generative_thought_handoff": _thought_handoff(selected),
            "direct_answer_keeps_priority": True,
            "may_be_primary_when_no_answer_is_owed": bool(selected and not answer_available),
            "selection_creates_new_facts": False,
            "selection_creates_new_reasoning": False,
            "pressure_added": False,
            "out_of_turn_delivery": False,
            "writes_records": False,
            "visible_summary_only": True,
            "review_status": "status_only",
            "provenance_boundary": CONTRIBUTION_BOUNDARY,
        }
    )


def _explicit_candidate(raw: dict[str, Any]) -> tuple[dict[str, Any], str]:
    kind = str(raw.get("kind") or "").strip().lower()
    if kind not in CONTRIBUTION_KINDS:
        return {}, f"unsupported contribution kind: {kind or 'missing'}"
    text = _text(raw.get("text") or raw.get("question"), 1800)
    if not text:
        return {}, "contribution text is required"
    refs = _text_list(raw.get("source_refs"), 500, 30)
    if any(_private_ref(ref) for ref in refs):
        return {}, "private corpus or miner wording is not available to visible contribution"
    current_context_supported = raw.get("current_context_supported") is True
    if not (refs or current_context_supported or raw.get("upstream_validated") is True):
        return {}, "attributable current-turn or approved support is required"
    why = _text(raw.get("why_it_matters"), 900)
    if not why:
        return {}, "why the contribution matters to this exchange is required"
    return (
        _candidate(
            kind=kind,
            text=text,
            origin="explicit_upstream_candidate",
            why_it_matters=why,
            source_refs=refs or ["current_conversation:supported_context"],
            relevance=str(raw.get("relevance") or "high"),
            confidence=str(raw.get("confidence") or "supported_current_context"),
            what_would_change=_text_list(raw.get("what_would_change"), 900, 12),
            counterexamples=_text_list(raw.get("counterexamples"), 900, 12),
            advances_current_task=raw.get("advances_current_task") is not False,
        ),
        "",
    )


def _structural_candidates(
    discovery: dict[str, Any],
    *,
    selected_source_id: str,
) -> list[dict[str, Any]]:
    if discovery.get("status") != "structural_discovery_packet_ready":
        return []
    handoff = _dict(discovery.get("expression_handoff"))
    refs = _text_list(discovery.get("source_refs"), 500, 30)
    if not refs:
        refs = ["current_turn:structural_discovery"]
    relation = _text(handoff.get("transferred_relation"), 1800)
    if not relation or selected_source_id == "structural_discovery":
        return []
    return [
        _candidate(
            kind="connection",
            text=relation,
            origin="structural_discovery",
            why_it_matters="The supported relationship connects the current domains without treating the analogy as proof.",
            source_refs=refs,
            relevance="material",
            confidence="bounded_structural_connection",
            advances_current_task=True,
        )
    ]


def _knowledge_relationship_candidates(comprehension: dict[str, Any]) -> list[dict[str, Any]]:
    knowledge = _dict(comprehension.get("knowledge_context"))
    items = [
        item
        for item in knowledge.get("answer_eligible_items") or []
        if isinstance(item, dict)
    ]
    result: list[dict[str, Any]] = []
    for item in items[:8]:
        refs = _text_list(item.get("source_refs"), 500, 30)
        if not refs or any(_private_ref(ref) for ref in refs):
            continue
        for relationship in _text_list(item.get("relationships"), 1500, 4):
            result.append(
                _candidate(
                    kind="connection",
                    text=relationship,
                    origin="approved_knowledge_relationship",
                    why_it_matters="This reviewed relationship extends the currently relevant concept.",
                    source_refs=refs,
                    relevance="high",
                    confidence=str(item.get("confidence") or "reviewed"),
                    advances_current_task=True,
                )
            )
    return result


def _claim_candidates(packet: dict[str, Any]) -> list[dict[str, Any]]:
    if packet.get("status") != "claim_evidence_packet_ready":
        return []
    result: list[dict[str, Any]] = []
    for claim in packet.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_type = str(claim.get("claim_type") or "")
        validity = str(claim.get("validity") or "")
        if claim_type not in {"hypothesis", "model"} or validity in {
            "basis_missing",
            "superseded",
        }:
            continue
        changes = _text_list(claim.get("what_would_change"), 900, 12)
        counters = _text_list(claim.get("limitations"), 900, 12)
        refs = [
            *_text_list(claim.get("source_refs"), 500, 30),
            *_text_list(claim.get("evidence_refs"), 500, 30),
        ]
        if not changes or not counters or any(_private_ref(ref) for ref in refs):
            continue
        result.append(
            _candidate(
                kind="hypothesis",
                text=_text(claim.get("text"), 1800),
                origin="claim_evidence",
                why_it_matters="This supported provisional model may help explain the current evidence.",
                source_refs=refs or ["current_turn:claim_evidence"],
                relevance="high",
                confidence=str(claim.get("confidence") or "provisional"),
                what_would_change=changes,
                counterexamples=counters,
                advances_current_task=True,
                explicit_invitation_required=(
                    claim.get("contribution_warrant") is not True
                ),
            )
        )
    return result


def _callback_candidates(context: dict[str, Any]) -> list[dict[str, Any]]:
    braid = _dict(context.get("thread_braid"))
    actions = {
        str(item.get("action") or "")
        for item in braid.get("turn_traversal") or []
        if isinstance(item, dict)
    }
    if not actions.intersection({"resume", "revise_with_dependency", "land"}):
        return []
    active_thread = str(braid.get("active_thread_id") or "")
    landmarks = [
        item
        for item in context.get("session_landmarks") or []
        if isinstance(item, dict)
        and str(item.get("summary") or "").strip()
        and (not active_thread or str(item.get("thread_id") or "") == active_thread)
    ]
    if not landmarks:
        return []
    item = landmarks[-1]
    return [
        _candidate(
            kind="callback",
            text=_text(item.get("summary"), 1800),
            origin="current_session_landmark",
            why_it_matters="The current thread returned to a prior supported point that remains relevant.",
            source_refs=[f"session_landmark:{item.get('id') or 'current'}"],
            relevance="high",
            confidence="visible_current_session",
            advances_current_task=True,
        )
    ]


def _candidate(
    *,
    kind: str,
    text: str,
    origin: str,
    why_it_matters: str,
    source_refs: list[str],
    relevance: str,
    confidence: str,
    advances_current_task: bool,
    what_would_change: list[str] | None = None,
    counterexamples: list[str] | None = None,
    explicit_invitation_required: bool = False,
) -> dict[str, Any]:
    clean = _text(text, 1800)
    digest = sha256(f"{kind}|{origin}|{clean}".encode("utf-8")).hexdigest()[:16]
    return {
        "candidate_id": f"contribution-{digest}",
        "kind": kind,
        "text": clean,
        "origin": origin,
        "why_it_matters": _text(why_it_matters, 900),
        "source_refs": list(dict.fromkeys(source_refs))[:30],
        "relevance": relevance if relevance in {"high", "material"} else "not_assessed",
        "confidence": confidence or "not_assessed",
        "what_would_change": list(what_would_change or []),
        "counterexamples": list(counterexamples or []),
        "advances_current_task": advances_current_task,
        "supported": True,
        "distinct_from_answer": True,
        "pressure_allowed": False,
        "explicit_invitation_required": explicit_invitation_required,
    }


def _ineligible_reason(
    candidate: dict[str, Any],
    *,
    content_seed: str,
    recent_texts: list[str],
    explicitly_invited: bool,
) -> str:
    text = _normalized(candidate.get("text"))
    if not text:
        return "empty_contribution"
    if not candidate.get("source_refs"):
        return "missing_attributable_support"
    if any(_private_ref(ref) for ref in candidate.get("source_refs") or []):
        return "private_source_not_available"
    if candidate.get("relevance") not in {"high", "material"}:
        return "relevance_not_high_enough"
    if candidate.get("advances_current_task") is not True:
        return "does_not_advance_current_exchange"
    if candidate.get("explicit_invitation_required") is True and not explicitly_invited:
        return "provisional_model_needs_specific_contribution_warrant_or_invitation"
    content = _normalized(content_seed)
    if content and (text in content or content in text):
        return "meaning_already_present_in_answer"
    if any(text in _normalized(item) or _normalized(item) in text for item in recent_texts):
        return "meaning_repeats_recent_selene_expression"
    return ""


def _select_candidate(
    candidates: list[dict[str, Any]],
    *,
    explicitly_invited: bool,
    social_turn: bool,
    answer_available: bool,
) -> dict[str, Any]:
    order = {
        "connection": 0,
        "idea": 1,
        "hypothesis": 2,
        "callback": 3,
        "observation": 4,
        "next_step": 5,
        "curiosity": 6,
    }
    ranked = sorted(
        candidates,
        key=lambda item: (
            0 if item.get("relevance") == "material" else 1,
            0 if explicitly_invited else 1,
            0 if answer_available else 1,
            0 if social_turn and item.get("kind") != "curiosity" else 1,
            order.get(str(item.get("kind") or ""), 99),
            str(item.get("candidate_id") or ""),
        ),
    )
    return ranked[0] if ranked else {}


def _energy_handoff(selected: dict[str, Any]) -> dict[str, Any]:
    if not selected:
        return {}
    kind = str(selected.get("kind") or "")
    common = {
        "text": str(selected.get("text") or ""),
        "why_it_matters": str(selected.get("why_it_matters") or ""),
        "relevance": str(selected.get("relevance") or "high"),
        "supported": True,
        "source_refs": selected.get("source_refs") or [],
        "advances_current_task": selected.get("advances_current_task") is True,
        "task_active": True,
        "distinct_from_answer": True,
    }
    if kind in {"connection", "callback", "observation"}:
        return {"supported_connection": common}
    if kind in {"idea", "next_step"}:
        return {"supported_idea": common}
    if kind == "curiosity":
        return {
            "curiosity": {
                "question": common["text"],
                "why_it_matters": common["why_it_matters"],
                "relevant": True,
                "answer_matters_to_understanding": True,
                "genuine_interest": True,
                "engagement_maintenance": False,
            }
        }
    return {}


def _thought_handoff(selected: dict[str, Any]) -> dict[str, Any]:
    if not selected or selected.get("kind") != "hypothesis":
        return {}
    return {
        "expression_requested": True,
        "requested_kind": "hypothesis",
        "thought_candidates": [
            {
                "kind": "hypothesis",
                "text": selected.get("text"),
                "current_context_supported": True,
                "source_refs": selected.get("source_refs") or [],
                "why_it_matters": selected.get("why_it_matters") or "",
                "what_would_change": selected.get("what_would_change") or [],
                "counterexamples": selected.get("counterexamples") or [],
                "confidence": selected.get("confidence") or "provisional",
            }
        ],
    }


def _deduplicate(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (str(candidate.get("kind") or ""), _normalized(candidate.get("text")))
        if not key[1] or key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result[:30]


def _private_ref(value: Any) -> bool:
    lower = str(value or "").strip().lower()
    return any(lower.startswith(prefix) for prefix in PRIVATE_SOURCE_PREFIXES)


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any, limit: int) -> str:
    return truncate(" ".join(str(value or "").split()), limit)


def _text_list(value: Any, item_limit: int, count_limit: int) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return [
        _text(item, item_limit)
        for item in value
        if _text(item, item_limit)
    ][:count_limit]


def _normalized(value: Any) -> str:
    return " ".join(str(value or "").lower().split())


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
