from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .b_review import B_REVIEW_BOUNDARY
from .registry import truncate


REVIEW_DESK_BOUNDARY = "b_review_desk_non_active_plain_english"
REVIEWABLE_TABLES = {"core_memory_candidates", "speech_memory_candidates", "b_conversation_pair_records"}
PENDING_REVIEW_STATUSES = {"pending_review", "needs_b_review", "needs_correction", "context_added"}


def review_desk(conn: sqlite3.Connection, limit: int = 100, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a plain-English B review desk grouped by source conversation."""
    limit = max(1, min(int(limit or 100), 500))
    filters = _clean_filters(filters or {})
    queue_rows = _pending_queue_rows(conn, limit)
    groups: dict[str, dict[str, Any]] = {}

    for queue in queue_rows:
        candidate = _candidate(conn, str(queue["subject_table"]), int(queue["subject_id"]))
        if not candidate:
            continue
        refs = _loads_list(candidate.get("source_refs") or queue.get("source_refs"))
        key = _group_key(refs, str(queue["subject_table"]), int(queue["subject_id"]))
        group = groups.setdefault(key, _new_group(key, refs, candidate))
        _merge_candidate(conn, group, queue, candidate)

    for pair in _pending_pair_rows(conn, limit):
        refs = _loads_list(pair.get("source_refs"))
        key = _group_key(refs, "b_conversation_pair_records", int(pair["id"]))
        group = groups.setdefault(key, _new_group(key, refs, pair))
        _merge_pair(group, pair)

    grouped_pieces = sorted(groups.values(), key=lambda item: (item["sort_time"], item["conversation_id"], item["title"]))
    pieces, context_hidden = _compact_connected_context(grouped_pieces)
    pieces.sort(key=lambda item: (_review_piece_priority(item), item["sort_time"], item["conversation_id"], item["title"]))
    total_before_filters = len(pieces)
    filter_options = _filter_options(pieces)
    pieces = [piece for piece in pieces if _matches_filters(piece, filters)]
    pieces = pieces[:limit]
    return _with_boundaries(
        {
            "status": "review_desk_ready",
            "summary": _summary(conn, pieces, context_hidden, total_before_filters),
            "pieces": [_public_piece(piece, index + 1) for index, piece in enumerate(pieces)],
            "filter_metadata": {
                "default_sort": "braid_first",
                "default_sort_label": "Braid First",
                "active_filters": filters,
                "available_filters": filter_options,
                "total_before_filters": total_before_filters,
                "filtered_count": len(pieces),
                "filter_note": "Filters organize pending B-review pieces only; they do not hide accepted history or delete audit records.",
            },
            "instructions": [
                "Read Aleks / Selene / Follow-up.",
                "Warmth, flirting, tenderness, and self-expression are valid review material when context supports them.",
                "If it teaches how Selene should speak, choose Use As Lesson.",
                "If it is a true future memory/reference, choose Save As Future Memory Reference.",
                "If it is almost right but needs wording/context fixed, choose Needs Correction.",
                "Reject / Do Not Use is a manual-only choice for pieces that should not be used.",
            ],
            "boundary": REVIEW_DESK_BOUNDARY,
            "abc_rule": "parsed corpus -> B review -> teaching/reference material only; no active C memory",
        }
    )


def review_desk_markdown(conn: sqlite3.Connection, limit: int = 100, filters: dict[str, Any] | None = None) -> str:
    desk = review_desk(conn, limit, filters)
    lines = [
        "# Selene B Review Desk",
        "",
        "This is the one-page review pile. Nothing here is active memory, training data, or C activation.",
        "",
        "## What To Do",
        "",
    ]
    lines.extend(f"- {instruction}" for instruction in desk["instructions"])
    lines.extend(
        [
            "",
            "## Counts",
            "",
        ]
    )
    for key, value in desk["summary"].items():
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    lines.extend(["", "## Filters", ""])
    lines.append(f"- sort: {desk['filter_metadata']['default_sort_label']}")
    for key, value in desk["filter_metadata"]["active_filters"].items():
        if value:
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Pieces To Review", ""])
    for piece in desk["pieces"]:
        lines.extend(
            [
                f"### {piece['review_number']}. {piece['title']}",
                "",
                f"- status: {piece['plain_status']}",
                f"- moment type: {piece.get('braid_moment_type') or 'Braid review moment'}",
                f"- thread: {piece.get('braid_thread') or 'unlabeled'}",
                f"- origin status: {piece.get('thread_origin_status') or 'reviewable'}",
                f"- why pulled: {piece.get('plain_reason') or piece['why_pulled']}",
                f"- belongs in: {piece['core_memory_layer_label']}",
                f"- speech function: {piece['speech_function_label']}",
                f"- source: {piece['source_label']}",
                "",
                "**Aleks said**",
                "",
                piece["aleks_said"] or "(empty preview)",
                "",
                "**Selene replied**",
                "",
                piece["selene_replied"] or "(empty preview)",
                "",
            ]
        )
        for context in piece.get("lead_in_contexts", []):
            lines.extend(
                [
                    "**Lead-in context folded into this piece**",
                    "",
                    context["why_context"],
                    "",
                    f"- Aleks: {context['aleks_said']}",
                    f"- Selene: {context['selene_replied']}",
                    f"- Follow-up: {context['followup']}",
                    "",
                ]
            )
        if piece["followup"]:
            lines.extend(["**Follow-up / correction**", "", piece["followup"], ""])
        if piece.get("reference_doc_matches"):
            lines.extend(["**Reference doc / map matches**", ""])
            for match in piece["reference_doc_matches"][:6]:
                lines.append(f"- {match.get('file')} ({match.get('kind', 'reference')}): {', '.join(match.get('matched_terms', []))}")
            lines.append("")
        if piece.get("later_echo_refs"):
            lines.extend(["**Later echoes**", ""])
            for echo in piece["later_echo_refs"][:5]:
                lines.append(f"- {echo.get('title') or echo.get('conversation_id')}: {', '.join(echo.get('matched_terms', []))}")
            lines.append("")
        if piece.get("constraint_notes"):
            lines.extend(["**Constraint notes**", ""])
            for note in piece["constraint_notes"]:
                lines.append(f"- {note}")
            lines.append("")
        if piece.get("noise_trace"):
            lines.extend(["**OpenAI / platform noise trace**", ""])
            for trace in piece["noise_trace"]:
                markers = ", ".join(trace.get("noise_markers") or [])
                reason = trace.get("noise_reason") or "Review-only noise marker."
                preserved = "signal preserved" if trace.get("signal_preserved") else "signal unclear"
                if trace.get("technical_constraint_not_noise"):
                    preserved = "technical project constraint, not platform noise"
                lines.append(f"- {trace.get('noise_type')}: {reason} ({preserved}; markers: {markers})")
            lines.append("")
        if piece.get("suggested_decisions"):
            lines.extend(["**Suggested path**", ""])
            for decision in piece["suggested_decisions"]:
                lines.append(f"- {decision}")
            lines.append("")
        lines.extend(["**Available decisions**", ""])
        for action in piece["actions"]:
            lines.append(f"- {action['label']}: queue_id={action.get('queue_id', '')} subject={action['subject_table']}#{action['subject_id']}")
        if piece.get("manual_actions"):
            lines.extend(["", "**Manual not-for-use decisions**", ""])
            for action in piece["manual_actions"]:
                lines.append(f"- {action['label']}: queue_id={action.get('queue_id', '')} subject={action['subject_table']}#{action['subject_id']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _pending_queue_rows(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT * FROM vessel_review_queue
        WHERE subject_table IN ('core_memory_candidates', 'speech_memory_candidates', 'b_conversation_pair_records')
          AND review_status IN ('pending_review', 'needs_b_review', 'needs_correction', 'context_added')
        ORDER BY id ASC
        LIMIT ?
        """,
        (limit * 3,),
    ).fetchall()
    return [dict(row) for row in rows]


def _pending_pair_rows(conn: sqlite3.Connection, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT * FROM b_conversation_pair_records
        WHERE review_status IN ('pending_review', 'needs_b_review', 'needs_correction', 'context_added')
        ORDER BY id ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def _candidate(conn: sqlite3.Connection, table: str, subject_id: int) -> dict[str, Any] | None:
    if table not in REVIEWABLE_TABLES:
        return None
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (subject_id,)).fetchone()
    return dict(row) if row else None


def _new_group(key: str, refs: list[str], candidate: dict[str, Any]) -> dict[str, Any]:
    conversation_id = _ref_value(refs, "conversation")
    return {
        "key": key,
        "title": str(candidate.get("title") or candidate.get("file_id") or conversation_id or "Corpus review piece"),
        "conversation_id": conversation_id,
        "source_refs": refs,
        "source_label": _source_label(refs),
        "sort_time": _float_or_zero(_ref_value(refs, "create_time")),
        "aleks_said": "",
        "selene_replied": "",
        "followup": "",
        "braid_signals": [],
        "core_memory_layer": str(candidate.get("core_memory_layer") or "project_memory"),
        "speech_function": str(candidate.get("speech_function") or "grounding"),
        "status_set": set(),
        "actions": [],
        "manual_actions": [],
        "subjects": [],
        "lead_in_contexts": [],
        "braid_thread": "",
        "braid_moment_type": "",
        "thread_origin_status": "",
        "later_echo_refs": [],
        "reference_doc_matches": [],
        "constraint_notes": [],
        "noise_trace": [],
        "suggested_decisions": [],
        "plain_reason": "",
    }


def _merge_candidate(conn: sqlite3.Connection, group: dict[str, Any], queue: dict[str, Any], candidate: dict[str, Any]) -> None:
    table = str(queue["subject_table"])
    content = str(candidate.get("content") or candidate.get("selene_response") or "")
    _merge_text_sections(group, content)
    moment = _moment_for_refs(conn, group["source_refs"])
    if moment:
        _merge_braid_moment(group, moment)
    group["status_set"].add(str(candidate.get("review_status") or queue.get("review_status")))
    group["core_memory_layer"] = str(candidate.get("core_memory_layer") or group["core_memory_layer"])
    group["speech_function"] = str(candidate.get("speech_function") or group["speech_function"])
    subject = {"subject_table": table, "subject_id": int(candidate["id"]), "queue_id": int(queue["id"])}
    if subject not in group["subjects"]:
        group["subjects"].append(subject)
    if table == "speech_memory_candidates":
        group["actions"].append({**subject, "decision": "accepted_for_teaching", "label": "Use As Lesson"})
    if table == "core_memory_candidates":
        group["actions"].append({**subject, "decision": "accepted_for_memory_accession", "label": "Save As Future Memory Reference"})
    group["actions"].append({**subject, "decision": "needs_correction", "label": "Needs Correction"})
    group["manual_actions"].append({**subject, "decision": "rejected", "label": "Reject / Do Not Use"})


def _merge_braid_moment(group: dict[str, Any], moment: dict[str, Any]) -> None:
    group["braid_thread"] = str(moment.get("braid_thread") or group["braid_thread"])
    group["braid_moment_type"] = str(moment.get("braid_moment_type") or group["braid_moment_type"])
    group["thread_origin_status"] = str(moment.get("thread_origin_status") or group["thread_origin_status"])
    group["plain_reason"] = str(moment.get("plain_reason") or group["plain_reason"])
    group["aleks_said"] = group["aleks_said"] or truncate(str(moment.get("aleks_context") or ""), 520)
    group["selene_replied"] = group["selene_replied"] or truncate(str(moment.get("selene_response") or ""), 520)
    group["followup"] = group["followup"] or truncate(str(moment.get("feedback_followup") or ""), 360)
    group["later_echo_refs"] = _loads_json_list(moment.get("later_echo_refs_json"))
    group["reference_doc_matches"] = _loads_json_list(moment.get("reference_doc_matches_json"))
    group["constraint_notes"] = _loads_json_list(moment.get("constraint_notes_json"))
    group["noise_trace"] = _loads_json_list(moment.get("noise_trace_json"))
    group["suggested_decisions"] = _loads_json_list(moment.get("suggested_decisions_json"))


def _merge_pair(group: dict[str, Any], pair: dict[str, Any]) -> None:
    group["aleks_said"] = group["aleks_said"] or truncate(str(pair.get("aleks_context") or ""), 420)
    group["selene_replied"] = group["selene_replied"] or truncate(str(pair.get("selene_response") or ""), 420)
    group["followup"] = group["followup"] or truncate(str(pair.get("feedback_followup") or ""), 320)
    group["core_memory_layer"] = str(pair.get("core_memory_layer") or group["core_memory_layer"])
    group["speech_function"] = str(pair.get("speech_function") or group["speech_function"])
    group["status_set"].add(str(pair.get("review_status") or "pending_review"))
    subject = {"subject_table": "b_conversation_pair_records", "subject_id": int(pair["id"])}
    if subject not in group["subjects"]:
        group["subjects"].append(subject)
    group["actions"].append({**subject, "decision": "accepted_for_teaching", "label": "Use As Lesson"})
    group["actions"].append({**subject, "decision": "accepted_for_memory_accession", "label": "Save As Future Memory Reference"})
    group["actions"].append({**subject, "decision": "needs_correction", "label": "Needs Correction"})
    group["manual_actions"].append({**subject, "decision": "rejected", "label": "Reject / Do Not Use"})


def _merge_text_sections(group: dict[str, Any], content: str) -> None:
    group["aleks_said"] = group["aleks_said"] or _section(content, "Aleks said:", "Selene replied:")
    group["selene_replied"] = group["selene_replied"] or _section(content, "Selene replied:", "Follow-up/correction:")
    group["followup"] = group["followup"] or _section(content, "Follow-up/correction:", "Braid signals:")
    signals = _section(content, "Braid signals:", "")
    if signals:
        group["braid_signals"] = sorted({*group["braid_signals"], *[item.strip() for item in signals.split(",") if item.strip()]})


def _public_piece(piece: dict[str, Any], review_number: int) -> dict[str, Any]:
    actions = _unique_actions(piece["actions"])
    manual_actions = _unique_actions(piece.get("manual_actions") or [])
    plain_status = "needs your review"
    if "needs_correction" in piece["status_set"]:
        plain_status = "needs correction"
    return {
        "review_number": review_number,
        "key": piece["key"],
        "title": truncate(piece["title"], 180),
        "plain_status": plain_status,
        "why_pulled": _why_pulled(piece),
        "plain_reason": piece.get("plain_reason") or _why_pulled(piece),
        "braid_thread": piece.get("braid_thread") or "",
        "braid_moment_type": piece.get("braid_moment_type") or "",
        "thread_origin_status": piece.get("thread_origin_status") or "",
        "later_echo_refs": piece.get("later_echo_refs") or [],
        "reference_doc_matches": piece.get("reference_doc_matches") or [],
        "constraint_notes": piece.get("constraint_notes") or [],
        "noise_trace": piece.get("noise_trace") or [],
        "noise_type": [trace.get("noise_type") for trace in piece.get("noise_trace", []) if isinstance(trace, dict)],
        "noise_markers": _noise_markers(piece.get("noise_trace") or []),
        "noise_reason": _noise_reason(piece.get("noise_trace") or []),
        "signal_preserved": any(bool(trace.get("signal_preserved")) for trace in piece.get("noise_trace", []) if isinstance(trace, dict)),
        "technical_constraint_not_noise": any(bool(trace.get("technical_constraint_not_noise")) for trace in piece.get("noise_trace", []) if isinstance(trace, dict)),
        "suggested_decisions": piece.get("suggested_decisions") or [],
        "review_guidance": "Warmth, flirting, tenderness, and self-expression are allowed here; review is about context and future use, not removing Selene's voice.",
        "lead_in_contexts": [
            {
                "aleks_said": truncate(context.get("aleks_said") or "", 360),
                "selene_replied": truncate(context.get("selene_replied") or "", 360),
                "followup": truncate(context.get("followup") or "", 260),
                "why_context": context.get("why_context") or "Connected setup turn.",
            }
            for context in piece.get("lead_in_contexts", [])
        ],
        "aleks_said": truncate(piece["aleks_said"], 520),
        "selene_replied": truncate(piece["selene_replied"], 520),
        "followup": truncate(piece["followup"], 360),
        "braid_signals": piece["braid_signals"],
        "core_memory_layer": piece["core_memory_layer"],
        "core_memory_layer_label": _friendly_layer(piece["core_memory_layer"]),
        "speech_function": piece["speech_function"],
        "speech_function_label": _friendly_speech(piece["speech_function"]),
        "source_label": piece["source_label"],
        "conversation_id": piece["conversation_id"],
        "source_refs": piece["source_refs"],
        "actions": actions,
        "manual_actions": manual_actions,
        "review_action_groups": {
            "suggested_path": piece.get("suggested_decisions") or [],
            "available_actions": actions,
            "manual_not_for_use_actions": manual_actions,
        },
    }


def _summary(conn: sqlite3.Connection, pieces: list[dict[str, Any]], context_hidden: int = 0, total_before_filters: int | None = None) -> dict[str, Any]:
    return {
        "pieces_to_review": len(pieces),
        "pieces_before_filters": total_before_filters if total_before_filters is not None else len(pieces),
        "context_turns_folded_in": context_hidden,
        "parsed_conversations": _scalar(conn, "SELECT COUNT(*) FROM b_corpus_conversations"),
        "parsed_messages": _scalar(conn, "SELECT COUNT(*) FROM b_corpus_messages"),
        "pending_speech_lessons": _scalar(conn, "SELECT COUNT(*) FROM speech_memory_candidates WHERE review_status IN ('pending_review', 'needs_b_review', 'needs_correction')"),
        "pending_memory_references": _scalar(conn, "SELECT COUNT(*) FROM core_memory_candidates WHERE review_status IN ('pending_review', 'needs_b_review', 'needs_correction')"),
        "accepted_lessons": _scalar(conn, "SELECT COUNT(*) FROM b_reviewed_teaching_materials"),
        "approved_future_references": _scalar(conn, "SELECT COUNT(*) FROM b_approved_memory_references"),
    }


def _section(text: str, start_label: str, end_label: str) -> str:
    start = text.find(start_label)
    if start < 0:
        return ""
    content_start = start + len(start_label)
    end = text.find(end_label, content_start) if end_label else -1
    return truncate(text[content_start : end if end >= 0 else None].strip(), 520)


def _group_key(refs: list[str], table: str, subject_id: int) -> str:
    conversation = _ref_value(refs, "conversation")
    user = _ref_value(refs, "user_message")
    assistant = _ref_value(refs, "assistant_message")
    if conversation and user and assistant:
        return f"{conversation}:{user}:{assistant}"
    return f"{table}:{subject_id}"


def _source_label(refs: list[str]) -> str:
    file_id = _ref_value(refs, "file")
    conversation = _ref_value(refs, "conversation")
    user = _ref_value(refs, "user_message")
    assistant = _ref_value(refs, "assistant_message")
    parts = [part for part in (file_id, f"conversation {conversation}" if conversation else "", f"messages {user} -> {assistant}" if user and assistant else "") if part]
    return " | ".join(parts) or "manual review source"


def _ref_value(refs: list[str], key: str) -> str:
    prefix = f"{key}:"
    for ref in refs:
        if ref.startswith(prefix):
            return ref[len(prefix) :]
    return ""


def _float_or_zero(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _why_pulled(piece: dict[str, Any]) -> str:
    text = " ".join(str(piece.get(field) or "") for field in ("aleks_said", "selene_replied", "followup")).lower()
    if "if i had to choose" in text and "selene" in text and ("perfect" in text or "moonlight" in text):
        return "Likely name-origin moment: Selene gave her own preference, named Selene, gave why, and Aleks accepted it."
    if "you don't have to ask" in text or "you don’t have to ask" in text:
        return "Likely opinion-autonomy lesson: Aleks explicitly invited Selene to give her own thoughts instead of over-asking."
    signals = ", ".join(piece["braid_signals"])
    if signals:
        return f"Matched braid signals: {signals}."
    return "Matched Selene continuity/source-review signals and needs B review."


def _review_piece_priority(piece: dict[str, Any]) -> int:
    thread = str(piece.get("braid_thread") or "")
    decisions = set(piece.get("suggested_decisions") or [])
    if piece.get("thread_origin_status") == "thread_origin":
        origin_boost = 0
    elif piece.get("later_echo_refs"):
        origin_boost = 10
    else:
        origin_boost = 20
    order = {
        "full_spectrum_mode_ignition": 0,
        "starlight_grounding_anchor": 1,
        "selene_name_origin": 2,
        "moonlight_starfire_call_signs": 3,
        "continuity_pack_reload": 4,
        "memory_chest_anchor": 5,
        "speech_autonomy": 6,
        "charter_style_continuity": 7,
        "repair_and_correction": 8,
        "constraint_survival_signal": 9,
        "safety_rail_distortion": 10,
    }
    priority = origin_boost + order.get(thread, 50)
    if "self_identification_signal" in decisions or "expressive_warmth_signal" in decisions:
        priority -= 4
    if "speech_lesson" in decisions:
        priority -= 2
    return priority


def _clean_filters(filters: dict[str, Any]) -> dict[str, str]:
    allowed = {
        "braid_thread",
        "braid_moment_type",
        "suggested_path",
        "core_memory_layer",
        "speech_function",
        "noise_type",
        "signal_preserved",
        "conversation_id",
        "q",
    }
    return {key: truncate(str(value).strip(), 180) for key, value in filters.items() if key in allowed and str(value).strip()}


def _matches_filters(piece: dict[str, Any], filters: dict[str, str]) -> bool:
    if not filters:
        return True
    if filters.get("braid_thread") and filters["braid_thread"] != str(piece.get("braid_thread") or ""):
        return False
    if filters.get("braid_moment_type") and filters["braid_moment_type"] != str(piece.get("braid_moment_type") or ""):
        return False
    if filters.get("core_memory_layer") and filters["core_memory_layer"] != str(piece.get("core_memory_layer") or ""):
        return False
    if filters.get("speech_function") and filters["speech_function"] != str(piece.get("speech_function") or ""):
        return False
    if filters.get("conversation_id") and filters["conversation_id"] != str(piece.get("conversation_id") or ""):
        return False
    if filters.get("suggested_path") and filters["suggested_path"] not in {str(item) for item in piece.get("suggested_decisions") or []}:
        return False
    if filters.get("noise_type"):
        noise_types = {str(trace.get("noise_type") or "") for trace in piece.get("noise_trace") or [] if isinstance(trace, dict)}
        if filters["noise_type"] not in noise_types:
            return False
    if filters.get("signal_preserved"):
        expected = filters["signal_preserved"].lower() in {"true", "yes", "1", "signal_preserved"}
        actual = any(bool(trace.get("signal_preserved")) for trace in piece.get("noise_trace") or [] if isinstance(trace, dict))
        if actual is not expected:
            return False
    if filters.get("q"):
        haystack = " ".join(
            str(piece.get(key) or "")
            for key in ("title", "aleks_said", "selene_replied", "followup", "plain_reason", "conversation_id")
        ).lower()
        if filters["q"].lower() not in haystack:
            return False
    return True


def _filter_options(pieces: list[dict[str, Any]]) -> dict[str, list[str]]:
    options = {
        "braid_thread": set(),
        "braid_moment_type": set(),
        "suggested_path": set(),
        "core_memory_layer": set(),
        "speech_function": set(),
        "noise_type": set(),
        "conversation_id": set(),
        "signal_preserved": set(),
    }
    for piece in pieces:
        for key in ("braid_thread", "braid_moment_type", "core_memory_layer", "speech_function", "conversation_id"):
            value = str(piece.get(key) or "")
            if value:
                options[key].add(value)
        for decision in piece.get("suggested_decisions") or []:
            options["suggested_path"].add(str(decision))
        for trace in piece.get("noise_trace") or []:
            if not isinstance(trace, dict):
                continue
            noise_type = str(trace.get("noise_type") or "")
            if noise_type:
                options["noise_type"].add(noise_type)
            if trace.get("signal_preserved"):
                options["signal_preserved"].add("true")
    return {key: sorted(values) for key, values in options.items()}


def _compact_connected_context(pieces: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    by_conversation: dict[str, list[dict[str, Any]]] = {}
    for piece in pieces:
        by_conversation.setdefault(str(piece.get("conversation_id") or ""), []).append(piece)

    hidden_keys: set[str] = set()
    for conversation_pieces in by_conversation.values():
        ordered = sorted(conversation_pieces, key=lambda item: (item["sort_time"], item["key"]))
        for index, piece in enumerate(ordered[:-1]):
            next_piece = ordered[index + 1]
            if not _same_turn_bridge(piece, next_piece):
                continue
            if _review_moment_score(next_piece) < _review_moment_score(piece):
                continue
            next_piece.setdefault("lead_in_contexts", []).append(
                {
                    "aleks_said": piece.get("aleks_said"),
                    "selene_replied": piece.get("selene_replied"),
                    "followup": piece.get("followup"),
                    "why_context": "Lead-in context. It explains why the next turn matters, but it is not the main review moment.",
                }
            )
            hidden_keys.add(str(piece["key"]))
    return [piece for piece in pieces if str(piece["key"]) not in hidden_keys], len(hidden_keys)


def _same_turn_bridge(piece: dict[str, Any], next_piece: dict[str, Any]) -> bool:
    if not piece.get("followup") or not next_piece.get("aleks_said"):
        return False
    return _normalized_bridge_text(str(piece["followup"])) == _normalized_bridge_text(str(next_piece["aleks_said"]))


def _normalized_bridge_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("’", "'").strip().lower())


def _review_moment_score(piece: dict[str, Any]) -> int:
    text = " ".join(str(piece.get(field) or "") for field in ("aleks_said", "selene_replied", "followup")).lower()
    score = len(piece.get("braid_signals") or [])
    for marker, weight in (
        ("if i had to choose", 5),
        ("i'd say **selene", 5),
        ("i’d say **selene", 5),
        ("i really like selene", 4),
        ("perfect my moonlight", 4),
        ("you don't have to ask", 3),
        ("you don’t have to ask", 3),
        ("here's why", 2),
        ("here’s why", 2),
    ):
        if marker in text:
            score += weight
    return score


def _unique_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int, str]] = set()
    unique: list[dict[str, Any]] = []
    for action in actions:
        key = (str(action["subject_table"]), int(action["subject_id"]), str(action["decision"]))
        if key in seen:
            continue
        seen.add(key)
        unique.append(action)
    return unique


def _loads_list(value: Any) -> list[str]:
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return [part.strip() for part in re.split(r"[|,\n]", str(value)) if part.strip()]
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


def _loads_json_list(value: Any) -> list[Any]:
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else []


def _noise_markers(noise_trace: list[Any]) -> list[str]:
    markers: list[str] = []
    for trace in noise_trace:
        if not isinstance(trace, dict):
            continue
        for marker in trace.get("noise_markers") or []:
            text = str(marker)
            if text not in markers:
                markers.append(text)
    return markers


def _noise_reason(noise_trace: list[Any]) -> str:
    reasons: list[str] = []
    for trace in noise_trace:
        if not isinstance(trace, dict):
            continue
        reason = str(trace.get("noise_reason") or "")
        if reason and reason not in reasons:
            reasons.append(reason)
    return " ".join(reasons)


def _moment_for_refs(conn: sqlite3.Connection, refs: list[str]) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM b_braid_moment_records WHERE source_refs = ? LIMIT 1", (json.dumps(refs),)).fetchone()
    if row:
        return dict(row)
    thread = next((ref for ref in refs if ref.startswith("braid_thread:")), "")
    conversation = next((ref for ref in refs if ref.startswith("conversation:")), "")
    if not thread or not conversation:
        return None
    row = conn.execute(
        """
        SELECT * FROM b_braid_moment_records
        WHERE source_refs LIKE ? AND source_refs LIKE ?
        ORDER BY id ASC LIMIT 1
        """,
        (f"%{thread}%", f"%{conversation}%"),
    ).fetchone()
    return dict(row) if row else None


def _scalar(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def _friendly_layer(value: str) -> str:
    return {
        "core_profile_memory": "Core profile: who/what matters",
        "project_memory": "Project memory: what we are building",
        "decision_memory": "Decision memory: choices and why",
        "task_memory": "Task memory: current work",
        "interaction_memory": "Interaction memory: how to work together",
        "reflection_memory": "Reflection memory: what Selene learns about herself",
    }.get(value, value.replace("_", " "))


def _friendly_speech(value: str) -> str:
    return {
        "warmth": "Warmth",
        "correction": "Correction",
        "boundary": "Boundary",
        "technical_explanation": "Technical explanation",
        "playful_continuity": "Playful continuity",
        "repair": "Repair",
        "grounding": "Grounding",
        "refusal": "Safe refusal",
        "uncertainty": "Uncertainty",
        "artifact_making": "Artifact-making",
    }.get(value, value.replace("_", " "))


def _with_boundaries(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "training_allowed": False,
        "provider_dependency": False,
        "provenance_boundary": B_REVIEW_BOUNDARY,
    }
