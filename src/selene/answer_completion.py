from __future__ import annotations

import re
from typing import Any

from .answer_substance import build_answer_substance
from .pragmatic_planner import evaluate_response_coverage
from .registry import truncate


COMPLETION_BOUNDARY = (
    "one_pass_supported_obligation_completion_only_no_fact_invention_memory_identity_governance_authority_or_recursion"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
}

_STOP = {
    "about", "after", "again", "also", "and", "answer", "because", "before", "can", "could", "does",
    "explain", "for", "from", "give", "have", "how", "into", "just", "more", "please", "should", "that",
    "the", "their", "then", "there", "this", "what", "when", "where", "which", "with", "would", "you", "your",
}


def build_bounded_answer_completion(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Complete missing visible obligations once from already supported material.

    The pass may reuse approved knowledge or prompt-grounded reasoning methods.
    When neither can answer a part, it states the missing ground instead of
    manufacturing content. It never recurses or calls a provider.
    """
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or ""), 2400)
    seed = truncate(str(payload.get("content_seed") or "").strip(), 5000)
    obligations = [item for item in payload.get("response_obligations") or [] if isinstance(item, dict)][:20]
    knowledge_items = [item for item in payload.get("knowledge_items") or [] if isinstance(item, dict)][:10]
    observations = [item for item in payload.get("observations") or [] if isinstance(item, dict)][:20]
    spine = payload.get("conversation_spine") if isinstance(payload.get("conversation_spine"), dict) else {}
    coverage_plan = {"response_obligations": obligations}
    initial_coverage = evaluate_response_coverage(coverage_plan, seed, conversation_spine=spine)
    base = {
        "status": "bounded_answer_completion_not_needed",
        "attempted": False,
        "accepted": False,
        "count": 0,
        "limit": 1,
        "recursion_allowed": False,
        "provider_call_allowed": False,
        "content_seed": seed,
        "initial_coverage": initial_coverage,
        "final_coverage": initial_coverage,
        "resolutions": [],
        "source_classes": [],
        "unsupported_parts_remain_visible": True,
        "provenance_boundary": COMPLETION_BOUNDARY,
    }
    if not obligations or initial_coverage.get("all_required_addressed") is True:
        return _with_guards(base)

    missing_ids = {
        str(item.get("obligation_id") or "")
        for item in initial_coverage.get("items") or []
        if isinstance(item, dict) and item.get("addressed") is not True
    }
    fragments: list[str] = []
    resolutions: list[dict[str, Any]] = []
    source_classes: list[str] = []
    for obligation in obligations:
        obligation_id = str(obligation.get("id") or "")
        if obligation_id not in missing_ids or obligation.get("required") is False:
            continue
        kind = str(obligation.get("kind") or "direct_question")
        source_text = truncate(str(obligation.get("source_text") or prompt), 700)
        reasoning_text = truncate(
            source_text
            if not prompt or prompt.lower() in source_text.lower()
            else f"{prompt} {source_text}",
            1800,
        )
        if kind == "correction_update":
            continue
        knowledge_query = " ".join(
            part
            for part in (
                source_text,
                str(obligation.get("parent_source_text") or ""),
                str(obligation.get("topic") or ""),
            )
            if part.strip()
        )
        knowledge = _best_knowledge_item(knowledge_query, knowledge_items)
        fragment, support_kind = _knowledge_fragment(obligation, knowledge) if knowledge else ("", "")
        source_class = "approved_knowledge" if fragment else ""
        if not fragment and kind in {
            "comparison", "reason", "method", "choice_or_priority", "direct_request", "direct_question",
            "constraint_preservation", "limitation", "requested_output", "requested_section",
        }:
            substance = build_answer_substance(reasoning_text, observations)
            fragment = truncate(str(substance.get("answer") or ""), 1200)
            support_kind = str(substance.get("answer_kind") or "prompt_grounded_method")
            if substance.get("source_required_for_factual_claim") is True or support_kind in {
                "bounded_knowledge_gap", "source_needed", "causal_evidence_needed", "unsupported_fact"
            }:
                support_kind = "explicit_unsupported_part"
                source_class = "conversation"
            else:
                source_class = "reasoning_answer"
        if not fragment:
            topic = " ".join(_terms(source_text)[:8]) or "that part"
            fragment = (
                f"On {topic}, I do not have enough grounded information to answer that part reliably yet."
            )
            support_kind = "explicit_unsupported_part"
            source_class = "conversation"
        key = " ".join(fragment.lower().split()).rstrip(". ")
        if key and key not in {" ".join(item.lower().split()).rstrip(". ") for item in fragments}:
            fragments.append(fragment)
        resolutions.append(
            {
                "obligation_id": obligation_id,
                "kind": kind,
                "resolution": support_kind,
                "source_class": source_class,
                "concept_id": (knowledge or {}).get("id") or (knowledge or {}).get("concept_id"),
                "source_refs": _texts((knowledge or {}).get("source_refs")),
                "unsupported": support_kind == "explicit_unsupported_part",
            }
        )
        source_classes.append(source_class)

    combined = _combine(seed, fragments)
    final_coverage = evaluate_response_coverage(coverage_plan, combined, conversation_spine=spine)
    improved = _coverage_rank(final_coverage) > _coverage_rank(initial_coverage)
    status = "bounded_answer_completion_improved" if improved else "bounded_answer_completion_no_improvement"
    return _with_guards(
        {
            **base,
            "status": status,
            "attempted": True,
            "accepted": improved,
            "count": 1,
            "content_seed": combined if improved else seed,
            "initial_coverage": initial_coverage,
            "final_coverage": final_coverage if improved else initial_coverage,
            "resolutions": resolutions,
            "source_classes": list(dict.fromkeys(source_classes)),
            "unsupported_resolution_count": sum(1 for item in resolutions if item.get("unsupported") is True),
        }
    )


def _best_knowledge_item(text: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
    query = set(_terms(text))
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(items):
        haystack = " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("central_claim") or ""),
                *[str(value) for value in item.get("principles") or []],
                *[str(value) for value in item.get("relationships") or []],
                *[str(value) for value in item.get("examples") or []],
                *[str(value) for value in item.get("limits") or []],
            ]
        )
        overlap = query & set(_terms(haystack))
        anchored = query & set(item.get("answer_alignment_terms") or [])
        subject = query & set(item.get("answer_subject_terms") or [])
        alignment_metadata_present = (
            "answer_alignment_terms" in item or "answer_subject_terms" in item
        )
        if alignment_metadata_present:
            if not anchored and not subject:
                continue
        else:
            title_overlap = query & set(_terms(str(item.get("title") or "")))
            generic = {"answer", "change", "choose", "first", "reason", "result", "step"}
            distinctive_overlap = overlap - generic
            if not title_overlap and len(distinctive_overlap) < 2:
                continue
        scored.append((len(overlap) + 2 * len(anchored) + 3 * len(subject), -index, item))
    scored.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return scored[0][2] if scored else None


def _knowledge_fragment(obligation: dict[str, Any], item: dict[str, Any]) -> tuple[str, str]:
    kind = str(obligation.get("kind") or "direct_question")
    lower = str(obligation.get("source_text") or "").lower()
    if kind == "analogy" or "example" in lower or "analogy" in lower:
        examples = _texts(item.get("examples"))
        if not examples:
            return "", ""
        prefix = "Yes. For example," if kind == "yes_or_no" else "For example,"
        return f"{prefix} {examples[0].rstrip('. ')}.", "approved_distinct_example"
    if "evidence" in lower and any(
        marker in lower for marker in ("change", "revise", "reopen", "different answer")
    ):
        conditions = [*_texts(item.get("counterexamples")), *_texts(item.get("limits"))]
        return (
            (
                f"Evidence that this condition applies would change the answer: "
                f"{conditions[0].rstrip('. ')}."
            ),
            "approved_change_condition",
        ) if conditions else ("", "")
    if kind == "limitation" or any(marker in lower for marker in ("limit", "exception", "counterexample", "not apply")):
        limits = [*_texts(item.get("counterexamples")), *_texts(item.get("limits"))]
        return (f"A limitation is that {limits[0].rstrip('. ')}.", "approved_limit_or_counterexample") if limits else ("", "")
    if kind == "reason" or any(marker in lower for marker in ("why", "reason", "cause", "mechanism")):
        reasons = [*_texts(item.get("principles")), *_texts(item.get("relationships"))]
        return (f"The reason is that {reasons[0].rstrip('. ')}.", "approved_reason_or_relationship") if reasons else ("", "")
    central = truncate(str(item.get("central_claim") or ""), 1200)
    return (central, "approved_central_claim") if central else ("", "")


def _combine(seed: str, fragments: list[str]) -> str:
    parts = [seed] if seed else []
    seen = {" ".join(seed.lower().split()).rstrip(". ")} if seed else set()
    for fragment in fragments:
        key = " ".join(fragment.lower().split()).rstrip(". ")
        if not key or key in seen or key in " ".join(seed.lower().split()):
            continue
        seen.add(key)
        parts.append(fragment)
    return truncate("\n\n".join(parts), 5000)


def _coverage_rank(coverage: dict[str, Any]) -> tuple[int, int]:
    return int(coverage.get("addressed_count") or 0), -int(coverage.get("unresolved_count") or 0)


def _terms(value: str) -> list[str]:
    words = [
        _term_key(word.lower())
        for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)
    ]
    return list(dict.fromkeys(word for word in words if word not in _STOP))[:60]


def _term_key(word: str) -> str:
    return {
        "answers": "answer",
        "differences": "difference",
        "effects": "effect",
        "fairly": "fair",
        "fairness": "fair",
        "identically": "identical",
        "opportunities": "opportunity",
        "questions": "question",
        "reasons": "reason",
        "reflections": "reflection",
        "rules": "rule",
        "situations": "situation",
        "treated": "treat",
        "treating": "treat",
        "treatment": "treat",
    }.get(word, word)


def _texts(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [truncate(str(item), 1000).strip() for item in value if str(item).strip()][:20]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
