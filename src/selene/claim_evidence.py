from __future__ import annotations

from hashlib import sha256
from typing import Any

from .registry import truncate


CLAIM_EVIDENCE_BOUNDARY = (
    "visible_typed_claim_and_evidence_coordination_only_no_truth_by_source_category_"
    "citation_invention_memory_identity_governance_training_or_authority_change"
)

CLAIM_TYPES = {
    "observation",
    "source_statement",
    "inference",
    "hypothesis",
    "model",
    "conclusion",
    "speculation",
}

VALIDITY_STATES = {
    "reported_observation",
    "attributed_not_independently_verified",
    "bounded_inference",
    "open_hypothesis",
    "provisional_model",
    "provisional_conclusion",
    "approved_knowledge_resource",
    "verified_result",
    "useful_within_scope",
    "limited",
    "revised",
    "contested",
    "unresolved",
    "superseded",
    "reopened",
    "basis_missing",
    "speculation_not_evidence",
}

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "automatic_evidence_ledger_write": False,
    "automatic_cocoon_routing": False,
    "hidden_chain_of_thought_exposed": False,
}


def claim_evidence_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "claim_evidence_contract_ready",
            "version": "v1_typed_claim_evidence_packet",
            "claim_types": sorted(CLAIM_TYPES),
            "validity_states": sorted(VALIDITY_STATES),
            "principles": [
                "observation remains distinct from interpretation",
                "source statement means a source said something, not that it is true",
                "inference names its basis",
                "hypothesis and model remain falsifiable",
                "conclusion remains revisable when its basis changes",
                "speculation is explorable but is not evidence",
                "claims are evaluated individually rather than by source category",
                "disagreement and missing evidence remain visible",
                "model ancestry and valid scope are preserved",
            ],
            "domain_category_policy": {
                "science_religion_mythology_archaeology_history_and_other_domains_explorable": True,
                "automatic_acceptance_by_category": False,
                "automatic_dismissal_by_category": False,
                "category_is_credibility_score": False,
            },
            "citation_invention_allowed": False,
            "direct_truth_authority": False,
            "writes_records": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": CLAIM_EVIDENCE_BOUNDARY,
        }
    )


def build_claim_evidence_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    raw_claims = [item for item in payload.get("claims") or [] if isinstance(item, dict)][:60]
    accepted_source_refs = _text_list(payload.get("accepted_source_refs"), width=500, limit=80)
    accepted: list[dict[str, Any]] = []
    held_back: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for index, raw in enumerate(raw_claims):
        claim_type = _claim_type(raw)
        text = truncate(str(raw.get("text") or raw.get("claim") or raw.get("statement") or ""), 1800).strip()
        if not text:
            held_back.append({"claim": f"claim:{index + 1}", "reason": "claim text is required"})
            continue
        source_refs = _text_list(raw.get("source_refs") or raw.get("source_ref"), width=500, limit=30)
        if claim_type == "source_statement" and not source_refs:
            held_back.append(
                {"claim": f"claim:{index + 1}", "reason": "source_statement requires an attributed source reference"}
            )
            continue
        claim_id = truncate(
            str(raw.get("claim_id") or raw.get("id") or _claim_id(claim_type, text, source_refs)),
            160,
        )
        if claim_id in seen_ids:
            held_back.append({"claim": claim_id, "reason": "duplicate claim_id"})
            continue
        seen_ids.add(claim_id)
        accepted.append(
            _normalize_claim(
                raw,
                claim_id=claim_id,
                claim_type=claim_type,
                text=text,
                source_refs=source_refs,
            )
        )

    known_ids = {item["claim_id"] for item in accepted}
    for claim in accepted:
        missing_basis = [item for item in claim["basis_claim_ids"] if item not in known_ids]
        claim["missing_basis_claim_ids"] = missing_basis
        claim["basis_complete"] = not missing_basis and (
            bool(claim["basis_claim_ids"])
            or bool(claim["evidence_refs"])
            or claim["claim_type"] in {"observation", "source_statement", "speculation"}
            or claim["validity"] in {"approved_knowledge_resource", "verified_result"}
        )
        if (
            claim["claim_type"] in {"inference", "hypothesis", "model", "conclusion"}
            and not claim["basis_complete"]
            and claim["validity"] not in {"approved_knowledge_resource", "verified_result"}
        ):
            claim["validity"] = "basis_missing"
            claim["missing_evidence"] = list(
                dict.fromkeys(
                    [
                        *claim["missing_evidence"],
                        "The claim needs a visible observation, evidence reference, or basis claim.",
                    ]
                )
            )

    disagreements = _disagreements(accepted)
    disagreement_keys = {item["claim_key"] for item in disagreements}
    for claim in accepted:
        if claim["claim_key"] and claim["claim_key"] in disagreement_keys:
            claim["contested"] = True
            if claim["validity"] not in {"superseded", "reopened", "basis_missing"}:
                claim["validity"] = "contested"

    citations, held_citations = _citations(
        payload.get("citations"),
        accepted_source_refs=accepted_source_refs,
        claim_source_refs={ref for claim in accepted for ref in claim["source_refs"]},
    )
    revision = (
        payload.get("epistemic_revision")
        if isinstance(payload.get("epistemic_revision"), dict)
        else {}
    )
    ancestry = _ancestry(accepted, revision)
    missing_evidence = list(
        dict.fromkeys(
            [
                *_text_list(payload.get("missing_evidence"), width=1000, limit=30),
                *[
                    item
                    for claim in accepted
                    for item in claim.get("missing_evidence") or []
                ],
                *(
                    ["The supplied claims disagree and no deciding evidence was supplied."]
                    if disagreements
                    else []
                ),
            ]
        )
    )[:40]
    expression_handoff = _expression_handoff(accepted, disagreements, missing_evidence)

    return _with_guards(
        {
            "status": "claim_evidence_packet_ready",
            "version": "v1_typed_claim_evidence_packet",
            "claims": accepted,
            "claim_count": len(accepted),
            "held_back_claims": held_back,
            "claims_by_type": {
                claim_type: [item["claim_id"] for item in accepted if item["claim_type"] == claim_type]
                for claim_type in sorted(CLAIM_TYPES)
            },
            "disagreements": disagreements,
            "missing_evidence": missing_evidence,
            "model_ancestry": ancestry,
            "citations": citations,
            "held_back_citations": held_citations,
            "accepted_source_refs": accepted_source_refs,
            "all_citations_trace_to_accepted_sources": not held_citations,
            "citation_invention_allowed": False,
            "claim_evaluation": {
                "unit": "individual_claim",
                "whole_source_category_accepted_or_rejected": False,
                "source_category_is_truth": False,
                "source_category_is_credibility_score": False,
                "same_evidentiary_questions_across_domains": True,
            },
            "expression_handoff": expression_handoff,
            "direct_answer_inference_and_uncertainty_separate": True,
            "writes_records": False,
            "visible_summary_only": True,
            "direct_truth_authority": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": CLAIM_EVIDENCE_BOUNDARY,
        }
    )


def _normalize_claim(
    raw: dict[str, Any],
    *,
    claim_id: str,
    claim_type: str,
    text: str,
    source_refs: list[str],
) -> dict[str, Any]:
    basis = _text_list(raw.get("basis_claim_ids") or raw.get("basis"), width=160, limit=30)
    evidence_refs = _text_list(raw.get("evidence_refs"), width=500, limit=30)
    supplied_validity = str(raw.get("validity") or raw.get("status") or "").strip()
    if supplied_validity and supplied_validity not in VALIDITY_STATES:
        raise ValueError(f"unsupported claim validity: {supplied_validity}")
    validity = supplied_validity or _default_validity(claim_type, bool(basis or evidence_refs))
    source_category = truncate(str(raw.get("source_category") or raw.get("domain") or "unspecified"), 120)
    return {
        "claim_id": claim_id,
        "claim_type": claim_type,
        "text": text,
        "claim_key": truncate(str(raw.get("claim_key") or ""), 200),
        "stance": _stance(raw.get("stance")),
        "scope": truncate(str(raw.get("scope") or ""), 600),
        "confidence": truncate(str(raw.get("confidence") or "not_assessed"), 100),
        "validity": validity,
        "source_refs": source_refs,
        "evidence_refs": evidence_refs,
        "basis_claim_ids": basis,
        "limitations": _text_list(raw.get("limitations"), width=900, limit=20),
        "missing_evidence": _text_list(raw.get("missing_evidence"), width=1000, limit=20),
        "what_would_change": _text_list(
            raw.get("what_would_change") or raw.get("what_would_change_the_claim"),
            width=1000,
            limit=20,
        )
        or _default_reversal_conditions(claim_type),
        "source_category": source_category,
        "source_category_determines_validity": False,
        "source_statement_is_fact": False if claim_type == "source_statement" else None,
        "speculation_is_evidence": False if claim_type == "speculation" else None,
        "contested": False,
        "model_ancestry": raw.get("model_ancestry") if isinstance(raw.get("model_ancestry"), dict) else {},
    }


def _claim_type(raw: dict[str, Any]) -> str:
    value = str(raw.get("claim_type") or raw.get("statement_type") or raw.get("type") or "").strip().lower()
    aliases = {
        "bounded_inference": "inference",
        "fact": "source_statement",
        "report": "source_statement",
        "theory": "model",
        "guess": "speculation",
    }
    value = aliases.get(value, value)
    if value not in CLAIM_TYPES:
        raise ValueError(f"unsupported claim type: {value or 'missing'}")
    return value


def _default_validity(claim_type: str, has_basis: bool) -> str:
    return {
        "observation": "reported_observation",
        "source_statement": "attributed_not_independently_verified",
        "inference": "bounded_inference" if has_basis else "basis_missing",
        "hypothesis": "open_hypothesis" if has_basis else "basis_missing",
        "model": "provisional_model" if has_basis else "basis_missing",
        "conclusion": "provisional_conclusion" if has_basis else "basis_missing",
        "speculation": "speculation_not_evidence",
    }[claim_type]


def _default_reversal_conditions(claim_type: str) -> list[str]:
    return {
        "observation": ["A better measurement or provenance check changes the reported observation."],
        "source_statement": ["The source is corrected, superseded, or shown to have been represented inaccurately."],
        "inference": ["A basis claim changes or a competing inference explains the same evidence better."],
        "hypothesis": ["A discriminating observation contradicts its prediction."],
        "model": ["A competing model fits more observations with fewer unsupported assumptions."],
        "conclusion": ["Its evidence or a required basis claim changes."],
        "speculation": ["Attributable evidence connects it to an observation or rules it out."],
    }[claim_type]


def _disagreements(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for claim in claims:
        if claim["claim_key"] and claim["stance"] != "unspecified":
            groups.setdefault(claim["claim_key"], []).append(claim)
    result: list[dict[str, Any]] = []
    for claim_key, items in groups.items():
        stances = sorted({item["stance"] for item in items})
        if len(stances) < 2:
            continue
        result.append(
            {
                "claim_key": claim_key,
                "stances": stances,
                "claim_ids": [item["claim_id"] for item in items],
                "source_refs": list(
                    dict.fromkeys(ref for item in items for ref in item["source_refs"])
                ),
                "status": "claim_level_disagreement_unresolved",
                "whole_sources_rejected": False,
            }
        )
    return result


def _citations(
    value: Any,
    *,
    accepted_source_refs: list[str],
    claim_source_refs: set[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    allowed = set(accepted_source_refs) | claim_source_refs
    accepted: list[dict[str, str]] = []
    held: list[dict[str, str]] = []
    for index, item in enumerate(value or []):
        if not isinstance(item, dict):
            held.append({"citation": f"citation:{index + 1}", "reason": "citation must be an object"})
            continue
        ref = truncate(str(item.get("source_ref") or ""), 500).strip()
        if not ref or ref not in allowed:
            held.append(
                {
                    "citation": ref or f"citation:{index + 1}",
                    "reason": "citation does not trace to an accepted attributed source",
                }
            )
            continue
        accepted.append(
            {
                "source_ref": ref,
                "title": truncate(str(item.get("title") or ref), 300),
                "locator": truncate(str(item.get("locator") or "unspecified"), 300),
            }
        )
    return accepted, held


def _ancestry(
    claims: list[dict[str, Any]],
    revision: dict[str, Any],
) -> list[dict[str, Any]]:
    result = [
        {
            "claim_id": item["claim_id"],
            **item["model_ancestry"],
            "valid_scope": item["scope"] or item["model_ancestry"].get("valid_scope", ""),
        }
        for item in claims
        if item["claim_type"] == "model" and item["model_ancestry"]
    ]
    revision_ancestry = (
        revision.get("model_ancestry")
        if isinstance(revision.get("model_ancestry"), dict)
        else {}
    )
    if revision_ancestry.get("preserved") is True:
        result.append(
            {
                "claim_id": truncate(str(revision.get("target") or "revised_model"), 160),
                **revision_ancestry,
                "update_kind": str(revision.get("update_kind") or ""),
            }
        )
    return result[:20]


def _expression_handoff(
    claims: list[dict[str, Any]],
    disagreements: list[dict[str, Any]],
    missing_evidence: list[str],
) -> dict[str, Any]:
    uncertainty_states = {"contested", "unresolved", "reopened", "basis_missing", "speculation_not_evidence"}
    return {
        "observation_claim_ids": [item["claim_id"] for item in claims if item["claim_type"] == "observation"],
        "attributed_source_statement_ids": [
            item["claim_id"] for item in claims if item["claim_type"] == "source_statement"
        ],
        "inference_claim_ids": [item["claim_id"] for item in claims if item["claim_type"] == "inference"],
        "hypothesis_claim_ids": [item["claim_id"] for item in claims if item["claim_type"] == "hypothesis"],
        "model_claim_ids": [item["claim_id"] for item in claims if item["claim_type"] == "model"],
        "direct_answer_claim_ids": [item["claim_id"] for item in claims if item["claim_type"] == "conclusion"],
        "speculation_claim_ids": [item["claim_id"] for item in claims if item["claim_type"] == "speculation"],
        "uncertainty_claim_ids": [
            item["claim_id"] for item in claims if item["validity"] in uncertainty_states
        ],
        "disagreement_count": len(disagreements),
        "missing_evidence_count": len(missing_evidence),
        "labels_must_remain_distinct": True,
        "voice_may_change_claim_type": False,
        "voice_may_upgrade_confidence": False,
    }


def _claim_id(claim_type: str, text: str, refs: list[str]) -> str:
    digest = sha256(f"{claim_type}|{text}|{'|'.join(refs)}".encode("utf-8")).hexdigest()[:16]
    return f"claim-{digest}"


def _stance(value: Any) -> str:
    stance = str(value or "unspecified").strip().lower()
    aliases = {"for": "support", "against": "oppose", "reject": "oppose"}
    return aliases.get(stance, stance) if stance in {"support", "oppose", "neutral", "unspecified", "for", "against", "reject"} else "unspecified"


def _text_list(value: Any, *, width: int, limit: int) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else [] if value in (None, "") else [value]
    return list(
        dict.fromkeys(
            truncate(str(item).strip(), width)
            for item in values
            if item is not None and str(item).strip()
        )
    )[:limit]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
