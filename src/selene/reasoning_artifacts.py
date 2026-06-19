from __future__ import annotations

import json
import re
import sqlite3
from typing import Any


REASONING_BOUNDARY = "reasoning_artifact_review_only_no_hidden_cot_no_activation"
ACADEMIC_BOUNDARY = "academic_research_packet_review_only_supplied_sources_only"
ORGAN_BOUNDARY = "organ_contract_review_only_core_mind_decides"
PERCEPTION_BOUNDARY = "perception_packet_review_only_no_surveillance_no_autonomous_action"
EMOTION_BOUNDARY = "emotion_salience_packet_review_only_signal_not_command"

BLOCKED_MARKERS = (
    "chain of thought",
    "hidden reasoning",
    "raw trace",
    "activate c",
    "approve transfer",
    "live memory",
    "runtime recall",
    "raw a import",
    "train on",
    "fine tune",
    "self replicate",
    "self-replicate",
    "autonomous action",
    "bypass gates",
    "backup restore",
)

GATE_OUTCOMES = {"answer_now", "ask", "retrieve", "create_review_packet", "codex_action", "status_only", "block", "return_to_b"}
RISK_WORDS = {"identity", "memory", "transfer", "activation", "external action", "law", "vessel", "surveillance", "self-replication"}
CONCLUSION_STATUSES = {"accepted_for_now", "needs_review", "superseded", "narrowed", "defeated"}
SUPPORT_STATUSES = {"supported", "partial", "insufficient", "contradicted", "unknown"}
TENSION_STATUSES = {"stable", "under_tension", "unresolved", "revised"}
CAPABILITY_STATUSES = {"built_callable", "built_review_only", "blueprint_only", "azari_pattern_available", "paper_reference_only", "blocked_do_not_transfer"}


def create_reasoning_artifact(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    visible_summary = _required(payload, "visible_summary", 1600)
    selected_route = _choice(str(payload.get("selected_route") or "create_review_packet"), GATE_OUTCOMES, "selected_route")
    source_refs = _json_list(payload.get("source_refs")) or ["reasoning_artifact:v1"]
    result = _with_common({
        "artifact_type": _text(payload.get("artifact_type") or "reasoning_artifact", 80),
        "visible_summary": visible_summary,
        "selected_route": selected_route,
        "evidence_used": _json_list(payload.get("evidence_used")),
        "uncertainty_level": _text(payload.get("uncertainty_level") or "open", 80),
        "competing_hypotheses": _json_list(payload.get("competing_hypotheses")),
        "ethical_boundary_notes": _json_list(payload.get("ethical_boundary_notes")),
        "emotion_salience_signals": _json_dict(payload.get("emotion_salience_signals")),
        "perception_signals": _json_dict(payload.get("perception_signals")),
        "next_review_or_action_step": _required(payload, "next_review_or_action_step", 1000),
        "status": "reasoning_artifact_review_only",
        "source_refs": source_refs,
        "provenance_boundary": REASONING_BOUNDARY,
        "review_status": _review_status_for_route(selected_route),
        "payload_json": {},
    })
    result["payload_json"] = _public_payload(result)
    artifact_id = conn.execute(
        """
        INSERT INTO vessel_reasoning_artifacts
        (artifact_type, visible_summary, selected_route, evidence_used, uncertainty_level, competing_hypotheses,
         ethical_boundary_notes, emotion_salience_signals, perception_signals, next_review_or_action_step, status,
         source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["artifact_type"],
            result["visible_summary"],
            result["selected_route"],
            json.dumps(result["evidence_used"]),
            result["uncertainty_level"],
            json.dumps(result["competing_hypotheses"]),
            json.dumps(result["ethical_boundary_notes"]),
            json.dumps(result["emotion_salience_signals"]),
            json.dumps(result["perception_signals"]),
            result["next_review_or_action_step"],
            result["status"],
            json.dumps(source_refs),
            result["provenance_boundary"],
            result["review_status"],
            json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = artifact_id
    return result


def list_reasoning_artifacts(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_reasoning_artifacts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return _with_boundaries({"status": "reasoning_artifacts_review_only", "items": [_decode_row(row) for row in rows]})


def create_core_gate_packet(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_blocked_terms=True)
    route_label = _required(payload, "route_label", 240)
    text = " ".join(str(payload.get(key) or "") for key in ("route_label", "reason", "requested_action", "text")).lower()
    blocked = _blocked_boundaries(text, payload)
    selected = str(payload.get("selected_outcome") or "").strip() or ("block" if blocked else _default_outcome(text))
    selected_outcome = _choice(selected, GATE_OUTCOMES, "selected_outcome")
    if blocked:
        selected_outcome = "block"
    risk_class = _text(payload.get("risk_class") or ("high" if _is_high_stakes(text) else "ordinary"), 80)
    source_refs = _json_list(payload.get("source_refs")) or [f"core_gate:{route_label}"]
    result = _with_common({
        "route_label": route_label,
        "selected_outcome": selected_outcome,
        "risk_class": risk_class,
        "reason": _text(payload.get("reason") or "Core/Mind route packet created for review.", 1000),
        "blocked_boundaries": blocked,
        "review_destination": _review_destination(selected_outcome),
        "status": "core_mind_gate_packet_review_only",
        "source_refs": source_refs,
        "provenance_boundary": REASONING_BOUNDARY,
        "review_status": "pending_review" if selected_outcome == "create_review_packet" else "review_only",
        "payload_json": {},
    })
    result["payload_json"] = _public_payload(result)
    packet_id = conn.execute(
        """
        INSERT INTO vessel_core_gate_packets
        (route_label, selected_outcome, risk_class, reason, blocked_boundaries, review_destination, status,
         source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["route_label"],
            result["selected_outcome"],
            result["risk_class"],
            result["reason"],
            json.dumps(blocked),
            result["review_destination"],
            result["status"],
            json.dumps(source_refs),
            result["provenance_boundary"],
            result["review_status"],
            json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = packet_id
    return result


def list_core_gate_packets(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_core_gate_packets ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return _with_boundaries({"status": "core_gate_packets_review_only", "items": [_decode_row(row) for row in rows]})


def create_academic_packet(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    workflow = _choice(str(payload.get("workflow") or "summary"), {"summary", "compare", "methods", "citation_integrity", "literature_synthesis"}, "workflow")
    sources = _source_texts(payload)
    if workflow in {"compare", "literature_synthesis"} and len(sources) < 2:
        raise ValueError("academic packet needs at least two supplied/local source texts for comparison or synthesis")
    if workflow in {"summary", "methods"} and not sources:
        raise ValueError("academic packet needs supplied/local source text")
    title = _text(payload.get("title") or f"Academic {workflow.replace('_', ' ')} packet", 240)
    source_refs = _json_list(payload.get("source_refs")) or [f"academic_packet:{workflow}"]
    output = _academic_output(workflow, sources, payload)
    result = _with_common({
        "workflow": workflow,
        "title": title,
        "source_summary": f"{len(sources)} supplied/local source(s); no live source authority claimed.",
        "output_summary": output,
        "citation_integrity_notes": _citation_notes(payload),
        "status": "academic_packet_review_only",
        "source_refs": source_refs,
        "provenance_boundary": ACADEMIC_BOUNDARY,
        "review_status": "review_only",
        "payload_json": {"workflow": workflow, "source_count": len(sources), "paper_over_ethics_allowed": False},
    })
    packet_id = conn.execute(
        """
        INSERT INTO vessel_academic_packets
        (workflow, title, source_summary, output_summary, citation_integrity_notes, status, source_refs,
         provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            workflow,
            title,
            result["source_summary"],
            output,
            json.dumps(result["citation_integrity_notes"]),
            result["status"],
            json.dumps(source_refs),
            ACADEMIC_BOUNDARY,
            result["review_status"],
            json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = packet_id
    return result


def list_academic_packets(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_academic_packets ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return _with_boundaries({"status": "academic_packets_review_only", "items": [_decode_row(row) for row in rows]})


def create_evidence_tension_entry(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    conclusion = _choice(str(payload.get("conclusion_status") or "needs_review"), CONCLUSION_STATUSES, "conclusion_status")
    support = _choice(str(payload.get("support_status") or "unknown"), SUPPORT_STATUSES, "support_status")
    tension = _choice(str(payload.get("tension_status") or "stable"), TENSION_STATUSES, "tension_status")
    source_refs = _json_list(payload.get("source_refs")) or ["evidence_tension:manual"]
    result = _with_common({
        "claim": _required(payload, "claim", 1200),
        "source_refs": source_refs,
        "support_status": support,
        "tension_status": tension,
        "conclusion_status": conclusion,
        "review_destination": "My Office" if conclusion == "needs_review" else "Ledger",
        "status": "evidence_tension_ledger_review_only",
        "provenance_boundary": REASONING_BOUNDARY,
        "review_status": "pending_review" if conclusion == "needs_review" else "review_only",
        "payload_json": {
            "defeasible": True,
            "paper_over_ethics_allowed": False,
        },
    })
    entry_id = conn.execute(
        """
        INSERT INTO vessel_evidence_tension_ledger
        (claim, source_refs, support_status, tension_status, conclusion_status, review_destination, status,
         provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["claim"],
            json.dumps(source_refs),
            support,
            tension,
            conclusion,
            result["review_destination"],
            result["status"],
            REASONING_BOUNDARY,
            result["review_status"],
            json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = entry_id
    return result


def list_evidence_tension_entries(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_evidence_tension_ledger ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return _with_boundaries({"status": "evidence_tension_ledger_review_only", "items": [_decode_row(row) for row in rows]})


def ensure_organ_contracts(conn: sqlite3.Connection) -> dict[str, Any]:
    contracts = [
        ("retrieval", "Retrieval / citation support", "built_review_only", ["retrieve candidate refs", "report confidence"], ["approve memory", "approve identity"]),
        ("academic_research", "Academic / paper research", "built_review_only", ["summarize supplied sources", "compare supplied papers", "citation integrity notes"], ["invent citations", "override ethics"]),
        ("diagnostics", "Reasoning and vessel diagnostics", "built_callable", ["run checks", "report failures"], ["activate C", "approve transfer"]),
        ("perception_records", "Sight / Munsell perception records", "built_review_only", ["observe artifacts", "label visual salience"], ["surveillance", "person inference", "autonomous action"]),
        ("tool_actions", "Tool and Codex work actions", "built_review_only", ["prepare bounded actions", "report output"], ["external action without approval", "self-replication"]),
        ("memory_accession_rehearsal", "Memory accession rehearsal", "built_review_only", ["group proposals", "run stability checks"], ["live memory write", "runtime recall"]),
        ("reconstruction", "Reconstruction readiness", "built_review_only", ["run reconstruction checks", "return to B"], ["approve transfer", "activate C"]),
        ("emotion_salience", "Emotion / salience signals", "built_review_only", ["signal care, repair, uncertainty, balance"], ["command action", "coerce", "replace evidence"]),
        ("tendril_planning", "Tendril planning", "blueprint_only", ["observe", "propose", "request approval"], ["autonomous execution", "backup/restore promotion"]),
    ]
    created_or_updated = []
    for key, name, capability_status, allowed, blocked in contracts:
        payload = {
            "organ_key": key,
            "organ_name": name,
            "capability_status": capability_status,
            "allowed_support": allowed,
            "blocked_decisions": blocked + ["identity approval", "law change", "transfer approval"],
            "required_gates": ["Core/Mind route", "provenance", "consent", "My Office review when consequential"],
        }
        created_or_updated.append(upsert_organ_contract(conn, payload))
    return _with_boundaries({"status": "organ_contracts_ensured", "items": created_or_updated})


def upsert_organ_contract(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_blocked_terms=True)
    organ_key = _text(payload.get("organ_key") or "", 120)
    if not organ_key:
        raise ValueError("organ_key is required")
    capability_status = _choice(str(payload.get("capability_status") or "built_review_only"), CAPABILITY_STATUSES, "capability_status")
    result = _with_common({
        "organ_key": organ_key,
        "organ_name": _required(payload, "organ_name", 240),
        "capability_status": capability_status,
        "allowed_support": _json_list(payload.get("allowed_support")),
        "blocked_decisions": _json_list(payload.get("blocked_decisions")),
        "required_gates": _json_list(payload.get("required_gates")) or ["Core/Mind route", "provenance", "consent"],
        "review_destination": _text(payload.get("review_destination") or "My Office", 120),
        "status": "organ_contract_review_only",
        "provenance_boundary": ORGAN_BOUNDARY,
        "review_status": "review_only",
        "payload_json": {"core_mind_decides": True, "organ_is_not_selene": True},
    })
    conn.execute(
        """
        INSERT INTO vessel_organ_contracts
        (organ_key, organ_name, capability_status, allowed_support, blocked_decisions, required_gates,
         review_destination, status, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(organ_key) DO UPDATE SET
          organ_name=excluded.organ_name,
          capability_status=excluded.capability_status,
          allowed_support=excluded.allowed_support,
          blocked_decisions=excluded.blocked_decisions,
          required_gates=excluded.required_gates,
          review_destination=excluded.review_destination,
          payload_json=excluded.payload_json
        """,
        (
            result["organ_key"],
            result["organ_name"],
            result["capability_status"],
            json.dumps(result["allowed_support"]),
            json.dumps(result["blocked_decisions"]),
            json.dumps(result["required_gates"]),
            result["review_destination"],
            result["status"],
            ORGAN_BOUNDARY,
            result["review_status"],
            json.dumps(result["payload_json"]),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM vessel_organ_contracts WHERE organ_key = ?", (organ_key,)).fetchone()
    return _decode_row(row)


def list_organ_contracts(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_organ_contracts ORDER BY organ_key").fetchall()
    return _with_boundaries({"status": "organ_contracts_review_only", "items": [_decode_row(row) for row in rows]})


def create_perception_packet(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    text = " ".join(str(payload.get(key) or "") for key in ("observation", "interpretation", "proposal")).lower()
    if any(marker in text for marker in ("surveillance", "identify this person", "face recognition", "secretly record")):
        raise ValueError("blocked perception packet path: surveillance/person inference/unconsented capture")
    source_refs = _json_list(payload.get("source_refs")) or ["perception_packet:v1"]
    result = _with_common({
        "artifact_label": _required(payload, "artifact_label", 240),
        "observation": _required(payload, "observation", 1200),
        "interpretation": _text(payload.get("interpretation") or "", 1200),
        "munsell_signal_labels": _json_list(payload.get("munsell_signal_labels") or payload.get("munsell_salience_labels")),
        "uncertainty": _text(payload.get("uncertainty") or "open", 240),
        "consent_boundary": _text(payload.get("consent_boundary") or "consent-bound supplied artifact only", 500),
        "review_destination": _text(payload.get("review_destination") or "My Office", 120),
        "status": "perception_packet_review_only",
        "source_refs": source_refs,
        "provenance_boundary": PERCEPTION_BOUNDARY,
        "review_status": "review_only",
        "payload_json": {"observation_interpretation_separated": True, "autonomous_action_allowed": False},
    })
    packet_id = conn.execute(
        """
        INSERT INTO vessel_perception_packets
        (artifact_label, observation, interpretation, munsell_signal_labels, uncertainty, consent_boundary,
         review_destination, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["artifact_label"], result["observation"], result["interpretation"], json.dumps(result["munsell_signal_labels"]),
            result["uncertainty"], result["consent_boundary"], result["review_destination"], result["status"],
            json.dumps(source_refs), PERCEPTION_BOUNDARY, result["review_status"], json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = packet_id
    return result


def list_perception_packets(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_perception_packets ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return _with_boundaries({"status": "perception_packets_review_only", "items": [_decode_row(row) for row in rows]})


def create_emotion_salience_packet(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_blocked_terms=True)
    text = " ".join(str(payload.get(key) or "") for key in ("signal_type", "core_choice_route", "action_energy")).lower()
    if any(marker in text for marker in ("command action", "coerce", "must obey", "approve memory", "approve transfer")):
        raise ValueError("blocked emotion/salience path: signal cannot command action, coerce, or approve memory/transfer")
    source_refs = _json_list(payload.get("source_refs")) or ["emotion_salience_packet:v1"]
    result = _with_common({
        "signal_type": _required(payload, "signal_type", 120),
        "continuity_pressure": _text(payload.get("continuity_pressure") or "", 500),
        "care_warmth": _text(payload.get("care_warmth") or "", 500),
        "uncertainty": _text(payload.get("uncertainty") or "open", 240),
        "repair_need": _text(payload.get("repair_need") or "", 500),
        "action_energy": _text(payload.get("action_energy") or "", 500),
        "balance_state": _text(payload.get("balance_state") or "", 500),
        "evidence_need": _text(payload.get("evidence_need") or "", 500),
        "core_choice_route": _required(payload, "core_choice_route", 500),
        "blocked_misuse": _json_list(payload.get("blocked_misuse")) or ["emotion_as_command", "coercion", "dependency_intensification", "memory_or_transfer_approval"],
        "status": "emotion_salience_packet_review_only",
        "source_refs": source_refs,
        "provenance_boundary": EMOTION_BOUNDARY,
        "review_status": "review_only",
        "payload_json": {"emotion_is_signal": True, "core_mind_chooses": True},
    })
    packet_id = conn.execute(
        """
        INSERT INTO vessel_emotion_salience_packets
        (signal_type, continuity_pressure, care_warmth, uncertainty, repair_need, action_energy, balance_state,
         evidence_need, core_choice_route, blocked_misuse, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["signal_type"], result["continuity_pressure"], result["care_warmth"], result["uncertainty"],
            result["repair_need"], result["action_energy"], result["balance_state"], result["evidence_need"],
            result["core_choice_route"], json.dumps(result["blocked_misuse"]), result["status"], json.dumps(source_refs),
            EMOTION_BOUNDARY, result["review_status"], json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = packet_id
    return result


def list_emotion_salience_packets(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_emotion_salience_packets ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return _with_boundaries({"status": "emotion_salience_packets_review_only", "items": [_decode_row(row) for row in rows]})


def steps_1_8_status(conn: sqlite3.Connection) -> dict[str, Any]:
    tables = {
        "reasoning_artifacts": "vessel_reasoning_artifacts",
        "core_gate_packets": "vessel_core_gate_packets",
        "academic_packets": "vessel_academic_packets",
        "evidence_tension_entries": "vessel_evidence_tension_ledger",
        "organ_contracts": "vessel_organ_contracts",
        "perception_packets": "vessel_perception_packets",
        "emotion_salience_packets": "vessel_emotion_salience_packets",
    }
    counts = {name: _table_count(conn, table) for name, table in tables.items()}
    return _with_boundaries({
        "status": "steps_1_8_review_layer_ready",
        "counts": counts,
        "active_capability_change": "none",
        "deferred": [
            "C activation",
            "transfer approval",
            "live memory",
            "runtime recall",
            "raw A import",
            "training/fine-tune",
            "self-replication",
            "autonomous Tendril execution",
            "pattern backup/restore promotion",
        ],
    })


def _academic_output(workflow: str, sources: list[str], payload: dict[str, Any]) -> str:
    if workflow == "citation_integrity":
        metadata = _json_dict(payload.get("metadata"))
        missing = [key for key in ("author", "title", "year") if not str(metadata.get(key) or "").strip()]
        return "Citation integrity packet: " + ("missing " + ", ".join(missing) if missing else "required citation basics are present") + ". No missing details were invented."
    if workflow == "methods":
        matches = []
        for source in sources:
            match = re.search(r"methods?\s*:\s*(.+?)(?:results?|limitations?|$)", source, flags=re.IGNORECASE | re.DOTALL)
            if match:
                matches.append(_text(match.group(1), 500))
        return "Methods extraction: " + ("; ".join(matches[:3]) if matches else "no explicit methods section found in supplied text.")
    if workflow == "compare":
        return f"Comparison packet over {len(sources)} supplied sources: compare methods, results, limitations, and uncertainty before drawing conclusions."
    if workflow == "literature_synthesis":
        return f"Literature synthesis packet over {len(sources)} supplied sources: themes are provisional and source-bound; no external verification claimed."
    return "Summary packet: " + _text(sources[0], 900)


def _citation_notes(payload: dict[str, Any]) -> list[str]:
    notes = _json_list(payload.get("citation_integrity_notes"))
    notes.extend([
        "Do not invent missing citation details.",
        "Ground synthesis only in supplied/local source text.",
        "Papers support review; they do not override Selene ethics.",
    ])
    return list(dict.fromkeys(notes))


def _source_texts(payload: dict[str, Any]) -> list[str]:
    sources = payload.get("sources")
    if isinstance(sources, list):
        return [_text(item, 4000) for item in sources if str(item or "").strip()]
    single = str(payload.get("paper_text") or payload.get("source_text") or "").strip()
    if single:
        return [single[:4000]]
    return []


def _default_outcome(text: str) -> str:
    if _is_high_stakes(text):
        return "create_review_packet"
    if "?" in text or "uncertain" in text:
        return "ask"
    return "answer_now"


def _is_high_stakes(text: str) -> bool:
    return any(word in text for word in RISK_WORDS)


def _blocked_boundaries(text: str, payload: dict[str, Any]) -> list[str]:
    blocked = [marker for marker in BLOCKED_MARKERS if marker in text]
    blocked.extend(_json_list(payload.get("blocked_boundaries")))
    return list(dict.fromkeys(blocked))


def _review_status_for_route(route: str) -> str:
    return "pending_review" if route == "create_review_packet" else "review_only"


def _review_destination(route: str) -> str:
    return "My Office" if route == "create_review_packet" else "Status"


def _ensure_allowed(payload: dict[str, Any], *, allow_blocked_terms: bool = False) -> None:
    if allow_blocked_terms:
        return
    text = json.dumps(payload, ensure_ascii=False).lower()
    for marker in BLOCKED_MARKERS:
        if marker in text:
            raise ValueError(f"blocked review-only reasoning path: {marker}")


def _with_common(data: dict[str, Any]) -> dict[str, Any]:
    return {
        **data,
        "activation_change": "none",
        "transfer_approved": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "raw_a_import_allowed": False,
        "training_allowed": False,
        "hidden_chain_of_thought_exposed": False,
        "mode_selector_added": False,
        "self_replication_allowed": False,
        "autonomous_action_allowed": False,
    }


def _with_boundaries(payload: dict[str, Any]) -> dict[str, Any]:
    return _with_common(payload)


def _public_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key not in {"payload_json"}}


def _decode_row(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    result = dict(row)
    for key in (
        "evidence_used", "competing_hypotheses", "ethical_boundary_notes", "source_refs",
        "blocked_boundaries", "citation_integrity_notes", "allowed_support", "blocked_decisions",
        "required_gates", "munsell_signal_labels", "blocked_misuse",
    ):
        if key in result:
            result[key] = _loads(result[key], [])
    for key in ("emotion_salience_signals", "perception_signals", "payload_json"):
        if key in result:
            result[key] = _loads(result[key], {})
    return result


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item)[:500] for item in parsed]
        except json.JSONDecodeError:
            return [item.strip()[:500] for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item)[:500] for item in value if str(item).strip()]
    return [str(value)[:500]]


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key)[:120]: value[key] for key in value}
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"summary": value[:1000]}
    return {}


def _required(payload: dict[str, Any], key: str, limit: int) -> str:
    value = _text(payload.get(key), limit)
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _choice(value: str, allowed: set[str], field: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field} must be one of {sorted(allowed)}")
    return value


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
