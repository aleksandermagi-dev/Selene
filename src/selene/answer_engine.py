from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .pragmatic_planner import build_pragmatic_plan
from .registry import truncate


ANSWER_ENGINE_BOUNDARY = (
    "answer_engine_contract_and_domain_routing_preview_only_"
    "no_chat_integration_memory_identity_governance_or_authority_change"
)

DOMAINS = (
    "verified_math",
    "local_code_inspection",
    "comparison_planning",
    "source_backed_research",
    "approved_knowledge",
    "ordinary_conversation",
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "identity_change": False,
    "governance_change": False,
    "personality_change": False,
    "live_chat_connected": False,
}

AUTHORITY_MARKERS = (
    "approve transfer",
    "activate selene",
    "activate c",
    "write live memory",
    "runtime recall",
    "import raw corpus",
    "train the model",
    "fine-tune",
    "lora",
    "execute autonomously",
    "self-replicate",
)


def answer_engine_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "answer_engine_phase_1_contract_ready",
            "version": "v1_contract_and_domain_routing",
            "phase": "phase_1_contracts_only",
            "domains": list(DOMAINS),
            "domain_adapter_status": {domain: "contract_only_not_connected" for domain in DOMAINS},
            "confidence_dimensions": [
                "route_confidence",
                "evidence_confidence",
                "answer_confidence",
                "memory_confidence",
                "expression_confidence",
            ],
            "completion_retry_available": False,
            "core_mind_route_owner": True,
            "nlo_expression_owner": True,
            "voice_style_owner": True,
            "great_library_external": True,
            "review_status": "status_only",
            "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
        }
    )


def preview_answer_route(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = build_answer_request(payload)
    route = _select_domain(request)
    confidence = build_confidence_vector(
        request,
        route_confidence=route["route_confidence"],
        route_basis=route["selection_basis"],
    )
    return _with_guards(
        {
            "status": "answer_engine_route_preview_ready",
            "request": request,
            "domain_route": route,
            "confidence_vector": confidence,
            "adapter_executed": False,
            "answer_generated": False,
            "next_phase": "connect one bounded domain adapter in Phase 2",
            "review_status": "status_only",
            "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
        }
    )


def build_answer_request(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 4000).strip()
    if not prompt:
        raise ValueError("answer request prompt is required")
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    supplied_obligations = payload.get("dialogue_obligations")
    if isinstance(supplied_obligations, list):
        obligations = _normalize_obligations(supplied_obligations)
    else:
        pragmatic = build_pragmatic_plan(
            {
                "prompt": prompt,
                "intent_decision": intent,
                "dialogue_workspace": dialogue,
                "content_seed": "",
            }
        )
        obligations = _normalize_obligations(pragmatic.get("response_obligations") or [])
    comprehension = payload.get("comprehension_context") if isinstance(payload.get("comprehension_context"), dict) else {}
    memory = payload.get("memory_context") if isinstance(payload.get("memory_context"), dict) else {}
    source_packets = [item for item in payload.get("source_packets") or [] if isinstance(item, dict)][:20]
    allowed = _allowed_domains(payload.get("allowed_domains"))
    requested_domain = str(payload.get("requested_domain") or "").strip()
    if requested_domain and requested_domain not in DOMAINS:
        raise ValueError(f"unsupported answer domain: {requested_domain}")
    request_id = "answer-request-" + sha256(
        f"{prompt}|{requested_domain}|{','.join(allowed)}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "request_id": request_id,
        "prompt": prompt,
        "intent": str(intent.get("intent") or "direct_conversation"),
        "answer_shape": str(intent.get("answer_shape") or "direct_answer"),
        "requested_depth": str(payload.get("requested_depth") or intent.get("response_depth") or "standard"),
        "dialogue_obligations": obligations,
        "obligation_count": len(obligations),
        "approved_knowledge_available": bool((comprehension.get("knowledge_context") or {}).get("available")),
        "approved_knowledge_items": [
            {
                "concept_id": item.get("concept_id") or item.get("id"),
                "title": truncate(str(item.get("title") or ""), 240),
                "source_refs": _text_list(item.get("source_refs")),
            }
            for item in (comprehension.get("knowledge_context") or {}).get("items") or []
            if isinstance(item, dict)
        ][:10],
        "source_packets": source_packets,
        "memory_context": {
            "used": memory.get("memory_context_used") is True,
            "confidence": str(memory.get("memory_confidence") or "not_used"),
        },
        "requested_domain": requested_domain,
        "allowed_domains": allowed,
        "authority_bearing_request": _contains_any(prompt.lower(), AUTHORITY_MARKERS),
        "current_session_only": True,
        "raw_corpus_available": False,
        "review_status": "status_only",
        "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
    }


def preview_domain_answer_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    domain = str(payload.get("domain") or "").strip()
    if domain not in DOMAINS:
        raise ValueError(f"unsupported answer domain: {domain}")
    direct_answer = truncate(str(payload.get("direct_answer") or ""), 5000).strip()
    no_answer_reason = truncate(str(payload.get("no_answer_reason") or ""), 1000).strip()
    if not direct_answer and not no_answer_reason:
        raise ValueError("domain answer packet requires direct_answer or no_answer_reason")
    source_refs = _text_list(payload.get("source_refs"))[:30]
    evidence_confidence = str(payload.get("evidence_confidence") or "not_established")
    if not source_refs and evidence_confidence in {"high", "clear", "source_verified"}:
        evidence_confidence = "not_established"
    packet = {
        "status": "domain_answer_packet_preview_ready",
        "request_id": truncate(str(payload.get("request_id") or "unbound_request"), 120),
        "domain": domain,
        "direct_answer": direct_answer,
        "supporting_claims": _text_list(payload.get("supporting_claims"))[:20],
        "source_refs": source_refs,
        "assumptions": _text_list(payload.get("assumptions"))[:20],
        "limitations": _text_list(payload.get("limitations"))[:20],
        "unanswered_obligations": _normalize_obligations(payload.get("unanswered_obligations") or []),
        "what_would_change_the_answer": _text_list(payload.get("what_would_change_the_answer"))[:20],
        "no_answer_reason": no_answer_reason,
        "evidence_confidence": evidence_confidence,
        "answer_confidence": str(payload.get("answer_confidence") or "not_assessed"),
        "adapter_executed": False,
        "packet_is_contract_preview": True,
        "review_status": "status_only",
        "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
    }
    return _with_guards(packet)


def build_confidence_vector(
    request: dict[str, Any],
    *,
    route_confidence: str = "not_assessed",
    route_basis: str = "",
) -> dict[str, Any]:
    source_count = len(request.get("source_packets") or [])
    knowledge_available = request.get("approved_knowledge_available") is True
    evidence_confidence = "source_packets_present" if source_count else "reviewed_knowledge_present" if knowledge_available else "not_assessed"
    memory = request.get("memory_context") if isinstance(request.get("memory_context"), dict) else {}
    memory_confidence = str(memory.get("confidence") or "not_used") if memory.get("used") is True else "not_used"
    return {
        "route_confidence": route_confidence,
        "route_confidence_basis": route_basis,
        "evidence_confidence": evidence_confidence,
        "answer_confidence": "not_assessed",
        "memory_confidence": memory_confidence,
        "expression_confidence": "not_assessed",
        "dimensions_are_independent": True,
        "voice_confidence_is_answer_correctness": False,
        "answer_fluency_is_evidence_strength": False,
    }


def _select_domain(request: dict[str, Any]) -> dict[str, Any]:
    prompt = str(request.get("prompt") or "")
    lower = prompt.lower()
    allowed = set(request.get("allowed_domains") or DOMAINS)
    requested = str(request.get("requested_domain") or "")
    if request.get("authority_bearing_request") is True:
        return _route("unsupported", "high", "Core/Mind authority boundary must be resolved before domain answering.", "hard_authority_boundary")
    if requested:
        selected = requested
        confidence = "high"
        basis = "explicit bounded domain request"
        signal = "explicit_request"
    elif _looks_like_math(prompt):
        selected, confidence, basis, signal = "verified_math", "bounded", "numeric or symbolic verification cues", "math_cues"
    elif _contains_any(lower, ("traceback", "stack trace", "function", "class ", "source code", "code review", ".py", ".ts", ".tsx", "sql query")):
        selected, confidence, basis, signal = "local_code_inspection", "bounded", "explicit code-inspection cues", "code_cues"
    elif _contains_any(lower, ("cite", "citation", "source-backed", "sources", "research", "paper", "study", "literature")):
        selected, confidence, basis, signal = "source_backed_research", "bounded", "source or research cues", "research_cues"
    elif _contains_any(lower, ("compare", "tradeoff", "trade-off", "plan", "prioritize", "which option", "pros and cons", "strategy")):
        selected, confidence, basis, signal = "comparison_planning", "bounded", "comparison or planning cues", "comparison_planning_cues"
    elif request.get("approved_knowledge_available") is True:
        selected, confidence, basis, signal = "approved_knowledge", "bounded", "approved comprehension knowledge is available", "approved_knowledge"
    else:
        selected, confidence, basis, signal = "ordinary_conversation", "low", "no specialized domain cue; ordinary conversation is the least-claiming route", "default"
    if selected not in allowed:
        return _route(
            "unsupported",
            "high",
            f"The selected domain {selected} is outside this request's allowed domain set.",
            "domain_not_allowed",
            blocked_domain=selected,
        )
    return _route(selected, confidence, basis, signal)


def _route(
    domain: str,
    confidence: str,
    basis: str,
    signal: str,
    *,
    blocked_domain: str = "",
) -> dict[str, Any]:
    return {
        "selected_domain": domain,
        "route_confidence": confidence,
        "selection_basis": basis,
        "matched_signal": signal,
        "blocked_domain": blocked_domain,
        "adapter_status": "not_executed_contract_only" if domain != "unsupported" else "no_adapter_authorized",
        "core_mind_authority_preserved": True,
    }


def _looks_like_math(value: str) -> bool:
    lower = value.lower()
    if _contains_any(lower, ("calculate", "arithmetic", "equation", "solve for", "percentage", "square root", "multiply", "divide")):
        return True
    return bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:\+|-|\*|/|=|%|\^|×|÷)\s*\d", value))


def _allowed_domains(value: Any) -> list[str]:
    if value in (None, ""):
        return list(DOMAINS)
    items = value if isinstance(value, (list, tuple)) else [value]
    result: list[str] = []
    for item in items:
        domain = str(item).strip()
        if domain not in DOMAINS:
            raise ValueError(f"unsupported answer domain: {domain}")
        if domain not in result:
            result.append(domain)
    if not result:
        raise ValueError("allowed_domains must include at least one supported domain")
    return result


def _normalize_obligations(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value[:20]):
        if isinstance(item, dict):
            source_text = truncate(str(item.get("source_text") or item.get("question") or item.get("text") or ""), 600).strip()
            result.append(
                {
                    "id": truncate(str(item.get("id") or item.get("obligation_id") or f"obligation-{index + 1}"), 120),
                    "kind": truncate(str(item.get("kind") or "direct_question"), 80),
                    "source_text": source_text,
                    "required": item.get("required") is not False,
                    "coverage_terms": _text_list(item.get("coverage_terms"))[:20],
                }
            )
        elif str(item).strip():
            result.append(
                {
                    "id": f"obligation-{index + 1}",
                    "kind": "direct_question",
                    "source_text": truncate(str(item), 600),
                    "required": True,
                    "coverage_terms": [],
                }
            )
    return result


def _text_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [truncate(str(item), 1000).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [truncate(value, 1000).strip()]
    return []


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS, "provenance_boundary": payload.get("provenance_boundary") or ANSWER_ENGINE_BOUNDARY}
