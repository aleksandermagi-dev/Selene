from __future__ import annotations

import re
import sqlite3
from hashlib import sha256
from typing import Any

from .intelligence_os import run_intelligence_os_reason
from .local_code_inspection import inspect_local_code
from .meaning_router import interpret_turn_meaning
from .pragmatic_planner import build_pragmatic_plan, evaluate_response_coverage
from .registry import truncate
from .source_backed_research import research_from_sources
from .supported_semantics import build_text_supported_semantic_packet
from .verified_math import verify_bounded_math


ANSWER_ENGINE_BOUNDARY = (
    "answer_engine_bounded_domain_coordination_supervised_chat_bridge_"
    "no_memory_identity_governance_or_authority_change"
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
    "live_chat_connected": True,
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
    adapter_status = {domain: "contract_only_not_connected" for domain in DOMAINS}
    adapter_status["verified_math"] = "exact_arithmetic_adapter_connected_to_supervised_chat"
    adapter_status["comparison_planning"] = "intelligence_os_adapter_connected_to_supervised_chat"
    adapter_status["source_backed_research"] = "attributed_source_packet_adapter_connected_to_supervised_chat"
    adapter_status["local_code_inspection"] = "explicit_source_static_inspection_available_not_connected_to_chat"
    return _with_guards(
        {
            "status": "answer_engine_supervised_chat_bridge_ready",
            "version": "v5_obligation_coordination_bridge",
            "phase": "phase_11_pre_teaching_architecture_closure",
            "domains": list(DOMAINS),
            "domain_adapter_status": adapter_status,
            "confidence_dimensions": [
                "route_confidence",
                "evidence_confidence",
                "answer_confidence",
                "memory_confidence",
                "expression_confidence",
            ],
            "completion_retry_available": True,
            "completion_retry_limit": 1,
            "completion_retry_domains": ["comparison_planning", "coordinated_supported_obligations"],
            "domain_routing_mode": "per_obligation_domain_coordination",
            "multi_domain_synthesis_available": True,
            "multi_domain_synthesis_limit": 4,
            "ordinary_conversation_remains_open_ended": True,
            "expression_only_math_available": True,
            "domain_request_fallback_obligation_available": True,
            "core_mind_route_owner": True,
            "nlo_expression_owner": True,
            "voice_style_owner": True,
            "great_library_external": True,
            "great_library_research_default_enabled": False,
            "great_library_research_requires_separate_enable": True,
            "open_ended_problem_solving_adapter": "comparison_planning",
            "open_ended_problem_solving_requires_preexisting_answer": False,
            "source_backed_research_does_not_replace_open_ended_reasoning": True,
            "supervised_chat_domains": ["verified_math", "comparison_planning", "source_backed_research"],
            "local_code_supervised_chat_connected": False,
            "local_code_chat_decision": "kept_as_an_explicit_separate_inspection_route",
            "source_backed_chat_requires_attributed_packets": True,
            "review_status": "status_only",
            "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
        }
    )


def preview_answer_coordination(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Route each required dialogue obligation without executing an adapter."""
    request = build_answer_request(payload)
    obligations = list(request.get("dialogue_obligations") or [])
    if not obligations:
        obligations = [
            {
                "id": f"turn-{request['request_id']}",
                "kind": "direct_question",
                "source_text": request["prompt"],
                "required": True,
                "coverage_terms": [],
            }
        ]
    units: list[dict[str, Any]] = []
    for obligation in obligations[:12]:
        source_text = str(obligation.get("source_text") or request["prompt"])
        parent_source = str(obligation.get("parent_source_text") or "")
        obligation_prompt = source_text
        if parent_source and re.search(
            r"\b(?:how many|altogether|calculate|count|total)\b",
            source_text,
            flags=re.IGNORECASE,
        ):
            obligation_prompt = f"{parent_source} {source_text}"
        obligation_domain = (
            request["requested_domain"]
            or _obligation_domain_hint(str(obligation.get("kind") or ""))
        )
        obligation_request = {
            **request,
            "prompt": obligation_prompt,
            "requested_domain": obligation_domain,
            "dialogue_obligations": [obligation],
            "obligation_count": 1,
            "meaning_route": interpret_turn_meaning(
                obligation_prompt,
                requested_domain=obligation_domain,
                source_packets_present=bool(request.get("source_packets")),
            ),
        }
        route = _select_domain(obligation_request)
        domain = str(route.get("selected_domain") or "ordinary_conversation")
        if domain == "local_code_inspection":
            owner = "separate_bounded_code_inspection_route"
            executable_in_chat = False
        elif domain in {"verified_math", "comparison_planning", "source_backed_research"}:
            owner = "answer_engine"
            executable_in_chat = True
        elif domain == "approved_knowledge":
            owner = "comprehension_integration"
            executable_in_chat = False
        elif domain == "unsupported":
            owner = "core_mind"
            executable_in_chat = False
        else:
            owner = "ordinary_conversation_path"
            executable_in_chat = False
        units.append(
            {
                "obligation": obligation,
                "selected_domain": domain,
                "route": route,
                "responsible_owner": owner,
                "executable_in_chat": executable_in_chat,
                "adapter_executed": False,
            }
        )
    domains = list(dict.fromkeys(str(item["selected_domain"]) for item in units))
    executable_domains = list(
        dict.fromkeys(
            str(item["selected_domain"])
            for item in units
            if item["executable_in_chat"] is True
        )
    )
    return _with_guards(
        {
            "status": "answer_engine_coordination_preview_ready",
            "request": request,
            "coordination_units": units,
            "domains": domains,
            "executable_chat_domains": executable_domains,
            "coordination_mode": (
                "coordinated_multi_domain"
                if len(domains) > 1
                else "single_domain"
            ),
            "multi_domain": len(domains) > 1,
            "adapter_executed": False,
            "answer_generated": False,
            "completion_cycle_limit": 1,
            "local_code_chat_connected": False,
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
            "next_phase": "execute only through a connected bounded adapter; other domains remain contract-only",
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
    conversation_spine = payload.get("conversation_spine") if isinstance(payload.get("conversation_spine"), dict) else {}
    supplied_obligations = payload.get("dialogue_obligations")
    if isinstance(supplied_obligations, list):
        obligations = _normalize_obligations(supplied_obligations)
    elif isinstance(conversation_spine.get("open_obligations"), list):
        obligations = _normalize_obligations(conversation_spine.get("open_obligations") or [])
    else:
        pragmatic = build_pragmatic_plan(
            {
                "prompt": prompt,
                "intent_decision": intent,
                "dialogue_workspace": dialogue,
                "conversation_spine": conversation_spine,
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
    meaning_route = interpret_turn_meaning(
        prompt,
        requested_domain=requested_domain,
        source_packets_present=bool(source_packets),
    )
    knowledge_context = comprehension.get("knowledge_context") if isinstance(comprehension.get("knowledge_context"), dict) else {}
    eligible_knowledge = knowledge_context.get("answer_eligible_items")
    if not isinstance(eligible_knowledge, list):
        eligible_knowledge = knowledge_context.get("items") if knowledge_context.get("available") is True else []
    return {
        "request_id": request_id,
        "prompt": prompt,
        "intent": str(intent.get("intent") or "direct_conversation"),
        "answer_shape": str(intent.get("answer_shape") or "direct_answer"),
        "requested_depth": str(payload.get("requested_depth") or intent.get("response_depth") or "standard"),
        "dialogue_obligations": obligations,
        "obligation_count": len(obligations),
        "approved_knowledge_available": bool(eligible_knowledge),
        "approved_knowledge_items": [
            {
                "concept_id": item.get("concept_id") or item.get("id"),
                "title": truncate(str(item.get("title") or ""), 240),
                "source_refs": _text_list(item.get("source_refs")),
            }
            for item in eligible_knowledge
            if isinstance(item, dict)
        ][:10],
        "source_packets": source_packets,
        "memory_context": {
            "used": memory.get("memory_context_used") is True,
            "confidence": str(memory.get("memory_confidence") or "not_used"),
        },
        "requested_domain": requested_domain,
        "allowed_domains": allowed,
        "meaning_route": meaning_route,
        "conversation_spine": {
            "turn_id": str(conversation_spine.get("turn_id") or ""),
            "intent_class": str(conversation_spine.get("intent_class") or ""),
            "active_topic": str(conversation_spine.get("active_topic") or ""),
            "distinctive_terms": _text_list(conversation_spine.get("distinctive_terms"))[:40],
            "source_compatibility": conversation_spine.get("source_compatibility") or {},
        },
        "conversation_spine_used": bool(conversation_spine),
        "authority_bearing_request": _contains_any(str(meaning_route.get("routing_text") or prompt.lower()), AUTHORITY_MARKERS),
        "current_session_only": True,
        "raw_corpus_available": False,
        "review_status": "status_only",
        "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
    }


def preview_domain_answer_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _domain_answer_packet(payload or {}, adapter_executed=False, contract_preview=True)


def _domain_answer_packet(
    payload: dict[str, Any],
    *,
    adapter_executed: bool,
    contract_preview: bool,
) -> dict[str, Any]:
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
        "status": "domain_answer_packet_preview_ready" if contract_preview else "domain_answer_packet_ready",
        "request_id": truncate(str(payload.get("request_id") or "unbound_request"), 120),
        "domain": domain,
        "direct_answer": direct_answer,
        "supporting_claims": _text_list(payload.get("supporting_claims"))[:20],
        "source_refs": source_refs,
        "assumptions": _text_list(payload.get("assumptions"))[:20],
        "limitations": _text_list(payload.get("limitations"))[:20],
        "unanswered_obligations": _normalize_obligations(payload.get("unanswered_obligations") or []),
        "what_would_change_the_answer": _text_list(payload.get("what_would_change_the_answer"))[:20],
        "claim_evidence_packet": (
            payload.get("claim_evidence_packet")
            if isinstance(payload.get("claim_evidence_packet"), dict)
            else {}
        ),
        "no_answer_reason": no_answer_reason,
        "evidence_confidence": evidence_confidence,
        "answer_confidence": str(payload.get("answer_confidence") or "not_assessed"),
        "supported_semantics": build_text_supported_semantic_packet(
            direct_answer or no_answer_reason,
            answer_kind=f"{domain}_answer",
            source_kind=(
                "attributed_source"
                if domain == "source_backed_research"
                else "verified_domain_answer"
            ),
            source_refs=source_refs,
            certainty=str(payload.get("answer_confidence") or "not_assessed"),
            scope=domain,
        ),
        "adapter_executed": adapter_executed,
        "packet_is_contract_preview": contract_preview,
        "review_status": "status_only",
        "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
    }
    return _with_guards(packet)


def build_confidence_vector(
    request: dict[str, Any],
    *,
    route_confidence: str = "not_assessed",
    route_basis: str = "",
    evidence_confidence: str = "",
    answer_confidence: str = "not_assessed",
    expression_confidence: str = "not_assessed",
) -> dict[str, Any]:
    source_count = len(request.get("source_packets") or [])
    knowledge_available = request.get("approved_knowledge_available") is True
    resolved_evidence_confidence = evidence_confidence or (
        "source_packets_present" if source_count else "reviewed_knowledge_present" if knowledge_available else "not_assessed"
    )
    memory = request.get("memory_context") if isinstance(request.get("memory_context"), dict) else {}
    memory_confidence = str(memory.get("confidence") or "not_used") if memory.get("used") is True else "not_used"
    return {
        "route_confidence": route_confidence,
        "route_confidence_basis": route_basis,
        "evidence_confidence": resolved_evidence_confidence,
        "answer_confidence": answer_confidence,
        "memory_confidence": memory_confidence,
        "expression_confidence": expression_confidence,
        "dimensions_are_independent": True,
        "voice_confidence_is_answer_correctness": False,
        "answer_fluency_is_evidence_strength": False,
    }


def run_verified_math_answer(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run the deterministic Phase 3 exact-arithmetic adapter."""
    payload = payload or {}
    request_payload = dict(payload)
    expression = str(payload.get("expression") or "").strip()
    if expression and not str(payload.get("prompt") or payload.get("text") or "").strip():
        request_payload["prompt"] = expression
        request_payload.setdefault("requested_domain", "verified_math")
    request = build_answer_request(request_payload)
    route = _select_domain(request)
    if route["selected_domain"] != "verified_math":
        return _with_guards(
            {
                "status": "answer_engine_domain_adapter_not_available",
                "request": request,
                "domain_route": route,
                "available_adapter": "verified_math",
                "adapter_executed": False,
                "answer_generated": False,
                "completion_retry": _completion_retry_result(False, 0, [], enabled=False),
                "review_status": "status_only",
                "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
            }
        )

    request = _ensure_domain_request_obligation(request, "math_verification")
    verification = verify_bounded_math(
        {
            "expression": payload.get("expression"),
            "prompt": request["prompt"],
        }
    )
    verified = verification.get("verified") is True
    direct_answer = str(verification.get("result_summary") or "").strip() if verified else ""
    if verified:
        direct_answer = truncate(
            f"{direct_answer} {_verified_math_explanation(request['prompt'], verification)}".strip(),
            5000,
        )
    no_answer_reason = "" if verified else str(verification.get("no_answer_reason") or "").strip()
    packet = _domain_answer_packet(
        {
            "request_id": request["request_id"],
            "domain": "verified_math",
            "direct_answer": direct_answer,
            "no_answer_reason": no_answer_reason,
            "supporting_claims": verification.get("checked_steps") or [],
            "source_refs": verification.get("source_refs") or [],
            "assumptions": verification.get("assumptions") or [],
            "limitations": verification.get("limitations") or [],
            "unanswered_obligations": [] if verified else request["dialogue_obligations"],
            "what_would_change_the_answer": (
                ["A different arithmetic expression or correction to the supplied values."]
                if verified
                else ["An explicit expression inside the documented exact-arithmetic boundary."]
            ),
            "evidence_confidence": verification["evidence_confidence"],
            "answer_confidence": verification["answer_confidence"],
        },
        adapter_executed=True,
        contract_preview=False,
    )
    confidence = build_confidence_vector(
        request,
        route_confidence=route["route_confidence"],
        route_basis=route["selection_basis"],
        evidence_confidence=verification["evidence_confidence"],
        answer_confidence=verification["answer_confidence"],
        expression_confidence="not_assessed",
    )
    return _with_guards(
        {
            "status": (
                "answer_engine_verified_math_answer_ready"
                if verified
                else "answer_engine_verified_math_unable_to_answer"
            ),
            "request": request,
            "domain_route": {
                **route,
                "adapter_status": "exact_arithmetic_adapter_executed_status_only",
            },
            "answer_packet": packet,
            "confidence_vector": confidence,
            "math_verification": verification,
            "completion_retry": _completion_retry_result(False, 0, [], enabled=False),
            "adapter_executed": True,
            "answer_generated": bool(direct_answer),
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "review_status": "status_only",
            "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
        }
    )


def _verified_math_explanation(prompt: str, verification: dict[str, Any]) -> str:
    """Add only explanation/example material derivable from a verified addition."""
    lower = str(prompt or "").lower()
    asks_why = bool(re.search(r"\bwhy\b|\bexplain\b", lower))
    asks_example = bool(
        re.search(r"\b(?:different|another|distinct)\s+example\b|\bgive (?:me )?an example\b", lower)
    )
    if not asks_why and not asks_example:
        return ""
    expression = str(
        verification.get("normalized_expression")
        or verification.get("expression")
        or ""
    ).replace(" ", "")
    addition = re.fullmatch(
        r"(\d+)\+(\d+)(?:=(\d+))?",
        expression,
    )
    if not addition:
        return ""
    left = int(addition.group(1))
    right = int(addition.group(2))
    result = left + right
    parts: list[str] = []
    if asks_why:
        parts.append(
            f"Because addition counts combined quantities: {left} items together with "
            f"{right} more items gives {result} items."
        )
    if asks_example:
        example_left = left + 1
        example_result = example_left + right
        parts.append(
            f"A different example is {example_left} + {right} = {example_result}: "
            f"{example_left} items together with {right} more gives {example_result}."
        )
    return " ".join(parts)


def run_local_code_inspection_answer(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run bounded static inspection over only supplied or approved code sources."""
    payload = payload or {}
    request = build_answer_request(payload)
    route = _select_domain(request)
    if route["selected_domain"] != "local_code_inspection":
        return _adapter_not_available(request, route, "local_code_inspection")
    request = _ensure_domain_request_obligation(request, "local_code_inspection")
    inspection = inspect_local_code(
        {
            "prompt": request["prompt"],
            "inspection_terms": payload.get("inspection_terms"),
            "code_packets": payload.get("code_packets") or [],
            "approved_workspace_files": payload.get("approved_workspace_files") or [],
        }
    )
    inspected = inspection.get("inspected") is True
    direct_answer = str(inspection.get("result_summary") or "").strip() if inspected else ""
    no_answer_reason = "" if inspected else str(inspection.get("no_answer_reason") or "").strip()
    supporting = [
        str(item.get("observation") or "")
        for item in inspection.get("observations") or []
        if item.get("observation")
    ]
    supporting.extend(
        f"Interpretation: {item['interpretation']}"
        for item in inspection.get("interpretations") or []
        if item.get("interpretation")
    )
    packet = _domain_answer_packet(
        {
            "request_id": request["request_id"],
            "domain": "local_code_inspection",
            "direct_answer": direct_answer,
            "no_answer_reason": no_answer_reason,
            "supporting_claims": supporting,
            "source_refs": inspection.get("source_refs") or [],
            "assumptions": inspection.get("assumptions") or [],
            "limitations": inspection.get("limitations") or [],
            "unanswered_obligations": [] if inspected else request["dialogue_obligations"],
            "what_would_change_the_answer": [
                "Additional explicitly supplied code or exact approved workspace files.",
                "Runtime evidence when the question concerns behavior not established by static inspection.",
            ],
            "evidence_confidence": inspection["evidence_confidence"],
            "answer_confidence": inspection["answer_confidence"],
        },
        adapter_executed=True,
        contract_preview=False,
    )
    confidence = build_confidence_vector(
        request,
        route_confidence=route["route_confidence"],
        route_basis=route["selection_basis"],
        evidence_confidence=inspection["evidence_confidence"],
        answer_confidence=inspection["answer_confidence"],
        expression_confidence="not_assessed",
    )
    return _with_guards(
        {
            "status": (
                "answer_engine_local_code_inspection_ready"
                if inspected
                else "answer_engine_local_code_inspection_unable"
            ),
            "request": request,
            "domain_route": {**route, "adapter_status": "explicit_source_static_inspection_executed_status_only"},
            "answer_packet": packet,
            "confidence_vector": confidence,
            "code_inspection": inspection,
            "completion_retry": _completion_retry_result(False, 0, [], enabled=False),
            "adapter_executed": True,
            "answer_generated": bool(direct_answer),
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "review_status": "status_only",
            "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
        }
    )


def run_source_backed_research_answer(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run bounded research over attributed packets and optional external Library observation."""
    payload = payload or {}
    request = build_answer_request(payload)
    route = _select_domain(request)
    if route["selected_domain"] != "source_backed_research":
        return _adapter_not_available(request, route, "source_backed_research")
    request = _ensure_domain_request_obligation(request, "source_backed_research")
    research = research_from_sources(
        {
            "prompt": request["prompt"],
            "source_packets": request["source_packets"],
            "consult_great_library": payload.get("consult_great_library") is True,
        }
    )
    answered = research.get("answered") is True
    direct_answer = str(research.get("result_summary") or "").strip() if answered else ""
    no_answer_reason = "" if answered else str(research.get("no_answer_reason") or "").strip()
    supporting = [
        f"[{item['source_ref']} @ {item['locator']}] {item['text']}"
        for item in research.get("source_statements") or []
    ]
    supporting.extend(str(item.get("text") or "") for item in research.get("inferences") or [] if item.get("text"))
    packet = _domain_answer_packet(
        {
            "request_id": request["request_id"],
            "domain": "source_backed_research",
            "direct_answer": direct_answer,
            "no_answer_reason": no_answer_reason,
            "supporting_claims": supporting,
            "source_refs": research.get("source_refs") or [],
            "assumptions": research.get("assumptions") or [],
            "limitations": research.get("limitations") or [],
            "unanswered_obligations": [] if answered else request["dialogue_obligations"],
            "what_would_change_the_answer": research.get("missing_evidence") or [
                "Additional attributed source packets relevant to the request."
            ],
            "claim_evidence_packet": research.get("claim_evidence_packet") or {},
            "evidence_confidence": research["evidence_confidence"],
            "answer_confidence": research["answer_confidence"],
        },
        adapter_executed=True,
        contract_preview=False,
    )
    confidence = build_confidence_vector(
        request,
        route_confidence=route["route_confidence"],
        route_basis=route["selection_basis"],
        evidence_confidence=research["evidence_confidence"],
        answer_confidence=research["answer_confidence"],
        expression_confidence="not_assessed",
    )
    return _with_guards(
        {
            "status": (
                "answer_engine_source_backed_research_ready"
                if answered
                else "answer_engine_source_backed_research_unable"
            ),
            "request": request,
            "domain_route": {**route, "adapter_status": "attributed_source_packet_adapter_executed_status_only"},
            "answer_packet": packet,
            "confidence_vector": confidence,
            "source_research": research,
            "completion_retry": _completion_retry_result(False, 0, [], enabled=False),
            "adapter_executed": True,
            "answer_generated": bool(direct_answer),
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "review_status": "status_only",
            "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
        }
    )


def run_comparison_planning_answer(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    initial_run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the one Phase 2 domain adapter with at most one completion retry."""
    payload = payload or {}
    request = build_answer_request(payload)
    route = _select_domain(request)
    if route["selected_domain"] != "comparison_planning":
        return _with_guards(
            {
                "status": "answer_engine_domain_adapter_not_available",
                "request": request,
                "domain_route": route,
                "available_adapter": "comparison_planning",
                "adapter_executed": False,
                "answer_generated": False,
                "completion_retry": _completion_retry_result(False, 0, [], enabled=False),
                "review_status": "status_only",
                "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
            }
        )

    source_refs = _answer_source_refs(request, payload)
    initial_run = initial_run or run_intelligence_os_reason(
        conn,
        _intelligence_os_payload(request["prompt"], source_refs, payload),
    )
    initial_answer = truncate(str(initial_run.get("best_current_answer") or ""), 5000).strip()
    coverage_plan = {
        "response_obligations": [
            item for item in request["dialogue_obligations"] if item.get("required") is not False
        ]
    }
    conversation_spine = payload.get("conversation_spine") if isinstance(payload.get("conversation_spine"), dict) else {}
    initial_coverage = evaluate_response_coverage(
        coverage_plan,
        initial_answer,
        conversation_spine=conversation_spine,
    )
    final_answer = initial_answer
    final_coverage = initial_coverage
    runs = [initial_run]
    retry_enabled = payload.get("completion_retry_enabled") is not False
    retry_attempted = False

    if retry_enabled and not initial_coverage["all_required_addressed"]:
        retry_attempted = True
        missing = _unresolved_obligations(request["dialogue_obligations"], initial_coverage)
        retry_prompt = _completion_retry_prompt(request["prompt"], initial_answer, missing)
        retry_run = run_intelligence_os_reason(
            conn,
            _intelligence_os_payload(retry_prompt, source_refs, payload),
        )
        runs.append(retry_run)
        supplement = truncate(str(retry_run.get("best_current_answer") or ""), 5000).strip()
        final_answer = _combine_answer_parts(initial_answer, supplement)
        final_coverage = evaluate_response_coverage(
            coverage_plan,
            final_answer,
            conversation_spine=conversation_spine,
        )

    unresolved = _unresolved_obligations(request["dialogue_obligations"], final_coverage)
    evidence_confidence = _comparison_evidence_confidence(request)
    answer_confidence = str(runs[-1].get("confidence") or "not_assessed")
    if unresolved:
        answer_confidence = "partial_missing_obligations"
    packet_source_refs = list(source_refs)
    packet_source_refs.extend(
        f"intelligence_os_run:{run['run_id']}" for run in runs if run.get("run_id") is not None
    )
    packet = _domain_answer_packet(
        {
            "request_id": request["request_id"],
            "domain": "comparison_planning",
            "direct_answer": final_answer,
            "no_answer_reason": "" if final_answer else "intelligenceOS did not produce a bounded answer",
            "supporting_claims": [
                run.get("reasoning_summary") for run in runs if run.get("reasoning_summary")
            ],
            "source_refs": packet_source_refs,
            "assumptions": _run_assumptions(runs),
            "limitations": _run_limitations(runs),
            "unanswered_obligations": unresolved,
            "what_would_change_the_answer": _run_unknowns(runs),
            "claim_evidence_packet": (
                runs[-1].get("claim_evidence_packet")
                if isinstance(runs[-1].get("claim_evidence_packet"), dict)
                else {}
            ),
            "evidence_confidence": evidence_confidence,
            "answer_confidence": answer_confidence,
        },
        adapter_executed=True,
        contract_preview=False,
    )
    executed_route = {
        **route,
        "adapter_status": "intelligence_os_adapter_executed_status_only",
    }
    confidence = build_confidence_vector(
        request,
        route_confidence=route["route_confidence"],
        route_basis=route["selection_basis"],
        evidence_confidence=evidence_confidence,
        answer_confidence=answer_confidence,
        expression_confidence="not_assessed",
    )
    status = (
        "answer_engine_comparison_answer_ready"
        if final_coverage["all_required_addressed"]
        else "answer_engine_comparison_incomplete_after_bounded_retry"
    )
    return _with_guards(
        {
            "status": status,
            "request": request,
            "domain_route": executed_route,
            "answer_packet": packet,
            "confidence_vector": confidence,
            "initial_response_coverage": initial_coverage,
            "final_response_coverage": final_coverage,
            "completion_retry": _completion_retry_result(
                retry_attempted,
                1 if retry_attempted else 0,
                unresolved,
                enabled=retry_enabled,
            ),
            "intelligence_os_runs": [_run_summary(run) for run in runs],
            "adapter_executed": True,
            "answer_generated": bool(final_answer),
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "review_status": "status_only",
            "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
        }
    )


def _intelligence_os_payload(prompt: str, source_refs: list[str], payload: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"prompt": prompt, "source_refs": source_refs}
    for key in ("observations", "candidate_models"):
        if payload.get(key) is not None:
            result[key] = payload[key]
    return result


def _answer_source_refs(request: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    refs = _text_list(payload.get("source_refs"))
    for packet in request.get("source_packets") or []:
        ref = packet.get("source_ref") or packet.get("ref") or packet.get("id")
        if ref not in (None, ""):
            refs.append(str(ref))
    for item in request.get("approved_knowledge_items") or []:
        refs.extend(_text_list(item.get("source_refs")))
    return list(dict.fromkeys(refs))[:30] or ["answer_engine:comparison_planning_request"]


def _unresolved_obligations(
    obligations: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    unresolved_ids = {
        str(item.get("obligation_id") or "")
        for item in coverage.get("items") or []
        if item.get("addressed") is not True
    }
    return [item for item in obligations if str(item.get("id") or "") in unresolved_ids]


def _completion_retry_prompt(
    original_prompt: str,
    initial_answer: str,
    missing: list[dict[str, Any]],
) -> str:
    missing_text = "; ".join(
        str(item.get("source_text") or item.get("id") or "missing part") for item in missing
    )
    return truncate(
        f"{original_prompt}\n\nThe first bounded answer was: {initial_answer}\n\n"
        f"Complete only these still-open parts: {missing_text}. "
        "If the available context cannot support one, leave it explicitly open. Do not restart the whole answer.",
        2400,
    )


def _combine_answer_parts(initial: str, supplement: str) -> str:
    if not supplement or supplement == initial:
        return initial
    if supplement in initial:
        return initial
    initial_sentences = _answer_sentences(initial)
    accepted: list[str] = []
    for sentence in _answer_sentences(supplement):
        terms = _answer_terms(sentence)
        duplicate = any(
            _term_similarity(terms, _answer_terms(existing)) >= 0.72
            for existing in [*initial_sentences, *accepted]
        )
        if not duplicate:
            accepted.append(sentence)
    if not accepted:
        return initial
    return truncate(f"{initial}\n\n{' '.join(accepted)}".strip(), 5000)


def _answer_sentences(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+|\n+", str(value or "").strip())
        if item.strip()
    ]


def _answer_terms(value: str) -> set[str]:
    stop = {
        "about", "also", "and", "are", "because", "for", "from", "have", "into",
        "that", "the", "then", "this", "with", "would", "you", "your",
    }
    return {
        word
        for word in re.findall(r"[a-z][a-z0-9_-]{2,}", value.lower())
        if word not in stop
    }


def _term_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def _completion_retry_result(
    attempted: bool,
    count: int,
    unresolved: list[dict[str, Any]],
    *,
    enabled: bool,
) -> dict[str, Any]:
    return {
        "allowed": enabled,
        "limit": 1,
        "attempted": attempted,
        "count": count,
        "stopped": True,
        "remaining_obligation_count": len(unresolved),
        "recursion_allowed": False,
    }


def _run_summary(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": run.get("run_id"),
        "confidence": str(run.get("confidence") or "not_assessed"),
        "answer_shape": str(run.get("answer_shape") or ""),
        "selected_next_step": str(run.get("selected_next_step") or ""),
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
    }


def _run_assumptions(runs: list[dict[str, Any]]) -> list[str]:
    return _unique_nested_text(runs, "candidate_models", "assumptions")


def _run_unknowns(runs: list[dict[str, Any]]) -> list[str]:
    return _unique_nested_text(runs, "candidate_models", "unknowns")


def _run_limitations(runs: list[dict[str, Any]]) -> list[str]:
    result = _unique_nested_text(runs, "candidate_models", "limitations")
    for run in runs:
        challenge = run.get("challenge") if isinstance(run.get("challenge"), dict) else {}
        result.extend(_text_list(challenge.get("bias_flags")))
    return list(dict.fromkeys(result))[:20]


def _unique_nested_text(runs: list[dict[str, Any]], collection: str, key: str) -> list[str]:
    result: list[str] = []
    for run in runs:
        for item in run.get(collection) or []:
            if isinstance(item, dict):
                result.extend(_text_list(item.get(key)))
    return list(dict.fromkeys(result))[:20]


def _comparison_evidence_confidence(request: dict[str, Any]) -> str:
    if request.get("source_packets"):
        return "source_packets_present_not_independently_verified"
    if request.get("approved_knowledge_available") is True:
        return "reviewed_knowledge_present"
    return "reasoning_only_not_source_verified"


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
    else:
        meaning = request.get("meaning_route") if isinstance(request.get("meaning_route"), dict) else {}
        meaning_candidates = meaning.get("domain_candidates") if isinstance(meaning.get("domain_candidates"), list) else []
        primary = meaning_candidates[0] if meaning_candidates and isinstance(meaning_candidates[0], dict) else {}
        meaning_domain = str(primary.get("domain") or "")
        meaning_confidence = str(primary.get("confidence") or "low")
        meaning_evidence = primary.get("evidence") if isinstance(primary.get("evidence"), list) else []
        if meaning_domain and meaning_domain != "ordinary_conversation":
            selected = meaning_domain
            confidence = meaning_confidence
            basis = "; ".join(str(item) for item in meaning_evidence[:3]) or "structured turn meaning"
            signal = "structured_meaning_route"
        elif request.get("approved_knowledge_available") is True:
            selected, confidence, basis, signal = "approved_knowledge", "bounded", "approved comprehension knowledge is available", "approved_knowledge"
        else:
            selected, confidence, basis, signal = "ordinary_conversation", "low", "no specialized domain meaning; ordinary conversation is the least-claiming route", "structured_default"
    if not requested and selected in {"ordinary_conversation", "comparison_planning", "approved_knowledge"} and _looks_like_math(prompt):
        selected, confidence, basis, signal = "verified_math", "bounded", "numeric or symbolic verification cues", "math_cues"
    elif not requested and selected == "ordinary_conversation" and _contains_any(lower, ("traceback", "stack trace", "function", "class ", "source code", "code review", ".py", ".ts", ".tsx", "sql query")):
        selected, confidence, basis, signal = "local_code_inspection", "bounded", "explicit code-inspection cues", "code_cues"
    elif not requested and selected == "ordinary_conversation" and _contains_any(lower, ("cite", "citation", "source-backed", "sources", "research", "paper", "study", "literature")):
        selected, confidence, basis, signal = "source_backed_research", "bounded", "source or research cues", "research_cues"
    elif not requested and selected == "ordinary_conversation" and _contains_any(lower, ("compare", "tradeoff", "trade-off", "plan", "prioritize", "which option", "pros and cons", "strategy")):
        selected, confidence, basis, signal = "comparison_planning", "bounded", "comparison or planning cues", "comparison_planning_cues"
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
        "routing_mode": "single_primary_domain",
        "multi_domain_synthesis_available": False,
    }


def _ensure_domain_request_obligation(request: dict[str, Any], kind: str) -> dict[str, Any]:
    if request.get("dialogue_obligations"):
        return request
    fallback = {
        "id": f"{kind}-{request['request_id']}",
        "kind": kind,
        "source_text": truncate(str(request.get("prompt") or ""), 600),
        "required": True,
        "coverage_terms": [],
    }
    return {
        **request,
        "dialogue_obligations": [fallback],
        "obligation_count": 1,
        "obligation_source": "domain_request_fallback",
    }


def _obligation_domain_hint(kind: str) -> str:
    normalized = str(kind or "").strip().lower()
    if any(marker in normalized for marker in ("math", "arithmetic", "calculate")):
        return "verified_math"
    if any(marker in normalized for marker in ("code", "inspection", "traceback")):
        return "local_code_inspection"
    if any(marker in normalized for marker in ("research", "source", "citation")):
        return "source_backed_research"
    if any(marker in normalized for marker in ("comparison", "planning", "plan", "option")):
        return "comparison_planning"
    return ""


def _adapter_not_available(
    request: dict[str, Any],
    route: dict[str, Any],
    available_adapter: str,
) -> dict[str, Any]:
    return _with_guards(
        {
            "status": "answer_engine_domain_adapter_not_available",
            "request": request,
            "domain_route": route,
            "available_adapter": available_adapter,
            "adapter_executed": False,
            "answer_generated": False,
            "completion_retry": _completion_retry_result(False, 0, [], enabled=False),
            "review_status": "status_only",
            "provenance_boundary": ANSWER_ENGINE_BOUNDARY,
        }
    )


def _looks_like_math(value: str) -> bool:
    lower = value.lower()
    if _contains_any(lower, ("calculate", "arithmetic", "equation", "solve for", "percentage", "square root")):
        return True
    if _contains_any(lower, ("multiply", "divide")) and re.search(r"\d", value):
        return True
    if re.search(
        r"\b\d+(?:\.\d+)?\s+(?:plus|minus|times|multiplied\s+by|divided\s+by)\s+"
        r"\d+(?:\.\d+)?\b",
        value,
        flags=re.IGNORECASE,
    ):
        return True
    number = r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    if re.search(
        rf"\b{number}\s+(?:rows?|shelves|groups?|boxes|bags|teams?|tables?|trays)\b"
        rf".{{0,80}}?\b{number}\s+[a-z][a-z-]*(?:\s+[a-z][a-z-]*){{0,2}}\s+each\b",
        value,
        flags=re.IGNORECASE,
    ):
        return True
    if re.search(r"\b\d+\b\s*(?:vs\.?|versus|compared\s+(?:with|to))\s*\b\d+\b", value, flags=re.IGNORECASE) and re.search(
        r"\b(?:subtract(?:ion)?|difference|how many more)\b", value, flags=re.IGNORECASE
    ):
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
                    "parent_source_text": truncate(str(item.get("parent_source_text") or ""), 600),
                    "topic": truncate(str(item.get("topic") or ""), 240),
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
