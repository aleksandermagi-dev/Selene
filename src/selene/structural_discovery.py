from __future__ import annotations

from typing import Any

from .claim_evidence import build_claim_evidence_packet
from .registry import truncate


STRUCTURAL_DISCOVERY_BOUNDARY = (
    "reviewable_cross_domain_structural_mapping_and_hypothesis_only_"
    "no_analogy_as_proof_private_corpus_wording_memory_identity_governance_training_or_authority_change"
)

RELATION_TYPES = {
    "pattern",
    "analogy",
    "homology",
    "causal_connection",
    "equivalence",
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
    "automatic_cocoon_routing": False,
    "hidden_chain_of_thought_exposed": False,
}


def structural_discovery_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "structural_discovery_contract_ready",
            "version": "v1_cross_domain_mapping_and_hypothesis",
            "relation_types": sorted(RELATION_TYPES),
            "principles": [
                "map roles and relationships rather than surface words",
                "state exactly which relationship transfers",
                "name where the mapping holds and where it breaks",
                "pattern is not automatically cause",
                "analogy is not evidence or proof",
                "homology requires shared-origin evidence",
                "causal connection requires a mechanism and discriminating evidence",
                "equivalence requires a bidirectional mapping within explicit scope",
                "logical leaps remain hypotheses until independently checked",
                "approved earlier knowledge may inform a later domain without becoming personal memory",
            ],
            "writes_records": False,
            "direct_truth_authority": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": STRUCTURAL_DISCOVERY_BOUNDARY,
        }
    )


def build_structural_discovery_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    source_domain = _text(payload.get("source_domain"), 160)
    target_domain = _text(payload.get("target_domain"), 160)
    source_relation = _text(payload.get("source_relation"), 1000)
    target_relation = _text(payload.get("target_relation"), 1000)
    transferred_relation = _text(payload.get("transferred_relation"), 1000)
    requested_type = str(payload.get("relation_type") or "analogy").strip().lower()
    if requested_type not in RELATION_TYPES:
        raise ValueError(f"unsupported structural relation type: {requested_type}")
    source_refs = _text_list(payload.get("source_refs"), width=500, limit=50)
    private_refs = [ref for ref in source_refs if _private_ref(ref)]
    source_class = str(payload.get("source_provenance_class") or "current_conversation").strip().lower()
    private_source = source_class in {
        "raw_private_corpus",
        "private_corpus",
        "aleks_metacognition_miner",
    } or bool(private_refs)
    if private_source:
        return _private_source_hold(requested_type)
    mappings, held_mappings = _mappings(payload.get("mappings"))
    holds_where = _text_list(payload.get("holds_where"), width=900, limit=20)
    breaks_where = _text_list(payload.get("breaks_where"), width=900, limit=20)
    mechanism = _text(payload.get("mechanism"), 1200)
    evidence_refs = [
        ref
        for ref in _text_list(payload.get("evidence_refs"), width=500, limit=50)
        if not _private_ref(ref)
    ]
    shared_origin_refs = [
        ref
        for ref in _text_list(payload.get("shared_origin_evidence_refs"), width=500, limit=30)
        if not _private_ref(ref)
    ]
    approved_links, held_links = _approved_knowledge_links(payload.get("approved_knowledge_links"))
    bridge = [
        {
            "source_role": item["source_role"],
            "target_role": item["target_role"],
            "relation_preserved": item["relation_preserved"],
            "basis": item["basis"],
        }
        for item in mappings
    ]
    missing: list[str] = []
    if not source_domain or not target_domain:
        missing.append("Both source and target domains are required.")
    if source_domain and target_domain and source_domain.lower() == target_domain.lower():
        missing.append("Cross-domain discovery requires distinct source and target domains.")
    if not source_relation or not target_relation or not transferred_relation:
        missing.append("The source relation, target relation, and transferred relation must be explicit.")
    if len(mappings) < 2:
        missing.append("At least two role mappings are needed to show structure rather than a shared word.")
    if not holds_where:
        missing.append("Name where the proposed mapping holds.")
    if requested_type != "equivalence" and not breaks_where:
        missing.append("Name at least one boundary or counterexample where the mapping breaks.")

    structural_ready = not any(
        marker in item
        for item in missing
        for marker in (
            "Both source",
            "distinct source",
            "source relation",
            "At least two",
            "Private corpus",
        )
    )
    classification = _classify_relation(
        requested_type,
        structural_ready=structural_ready,
        breaks_where=breaks_where,
        mechanism=mechanism,
        evidence_refs=evidence_refs,
        shared_origin_refs=shared_origin_refs,
        bidirectional=payload.get("bidirectional_mapping") is True,
        shared_constraints=payload.get("shared_constraints_verified") is True,
    )
    hypothesis = _hypothesis(
        payload.get("hypothesis"),
        fallback_statement=(
            transferred_relation
            if requested_type in {"homology", "causal_connection", "equivalence"}
            else ""
        ),
    )
    if hypothesis and not hypothesis["discriminating_observations"]:
        missing.append("A logical leap needs at least one discriminating observation.")
    if hypothesis and not hypothesis["counterexamples"]:
        missing.append("A logical leap needs a counterexample or failure condition.")

    claims = _claims(
        source_relation=source_relation,
        target_relation=target_relation,
        transferred_relation=transferred_relation,
        source_refs=[ref for ref in source_refs if not _private_ref(ref)],
        evidence_refs=evidence_refs,
        structural_ready=structural_ready and not private_source,
        requested_type=requested_type,
        classification=classification,
        hypothesis=hypothesis,
        breaks_where=breaks_where,
        approved_knowledge_links=approved_links,
    )
    claim_evidence = build_claim_evidence_packet(
        {
            "claims": claims,
            "accepted_source_refs": [
                *[ref for ref in source_refs if not _private_ref(ref)],
                *evidence_refs,
                *shared_origin_refs,
                *[ref for item in approved_links for ref in item["source_refs"]],
            ],
            "missing_evidence": missing,
        }
    )
    ready = structural_ready and not missing
    status = (
        "structural_discovery_packet_ready"
        if ready
        else "structural_discovery_held_for_missing_or_private_basis"
    )
    packet = {
        "status": status,
        "version": "v1_cross_domain_mapping_and_hypothesis",
        "source_domain": source_domain,
        "target_domain": target_domain,
        "requested_relation_type": requested_type,
        "classification": classification,
        "source_relation": source_relation,
        "target_relation": target_relation,
        "transferred_relation": transferred_relation,
        "structural_bridge": bridge,
        "bridge_traceable": len(bridge) >= 2 and bool(transferred_relation),
        "surface_similarity_used_as_bridge": False,
        "holds_where": holds_where,
        "breaks_where": breaks_where,
        "mechanism": mechanism,
        "hypothesis": hypothesis,
        "hypothesis_testable": bool(
            hypothesis
            and hypothesis["discriminating_observations"]
            and hypothesis["counterexamples"]
        ),
        "approved_knowledge_links": approved_links,
        "held_back_knowledge_links": held_links,
        "earlier_approved_knowledge_reused": bool(approved_links),
        "personal_memory_used_as_domain_knowledge": False,
        "held_back_mappings": held_mappings,
        "missing_evidence": list(dict.fromkeys(missing))[:30],
        "claim_evidence_packet": claim_evidence,
        "expression_handoff": {
            "relation_label": classification["label"],
            "source_domain": source_domain,
            "target_domain": target_domain,
            "transferred_relation": transferred_relation,
            "holds_where": holds_where,
            "breaks_where": breaks_where,
            "hypothesis_statement": str(hypothesis.get("statement") or "") if hypothesis else "",
            "discriminating_observations": (
                hypothesis.get("discriminating_observations") or [] if hypothesis else []
            ),
            "counterexamples": hypothesis.get("counterexamples") or [] if hypothesis else [],
            "analogy_is_proof": False,
            "logical_leap_is_conclusion": False,
            "voice_may_upgrade_relation": False,
        },
        "analogy_is_evidence": False,
        "analogy_is_proof": False,
        "pattern_is_causal_connection": False,
        "homology_without_origin_evidence_allowed": False,
        "equivalence_without_bidirectional_scope_allowed": False,
        "direct_truth_authority": False,
        "writes_records": False,
        "visible_summary_only": True,
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": STRUCTURAL_DISCOVERY_BOUNDARY,
    }
    packet["response_seed"] = structural_discovery_response_seed(packet)
    return _with_guards(packet)


def structural_discovery_response_seed(packet: dict[str, Any] | None) -> str:
    packet = packet if isinstance(packet, dict) else {}
    if packet.get("status") != "structural_discovery_packet_ready":
        return ""
    classification = _dict(packet.get("classification"))
    source_domain = str(packet.get("source_domain") or "the source domain")
    target_domain = str(packet.get("target_domain") or "the target domain")
    relation = str(packet.get("transferred_relation") or "")
    parts = [
        (
            f"The structural relationship I am transferring from {source_domain} to {target_domain} is: "
            f"{relation.rstrip('. ')}."
        ),
        f"The proportional label is {str(classification.get('label') or 'open analogy').replace('_', ' ')}; the analogy is not proof.",
    ]
    holds = [str(item) for item in packet.get("holds_where") or [] if str(item).strip()]
    breaks = [str(item) for item in packet.get("breaks_where") or [] if str(item).strip()]
    if holds:
        parts.append("It holds where: " + " ".join(_sentence(item) for item in holds[:3]))
    if breaks:
        parts.append("It breaks where: " + " ".join(_sentence(item) for item in breaks[:3]))
    hypothesis = _dict(packet.get("hypothesis"))
    if hypothesis.get("statement"):
        parts.append(f"Hypothesis: {_sentence(str(hypothesis['statement']))}")
    tests = [str(item) for item in hypothesis.get("discriminating_observations") or [] if str(item).strip()]
    if tests:
        parts.append("A discriminating check would be: " + " ".join(_sentence(item) for item in tests[:3]))
    counterexamples = [str(item) for item in hypothesis.get("counterexamples") or [] if str(item).strip()]
    if counterexamples:
        parts.append("A counterexample or failure condition is: " + " ".join(_sentence(item) for item in counterexamples[:3]))
    return truncate("\n\n".join(parts), 4800)


def _private_source_hold(requested_type: str) -> dict[str, Any]:
    claim_evidence = build_claim_evidence_packet(
        {
            "claims": [],
            "missing_evidence": [
                "Private corpus or miner wording was held out of cross-domain reasoning."
            ],
        }
    )
    return _with_guards(
        {
            "status": "structural_discovery_held_for_missing_or_private_basis",
            "version": "v1_cross_domain_mapping_and_hypothesis",
            "source_domain": "",
            "target_domain": "",
            "requested_relation_type": requested_type,
            "classification": {
                "label": "private_source_held",
                "asserted_as": "not_evaluated",
                "confidence": "not_assessed",
                "reason": "Private source wording is outside this contract.",
            },
            "source_relation": "",
            "target_relation": "",
            "transferred_relation": "",
            "structural_bridge": [],
            "bridge_traceable": False,
            "surface_similarity_used_as_bridge": False,
            "holds_where": [],
            "breaks_where": [],
            "mechanism": "",
            "hypothesis": {},
            "hypothesis_testable": False,
            "approved_knowledge_links": [],
            "held_back_knowledge_links": [],
            "earlier_approved_knowledge_reused": False,
            "personal_memory_used_as_domain_knowledge": False,
            "held_back_mappings": [],
            "missing_evidence": [
                "Private corpus or miner wording was held out of cross-domain reasoning."
            ],
            "claim_evidence_packet": claim_evidence,
            "expression_handoff": {},
            "analogy_is_evidence": False,
            "analogy_is_proof": False,
            "pattern_is_causal_connection": False,
            "homology_without_origin_evidence_allowed": False,
            "equivalence_without_bidirectional_scope_allowed": False,
            "direct_truth_authority": False,
            "writes_records": False,
            "visible_summary_only": True,
            "response_seed": "",
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": STRUCTURAL_DISCOVERY_BOUNDARY,
        }
    )


def _classify_relation(
    requested: str,
    *,
    structural_ready: bool,
    breaks_where: list[str],
    mechanism: str,
    evidence_refs: list[str],
    shared_origin_refs: list[str],
    bidirectional: bool,
    shared_constraints: bool,
) -> dict[str, Any]:
    if not structural_ready:
        return {
            "label": "unresolved_surface_or_incomplete_pattern",
            "asserted_as": "not_yet_structural",
            "confidence": "not_established",
            "reason": "The role mapping is incomplete.",
        }
    if requested == "pattern":
        return {
            "label": "structural_pattern",
            "asserted_as": "pattern",
            "confidence": "bounded",
            "reason": "A relationship recurs across the mapped roles; cause is not implied.",
        }
    if requested == "analogy":
        return {
            "label": "bounded_structural_analogy",
            "asserted_as": "analogy",
            "confidence": "bounded",
            "reason": "The named relation transfers within explicit hold and break conditions.",
        }
    if requested == "homology":
        if shared_origin_refs:
            return {
                "label": "provisional_homology",
                "asserted_as": "hypothesis",
                "confidence": "provisional",
                "reason": "Shared-origin evidence is supplied, but homology remains revisable.",
            }
        return {
            "label": "homology_hypothesis_not_established",
            "asserted_as": "hypothesis",
            "confidence": "open",
            "reason": "Structural similarity alone cannot establish shared origin.",
        }
    if requested == "causal_connection":
        if mechanism and evidence_refs:
            return {
                "label": "supported_causal_hypothesis",
                "asserted_as": "hypothesis",
                "confidence": "provisional",
                "reason": "A mechanism and evidence are supplied, but causal fit still needs discriminating checks.",
            }
        return {
            "label": "causal_hypothesis_not_established",
            "asserted_as": "hypothesis",
            "confidence": "open",
            "reason": "A repeated pattern or analogy cannot establish cause without mechanism and evidence.",
        }
    if bidirectional and shared_constraints and evidence_refs and not breaks_where:
        return {
            "label": "provisional_scoped_equivalence",
            "asserted_as": "provisional_equivalence",
            "confidence": "provisional",
            "reason": "The mapping is bidirectional within the supplied common constraints and evidence.",
        }
    return {
        "label": "analogy_not_equivalence",
        "asserted_as": "analogy",
        "confidence": "bounded",
        "reason": "A one-way mapping, known break, or scope mismatch prevents equivalence.",
    }


def _mappings(value: Any) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    accepted: list[dict[str, str]] = []
    held: list[dict[str, str]] = []
    for index, item in enumerate(value or []):
        if not isinstance(item, dict):
            held.append({"mapping": f"mapping:{index + 1}", "reason": "mapping must be an object"})
            continue
        source_role = _text(item.get("source_role"), 300)
        target_role = _text(item.get("target_role"), 300)
        relation = _text(item.get("relation_preserved") or item.get("relation"), 600)
        basis = _text(item.get("basis"), 700)
        if not source_role or not target_role or not relation:
            held.append(
                {
                    "mapping": f"mapping:{index + 1}",
                    "reason": "source role, target role, and preserved relation are required",
                }
            )
            continue
        accepted.append(
            {
                "source_role": source_role,
                "target_role": target_role,
                "relation_preserved": relation,
                "basis": basis,
            }
        )
    return accepted[:30], held[:30]


def _approved_knowledge_links(value: Any) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    accepted: list[dict[str, Any]] = []
    held: list[dict[str, str]] = []
    for index, item in enumerate(value or []):
        if not isinstance(item, dict):
            held.append({"knowledge": f"knowledge:{index + 1}", "reason": "knowledge link must be an object"})
            continue
        refs = _text_list(item.get("source_refs"), width=500, limit=30)
        claim = _text(item.get("claim") or item.get("central_claim"), 1200)
        identifier = _text(item.get("concept_id") or item.get("id") or f"knowledge:{index + 1}", 160)
        if item.get("approved") is not True:
            held.append({"knowledge": identifier, "reason": "knowledge is not approved for current use"})
            continue
        if not claim or not refs or any(_private_ref(ref) for ref in refs):
            held.append({"knowledge": identifier, "reason": "approved knowledge needs public/reviewed provenance"})
            continue
        accepted.append(
            {
                "concept_id": identifier,
                "domain": _text(item.get("domain"), 160),
                "claim": claim,
                "source_refs": refs,
                "approved": True,
                "personal_memory": False,
            }
        )
    return accepted[:20], held[:30]


def _hypothesis(value: Any, *, fallback_statement: str) -> dict[str, Any]:
    item = _dict(value)
    statement = _text(item.get("statement") or fallback_statement, 1400)
    if not statement:
        return {}
    return {
        "statement": statement,
        "predictions": _text_list(item.get("predictions"), width=900, limit=20),
        "discriminating_observations": _text_list(
            item.get("discriminating_observations") or item.get("tests"),
            width=1000,
            limit=20,
        ),
        "counterexamples": _text_list(
            item.get("counterexamples") or item.get("failure_conditions"),
            width=1000,
            limit=20,
        ),
        "what_would_change": _text_list(
            item.get("what_would_change") or item.get("reversal_conditions"),
            width=1000,
            limit=20,
        ),
        "logical_leap": item.get("logical_leap") is True,
        "conclusion": False,
        "falsifiable": True,
    }


def _claims(
    *,
    source_relation: str,
    target_relation: str,
    transferred_relation: str,
    source_refs: list[str],
    evidence_refs: list[str],
    structural_ready: bool,
    requested_type: str,
    classification: dict[str, Any],
    hypothesis: dict[str, Any],
    breaks_where: list[str],
    approved_knowledge_links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    if source_relation:
        claims.append(
            {
                "claim_id": "discovery-source-relation",
                "claim_type": "observation",
                "text": source_relation,
                "source_refs": source_refs,
                "confidence": "supplied_current_context",
            }
        )
    if target_relation:
        claims.append(
            {
                "claim_id": "discovery-target-relation",
                "claim_type": "observation",
                "text": target_relation,
                "source_refs": source_refs,
                "confidence": "supplied_current_context",
            }
        )
    for index, item in enumerate(approved_knowledge_links):
        claims.append(
            {
                "claim_id": f"discovery-approved-knowledge-{item.get('concept_id') or index + 1}",
                "claim_type": "conclusion",
                "text": str(item.get("claim") or ""),
                "source_refs": item.get("source_refs") or [],
                "evidence_refs": item.get("source_refs") or [],
                "scope": str(item.get("domain") or "approved_knowledge"),
                "confidence": "reviewed",
                "validity": "approved_knowledge_resource",
                "source_category": "approved_knowledge",
            }
        )
    basis = [item["claim_id"] for item in claims]
    if structural_ready and transferred_relation:
        claims.append(
            {
                "claim_id": "discovery-structural-inference",
                "claim_type": "inference",
                "text": transferred_relation,
                "basis_claim_ids": basis,
                "evidence_refs": evidence_refs,
                "confidence": classification.get("confidence") or "bounded",
                "limitations": breaks_where,
                "what_would_change": [
                    "A mapped role fails to preserve the named relationship.",
                    "A counterexample shows the proposed transfer reverses or omits a required mechanism.",
                ],
                "source_category": requested_type,
            }
        )
    if hypothesis:
        hypothesis_basis = [*basis]
        if any(item["claim_id"] == "discovery-structural-inference" for item in claims):
            hypothesis_basis.append("discovery-structural-inference")
        claims.append(
            {
                "claim_id": "discovery-open-hypothesis",
                "claim_type": "hypothesis",
                "text": hypothesis["statement"],
                "basis_claim_ids": hypothesis_basis,
                "evidence_refs": evidence_refs,
                "confidence": classification.get("confidence") or "open",
                "limitations": [*breaks_where, *hypothesis["counterexamples"]],
                "missing_evidence": (
                    []
                    if hypothesis["discriminating_observations"]
                    else ["A discriminating observation is still required."]
                ),
                "what_would_change": [
                    *hypothesis["what_would_change"],
                    *hypothesis["discriminating_observations"],
                    *hypothesis["counterexamples"],
                ],
                "source_category": requested_type,
            }
        )
    return claims


def _private_ref(value: str) -> bool:
    lower = str(value or "").strip().lower()
    return any(lower.startswith(prefix) for prefix in PRIVATE_SOURCE_PREFIXES)


def _text(value: Any, width: int) -> str:
    return truncate(str(value or "").strip(), width)


def _text_list(value: Any, *, width: int, limit: int) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else [] if value in (None, "") else [value]
    return list(
        dict.fromkeys(
            truncate(str(item).strip(), width)
            for item in values
            if item is not None and str(item).strip()
        )
    )[:limit]


def _sentence(value: str) -> str:
    text = " ".join(str(value or "").split()).strip()
    return text if text.endswith((".", "!", "?")) else f"{text}."


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
