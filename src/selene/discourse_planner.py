from __future__ import annotations

import re
from typing import Any

from .registry import truncate


DISCOURSE_BOUNDARY = (
    "supported_content_organization_only_no_fact_generation_memory_identity_authority_or_hidden_reasoning"
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
}

STOP_WORDS = {
    "a", "about", "and", "are", "as", "at", "be", "but", "can", "could", "did", "do", "does",
    "explain", "for", "from", "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or",
    "please", "should", "so", "that", "the", "this", "to", "we", "what", "when", "where", "which",
    "who", "why", "will", "with", "would", "you", "your",
}


def build_supported_discourse_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    seed = truncate(str(payload.get("content_seed") or ""), 5000).strip()
    depth = str(payload.get("response_depth") or "standard")
    profile = str(payload.get("expression_profile") or "direct")
    obligations = [item for item in payload.get("response_obligations") or [] if isinstance(item, dict)][:12]
    correction = payload.get("correction_refinement") if isinstance(payload.get("correction_refinement"), dict) else {}
    answer_support = payload.get("answer_support") if isinstance(payload.get("answer_support"), dict) else {}
    units = _content_units(
        seed,
        payload.get("support_points"),
        payload.get("examples"),
        payload.get("next_steps"),
        answer_support,
        correction,
    )
    bindings = _bind_obligations(obligations, units)
    uncovered = [
        str(item.get("obligation_id") or "")
        for item in bindings
        if item.get("required") is True and item.get("grounded") is not True
    ]
    paragraphs = _paragraph_plan(depth, units, bindings)
    closure = _closure_plan(units)
    return _with_guards(
        {
            "status": "supported_discourse_plan_ready",
            "version": "v1_grounded_obligation_discourse",
            "response_depth": depth,
            "expression_profile": profile,
            "thesis_unit_id": next((item["id"] for item in units if item["role"] == "thesis"), ""),
            "content_units": units,
            "obligation_bindings": bindings,
            "uncovered_obligation_ids": uncovered,
            "all_obligations_grounded": not uncovered,
            "paragraph_plan": paragraphs,
            "closure_plan": closure,
            "content_generation_allowed": False,
            "unsupported_gaps_must_remain_visible": True,
            "source_refs": _strings(payload.get("source_refs"))[:30],
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": DISCOURSE_BOUNDARY,
        }
    )


def _content_units(
    seed: str,
    support_points_value: Any,
    examples_value: Any,
    next_steps_value: Any,
    answer_support: dict[str, Any],
    correction: dict[str, Any],
) -> list[dict[str, Any]]:
    raw: list[tuple[str, str, str]] = []
    for index, sentence in enumerate(_sentences(seed)):
        raw.append((sentence, "thesis" if index == 0 else "support", "supplied_content_seed"))
    for value in _strings(support_points_value):
        raw.append((value, "support", "intelligence_support"))
    for value in _strings(examples_value):
        raw.append((value, "example", "supplied_semantic_example"))
    for value in _strings(next_steps_value):
        raw.append((value, "conclusion", "intelligence_support"))
    for value in _strings(answer_support.get("supporting_claims")):
        raw.append((value, "support", "answer_engine_support"))
    for value in _strings(answer_support.get("assumptions")):
        raw.append((value, "assumption", "answer_engine_support"))
    for value in _strings(answer_support.get("limitations")):
        raw.append((value, "limitation", "answer_engine_support"))
    for value in _strings(answer_support.get("what_would_change_the_answer")):
        raw.append((value, "reopening", "answer_engine_support"))
    corrected = truncate(str(correction.get("corrected_meaning") or ""), 300).strip()
    replaced = truncate(str(correction.get("replaced_meaning") or ""), 300).strip()
    if correction.get("detected") is True and corrected:
        text = f"{corrected} rather than {replaced}" if replaced else corrected
        raw.append((text, "correction", "current_session_correction"))

    units: list[dict[str, Any]] = []
    seen: set[str] = set()
    for text, role, source in raw:
        normalized = truncate(" ".join(text.split()), 900).strip()
        key = normalized.lower().rstrip(". ")
        if not key or key in seen:
            continue
        seen.add(key)
        units.append(
            {
                "id": f"content_{len(units) + 1}",
                "text": normalized,
                "role": role,
                "source": source,
                "terms": _terms(normalized),
                "supported": True,
            }
        )
    return units[:30]


def _bind_obligations(obligations: list[dict[str, Any]], units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for index, obligation in enumerate(obligations):
        obligation_id = str(obligation.get("id") or f"obligation_{index + 1}")
        kind = str(obligation.get("kind") or "direct_request")
        required = obligation.get("required") is not False
        expected = {
            str(item).lower()
            for item in obligation.get("coverage_terms") or _terms(str(obligation.get("source_text") or ""))
            if str(item).strip()
        }
        candidates: list[tuple[float, dict[str, Any]]] = []
        for unit in units:
            if kind == "correction_update" and unit.get("role") != "correction":
                continue
            if kind != "correction_update" and unit.get("role") == "correction":
                continue
            overlap = expected & set(unit.get("terms") or [])
            score = len(overlap) / len(expected) if expected else 0.0
            score += _role_bonus(kind, str(unit.get("role") or ""), str(unit.get("text") or "").lower())
            if overlap or (not expected and score > 0):
                candidates.append((score, unit))
        candidates.sort(key=lambda item: (-item[0], str(item[1].get("id") or "")))
        selected = [item for _, item in candidates[:2]]
        grounded = bool(selected)
        bindings.append(
            {
                "obligation_id": obligation_id,
                "kind": kind,
                "required": required,
                "source_text": truncate(str(obligation.get("source_text") or ""), 480),
                "content_unit_ids": [str(item.get("id") or "") for item in selected],
                "grounded": grounded,
                "coverage_state": "covered_by_supported_content" if grounded else "supported_content_gap",
                "binding_confidence": "bounded_lexical" if grounded else "unresolved",
            }
        )
    return bindings


def _role_bonus(kind: str, role: str, text: str) -> float:
    if kind == "correction_update" and role == "correction":
        return 1.0
    if kind == "reason" and role == "support":
        return 0.25
    if kind == "choice_or_priority" and any(word in text for word in ("first", "start", "priority", "before")):
        return 0.25
    if kind == "comparison" and any(word in text for word in ("both", "while", "whereas", "difference", "compare")):
        return 0.25
    if kind == "method" and any(word in text for word in ("first", "then", "step", "start")):
        return 0.25
    return 0.0


def _paragraph_plan(
    depth: str,
    units: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    thesis = [str(item["id"]) for item in units if item.get("role") == "thesis"][:1]
    bound = list(
        dict.fromkeys(
            unit_id
            for binding in bindings
            for unit_id in binding.get("content_unit_ids") or []
            if unit_id not in thesis
        )
    )
    support = [
        str(item["id"])
        for item in units
        if item.get("role") in {"support", "assumption", "example"}
        and str(item["id"]) not in thesis
        and str(item["id"]) not in bound
    ]
    limits = [str(item["id"]) for item in units if item.get("role") in {"limitation", "reopening", "conclusion"}]
    if depth == "brief":
        return [{"index": 1, "role": "answer", "content_unit_ids": [*thesis, *bound][:2], "transition": "none"}]
    if depth != "developed":
        return [
            {"index": 1, "role": "answer", "content_unit_ids": [*thesis, *bound], "transition": "none"},
            *(
                [{"index": 2, "role": "limit_or_reopening", "content_unit_ids": limits, "transition": "limit"}]
                if limits
                else []
            ),
        ]
    return [
        {"index": 1, "role": "answer", "content_unit_ids": thesis, "transition": "none"},
        {"index": 2, "role": "development", "content_unit_ids": [*bound, *support], "transition": "support"},
        {"index": 3, "role": "limit_and_closure", "content_unit_ids": limits, "transition": "reopening"},
    ]


def _closure_plan(units: list[dict[str, Any]]) -> dict[str, Any]:
    reopening = next((item for item in units if item.get("role") == "reopening"), None)
    limitation = next((item for item in units if item.get("role") == "limitation"), None)
    conclusion = next((item for item in units if item.get("role") == "conclusion"), None)
    selected = reopening or limitation or conclusion
    return {
        "mode": (
            "what_would_change"
            if reopening
            else "bounded_limit"
            if limitation
            else "supported_next_step"
            if conclusion
            else "stop_after_supported_content"
        ),
        "content_unit_id": str((selected or {}).get("id") or ""),
        "text": str((selected or {}).get("text") or ""),
        "question_required": False,
    }


def _sentences(value: str) -> list[str]:
    return [
        truncate(item.strip(), 900)
        for item in re.split(r"(?<=[.!?])\s+|\n+", value.strip())
        if item.strip()
    ][:16]


def _terms(value: str) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)]
    return list(dict.fromkeys(word for word in words if word not in STOP_WORDS))[:24]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [truncate(str(item), 900).strip() for item in value if str(item).strip()]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
