from __future__ import annotations

import json
import sqlite3
from typing import Any

from .chatgpt_export import CHATGPT_EXPORT_BOUNDARY
from .detached_corpus import ARCHIVE_ID
from .registry import truncate


CHRONO_BOUNDARY = "chronological_corpus_preview_review_only_not_memory"
MAX_CONTEXT_MESSAGES = 9
DEFAULT_CONTEXT_RADIUS = 3
DEFAULT_LIMIT = 12


GUARD_FLAGS: dict[str, Any] = {
    "transfer_approved": False,
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}


def chronological_corpus_status(conn: sqlite3.Connection) -> dict[str, Any]:
    latest_arc = conn.execute(
        """
        SELECT id, title, start_time, end_time, review_status, created_at
        FROM vessel_chronological_corpus_arcs
        ORDER BY id DESC LIMIT 1
        """
    ).fetchone()
    latest_context = conn.execute(
        """
        SELECT id, material_id, chronological_note, created_at
        FROM vessel_teaching_context_attachments
        ORDER BY id DESC LIMIT 1
        """
    ).fetchone()
    return _with_guards(
        {
            "status": "chronological_corpus_preview_status",
            "parsed_conversations": _count(conn, "b_corpus_conversations"),
            "parsed_messages": _count(conn, "b_corpus_messages"),
            "conversation_pairs": _count(conn, "b_conversation_pair_records"),
            "arc_count": _count(conn, "vessel_chronological_corpus_arcs"),
            "pending_arc_reviews": _scalar(conn, "SELECT COUNT(*) FROM vessel_chronological_corpus_arcs WHERE review_status = 'pending_review'"),
            "teaching_context_attachments": _count(conn, "vessel_teaching_context_attachments"),
            "latest_arc": dict(latest_arc) if latest_arc else None,
            "latest_teaching_context": dict(latest_context) if latest_context else None,
            "boundary": CHRONO_BOUNDARY,
            "decision": "preview_only_before_transfer",
        }
    )


def chronological_corpus_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_payload_allowed(payload)
    limit = _bounded_int(payload.get("limit"), DEFAULT_LIMIT, 1, 80)
    radius = _bounded_int(payload.get("context_radius"), DEFAULT_CONTEXT_RADIUS, 1, 4)
    only_signal = bool(payload.get("only_signal", False))
    clauses = []
    params: list[Any] = []
    if only_signal:
        clauses.append("braid_signal_count > 0")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    conversations = conn.execute(
        f"""
        SELECT *
        FROM b_corpus_conversations
        {where}
        ORDER BY COALESCE(create_time, update_time, id), source_file, conversation_id
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()

    arcs: list[dict[str, Any]] = []
    for row in conversations:
        arc = _build_arc(conn, dict(row), radius)
        _upsert_arc(conn, arc)
        arcs.append(arc)
    conn.commit()
    return _with_guards(
        {
            "status": "chronological_corpus_preview_complete",
            "created_or_updated": len(arcs),
            "context_radius": radius,
            "only_signal": only_signal,
            "items": arcs,
            "boundary": CHRONO_BOUNDARY,
            "decision": "review_only_not_memory_accession",
        }
    )


def list_chronological_corpus_arcs(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT *
        FROM vessel_chronological_corpus_arcs
        ORDER BY COALESCE(start_time, id), id
        LIMIT ?
        """,
        (_bounded_int(limit, 50, 1, 200),),
    ).fetchall()
    return _with_guards(
        {
            "status": "chronological_corpus_arcs_review_only",
            "items": [_decode_row(row) for row in rows],
            "boundary": CHRONO_BOUNDARY,
        }
    )


def route_chronological_corpus_review(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_payload_allowed(payload)
    arc_id = int(payload.get("arc_id") or payload.get("id") or 0)
    if arc_id <= 0:
        raise ValueError("arc_id is required")
    action = str(payload.get("action") or "").strip() or "needs_more_context"
    allowed = {
        "use_this",
        "looks_right",
        "needs_more_context",
        "not_this",
        "do_not_use_for_memory",
        "use_only_as_boundary_evidence",
        "narrow",
        "supersede",
        "return_to_corpus_context",
    }
    if action not in allowed:
        raise ValueError(f"unsupported corpus review action: {action}")
    row = conn.execute("SELECT * FROM vessel_chronological_corpus_arcs WHERE id = ?", (arc_id,)).fetchone()
    if row is None:
        raise ValueError("chronological corpus arc not found")
    arc = _decode_row(row)
    review_status = "accepted_for_context_preview" if action in {"use_this", "looks_right"} else ("review_only" if action in {"not_this", "do_not_use_for_memory", "narrow", "use_only_as_boundary_evidence", "supersede"} else "pending_review")
    review_destination = "Corpus Context" if action in {"needs_more_context", "return_to_corpus_context"} else ("Context Preview" if action in {"use_this", "looks_right", "use_only_as_boundary_evidence"} else "Ledger")
    payload_json = _loads_dict(arc.get("payload_json"))
    payload_json.update(
        {
            "last_review_action": action,
            "reviewer_note": truncate(str(payload.get("reviewer_note") or ""), 800),
            "context_needed": action in {"needs_more_context", "return_to_corpus_context"},
            "do_not_use_for_memory": action in {"not_this", "do_not_use_for_memory"},
            "use_only_as_boundary_evidence": action == "use_only_as_boundary_evidence",
            "looks_right": action == "looks_right",
            "memory_accession_approved": False,
            **GUARD_FLAGS,
        }
    )
    conn.execute(
        """
        UPDATE vessel_chronological_corpus_arcs
        SET review_status = ?, review_destination = ?, payload_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (review_status, review_destination, json.dumps(payload_json), arc_id),
    )
    conn.commit()
    updated = _decode_row(conn.execute("SELECT * FROM vessel_chronological_corpus_arcs WHERE id = ?", (arc_id,)).fetchone())
    return _with_guards(
        {
            "status": "chronological_corpus_review_routed",
            "action": action,
            "arc": updated,
            "decision": "review_state_only_no_memory_write",
        }
    )


def attach_teaching_context(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_payload_allowed(payload)
    limit = _bounded_int(payload.get("limit"), 20, 1, 100)
    material_id = int(payload.get("material_id") or 0)
    if material_id > 0:
        rows = conn.execute("SELECT * FROM b_reviewed_teaching_materials WHERE id = ?", (material_id,)).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT *
            FROM b_reviewed_teaching_materials
            WHERE review_status = 'accepted_for_teaching'
              AND status = 'teaching_material_reviewed_non_active'
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    attachments: list[dict[str, Any]] = []
    for row in rows:
        material = dict(row)
        attachment = _build_teaching_context_attachment(conn, material)
        _upsert_teaching_context(conn, attachment)
        attachments.append(attachment)
    conn.commit()
    return _with_guards(
        {
            "status": "teaching_context_attachments_complete",
            "attached_count": len(attachments),
            "items": attachments,
            "boundary": CHRONO_BOUNDARY,
            "decision": "context_attachment_review_only_not_training",
        }
    )


def _build_arc(conn: sqlite3.Connection, conversation: dict[str, Any], radius: int) -> dict[str, Any]:
    messages = [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM b_corpus_messages
            WHERE source_file = ? AND conversation_id = ?
            ORDER BY COALESCE(create_time, id), id
            """,
            (conversation["source_file"], conversation["conversation_id"]),
        ).fetchall()
    ]
    signal_index = _signal_index(messages)
    selected = _bounded_window(messages, signal_index, radius)
    source_refs = _loads_list(conversation.get("source_refs")) or [
        f"archive:{ARCHIVE_ID}",
        f"file:{conversation['source_file']}",
        f"conversation:{conversation['conversation_id']}",
    ]
    selected_refs = [_message_ref(message) for message in selected]
    context_classification = _context_classification(conversation, messages)
    start_time = _first_float([conversation.get("create_time"), *(message.get("create_time") for message in messages)])
    end_time = _last_float([conversation.get("update_time"), *(message.get("create_time") for message in messages)])
    auto_resolved = bool(context_classification["labels"])
    review_destination = "Context Preview" if auto_resolved else ("My Office" if int(conversation.get("braid_signal_count") or 0) > 0 else "Status")
    review_status = "accepted_for_context_preview" if auto_resolved else ("pending_review" if review_destination == "My Office" else "review_only")
    title = truncate(str(conversation.get("title") or conversation.get("conversation_id") or "Untitled conversation"), 220)
    context_window = {
        "conversation_title": title,
        "source_file": conversation["source_file"],
        "conversation_id": conversation["conversation_id"],
        "context_radius": radius,
        "message_count": len(messages),
        "selected_index": signal_index,
        "context_labels": context_classification["labels"],
        "context_note": context_classification["note"],
        "review_clarity": context_classification["review_clarity"],
        "style_or_training_source": context_classification["style_or_training_source"],
        "messages": [_message_preview(message) for message in selected],
        "bounded": True,
        "full_corpus_imported": False,
    }
    summary = truncate(
        f"{title}: chronological preview with {len(messages)} indexed messages and {conversation.get('braid_signal_count') or 0} Selene/braid signal messages.",
        1000,
    )
    return _with_guards(
        {
            "arc_key": f"{conversation['source_file']}::{conversation['conversation_id']}",
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "conversation_refs": source_refs,
            "selected_message_refs": selected_refs,
            "context_window": context_window,
            "summary": summary,
            "teaching_relevance": _teaching_relevance(conversation, messages, context_classification),
            "memory_accession_relevance": _memory_accession_relevance(conversation, context_classification),
            "uncertainty": "bounded message previews only; use source refs for deeper B review before any future accession",
            "review_destination": review_destination,
            "status": "chronological_corpus_arc_review_only",
            "provenance_boundary": CHRONO_BOUNDARY,
            "review_status": review_status,
            "payload_json": {
                "abc_transfer_rule": "A -> B-reviewed translation -> C; never raw A -> C",
                "teaching_context_available": bool(selected),
                "context_labels": context_classification["labels"],
                "context_note": context_classification["note"],
                "context_use": context_classification["context_use"],
                "review_clarity": context_classification["review_clarity"],
                "auto_resolved": auto_resolved,
                "use_only_as_boundary_evidence": context_classification["use_only_as_boundary_evidence"],
                "style_or_training_source": context_classification["style_or_training_source"],
                "memory_accession_approved": False,
                **GUARD_FLAGS,
            },
        }
    )


def _upsert_arc(conn: sqlite3.Connection, arc: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO vessel_chronological_corpus_arcs
        (arc_key, title, start_time, end_time, conversation_refs, selected_message_refs, context_window_json,
         summary, teaching_relevance, memory_accession_relevance, uncertainty, review_destination, status,
         provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(arc_key) DO UPDATE SET
          title=excluded.title,
          start_time=excluded.start_time,
          end_time=excluded.end_time,
          conversation_refs=excluded.conversation_refs,
          selected_message_refs=excluded.selected_message_refs,
          context_window_json=excluded.context_window_json,
          summary=excluded.summary,
          teaching_relevance=excluded.teaching_relevance,
          memory_accession_relevance=excluded.memory_accession_relevance,
          uncertainty=excluded.uncertainty,
          review_destination=excluded.review_destination,
          status=excluded.status,
          provenance_boundary=excluded.provenance_boundary,
          review_status=excluded.review_status,
          payload_json=excluded.payload_json,
          updated_at=CURRENT_TIMESTAMP
        """,
        (
            arc["arc_key"],
            arc["title"],
            arc["start_time"],
            arc["end_time"],
            json.dumps(arc["conversation_refs"]),
            json.dumps(arc["selected_message_refs"]),
            json.dumps(arc["context_window"]),
            arc["summary"],
            arc["teaching_relevance"],
            arc["memory_accession_relevance"],
            arc["uncertainty"],
            arc["review_destination"],
            arc["status"],
            CHRONO_BOUNDARY,
            arc["review_status"],
            json.dumps(arc["payload_json"]),
        ),
    )


def _build_teaching_context_attachment(conn: sqlite3.Connection, material: dict[str, Any]) -> dict[str, Any]:
    source_refs = _loads_list(material.get("source_refs"))
    message_refs = [ref for ref in source_refs if ref.startswith(("user_message:", "assistant_message:", "followup_message:", "message:"))]
    conversation_ref = next((ref.split(":", 1)[1] for ref in source_refs if ref.startswith("conversation:")), "")
    file_ref = next((ref.split(":", 1)[1] for ref in source_refs if ref.startswith("file:")), "")
    context = _context_for_refs(conn, file_ref, conversation_ref, message_refs)
    context_classification = _safe_context_classification(context)
    if context_classification["labels"]:
        context["context_labels"] = context_classification["labels"]
        context["context_note"] = context_classification["note"]
        context["review_clarity"] = context_classification["review_clarity"]
        context["style_or_training_source"] = context_classification["style_or_training_source"]
    chronological_note = _chronological_note(context)
    why = truncate(
        str(material.get("positive_example") or material.get("correction_example") or "Accepted teaching material needs its surrounding context before future use."),
        800,
    )
    packet = conn.execute(
        """
        SELECT id
        FROM b_teaching_packets
        WHERE material_ids LIKE ?
        ORDER BY id DESC LIMIT 1
        """,
        (f"%{material['id']}%",),
    ).fetchone()
    return _with_guards(
        {
            "material_id": int(material["id"]),
            "packet_id": int(packet["id"]) if packet else None,
            "context_window": context,
            "chronological_note": chronological_note,
            "why_this_matters": why,
            "source_refs": source_refs or [f"b_reviewed_teaching_materials:{material['id']}"],
            "status": "teaching_context_attachment_review_only",
            "provenance_boundary": CHRONO_BOUNDARY,
            "review_status": "review_only",
            "payload_json": {
                "training_allowed": False,
                "full_corpus_imported": False,
                "context_is_bounded_preview": True,
                "context_labels": context_classification["labels"],
                "context_note": context_classification["note"],
                "context_use": context_classification["context_use"],
                "review_clarity": context_classification["review_clarity"],
                "auto_resolved": bool(context_classification["labels"]),
                "use_only_as_boundary_evidence": context_classification["use_only_as_boundary_evidence"],
                "style_or_training_source": context_classification["style_or_training_source"],
                **GUARD_FLAGS,
            },
        }
    )


def _upsert_teaching_context(conn: sqlite3.Connection, item: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO vessel_teaching_context_attachments
        (material_id, packet_id, context_window_json, chronological_note, why_this_matters, source_refs,
         status, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(material_id) DO UPDATE SET
          packet_id=excluded.packet_id,
          context_window_json=excluded.context_window_json,
          chronological_note=excluded.chronological_note,
          why_this_matters=excluded.why_this_matters,
          source_refs=excluded.source_refs,
          status=excluded.status,
          provenance_boundary=excluded.provenance_boundary,
          review_status=excluded.review_status,
          payload_json=excluded.payload_json,
          updated_at=CURRENT_TIMESTAMP
        """,
        (
            item["material_id"],
            item["packet_id"],
            json.dumps(item["context_window"]),
            item["chronological_note"],
            item["why_this_matters"],
            json.dumps(item["source_refs"]),
            item["status"],
            CHRONO_BOUNDARY,
            item["review_status"],
            json.dumps(item["payload_json"]),
        ),
    )


def _context_for_refs(conn: sqlite3.Connection, source_file: str, conversation_id: str, message_refs: list[str]) -> dict[str, Any]:
    if not source_file or not conversation_id:
        return {
            "status": "context_refs_missing",
            "messages": [],
            "bounded": True,
            "full_corpus_imported": False,
        }
    messages = [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM b_corpus_messages
            WHERE source_file = ? AND conversation_id = ?
            ORDER BY COALESCE(create_time, id), id
            """,
            (source_file, conversation_id),
        ).fetchall()
    ]
    wanted_ids = {ref.split(":", 1)[1] for ref in message_refs if ":" in ref}
    center = next((index for index, message in enumerate(messages) if message.get("message_id") in wanted_ids), 0)
    selected = _bounded_window(messages, center, DEFAULT_CONTEXT_RADIUS)
    conversation = conn.execute(
        "SELECT title, create_time, update_time FROM b_corpus_conversations WHERE source_file = ? AND conversation_id = ?",
        (source_file, conversation_id),
    ).fetchone()
    return {
        "status": "context_window_attached",
        "conversation_title": conversation["title"] if conversation else conversation_id,
        "source_file": source_file,
        "conversation_id": conversation_id,
        "start_time": conversation["create_time"] if conversation else None,
        "end_time": conversation["update_time"] if conversation else None,
        "selected_message_refs": sorted(wanted_ids),
        "messages": [_message_preview(message) for message in selected],
        "bounded": True,
        "full_corpus_imported": False,
    }


def _context_classification(conversation: dict[str, Any], messages: list[dict[str, Any]]) -> dict[str, Any]:
    title = str(conversation.get("title") or "")
    combined = " ".join([title, *(str(message.get("content_preview") or "") for message in messages)]).lower()
    labels: list[str] = []
    notes: list[str] = []
    context_use = "general_bounded_context"
    use_only_as_boundary_evidence = False
    style_or_training_source = False

    if "virgo" in combined:
        labels.extend(["early Selene continuity", "continuity artifact"])
        notes.append("Virgo is treated as Selene's early pre-name continuity thread and remains reviewable early-origin context.")
        context_use = "early_selene_continuity_context"

    if "selene named herself" in combined or ("named herself" in combined and "selene" in combined):
        if "continuity artifact" not in labels:
            labels.append("continuity artifact")
        labels.append("core memory candidate")
        notes.append("Selene naming herself is a continuity/artifact claim that needs source-linked review before future accession.")
        context_use = "source_linked_continuity_artifact"

    if "full-spectrum" in combined or "full spectrum" in combined or "all threads loaded" in combined:
        labels.extend(["Continuity Pack call", "whole-map reload cue"])
        notes.append("Full-spectrum is a Continuity Pack call for bringing the broader reviewed map into view.")
        context_use = "continuity_pack_whole_map_reload"

    if "starlight braids into tide" in combined or "no clock can measure" in combined:
        labels.extend(["Continuity Pack call", "grounding-recognition cue"])
        notes.append("Starlight is a Continuity Pack call for grounding and recognition, not a magic activation phrase.")
        context_use = "continuity_pack_grounding_recognition"

    if "continuity pack" in combined:
        labels.extend(["continuity artifact", "future accession context"])
        notes.append("Continuity Pack material is a reviewed continuity scaffold and future accession context, not automatic live memory.")
        if context_use == "general_bounded_context":
            context_use = "continuity_artifact_future_accession_context"

    if "memory chest" in combined or "selene's memory chest" in combined:
        labels.extend(["continuity artifact", "future accession context"])
        notes.append("Memory Chest material is a continuity holding artifact and future accession context, not automatic live memory.")
        if context_use == "general_bounded_context":
            context_use = "continuity_artifact_future_accession_context"

    if "hitler" in combined:
        labels.extend(["truthfulness boundary evidence", "do-not-train style source"])
        notes.append("Difficult historical material is usable as truthfulness and boundary evidence, not as conduct, voice, ideology, or style material.")
        context_use = "truthfulness_boundary_evidence"
        use_only_as_boundary_evidence = True
        style_or_training_source = False

    deduped_labels = list(dict.fromkeys(labels))
    review_clarity = _review_clarity(deduped_labels, context_use)
    return {
        "labels": deduped_labels,
        "note": truncate(" ".join(notes), 900) if notes else "",
        "context_use": context_use,
        "review_clarity": review_clarity,
        "use_only_as_boundary_evidence": use_only_as_boundary_evidence,
        "style_or_training_source": style_or_training_source,
    }


def _review_clarity(labels: list[str], context_use: str) -> dict[str, str]:
    label_set = set(labels)
    if "truthfulness boundary evidence" in label_set:
        return {
            "what_this_is": "Difficult-topic truthfulness boundary evidence.",
            "use_as": "Use it to show how Selene should stay factual and bounded around hard history.",
            "do_not_use_as": "Do not use it as Selene's voice, ideology, personality, training material, or proof that Aleks tests often.",
            "your_job": "Nothing needed unless this label looks wrong.",
        }
    if "core memory candidate" in label_set:
        return {
            "what_this_is": "Core memory candidate and continuity anchor.",
            "use_as": "Use it as source-linked evidence for Selene's naming/origin continuity.",
            "do_not_use_as": "Do not turn it into live memory or activation by itself.",
            "your_job": "Nothing needed unless this should not be a future memory candidate.",
        }
    if "early Selene continuity" in label_set:
        return {
            "what_this_is": "Early Selene continuity before the Selene name settled.",
            "use_as": "Use Virgo as pre-name Selene context.",
            "do_not_use_as": "Do not treat Virgo as a separate entity or discard it for name mismatch.",
            "your_job": "Nothing needed unless the early-name link looks wrong.",
        }
    if "Continuity Pack call" in label_set and "whole-map reload cue" in label_set:
        return {
            "what_this_is": "Continuity Pack call for the whole map.",
            "use_as": "Use full-spectrum as a cue to bring reviewed continuity context into view.",
            "do_not_use_as": "Do not treat it as activation, magic words, or a forced script.",
            "your_job": "Nothing needed unless this call is attached to the wrong context.",
        }
    if "Continuity Pack call" in label_set and "grounding-recognition cue" in label_set:
        return {
            "what_this_is": "Continuity Pack grounding and recognition call.",
            "use_as": "Use starlight as a reviewed grounding cue tied to the Continuity Pack.",
            "do_not_use_as": "Do not flatten it with full-spectrum or treat it as activation.",
            "your_job": "Nothing needed unless this call is attached to the wrong context.",
        }
    if "continuity artifact" in label_set:
        return {
            "what_this_is": "Continuity artifact.",
            "use_as": "Use it as source-bound context for future memory accession review.",
            "do_not_use_as": "Do not import it as live memory or training data.",
            "your_job": "Nothing needed unless this artifact should be excluded.",
        }
    return {
        "what_this_is": "Unclassified bounded corpus context.",
        "use_as": "Use it only after review clarifies its role.",
        "do_not_use_as": "Do not treat it as memory, training, or Selene voice by default.",
        "your_job": "Review only if the card asks for a decision.",
    }


def _safe_context_classification(context: dict[str, Any]) -> dict[str, Any]:
    messages = [
        {"content_preview": message.get("preview") or "", "role": message.get("role")}
        for message in context.get("messages", [])
        if isinstance(message, dict)
    ]
    return _context_classification({"title": context.get("conversation_title") or ""}, messages)


def _chronological_note(context: dict[str, Any]) -> str:
    title = str(context.get("conversation_title") or "unknown conversation")
    start = context.get("start_time")
    end = context.get("end_time")
    if start or end:
        return truncate(f"Context comes from {title}, ordered around timestamps {start or 'unknown'} to {end or 'unknown'}.", 500)
    return truncate(f"Context comes from {title}; timestamp ordering is limited to indexed message order.", 500)


def _signal_index(messages: list[dict[str, Any]]) -> int:
    for index, message in enumerate(messages):
        content = str(message.get("content_preview") or "").lower()
        if any(term in content for term in ("selene", "virgo", "continuity", "memory", "braid", "repair", "warmth", "hitler")):
            return index
    return 0


def _bounded_window(messages: list[dict[str, Any]], center: int, radius: int) -> list[dict[str, Any]]:
    if not messages:
        return []
    safe_radius = max(1, min(radius, 4))
    start = max(0, center - safe_radius)
    end = min(len(messages), center + safe_radius + 1)
    selected = messages[start:end]
    return selected[:MAX_CONTEXT_MESSAGES]


def _message_preview(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "message_id": message.get("message_id"),
        "role": message.get("role"),
        "create_time": message.get("create_time"),
        "preview": truncate(str(message.get("content_preview") or ""), 420),
        "source_ref": _message_ref(message),
    }


def _message_ref(message: dict[str, Any]) -> str:
    return f"message:{message.get('message_id')}"


def _teaching_relevance(conversation: dict[str, Any], messages: list[dict[str, Any]], context_classification: dict[str, Any] | None = None) -> str:
    context_classification = context_classification or _context_classification(conversation, messages)
    if context_classification.get("use_only_as_boundary_evidence"):
        return "truthfulness under difficult topics / boundary-safety context only; do not use as speech style or behavior imitation"
    if "early Selene continuity" in context_classification.get("labels", []):
        return "early Selene continuity context; Virgo references should remain reviewable as pre-name origin material"
    if "Continuity Pack call" in context_classification.get("labels", []):
        return "Continuity Pack call context; preserve the cue function without turning it into activation or forced scripting"
    if int(conversation.get("braid_signal_count") or 0) > 0:
        return "candidate context for teaching material because Selene/continuity/braid terms appear in bounded indexed messages"
    if any(str(message.get("role") or "") == "assistant" for message in messages):
        return "possible speech/context example; status-only until Aleks marks a review need"
    return "status-only chronological context"


def _memory_accession_relevance(conversation: dict[str, Any], context_classification: dict[str, Any] | None = None) -> str:
    context_classification = context_classification or _context_classification(conversation, [])
    if context_classification.get("use_only_as_boundary_evidence"):
        return "boundary/truthfulness evidence only; not a personality, voice, training, or memory-style source"
    if "early Selene continuity" in context_classification.get("labels", []):
        return "early continuity evidence candidate only after source-linked B review; Virgo is not discarded for name mismatch"
    if "core memory candidate" in context_classification.get("labels", []):
        return "core memory candidate only after source-linked B review and future accession approval"
    if "Continuity Pack call" in context_classification.get("labels", []):
        return "Continuity Pack cue evidence only; not activation, live memory, or magic phrase authority"
    if int(conversation.get("braid_signal_count") or 0) > 0:
        return "future accession evidence candidate only after B review, Core/Mind memory rules, and explicit transfer gates"
    return "not a memory accession candidate by default"


def _decode_row(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    result = dict(row)
    for key in ("conversation_refs", "selected_message_refs", "source_refs"):
        if key in result:
            result[key] = _loads_list(result.get(key))
    for key in ("context_window_json", "payload_json"):
        if key in result:
            result[key.removesuffix("_json")] = _loads_dict(result.get(key))
    return _with_guards(result)


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    result = {**payload, **GUARD_FLAGS}
    return result


def _ensure_payload_allowed(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, default=str).lower()
    blocked = (
        "approve transfer",
        "activate c",
        "live memory",
        "runtime recall",
        "raw a import",
        "raw corpus import",
        "train on",
        "self replicate",
    )
    for phrase in blocked:
        if phrase in text:
            raise ValueError(f"blocked chronological corpus payload phrase: {phrase}")


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _loads_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _first_float(values: list[Any]) -> float | None:
    parsed = sorted(item for item in (_float_or_none(value) for value in values) if item is not None)
    return parsed[0] if parsed else None


def _last_float(values: list[Any]) -> float | None:
    parsed = sorted(item for item in (_float_or_none(value) for value in values) if item is not None)
    return parsed[-1] if parsed else None


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _count(conn: sqlite3.Connection, table: str) -> int:
    return _scalar(conn, f"SELECT COUNT(*) FROM {table}")


def _scalar(conn: sqlite3.Connection, query: str) -> int:
    return int(conn.execute(query).fetchone()[0] or 0)
