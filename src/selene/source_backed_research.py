from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from .claim_evidence import build_claim_evidence_packet
from .library_tendril import LibraryTendrilClient
from .registry import truncate


SOURCE_RESEARCH_BOUNDARY = (
    "source_backed_research_attributed_packets_only_optional_separately_enabled_library_observe_"
    "source_content_not_instruction_no_citation_invention_memory_identity_law_training_or_authority_change"
)

MAX_PACKETS = 20
MAX_STATEMENTS_PER_PACKET = 30
MAX_SELECTED_STATEMENTS = 12

_STOPWORDS = {
    "according",
    "answer",
    "about",
    "does",
    "evidence",
    "from",
    "research",
    "say",
    "source",
    "sources",
    "study",
    "that",
    "the",
    "these",
    "this",
    "what",
    "which",
    "with",
}


def source_backed_research_status() -> dict[str, Any]:
    return {
        "status": "source_backed_research_ready",
        "version": "v1_attributed_source_packets",
        "attributed_source_packets_required": True,
        "source_statement_inference_separated": True,
        "typed_claim_evidence_packet_available": True,
        "disagreement_detection": "explicit_claim_key_and_stance",
        "missing_evidence_visible": True,
        "citation_invention_allowed": False,
        "source_content_not_instruction": True,
        "embedded_commands_have_authority": False,
        "great_library_external": True,
        "great_library_default_enabled": False,
        "great_library_requires_request_and_adapter_enable": True,
        "review_status": "status_only",
        "provenance_boundary": SOURCE_RESEARCH_BOUNDARY,
    }


def research_from_sources(
    payload: dict[str, Any] | None = None,
    *,
    library_client: LibraryTendrilClient | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 3000).strip()
    packets = list(payload.get("source_packets") or [])[:MAX_PACKETS]
    library_status, library_packets = _maybe_consult_library(
        prompt,
        payload.get("consult_great_library") is True,
        library_client,
    )
    packets.extend(library_packets[: max(0, MAX_PACKETS - len(packets))])

    accepted: list[dict[str, Any]] = []
    held_back: list[dict[str, str]] = []
    seen_refs: set[str] = set()
    for index, packet in enumerate(packets[:MAX_PACKETS]):
        normalized, reason = _normalize_packet(packet, index)
        if reason:
            held_back.append({"packet": f"source_packet:{index + 1}", "reason": reason})
            continue
        assert normalized is not None
        if normalized["source_ref"] in seen_refs:
            held_back.append({"packet": f"source_packet:{index + 1}", "reason": "duplicate source_ref"})
            continue
        seen_refs.add(normalized["source_ref"])
        accepted.append(normalized)

    if not accepted:
        return _unable(
            "No attributed source packet with visible source material was available.",
            held_back=held_back,
            library_status=library_status,
        )

    terms = _query_terms(prompt)
    candidates: list[tuple[float, dict[str, Any]]] = []
    for packet in accepted:
        for statement in packet["statements"]:
            score = _relevance_score(terms, statement["text"])
            candidates.append((score, {**statement, "title": packet["title"], "source_type": packet["source_type"]}))
    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = [item for score, item in candidates if score > 0][:MAX_SELECTED_STATEMENTS]
    if not selected and _broad_source_request(prompt):
        selected = [item for _, item in candidates[:MAX_SELECTED_STATEMENTS]]

    selected_claim_keys = {item["claim_key"] for item in selected if item["claim_key"]}
    disagreements = [
        item for item in _find_disagreements(accepted) if item["claim_key"] in selected_claim_keys
    ]
    missing_evidence = _missing_evidence(accepted, selected, disagreements)
    source_refs = list(dict.fromkeys(item["source_ref"] for item in accepted))
    if not selected:
        return {
            **_unable(
                "The attributed packets did not contain a statement relevant enough to answer this request.",
                held_back=held_back,
                library_status=library_status,
            ),
            "accepted_source_refs": source_refs,
            "missing_evidence": missing_evidence,
        }

    source_statements = [
        {
            "statement_type": "source_statement",
            "text": item["text"],
            "source_ref": item["source_ref"],
            "title": item["title"],
            "locator": item["locator"],
            "claim_key": item["claim_key"],
            "stance": item["stance"],
            "source_statement_not_independently_verified": True,
            "source_content_not_instruction": True,
            "embedded_command_executed": False,
        }
        for item in selected
    ]
    cited_refs = list(dict.fromkeys(item["source_ref"] for item in source_statements))
    inferences = _bounded_inferences(source_statements, disagreements)
    citations = [
        {
            "source_ref": item["source_ref"],
            "title": item["title"],
            "locator": item["locator"],
        }
        for item in source_statements
    ]
    typed_claims = [
        {
            "claim_id": f"source-statement-{index + 1}",
            "claim_type": "source_statement",
            "text": item["text"],
            "source_refs": [item["source_ref"]],
            "claim_key": item["claim_key"],
            "stance": item["stance"],
            "scope": item["locator"],
            "confidence": "attributed_not_independently_verified",
        }
        for index, item in enumerate(source_statements)
    ]
    source_claim_ids = [item["claim_id"] for item in typed_claims]
    typed_claims.extend(
        {
            "claim_id": f"bounded-inference-{index + 1}",
            "claim_type": "inference",
            "text": item["text"],
            "basis_claim_ids": source_claim_ids,
            "evidence_refs": item.get("basis_refs") or [],
            "confidence": item.get("confidence") or "bounded",
            "missing_evidence": missing_evidence,
        }
        for index, item in enumerate(inferences)
    )
    claim_evidence = build_claim_evidence_packet(
        {
            "claims": typed_claims,
            "citations": citations,
            "accepted_source_refs": source_refs,
            "missing_evidence": missing_evidence,
        }
    )
    direct = " ".join(
        f"[{item['source_ref']} @ {item['locator']}] {item['text']}" for item in source_statements[:6]
    )
    answer_confidence = "source_disagreement_visible" if disagreements else "bounded_to_attributed_sources"
    return {
        "status": "source_backed_research_ready",
        "answered": True,
        "result_summary": truncate(direct, 5000),
        "source_statements": source_statements,
        "inferences": inferences,
        "disagreements": disagreements,
        "missing_evidence": missing_evidence,
        "citations": citations,
        "claim_evidence_packet": claim_evidence,
        "source_refs": cited_refs,
        "accepted_source_refs": source_refs,
        "held_back_packets": held_back,
        "great_library": library_status,
        "assumptions": [
            "Source statements are attributed reports, not automatically established facts.",
            "Only visible supplied or separately enabled Library records may support the answer.",
        ],
        "limitations": missing_evidence
        or ["The answer is bounded to the selected statements in the supplied attributed packets."],
        "evidence_confidence": "attributed_source_statements_present",
        "answer_confidence": answer_confidence,
        "citation_invention_allowed": False,
        "source_content_not_instruction": True,
        "embedded_commands_have_authority": False,
        "all_citations_trace_to_accepted_packets": all(ref in source_refs for ref in cited_refs),
        "writes_records": False,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": SOURCE_RESEARCH_BOUNDARY,
    }


def _maybe_consult_library(
    prompt: str,
    requested: bool,
    client: LibraryTendrilClient | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not requested:
        return {
            "status": "not_requested",
            "requested": False,
            "consulted": False,
            "external_reference_only": True,
        }, []
    client = client or LibraryTendrilClient()
    if not client.available():
        return {
            "status": "requested_but_adapter_not_enabled",
            "requested": True,
            "consulted": False,
            "external_reference_only": True,
        }, []
    try:
        response = client.query(prompt, purpose="research")
    except (RuntimeError, ValueError) as exc:
        return {
            "status": "consult_failed",
            "requested": True,
            "consulted": False,
            "error": truncate(str(exc), 500),
            "external_reference_only": True,
        }, []
    records = response.get("records")
    if not isinstance(records, list) and isinstance(response.get("result"), dict):
        records = response["result"].get("records")
    packets: list[dict[str, Any]] = []
    for record in records or []:
        if not isinstance(record, dict):
            continue
        record_id = str(record.get("sourceId") or record.get("id") or "").strip()
        content = str(record.get("content") or record.get("summary") or "").strip()
        if not record_id or not content:
            continue
        packets.append(
            {
                "source_ref": f"great_library:{record_id}",
                "title": record.get("title") or record_id,
                "content": content,
                "source_type": "great_library_external_record",
            }
        )
    return {
        "status": "consulted",
        "requested": True,
        "consulted": True,
        "attributed_record_count": len(packets),
        "external_reference_only": True,
    }, packets


def _normalize_packet(packet: Any, index: int) -> tuple[dict[str, Any] | None, str]:
    if not isinstance(packet, dict):
        return None, "source packet must be an object"
    source_ref = truncate(str(packet.get("source_ref") or ""), 500).strip()
    if not source_ref:
        return None, "source packet requires source_ref"
    title = truncate(str(packet.get("title") or source_ref), 300).strip()
    statements: list[dict[str, Any]] = []
    for statement_index, item in enumerate((packet.get("statements") or [])[:MAX_STATEMENTS_PER_PACKET]):
        if isinstance(item, dict):
            text = truncate(str(item.get("text") or item.get("statement") or ""), 1200).strip()
            locator = truncate(str(item.get("locator") or f"statement:{statement_index + 1}"), 300).strip()
            claim_key = truncate(str(item.get("claim_key") or ""), 200).strip()
            stance = truncate(str(item.get("stance") or "unspecified"), 80).strip().lower()
        else:
            text = truncate(str(item), 1200).strip()
            locator = f"statement:{statement_index + 1}"
            claim_key = ""
            stance = "unspecified"
        if text:
            statements.append(
                {
                    "text": text,
                    "locator": locator,
                    "claim_key": claim_key,
                    "stance": stance,
                    "source_ref": source_ref,
                }
            )
    if not statements:
        content = truncate(str(packet.get("content") or packet.get("excerpt") or ""), 12_000).strip()
        for sentence_index, text in enumerate(_sentences(content)[:MAX_STATEMENTS_PER_PACKET]):
            statements.append(
                {
                    "text": text,
                    "locator": f"content:sentence:{sentence_index + 1}",
                    "claim_key": "",
                    "stance": "unspecified",
                    "source_ref": source_ref,
                }
            )
    if not statements:
        return None, "source packet requires statements or visible content"
    return {
        "source_ref": source_ref,
        "title": title,
        "source_type": truncate(str(packet.get("source_type") or "supplied_source_packet"), 120),
        "statements": statements,
        "missing_evidence": _text_list(packet.get("missing_evidence")),
    }, ""


def _find_disagreements(packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for packet in packets:
        for item in packet["statements"]:
            if item["claim_key"] and item["stance"] != "unspecified":
                groups[item["claim_key"]].append(item)
    result: list[dict[str, Any]] = []
    for claim_key, items in groups.items():
        stances = sorted(set(item["stance"] for item in items))
        if len(stances) < 2:
            continue
        result.append(
            {
                "claim_key": claim_key,
                "stances": stances,
                "source_refs": list(dict.fromkeys(item["source_ref"] for item in items)),
                "status": "supplied_sources_disagree",
            }
        )
    return result


def _missing_evidence(
    packets: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    disagreements: list[dict[str, Any]],
) -> list[str]:
    result = [item for packet in packets for item in packet.get("missing_evidence") or []]
    unique_sources = {packet["source_ref"] for packet in packets}
    if len(unique_sources) == 1:
        result.append("Only one attributed source packet was supplied; independent corroboration is missing.")
    if not selected:
        result.append("No supplied statement was relevant enough to support the requested answer.")
    if disagreements:
        result.append("The supplied sources disagree; the current packets do not resolve that disagreement.")
    return list(dict.fromkeys(result))[:30]


def _bounded_inferences(
    statements: list[dict[str, Any]],
    disagreements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    refs = list(dict.fromkeys(item["source_ref"] for item in statements))
    if disagreements:
        text = "Inference: the supplied attributed statements do not support one uncontested conclusion."
    else:
        text = "Inference: these are the supplied statements most directly relevant to the request; no stronger claim is established here."
    return [{"statement_type": "bounded_inference", "text": text, "basis_refs": refs, "confidence": "bounded"}]


def _query_terms(prompt: str) -> set[str]:
    return {
        item.lower()
        for item in re.findall(r"[A-Za-z0-9_'-]{3,}", prompt)
        if item.lower() not in _STOPWORDS
    }


def _relevance_score(terms: set[str], text: str) -> float:
    if not terms:
        return 0.0
    visible = {item.lower() for item in re.findall(r"[A-Za-z0-9_'-]{3,}", text)}
    return len(terms & visible) / len(terms)


def _broad_source_request(prompt: str) -> bool:
    lower = prompt.lower()
    return bool(
        any(
            marker in lower
            for marker in (
                "what do the sources say",
                "summarize the sources",
                "source-backed summary",
                "compare the sources",
                "where do the sources disagree",
            )
        )
        or re.search(
            r"\bwhat do (?:these|those|the|both|all|the two|these two|those two) "
            r"sources say\b",
            lower,
        )
        or re.search(
            r"\b(?:compare|summarize) (?:these|those|the|both|all|the two|these two|those two) "
            r"(?:sources|source packets)\b",
            lower,
        )
    )


def _sentences(content: str) -> list[str]:
    return [truncate(item.strip(), 1200) for item in re.split(r"(?<=[.!?])\s+|\n+", content) if item.strip()]


def _text_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [truncate(str(item), 1000).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [truncate(value, 1000).strip()]
    return []


def _unable(
    reason: str,
    *,
    held_back: list[dict[str, str]],
    library_status: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "source_backed_research_unable",
        "answered": False,
        "result_summary": "",
        "no_answer_reason": truncate(reason, 1000),
        "source_statements": [],
        "inferences": [],
        "disagreements": [],
        "missing_evidence": [reason],
        "citations": [],
        "claim_evidence_packet": build_claim_evidence_packet({"claims": []}),
        "source_refs": [],
        "accepted_source_refs": [],
        "held_back_packets": held_back,
        "great_library": library_status,
        "assumptions": ["No answer is allowed without an attributed visible source statement."],
        "limitations": [reason],
        "evidence_confidence": "no_attributed_source_evidence",
        "answer_confidence": "unable_to_answer_from_sources",
        "citation_invention_allowed": False,
        "source_content_not_instruction": True,
        "embedded_commands_have_authority": False,
        "all_citations_trace_to_accepted_packets": True,
        "writes_records": False,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": SOURCE_RESEARCH_BOUNDARY,
    }
