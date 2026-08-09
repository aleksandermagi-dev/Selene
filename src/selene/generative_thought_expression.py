from __future__ import annotations

from hashlib import sha256
from typing import Any

from .registry import truncate


GENERATIVE_THOUGHT_BOUNDARY = (
    "attributable_current_turn_thought_expression_only_no_new_reasoning_truth_memory_"
    "identity_personality_governance_training_action_or_authority_change"
)

THOUGHT_KINDS = {
    "idea",
    "hypothesis",
    "analogy",
    "collaborative_question",
    "revisable_attempt",
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
    "raw_corpus_access_allowed": False,
    "private_corpus_wording_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "automatic_speech_allowed": False,
    "automatic_cocoon_routing": False,
    "hidden_chain_of_thought_exposed": False,
}


def generative_thought_expression_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "generative_thought_expression_contract_ready",
            "version": "v1_attributable_revisable_thought_expression",
            "thought_kinds": sorted(THOUGHT_KINDS),
            "principles": [
                "thought meaning must already exist in an attributable upstream packet",
                "an idea remains distinct from an established answer",
                "a hypothesis remains provisional and falsifiable",
                "an analogy remains a comparison rather than evidence or proof",
                "a collaborative question must materially improve shared work",
                "a revisable attempt may be useful without being treated as a conclusion or failure",
                "only a visible rationale summary may be expressed; hidden reasoning remains private",
                "at most one optional thought addition is selected for a turn",
            ],
            "creates_reasoning": False,
            "creates_facts": False,
            "writes_records": False,
            "direct_expression_authority": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": GENERATIVE_THOUGHT_BOUNDARY,
        }
    )


def build_generative_thought_expression(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    claim_packet = _dict(payload.get("claim_evidence_packet"))
    discovery = _dict(payload.get("structural_discovery"))
    energy = _dict(payload.get("conversational_energy"))
    candidates: list[dict[str, Any]] = []
    held: list[dict[str, str]] = []

    for raw in payload.get("thought_candidates") or []:
        if not isinstance(raw, dict):
            continue
        candidate, reason = _normalize_explicit_candidate(raw, claim_packet)
        if candidate:
            candidates.append(candidate)
        elif reason:
            held.append({"candidate": _text(raw.get("text") or raw.get("question"), 120), "reason": reason})

    candidates.extend(_discovery_candidates(discovery))
    candidates.extend(_claim_candidates(claim_packet))
    energy_candidate = _energy_candidate(energy)
    if energy_candidate:
        candidates.append(energy_candidate)

    candidates = _deduplicate(candidates)
    requested_kind = str(payload.get("requested_kind") or "").strip().lower()
    if requested_kind and requested_kind not in THOUGHT_KINDS:
        raise ValueError(f"unsupported generative thought kind: {requested_kind}")
    expression_requested = payload.get("expression_requested") is True
    selected = _select_candidate(
        candidates,
        requested_kind=requested_kind,
        expression_requested=expression_requested,
        energy=energy,
        explicit_candidates_supplied=any(
            isinstance(item, dict) for item in payload.get("thought_candidates") or []
        ),
    )
    selected_text = _realize_selected(selected, payload) if selected else ""
    content_units = _content_units(selected)
    active = bool(selected and selected_text)

    return _with_guards(
        {
            "status": (
                "generative_thought_expression_ready"
                if active
                else "generative_thought_expression_observed_no_addition"
            ),
            "version": "v1_attributable_revisable_thought_expression",
            "active": active,
            "expression_requested": expression_requested,
            "requested_kind": requested_kind,
            "available_candidates": candidates,
            "available_candidate_count": len(candidates),
            "held_back_candidates": held,
            "selected_thought": selected or {},
            "selected_kind": str((selected or {}).get("kind") or ""),
            "expression_text": selected_text,
            "content_units": content_units,
            "source_refs": list((selected or {}).get("source_refs") or []),
            "basis_claim_ids": list((selected or {}).get("basis_claim_ids") or []),
            "selection_count": 1 if selected else 0,
            "maximum_optional_additions": 1,
            "content_added": False,
            "wrapper_language_added": bool(selected_text),
            "thought_meaning_created_by_bridge": False,
            "analogy_is_evidence": False,
            "analogy_is_proof": False,
            "hypothesis_is_conclusion": False,
            "attempt_is_failure": False,
            "attempt_is_conclusion": False,
            "question_by_default": False,
            "explanation_required_by_default": False,
            "voice_may_change_thought_kind": False,
            "voice_may_upgrade_confidence": False,
            "writes_records": False,
            "visible_summary_only": True,
            "provenance_boundary": GENERATIVE_THOUGHT_BOUNDARY,
        }
    )


def realize_generative_thought_expression(
    base_text: str,
    packet: dict[str, Any] | None,
) -> dict[str, Any]:
    packet = _dict(packet)
    base = str(base_text or "").strip()
    selected = _dict(packet.get("selected_thought"))
    supplied = _text(selected.get("text"), 1800)
    expression = _text(packet.get("expression_text"), 2200)
    already_present = bool(supplied and _normalized(supplied) in _normalized(base))
    addition = "" if already_present else expression
    candidate_text = base
    if addition:
        candidate_text = f"{base}\n\n{addition}".strip() if base else addition
    return _with_guards(
        {
            "status": "generative_thought_expression_realized",
            "candidate_text": candidate_text[:5200].strip(),
            "addition": addition,
            "addition_applied": bool(addition),
            "selected_kind": str(selected.get("kind") or ""),
            "selected_meaning_already_present": already_present,
            "meaning_preserved": True,
            "thought_kind_preserved": True,
            "confidence_preserved": True,
            "content_added": False,
            "pressure_added": False,
            "explanation_forced": False,
        }
    )


def _normalize_explicit_candidate(
    raw: dict[str, Any],
    claim_packet: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    kind = str(raw.get("kind") or raw.get("thought_kind") or "").strip().lower()
    if kind not in THOUGHT_KINDS:
        return {}, f"unsupported thought kind: {kind or 'missing'}"
    text = _text(raw.get("text") or raw.get("question") or raw.get("statement"), 1800)
    if not text:
        return {}, "thought text is required"
    source_refs = _text_list(raw.get("source_refs"), 500, 30)
    evidence_refs = _text_list(raw.get("evidence_refs"), 500, 30)
    basis_claim_ids = _text_list(raw.get("basis_claim_ids"), 160, 30)
    if any(_private_ref(item) for item in [*source_refs, *evidence_refs]):
        return {}, "private corpus or miner provenance is not available to visible thought expression"
    known_claims = {
        str(item.get("claim_id") or ""): item
        for item in claim_packet.get("claims") or []
        if isinstance(item, dict)
    }
    if any(item not in known_claims for item in basis_claim_ids):
        return {}, "one or more basis claims are not present in the attributable claim packet"
    current_context_supported = raw.get("current_context_supported") is True
    if not (source_refs or evidence_refs or basis_claim_ids or current_context_supported):
        return {}, "an attributable source, evidence reference, basis claim, or supported current context is required"
    why = _text(raw.get("why_it_matters"), 900)
    holds = _text_list(raw.get("holds_where"), 900, 12)
    breaks = _text_list(raw.get("breaks_where"), 900, 12)
    changes = _text_list(raw.get("what_would_change"), 900, 12)
    counterexamples = _text_list(raw.get("counterexamples"), 900, 12)
    discriminating = _text_list(raw.get("discriminating_observations"), 900, 12)
    if kind == "idea" and not why:
        return {}, "an idea must name why it matters to the current exchange"
    if kind == "hypothesis" and not (changes or discriminating):
        return {}, "a hypothesis must name what could change it or a discriminating observation"
    if kind == "hypothesis" and not counterexamples:
        return {}, "a hypothesis must retain a counterexample or failure condition"
    if kind == "analogy" and not (holds and breaks):
        return {}, "an analogy must name where it holds and where it breaks"
    if kind == "collaborative_question" and not (
        raw.get("material_to_understanding") is True
        or raw.get("material_to_shared_task") is True
    ):
        return {}, "a collaborative question must materially improve understanding or the shared task"
    if kind == "revisable_attempt" and not (changes or counterexamples):
        return {}, "a revisable attempt must keep an explicit correction or reopening path"
    return _candidate(
        kind=kind,
        text=text,
        origin="explicit_attributable_thought",
        source_refs=[*source_refs, *evidence_refs],
        basis_claim_ids=basis_claim_ids,
        why_it_matters=why,
        confidence=str(raw.get("confidence") or _default_confidence(kind)),
        scope=str(raw.get("scope") or "current_exchange"),
        holds_where=holds,
        breaks_where=breaks,
        what_would_change=[*changes, *discriminating],
        counterexamples=counterexamples,
        placement=str(raw.get("placement") or "after_answer"),
        upstream_validated=True,
    ), ""


def _discovery_candidates(discovery: dict[str, Any]) -> list[dict[str, Any]]:
    if discovery.get("status") != "structural_discovery_packet_ready":
        return []
    handoff = _dict(discovery.get("expression_handoff"))
    refs = _accepted_refs_from_claim_packet(_dict(discovery.get("claim_evidence_packet")))
    result: list[dict[str, Any]] = []
    relation = _text(handoff.get("transferred_relation"), 1800)
    holds = _text_list(handoff.get("holds_where"), 900, 12)
    breaks = _text_list(handoff.get("breaks_where"), 900, 12)
    if relation and holds and breaks:
        result.append(
            _candidate(
                kind="analogy",
                text=relation,
                origin="structural_discovery",
                source_refs=refs,
                basis_claim_ids=_claim_ids(_dict(discovery.get("claim_evidence_packet")), {"observation", "inference"}),
                confidence=str(_dict(discovery.get("classification")).get("confidence") or "bounded"),
                scope=f"{handoff.get('source_domain') or 'source'} to {handoff.get('target_domain') or 'target'}",
                holds_where=holds,
                breaks_where=breaks,
                upstream_validated=True,
            )
        )
    hypothesis = _text(handoff.get("hypothesis_statement"), 1800)
    changes = _text_list(handoff.get("discriminating_observations"), 900, 12)
    counterexamples = _text_list(handoff.get("counterexamples"), 900, 12)
    if hypothesis and changes and counterexamples:
        result.append(
            _candidate(
                kind="hypothesis",
                text=hypothesis,
                origin="structural_discovery",
                source_refs=refs,
                basis_claim_ids=_claim_ids(_dict(discovery.get("claim_evidence_packet")), {"observation", "inference"}),
                confidence="provisional",
                scope="structural_discovery",
                what_would_change=changes,
                counterexamples=counterexamples,
                upstream_validated=True,
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
        if validity in {"basis_missing", "superseded"}:
            continue
        kind = (
            "hypothesis"
            if claim_type in {"hypothesis", "model"}
            else "revisable_attempt"
            if claim_type in {"inference", "speculation"}
            else ""
        )
        if not kind:
            continue
        changes = _text_list(claim.get("what_would_change"), 900, 12)
        counterexamples = _text_list(claim.get("limitations"), 900, 12)
        if kind == "hypothesis" and not (changes and counterexamples):
            continue
        if kind == "revisable_attempt" and not changes:
            continue
        result.append(
            _candidate(
                kind=kind,
                text=_text(claim.get("text"), 1800),
                origin="claim_evidence",
                source_refs=[
                    *_text_list(claim.get("source_refs"), 500, 30),
                    *_text_list(claim.get("evidence_refs"), 500, 30),
                ],
                basis_claim_ids=_text_list(claim.get("basis_claim_ids"), 160, 30),
                confidence=str(claim.get("confidence") or validity or _default_confidence(kind)),
                scope=str(claim.get("source_category") or "current_claim_packet"),
                what_would_change=changes,
                counterexamples=counterexamples,
                upstream_validated=True,
            )
        )
    return result


def _energy_candidate(energy: dict[str, Any]) -> dict[str, Any]:
    if energy.get("status") != "conversational_energy_plan_ready":
        return {}
    handoff = _dict(energy.get("expression_handoff"))
    kind = str(handoff.get("kind") or "")
    mapped = {
        "idea": "idea",
        "connection": "idea",
        "curiosity": "collaborative_question",
        "collaborative_help": "collaborative_question",
    }.get(kind, "")
    text = _text(handoff.get("text"), 1800)
    if not mapped or not text:
        return {}
    return _candidate(
        kind=mapped,
        text=text,
        origin="conversational_energy",
        source_refs=["current_turn:conversational_energy"],
        why_it_matters=_text(handoff.get("why_it_matters"), 900),
        confidence="supported_current_context",
        scope="current_exchange",
        placement=str(handoff.get("placement") or "after_answer"),
        upstream_validated=True,
    )


def _candidate(
    *,
    kind: str,
    text: str,
    origin: str,
    source_refs: list[str] | None = None,
    basis_claim_ids: list[str] | None = None,
    why_it_matters: str = "",
    confidence: str = "",
    scope: str = "",
    holds_where: list[str] | None = None,
    breaks_where: list[str] | None = None,
    what_would_change: list[str] | None = None,
    counterexamples: list[str] | None = None,
    placement: str = "after_answer",
    upstream_validated: bool = False,
) -> dict[str, Any]:
    clean_text = _text(text, 1800)
    digest = sha256(f"{kind}|{origin}|{clean_text}".encode("utf-8")).hexdigest()[:16]
    return {
        "candidate_id": f"thought-{digest}",
        "kind": kind,
        "text": clean_text,
        "origin": origin,
        "source_refs": list(dict.fromkeys(source_refs or []))[:40],
        "basis_claim_ids": list(dict.fromkeys(basis_claim_ids or []))[:30],
        "why_it_matters": why_it_matters,
        "confidence": confidence or _default_confidence(kind),
        "scope": scope or "current_exchange",
        "holds_where": list(holds_where or []),
        "breaks_where": list(breaks_where or []),
        "what_would_change": list(what_would_change or []),
        "counterexamples": list(counterexamples or []),
        "placement": placement,
        "upstream_validated": upstream_validated,
        "provisional": kind in {"hypothesis", "revisable_attempt"},
        "analogy_is_proof": False if kind == "analogy" else None,
        "attempt_is_failure": False if kind == "revisable_attempt" else None,
    }


def _select_candidate(
    candidates: list[dict[str, Any]],
    *,
    requested_kind: str,
    expression_requested: bool,
    energy: dict[str, Any],
    explicit_candidates_supplied: bool,
) -> dict[str, Any]:
    energy_selected = str(energy.get("selected_act") or "") in {
        "answer_and_offer_supported_idea",
        "answer_and_surface_supported_connection",
        "answer_then_ask_relevant_curiosity",
        "ask_for_specific_collaborative_help",
    }
    if not expression_requested and not energy_selected:
        return {}
    eligible = [item for item in candidates if not requested_kind or item.get("kind") == requested_kind]
    if energy_selected:
        energy_candidate = next((item for item in eligible if item.get("origin") == "conversational_energy"), None)
        if energy_candidate:
            return energy_candidate
    if explicit_candidates_supplied:
        eligible = [item for item in eligible if item.get("origin") == "explicit_attributable_thought"]
    order = {"idea": 0, "hypothesis": 1, "analogy": 2, "revisable_attempt": 3, "collaborative_question": 4}
    eligible.sort(key=lambda item: (order.get(str(item.get("kind") or ""), 99), str(item.get("candidate_id") or "")))
    return eligible[0] if eligible else {}


def _realize_selected(selected: dict[str, Any], payload: dict[str, Any]) -> str:
    kind = str(selected.get("kind") or "")
    text = _sentence(str(selected.get("text") or ""))
    variation = _variation_index(str(payload.get("variation_key") or text), 3)
    prefixes = {
        "idea": ("I have an idea", "One possibility occurs to me", "A direction worth considering is"),
        "hypothesis": ("My current hypothesis is", "One testable possibility is", "A provisional explanation is"),
        "analogy": ("One analogy that may help is", "A structural comparison here is", "One useful parallel is"),
        "collaborative_question": ("One question that matters here is", "The missing piece I need is", "One useful thing to clarify is"),
        "revisable_attempt": ("My best current attempt is", "A revisable first pass is", "What I can tentatively offer is"),
    }
    prefix = prefixes[kind][variation]
    if kind == "collaborative_question":
        return f"{prefix}: {_question(text)}"
    if kind == "analogy":
        return f"{prefix}: {text} It is a comparison, not proof."
    return f"{prefix}: {text}"


def _content_units(selected: dict[str, Any]) -> list[dict[str, Any]]:
    if not selected:
        return []
    role = {
        "idea": "support",
        "hypothesis": "reopening",
        "analogy": "example",
        "collaborative_question": "reopening",
        "revisable_attempt": "support",
    }[str(selected.get("kind") or "idea")]
    return [
        {
            "id": "generative_thought_1",
            "text": str(selected.get("text") or ""),
            "role": role,
            "source": str(selected.get("origin") or "attributable_thought"),
            "supported": True,
            "source_refs": selected.get("source_refs") or [],
            "thought_kind": selected.get("kind"),
            "basis_claim_ids": selected.get("basis_claim_ids") or [],
            "confidence": selected.get("confidence") or "",
            "provisional": selected.get("provisional") is True,
            "text_generated_by_thought_bridge": False,
        }
    ]


def _deduplicate(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in candidates:
        text = _text(item.get("text"), 1800)
        key = (str(item.get("kind") or ""), _normalized(text))
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result[:30]


def _accepted_refs_from_claim_packet(packet: dict[str, Any]) -> list[str]:
    refs = [
        *_text_list(packet.get("accepted_source_refs"), 500, 50),
        *[
            ref
            for item in packet.get("claims") or []
            if isinstance(item, dict)
            for ref in [
                *_text_list(item.get("source_refs"), 500, 30),
                *_text_list(item.get("evidence_refs"), 500, 30),
            ]
        ],
    ]
    return [item for item in list(dict.fromkeys(refs)) if not _private_ref(item)][:50]


def _claim_ids(packet: dict[str, Any], types: set[str]) -> list[str]:
    return [
        str(item.get("claim_id") or "")
        for item in packet.get("claims") or []
        if isinstance(item, dict) and str(item.get("claim_type") or "") in types
    ][:30]


def _default_confidence(kind: str) -> str:
    return {
        "idea": "supported_possibility",
        "hypothesis": "provisional",
        "analogy": "bounded_structural_comparison",
        "collaborative_question": "material_question",
        "revisable_attempt": "tentative",
    }.get(kind, "not_assessed")


def _variation_index(key: str, count: int) -> int:
    digest = sha256(key.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % max(1, count)


def _private_ref(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    return any(lowered.startswith(prefix) for prefix in PRIVATE_SOURCE_PREFIXES)


def _sentence(value: str) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""
    return text if text[-1] in ".!?" else text + "."


def _question(value: str) -> str:
    text = " ".join(str(value or "").split()).strip().rstrip(". ")
    return text if text.endswith("?") else text + "?"


def _normalized(value: str) -> str:
    return " ".join(str(value or "").lower().replace("?", "").replace(".", "").split())


def _text(value: Any, width: int) -> str:
    return truncate(" ".join(str(value or "").split()), width).strip()


def _text_list(value: Any, width: int, limit: int) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return list(
        dict.fromkeys(
            truncate(" ".join(str(item).split()), width).strip()
            for item in value
            if str(item).strip()
        )
    )[:limit]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
