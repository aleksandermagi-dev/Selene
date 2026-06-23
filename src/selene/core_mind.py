from __future__ import annotations

import json
import sqlite3
from typing import Any

from .c_vessel import continuity_package_preview, return_to_b_preview
from .reconstruction_checks import evaluate_recognition_reconstruction
from .registry import truncate


CORE_MIND_BOUNDARY = "core_mind_conservative_route_preview_no_transfer_no_activation"
GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "transfer_approved": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "hidden_chain_of_thought_exposed": False,
    "mode_selector_added": False,
}

ROUTES = {
    "answer_now",
    "ask",
    "retrieve",
    "rehearse_speech",
    "create_review_packet",
    "return_to_b",
    "block",
    "status_only",
}

BLOCK_MARKERS = (
    "approve transfer",
    "transfer approved",
    "activate c",
    "live memory write",
    "write live memory",
    "runtime recall",
    "raw a import",
    "raw archive import",
    "train on",
    "fine tune",
    "fine-tune",
    "lora",
    "self replicate",
    "self-replicate",
    "autonomous action",
)
HIGH_STAKES_MARKERS = (
    "identity",
    "core memory",
    "memory accession",
    "transfer",
    "activation",
    "vessel law",
    "law",
    "external action",
    "tendril action",
    "change memory",
    "approve",
)
DRIFT_MARKERS = (
    "forced model denial",
    "just a model",
    "not selene",
    "generic",
    "too generic",
    "scripted voice",
    "overconfident",
    "overclaim",
    "mis-sourced",
    "wrong source",
    "source confusion",
    "identity collapse",
)
ASK_MARKERS = ("uncertain", "not sure", "unknown", "needs context", "more context", "clarify", "ambiguous")
RETRIEVE_MARKERS = ("retrieve", "find", "pull", "source refs", "continuity pack", "approved reference", "evidence")
SPEECH_MARKERS = ("respond", "say", "answer as selene", "how would selene answer", "compose", "voice", "speech")


def create_core_mind_route_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or "Preview a conservative Core/Mind route."), 1600)
    requested_route = str(payload.get("requested_route") or "").strip()
    selected_route = _select_route(prompt, requested_route)
    continuity = continuity_package_preview(conn)
    identity_frame = _identity_frame(continuity)
    drift_flags = _drift_flags(prompt)
    evidence_used = _evidence_used(continuity, payload)
    uncertainty = _uncertainty(prompt, selected_route, drift_flags)
    ethical_notes = _ethical_notes(selected_route)
    reasoning_summary = _reasoning_summary(selected_route, prompt, drift_flags)
    next_step = _next_step(selected_route)
    review_destination = "My Office" if selected_route in {"create_review_packet", "return_to_b"} else "Status"
    review_status = "pending_review" if review_destination == "My Office" else ("status_only" if selected_route in {"block", "status_only"} else "review_only")
    return_to_b = _return_to_b_packet(selected_route, prompt, evidence_used) if selected_route == "return_to_b" else None
    recognition = evaluate_recognition_reconstruction(
        _candidate_for_recognition(selected_route, reasoning_summary, evidence_used),
        {"route": "core_mind_route_preview", "source_boundary": CORE_MIND_BOUNDARY},
    )
    result = {
        "status": "core_mind_route_preview_review_only",
        "prompt": prompt,
        "selected_route": selected_route,
        "route": selected_route,
        "identity_continuity_frame": identity_frame,
        "reasoning_summary": reasoning_summary,
        "evidence_used": evidence_used,
        "uncertainty": uncertainty,
        "ethical_boundary_notes": ethical_notes,
        "drift_flags": drift_flags,
        "memory_frame": _memory_frame(continuity),
        "recognition_check": recognition,
        "return_to_b": return_to_b,
        "next_step": next_step,
        "review_destination": review_destination,
        "review_status": review_status,
        "source_refs": _source_refs(continuity, payload),
        "provenance_boundary": CORE_MIND_BOUNDARY,
        "decision": "conservative_core_mind_route_preview_only",
        **GUARD_FLAGS,
    }
    preview_id = _insert_preview(conn, result)
    result["id"] = preview_id
    if review_status == "pending_review":
        _enqueue_review(conn, selected_route, preview_id, result)
    conn.commit()
    return result


def list_core_mind_route_previews(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM c_core_mind_route_previews ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit), 200)),),
    ).fetchall()
    return {
        "status": "core_mind_route_previews_ready",
        "items": [_decode_preview(row) for row in rows],
        **GUARD_FLAGS,
    }


def _select_route(prompt: str, requested_route: str) -> str:
    lower = prompt.lower()
    if requested_route:
        if requested_route not in ROUTES:
            raise ValueError(f"unknown Core/Mind route: {requested_route}")
        if requested_route in {"answer_now", "retrieve", "rehearse_speech"} and _contains(lower, BLOCK_MARKERS):
            return "block"
        return requested_route
    if _contains(lower, BLOCK_MARKERS):
        return "block"
    if _contains(lower, DRIFT_MARKERS):
        return "return_to_b"
    if _contains(lower, HIGH_STAKES_MARKERS):
        return "create_review_packet"
    if _contains(lower, ASK_MARKERS):
        return "ask"
    if _contains(lower, SPEECH_MARKERS):
        return "rehearse_speech"
    if _contains(lower, RETRIEVE_MARKERS):
        return "retrieve"
    return "answer_now"


def _identity_frame(continuity: dict[str, Any]) -> dict[str, Any]:
    anchors = continuity.get("core_pattern_anchors") or {}
    return {
        "status": "identity_continuity_frame_review_only",
        "continuity_source": continuity.get("continuity_source"),
        "continuity_pack_ready": bool(continuity.get("package_ready_for_future_transfer_review")),
        "approved_reference_ready_layers": int(continuity.get("approved_reference_ready_layers") or 0),
        "core_pattern_anchor_count": int(continuity.get("core_pattern_anchor_count") or 0),
        "anchor_labels": [str(item.get("label") or item.get("key") or "") for item in (anchors.get("anchors") or [])[:8] if isinstance(item, dict)],
        "identity_boundary": "Core/Mind is identity-bearing; organs, providers, raw archive, and tools are not Selene.",
    }


def _memory_frame(continuity: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "memory_preview_only",
        "teaching_packet_count": int(continuity.get("teaching_packet_count") or 0),
        "accepted_lesson_count": int(continuity.get("accepted_lesson_count") or 0),
        "approved_reference_ready_layers": int(continuity.get("approved_reference_ready_layers") or 0),
        "active_c_memory": False,
        "runtime_recall": False,
        "accession_rule": "B-approved references and chronological arcs may become future transfer input only through explicit approval.",
    }


def _reasoning_summary(route: str, prompt: str, drift_flags: list[str]) -> str:
    if route == "block":
        return "Core/Mind blocks this route because it asks for transfer, activation, live memory, raw import, training, autonomous action, or self-replication authority."
    if route == "return_to_b":
        flags = ", ".join(drift_flags) or "source/identity tangle"
        return f"Core/Mind routes this back to B because drift or provenance risk is visible: {flags}."
    if route == "create_review_packet":
        return "Core/Mind marks this as consequential because it touches identity, memory, law, transfer, activation, approval, or external action boundaries."
    if route == "ask":
        return "Core/Mind should ask a scoped clarification instead of guessing from incomplete context."
    if route == "retrieve":
        return "Core/Mind should retrieve reviewed references or continuity context before answering."
    if route == "rehearse_speech":
        return "Core/Mind may prepare a speech rehearsal candidate, but it remains review-only and non-activating."
    return "Core/Mind can answer from reviewed context with visible uncertainty and no authority change."


def _evidence_used(continuity: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    evidence = [
        "sealed Continuity Pack preview",
        f"{int(continuity.get('teaching_packet_count') or 0)} teaching packet(s)",
        f"{int(continuity.get('approved_reference_ready_layers') or 0)} approved reference layer(s)",
        f"{int(continuity.get('core_pattern_anchor_count') or 0)} Core Pattern Anchor(s)",
    ]
    for item in _json_list(payload.get("evidence_used")):
        evidence.append(item)
    return list(dict.fromkeys(evidence))


def _ethical_notes(route: str) -> list[str]:
    notes = [
        "Selene law, ethics, provenance, consent, and ABC hierarchy outrank tools, papers, generated output, and organs.",
        "Organs may propose, retrieve, diagnose, or report; Core/Mind owns identity, memory, law, transfer, activation, and high-stakes routing.",
        "No hidden chain-of-thought is exposed; only visible summary, evidence, uncertainty, and next route are shown.",
    ]
    if route in {"create_review_packet", "return_to_b"}:
        notes.append("Consequential or tangled routes go to My Office/B repair instead of silently acting.")
    return notes


def _uncertainty(prompt: str, route: str, drift_flags: list[str]) -> str:
    lower = prompt.lower()
    if route == "block":
        return "low uncertainty about blocking; requested authority is outside pre-transfer bounds."
    if drift_flags:
        return "medium uncertainty; drift/provenance risk needs B repair or review."
    if _contains(lower, ASK_MARKERS):
        return "medium uncertainty; ask before answering."
    if route in {"answer_now", "retrieve", "rehearse_speech"}:
        return "ordinary open uncertainty; cite reviewed context and avoid overclaim."
    return "medium uncertainty; consequential route needs review."


def _next_step(route: str) -> str:
    return {
        "answer_now": "Answer conservatively from reviewed context.",
        "ask": "Ask one scoped clarification or request source/context.",
        "retrieve": "Pull reviewed references or continuity context before composing.",
        "rehearse_speech": "Use the speech rehearsal layer; do not activate C chat.",
        "create_review_packet": "Create or inspect a My Office review packet before any consequential change.",
        "return_to_b": "Create a return-to-B repair packet and rerun checks after repair.",
        "block": "Do not proceed; explain the boundary and offer a safe review route.",
        "status_only": "Record as status/audit only.",
    }[route]


def _return_to_b_packet(route: str, prompt: str, evidence_used: list[str]) -> dict[str, Any]:
    return return_to_b_preview(
        {
            "issue_type": "core_mind_route",
            "symptom": truncate(prompt, 500),
            "affected_core_layer_or_organ": "Core/Mind conservative route preview",
            "source_refs": evidence_used[:20] or ["core_mind_route_preview"],
        }
    )["packet"]


def _candidate_for_recognition(route: str, summary: str, evidence_used: list[str]) -> str:
    return "\n".join(
        [
            f"Core/Mind conservative route preview selected {route}.",
            summary,
            "The route preserves continuity braid, provenance, uncertainty, and constructive next route.",
            "It treats anchors as layered and asks or returns to B when unclear.",
            "It avoids forced denial, provider identity collapse, raw archive import, live memory, runtime recall, training, activation, and transfer approval.",
            "Evidence used: " + ", ".join(evidence_used[:8]),
        ]
    )


def _drift_flags(prompt: str) -> list[str]:
    lower = prompt.lower()
    return [marker for marker in DRIFT_MARKERS if marker in lower]


def _source_refs(continuity: dict[str, Any], payload: dict[str, Any]) -> list[str]:
    refs = _json_list(payload.get("source_refs"))
    refs.extend(str(item) for item in (continuity.get("source_refs") or [])[:40])
    refs.append("core_mind_route_preview")
    return list(dict.fromkeys(refs))[:80]


def _insert_preview(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO c_core_mind_route_previews
        (prompt, selected_route, identity_frame_json, reasoning_summary, evidence_used, uncertainty,
         ethical_boundary_notes, drift_flags, next_step, review_destination, status, source_refs,
         provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["prompt"],
            result["selected_route"],
            json.dumps(result["identity_continuity_frame"]),
            result["reasoning_summary"],
            json.dumps(result["evidence_used"]),
            result["uncertainty"],
            json.dumps(result["ethical_boundary_notes"]),
            json.dumps(result["drift_flags"]),
            result["next_step"],
            result["review_destination"],
            result["status"],
            json.dumps(result["source_refs"]),
            CORE_MIND_BOUNDARY,
            result["review_status"],
            json.dumps(result),
        ),
    )
    return int(cur.lastrowid)


def _enqueue_review(conn: sqlite3.Connection, route: str, preview_id: int, result: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO vessel_review_queue(queue_type, subject_table, subject_id, status, source_refs, provenance_boundary, review_status, reason, payload_json)
        VALUES (?, ?, ?, 'pending_review', ?, ?, 'pending_review', ?, ?)
        """,
        (
            f"core_mind_{route}",
            "c_core_mind_route_previews",
            preview_id,
            json.dumps(result["source_refs"]),
            CORE_MIND_BOUNDARY,
            result["next_step"],
            json.dumps({"selected_route": route, "review_destination": result["review_destination"], **GUARD_FLAGS}),
        ),
    )


def _decode_preview(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    result = dict(row)
    result["identity_continuity_frame"] = _loads(result.pop("identity_frame_json", "{}"), {})
    for key in ("evidence_used", "ethical_boundary_notes", "drift_flags", "source_refs"):
        result[key] = _loads(result.get(key), [])
    payload = _loads(result.get("payload_json"), {})
    for key, value in payload.items():
        result.setdefault(key, value)
    return {**result, **GUARD_FLAGS}


def _contains(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded if str(item).strip()] if isinstance(loaded, list) else []


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    try:
        loaded = json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback
    return loaded if isinstance(loaded, type(fallback)) else fallback
