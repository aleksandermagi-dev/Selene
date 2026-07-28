from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .supported_semantics import (
    build_supported_semantic_packet,
    build_text_supported_semantic_packet,
    semantic_units_for_formation,
)


FORMATION_BRAID_BOUNDARY = (
    "selective_supported_meaning_coordination_only_no_fact_generation_memory_"
    "retention_identity_personality_governance_authority_or_expression_ownership_change"
)

ALLOWED_SOURCE_CLASSES = {
    "boundary_response",
    "conversation",
    "approved_knowledge",
    "domain_answer",
    "language_capability",
    "memory_reconstruction",
    "reasoning_answer",
    "self_state",
}

PROTECTIVE_ROLES = {"condition", "contrast", "limit", "reopening"}
EXACT_SOURCE_KINDS = {"attributed_source", "verified_domain_answer"}
SOURCE_PRIORITY = {
    "boundary_response": 80,
    "domain_answer": 70,
    "approved_knowledge": 60,
    "memory_reconstruction": 55,
    "self_state": 50,
    "reasoning_answer": 45,
    "language_capability": 35,
    "conversation": 30,
}

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
}

_STOP = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "answer",
    "because",
    "before",
    "being",
    "could",
    "does",
    "from",
    "have",
    "into",
    "just",
    "more",
    "that",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
    "your",
}


def build_selective_formation_braid(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select a bounded braid of already-supported meanings for NLO.

    The selector does not answer the prompt. It preserves one primary source
    and may add only relevant supported units from earlier organ handoffs.
    """
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or ""), 3000)
    primary_source_id = truncate(
        str(payload.get("primary_source_id") or "none"), 120
    )
    primary_source_class = truncate(
        str(payload.get("primary_source_class") or "conversation"), 80
    )
    primary_text = truncate(str(payload.get("primary_text") or ""), 5000)
    hard_boundary = payload.get("hard_boundary") is True
    max_packets = max(1, min(int(payload.get("max_packets") or 5), 8))
    max_units = max(1, min(int(payload.get("max_units") or 16), 24))
    spine = (
        payload.get("conversation_spine")
        if isinstance(payload.get("conversation_spine"), dict)
        else {}
    )
    obligations = [
        item
        for item in (
            payload.get("response_obligations")
            or spine.get("open_obligations")
            or []
        )
        if isinstance(item, dict)
    ][:20]
    obligation_map = {
        str(item.get("id") or f"obligation_{index + 1}"): {
            **item,
            "functions": _obligation_functions(item),
            "terms": _terms(
                " ".join(
                    [
                        str(item.get("source_text") or ""),
                        str(item.get("parent_source_text") or ""),
                        str(item.get("topic") or ""),
                        str(item.get("kind") or ""),
                    ]
                )
            ),
        }
        for index, item in enumerate(obligations)
    }
    prompt_terms = _terms(prompt)

    candidates = [
        _normalize_candidate(
            raw,
            index=index,
            primary_source_id=primary_source_id,
            primary_source_class=primary_source_class,
            primary_text=primary_text,
            obligation_map=obligation_map,
            prompt_terms=prompt_terms,
        )
        for index, raw in enumerate(payload.get("candidates") or [])
        if isinstance(raw, dict)
    ][:24]
    candidates = [item for item in candidates if item]
    if not any(item["primary"] for item in candidates) and primary_text:
        fallback = _normalize_candidate(
            {
                "source_id": primary_source_id,
                "source_class": primary_source_class,
                "text": primary_text,
                "primary": True,
                "source_refs": payload.get("source_refs") or [],
            },
            index=len(candidates),
            primary_source_id=primary_source_id,
            primary_source_class=primary_source_class,
            primary_text=primary_text,
            obligation_map=obligation_map,
            prompt_terms=prompt_terms,
        )
        if fallback:
            candidates.append(fallback)

    candidates.sort(
        key=lambda item: (
            item["primary"],
            item["score"],
            -item["index"],
        ),
        reverse=True,
    )
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    selected_units: list[dict[str, Any]] = []
    selected_fingerprints: set[str] = set()
    covered_obligations: set[str] = set()
    preserved_roles: set[str] = set()

    for candidate in candidates:
        summary = _candidate_summary(candidate)
        if candidate["eligible"] is not True:
            excluded.append({**summary, "reason": candidate["eligibility_reason"]})
            continue
        if hard_boundary and not candidate["primary"]:
            excluded.append({**summary, "reason": "hard_boundary_primary_only"})
            continue
        if len(selected) >= max_packets:
            excluded.append({**summary, "reason": "packet_budget_reached"})
            continue
        if not candidate["primary"] and not candidate["relevant"]:
            excluded.append({**summary, "reason": "no_requested_response_function"})
            continue

        available_units = []
        for unit in candidate["units"]:
            unit_obligation_ids = (
                list(candidate["candidate_obligation_ids"])
                if candidate["primary"]
                else _unit_obligation_ids(
                    unit,
                    candidate["candidate_obligation_ids"],
                    obligation_map,
                )
            )
            if not candidate["primary"] and not unit_obligation_ids:
                continue
            fingerprint = _unit_fingerprint(unit)
            if fingerprint and fingerprint in selected_fingerprints:
                continue
            available_units.append((unit, fingerprint, unit_obligation_ids))
        if not available_units:
            reason = (
                "duplicate_supported_meaning"
                if candidate["primary"]
                else "no_requested_response_function"
            )
            excluded.append({**summary, "reason": reason})
            continue
        remaining = max_units - len(selected_units)
        if remaining <= 0:
            excluded.append({**summary, "reason": "semantic_unit_budget_reached"})
            continue

        included_units = available_units[:remaining]
        inclusion_reasons = ["primary_visible_answer"] if candidate["primary"] else []
        if candidate["explicit_obligation_ids"]:
            inclusion_reasons.append("explicit_obligation_support")
        if candidate["matched_obligation_ids"]:
            inclusion_reasons.append("current_obligation_fit")
        candidate_roles = {
            str(unit.get("role") or "")
            for unit, _, _ in included_units
            if str(unit.get("role") or "") in PROTECTIVE_ROLES
        }
        new_protective_roles = candidate_roles - preserved_roles
        if new_protective_roles:
            inclusion_reasons.append("requested_qualification_preserved")
        if not inclusion_reasons:
            inclusion_reasons.append("requested_response_function")

        candidate_covered_ids: set[str] = set()
        for unit, fingerprint, unit_obligation_ids in included_units:
            origin_id = str(unit.get("id") or "semantic")
            exactness_lock = (
                candidate["exactness_lock"]
                or str(unit.get("source_kind") or "") in EXACT_SOURCE_KINDS
                or unit.get("exactness_lock") is True
            )
            selected_units.append(
                {
                    **unit,
                    "id": truncate(
                        f"{_slug(candidate['source_id'])}_{candidate['index'] + 1}_{_slug(origin_id)}",
                        120,
                    ),
                    "origin_packet_id": candidate["source_id"],
                    "origin_unit_id": origin_id,
                    "origin_source_class": candidate["source_class"],
                    "obligation_ids": unit_obligation_ids[:20],
                    "selection_reasons": inclusion_reasons,
                    "exactness_lock": exactness_lock,
                    "meaning_change_allowed": False,
                }
            )
            if fingerprint:
                selected_fingerprints.add(fingerprint)
            candidate_covered_ids.update(unit_obligation_ids)
        covered_obligations.update(candidate_covered_ids)
        preserved_roles.update(candidate_roles)
        selected.append(
            {
                **summary,
                "reason": inclusion_reasons,
                "selected_unit_count": len(included_units),
                "protective_roles": sorted(candidate_roles),
            }
        )

    if not selected_units:
        return _with_guards(
            {
                "status": "selective_formation_braid_unavailable",
                "version": "v1_selective_formation_braid",
                "primary_source_id": primary_source_id,
                "primary_source_class": primary_source_class,
                "selected_candidates": selected,
                "excluded_candidates": excluded,
                "selected_packet_count": 0,
                "selected_unit_count": 0,
                "packet_limit": max_packets,
                "unit_limit": max_units,
                "supported_semantics": {},
                "obligation_coverage": _obligation_coverage(
                    obligations, covered_obligations
                ),
                "protective_roles_preserved": [],
                "hard_boundary_primary_only": hard_boundary,
                "selection_is_answer_authority": False,
                "nlo_owns_expression": True,
                "visible_summary_only": True,
                "hidden_chain_of_thought_exposed": False,
                "provenance_boundary": FORMATION_BRAID_BOUNDARY,
            }
        )

    source_refs = list(
        dict.fromkeys(
            ref
            for candidate in candidates
            if any(
                selected_item["source_id"] == candidate["source_id"]
                for selected_item in selected
            )
            for ref in candidate["source_refs"]
        )
    )[:60]
    packet = build_supported_semantic_packet(
        {
            "answer_kind": "selective_formation_braid",
            "certainty": "mixed_source_bounded",
            "scope": "current_dialogue_obligations",
            "source_refs": source_refs,
            "fallback_text": primary_text,
            "units": selected_units,
        }
    )
    return _with_guards(
        {
            "status": "selective_formation_braid_ready",
            "version": "v1_selective_formation_braid",
            "primary_source_id": primary_source_id,
            "primary_source_class": primary_source_class,
            "selected_candidates": selected,
            "excluded_candidates": excluded,
            "selected_packet_count": len(selected),
            "selected_unit_count": len(
                semantic_units_for_formation(packet)
            ),
            "packet_limit": max_packets,
            "unit_limit": max_units,
            "supported_semantics": packet,
            "obligation_coverage": _obligation_coverage(
                obligations, covered_obligations
            ),
            "protective_roles_preserved": sorted(preserved_roles),
            "exactness_lock_count": sum(
                1
                for unit in semantic_units_for_formation(packet)
                if unit.get("exactness_lock") is True
            ),
            "hard_boundary_primary_only": hard_boundary,
            "selection_is_answer_authority": False,
            "core_mind_authority_unchanged": True,
            "answer_engine_ownership_unchanged": True,
            "nlo_owns_expression": True,
            "voice_owns_expression_style": True,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": FORMATION_BRAID_BOUNDARY,
        }
    )


def _normalize_candidate(
    raw: dict[str, Any],
    *,
    index: int,
    primary_source_id: str,
    primary_source_class: str,
    primary_text: str,
    obligation_map: dict[str, dict[str, Any]],
    prompt_terms: set[str],
) -> dict[str, Any] | None:
    source_id = truncate(str(raw.get("source_id") or f"candidate_{index + 1}"), 120)
    source_class = truncate(
        str(raw.get("source_class") or "conversation"), 80
    )
    text = truncate(str(raw.get("text") or ""), 5000).strip()
    primary = raw.get("primary") is True or (
        source_id == primary_source_id
        and source_class == primary_source_class
    )
    packet = (
        raw.get("supported_semantics")
        if isinstance(raw.get("supported_semantics"), dict)
        else raw.get("semantic_packet")
        if isinstance(raw.get("semantic_packet"), dict)
        else {}
    )
    if not semantic_units_for_formation(packet) and text:
        packet = build_text_supported_semantic_packet(
            text,
            answer_kind=f"{_slug(source_id)}_formation_source",
            source_kind=_source_kind(source_class),
            source_refs=_text_list(raw.get("source_refs")),
            certainty=truncate(str(raw.get("certainty") or "provisional"), 80),
            scope=truncate(
                str(raw.get("scope") or "current_dialogue_obligations"), 240
            ),
        )
    units = semantic_units_for_formation(packet)
    if not text:
        text = truncate(str(packet.get("fallback_text") or ""), 5000).strip()
    source_refs = list(
        dict.fromkeys(
            [
                *_text_list(raw.get("source_refs")),
                *_text_list(packet.get("source_refs")),
            ]
        )
    )[:40]
    if source_class not in ALLOWED_SOURCE_CLASSES:
        eligible, eligibility_reason = False, "source_class_not_formation_eligible"
    elif not units:
        eligible, eligibility_reason = False, "no_supported_semantic_units"
    elif packet.get("all_units_supported") is not True:
        eligible, eligibility_reason = False, "packet_contains_unsupported_meaning"
    else:
        eligible, eligibility_reason = True, "supported_semantic_packet"

    explicit_ids = [
        str(item)
        for item in raw.get("obligation_ids") or []
        if str(item) in obligation_map
    ][:20]
    candidate_terms = _terms(
        " ".join(
            [
                text,
                *[
                    " ".join(
                        [
                            str(unit.get("text") or ""),
                            str(unit.get("subject") or ""),
                            str(unit.get("predicate") or ""),
                            str(unit.get("object") or ""),
                            *[str(item) for item in unit.get("meaning_keys") or []],
                        ]
                    )
                    for unit in units
                ],
            ]
        )
    )
    matched_ids = [
        obligation_id
        for obligation_id, obligation in obligation_map.items()
        if _meaningful_overlap(candidate_terms, obligation["terms"])
    ]
    prompt_overlap = len(candidate_terms & prompt_terms)
    protective = any(str(unit.get("role") or "") in PROTECTIVE_ROLES for unit in units)
    candidate_obligation_ids = list(dict.fromkeys([*explicit_ids, *matched_ids]))
    relevant = bool(primary or candidate_obligation_ids)
    score = (
        (1000 if primary else 0)
        + 100 * len(explicit_ids)
        + 30 * len(matched_ids)
        + min(prompt_overlap, 8)
        + (10 if protective else 0)
        + SOURCE_PRIORITY.get(source_class, 0)
    )
    return {
        "index": index,
        "source_id": source_id,
        "source_class": source_class,
        "text": text or (primary_text if primary else ""),
        "packet": packet,
        "units": units,
        "source_refs": source_refs,
        "primary": primary,
        "eligible": eligible,
        "eligibility_reason": eligibility_reason,
        "explicit_obligation_ids": explicit_ids,
        "matched_obligation_ids": matched_ids,
        "candidate_obligation_ids": candidate_obligation_ids,
        "prompt_overlap_count": prompt_overlap,
        "protective": protective,
        "relevant": relevant,
        "exactness_lock": raw.get("exactness_lock") is True,
        "score": score,
    }


def _candidate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": candidate["source_id"],
        "source_class": candidate["source_class"],
        "primary": candidate["primary"],
        "supported_unit_count": len(candidate["units"]),
        "explicit_obligation_ids": candidate["explicit_obligation_ids"],
        "matched_obligation_ids": candidate["matched_obligation_ids"],
        "candidate_obligation_ids": candidate["candidate_obligation_ids"],
        "prompt_overlap_count": candidate["prompt_overlap_count"],
        "source_refs": candidate["source_refs"],
        "score": candidate["score"],
    }


def _obligation_coverage(
    obligations: list[dict[str, Any]],
    covered: set[str],
) -> dict[str, Any]:
    required_ids = [
        str(item.get("id") or f"obligation_{index + 1}")
        for index, item in enumerate(obligations)
        if item.get("required") is not False
    ]
    covered_ids = [item for item in required_ids if item in covered]
    uncovered_ids = [item for item in required_ids if item not in covered]
    return {
        "required_ids": required_ids,
        "covered_ids": covered_ids,
        "uncovered_ids": uncovered_ids,
        "covered_count": len(covered_ids),
        "required_count": len(required_ids),
        "all_required_covered": bool(required_ids) and not uncovered_ids,
    }


def _obligation_functions(obligation: dict[str, Any]) -> set[str]:
    """Return only response functions explicitly requested by the current turn."""
    kind = str(obligation.get("kind") or "direct_question").lower()
    source_text = " ".join(
        [
            str(obligation.get("source_text") or ""),
            str(obligation.get("parent_source_text") or ""),
            str(obligation.get("goal") or ""),
        ]
    ).lower()
    functions = {"answer"}
    if kind == "reason" or re.search(r"\b(?:why|reason|cause|mechanism|explain)\b", source_text):
        functions.add("reason")
    if kind == "method" or re.search(
        r"\b(?:how|steps?|method|process|walk me through|show me how)\b",
        source_text,
    ):
        functions.add("method")
    if kind == "analogy" or re.search(
        r"\b(?:example|analogy|illustrat(?:e|ion)|for instance)\b",
        source_text,
    ):
        functions.add("example")
    if kind in {"limitation", "constraint_preservation"} or re.search(
        r"\b(?:limit|limitation|exception|counterexample|condition|constraint|"
        r"when does|when would|not apply)\b",
        source_text,
    ):
        functions.add("limit")
    if kind in {"comparison", "correction_update"} or re.search(
        r"\b(?:compare|comparison|contrast|difference|versus|disagree|correction)\b",
        source_text,
    ):
        functions.add("contrast")
    if kind == "correction_update" or re.search(
        r"\b(?:reopen|revise|revision|contradiction|what would change|"
        r"uncertain|uncertainty|wrong)\b",
        source_text,
    ):
        functions.add("reopening")
    if kind == "session_summary":
        functions.add("summary")
    if kind == "self_state_check_in":
        functions.add("self_state")
    if kind == "rephrase_request":
        functions.add("rephrase")
    return functions


def _unit_obligation_ids(
    unit: dict[str, Any],
    candidate_obligation_ids: list[str],
    obligation_map: dict[str, dict[str, Any]],
) -> list[str]:
    supported_functions = _unit_response_functions(unit)
    return [
        obligation_id
        for obligation_id in candidate_obligation_ids
        if supported_functions & obligation_map[obligation_id]["functions"]
    ]


def _unit_response_functions(unit: dict[str, Any]) -> set[str]:
    role = str(unit.get("role") or "answer").lower()
    relation = str(unit.get("relation") or "").lower()
    if role == "support":
        text = " ".join(
            [
                str(unit.get("text") or ""),
                str(unit.get("reason") or ""),
                str(unit.get("condition") or ""),
            ]
        ).lower()
        if re.search(r"\b(?:step|first|then|through|method|process|by)\b", text):
            return {"reason", "method"}
        return {"reason"}
    if role == "example" or relation == "example":
        return {"example"}
    if role in {"limit", "condition"} or relation == "condition":
        return {"limit", "method"} if role == "condition" else {"limit"}
    if role == "contrast" or relation == "contrast":
        return {"contrast"}
    if role == "reopening" or relation == "return":
        return {"reopening"}
    if role == "conclusion" and relation == "conclusion":
        return {"answer"}
    if role == "request":
        return {"answer"}
    return {"answer"}


def _unit_fingerprint(unit: dict[str, Any]) -> str:
    text = " ".join(
        str(
            unit.get("text")
            or " ".join(
                [
                    str(unit.get("subject") or ""),
                    str(unit.get("predicate") or ""),
                    str(unit.get("object") or ""),
                ]
            )
        ).lower().split()
    ).rstrip(". ")
    if text:
        return text
    return "|".join(str(item).lower() for item in unit.get("meaning_keys") or [])


def _meaningful_overlap(left: set[str], right: set[str]) -> bool:
    overlap = left & right
    if len(overlap) >= 2:
        return True
    if len(overlap) == 1:
        token = next(iter(overlap))
        return len(token) >= 7
    return False


def _source_kind(source_class: str) -> str:
    return {
        "approved_knowledge": "approved_knowledge",
        "domain_answer": "verified_domain_answer",
        "memory_reconstruction": "reviewed_memory",
        "reasoning_answer": "prompt_grounded_method",
        "self_state": "current_session_observation",
    }.get(source_class, "compatibility_fallback")


def _terms(value: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", value.lower())
        if word not in _STOP
    }


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")[:48] or "source"


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [truncate(str(item), 240) for item in value if str(item).strip()][:40]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
