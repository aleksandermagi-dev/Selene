from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


THREAD_LOOM_BOUNDARY = (
    "current_session_discourse_thread_coordination_only_no_durable_memory_identity_personality_"
    "governance_training_authority_or_autonomous_action"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "durable_memory_write": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
}

_RETURN_RE = re.compile(
    r"\b(?:back|return|going back)\s+to\s+(.+?)"
    r"(?=\s+(?:because of|using|use|with that|in light of|which (?:changes|affects|means))\b|[:;,!?]|\.|$)|"
    r"\b(?:the point about|what you said about|we discussed)\s+(.+?)"
    r"(?=\s+(?:because|and|which|that)\b|[:;,!?]|\.|$)",
    re.IGNORECASE,
)
_BRANCH_RE = re.compile(
    r"\b(?:move|jump|turn|switch)\s+to\s+(.+?)(?=[:;,!?]|\.|$)|"
    r"\b(?:separately|as an aside|on another point|another thing)\s*[:,]?\s*(.+?)(?=[:;,!?]|\.|$)|"
    r"\b(?:separate|different|new)\s+(?:topic|question)\s*[:,]?\s*(.+?)(?=[:;,!?]|\.|$)|"
    r"\bon another topic\s*[:,]?\s*(.+?)(?=[:;,!?]|\.|$)",
    re.IGNORECASE,
)
_LAND_RE = re.compile(
    r"\b(?:finally|lastly)\s*[:,]?\s*(.+?)(?=[:;,!?]|\.|$)|"
    r"\b(?:finish|end|close)\s+(?:with|on)\s+(.+?)(?=[:;,!?]|\.|$)",
    re.IGNORECASE,
)
_DEPENDENCY_CUES = (
    "because of that",
    "using that",
    "use that",
    "with that",
    "from that",
    "in light of that",
    "which changes",
    "which affects",
    "which means",
    "based on that",
    "now that",
)
_TOPIC_STOP = {
    "about", "after", "again", "also", "and", "another", "back", "because", "before", "being",
    "can", "close", "does", "end", "finally", "finish", "first", "for", "from", "going", "have",
    "into", "jump", "lastly", "move", "next", "now", "on", "out", "return", "separately",
    "start", "switch", "that", "the", "then", "this", "to", "turn", "using", "what", "which", "with",
    "work", "would", "you", "your",
}


def build_thread_braid(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a visible session-only map of topic branches, returns, and dependencies.

    This is discourse coordination, not hidden reasoning. It records only the
    relationships that are visible in the user's wording or supplied semantic
    hints, and leaves ambiguous returns unresolved.
    """
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400).strip()
    session_id = int(payload.get("session_id") or 0)
    prior = payload.get("prior_braid") if isinstance(payload.get("prior_braid"), dict) else {}
    hints = [item for item in payload.get("thread_hints") or [] if isinstance(item, dict)][:16]
    units = [item for item in payload.get("utterance_units") or [] if isinstance(item, dict)]
    segments = _segments(prompt, units, hints)

    prior_thread_values = [
        *[item for item in prior.get("thread_index") or [] if isinstance(item, dict)],
        *[item for item in prior.get("threads") or [] if isinstance(item, dict)],
    ]
    threads = _merge_threads(prior_thread_values)[-64:]
    edges = [_normalize_edge(item) for item in prior.get("edges") or [] if isinstance(item, dict)][-96:]
    traversal: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    active_id = str(prior.get("active_thread_id") or "")
    protected_thread_ids = {
        str(item)
        for item in payload.get("protected_thread_ids") or []
        if str(item)
    }
    if not active_id and threads:
        active_id = str(next((item["id"] for item in reversed(threads) if item["state"] == "active"), threads[-1]["id"]))
    prior_active_id = active_id
    last_branch_id = ""

    for index, segment in enumerate(segments):
        text = str(segment.get("text") or "")
        hinted_action = str(segment.get("action") or "")
        action, target = _segment_action(text, hinted_action, str(segment.get("topic") or ""))
        source_span = str(segment.get("source_span") or f"segment_{index + 1}")

        if action == "resume":
            target_thread, ambiguous = _resolve_thread(target, threads, exclude_id="")
            if ambiguous or target_thread is None:
                unresolved.append(
                    {
                        "source_span": source_span,
                        "requested_topic": target,
                        "reason": "return_target_is_ambiguous_or_missing",
                        "ask_only_if_material": True,
                    }
                )
                traversal.append(
                    {
                        "index": len(traversal) + 1,
                        "thread_id": "",
                        "action": "hold_unresolved_return",
                        "source_span": source_span,
                        "text": text,
                    }
                )
                continue
            previous_id = active_id
            active_id = str(target_thread["id"])
            _set_thread_state(threads, active_id, "resumed")
            if previous_id and previous_id != active_id:
                _set_thread_state(threads, previous_id, "paused")
                _add_edge(edges, previous_id, active_id, "returns_to", source_span)
            dependency_id = _dependency_source(text, threads, active_id, previous_id or last_branch_id)
            return_action = "revise_with_dependency" if dependency_id else "continue"
            if dependency_id:
                _add_edge(edges, dependency_id, active_id, "updates", source_span)
                _add_edge(edges, active_id, dependency_id, "depends_on", source_span)
            traversal.append(_visit(traversal, active_id, return_action, source_span, text, dependency_id))
            continue

        if action in {"branch", "land"}:
            topic = target or _topic(text)
            target_thread, ambiguous = _resolve_thread(topic, threads, exclude_id="")
            if target_thread is None or ambiguous:
                target_thread = _new_thread(session_id, topic or text, source_span, "active")
                threads.append(target_thread)
            new_id = str(target_thread["id"])
            previous_id = active_id
            if previous_id and previous_id != new_id:
                _set_thread_state(threads, previous_id, "paused" if action == "branch" else "completed")
                _add_edge(edges, new_id, previous_id, "branches_from" if action == "branch" else "follows", source_span)
            active_id = new_id
            _set_thread_state(threads, active_id, "active")
            if action == "branch":
                last_branch_id = active_id
            traversal.append(_visit(traversal, active_id, "branch" if action == "branch" else "land", source_span, text))
            continue

        # A plain segment continues the active thread. If none exists, it starts
        # one from the visible segment rather than inventing a latent topic.
        if not active_id:
            topic = str(segment.get("topic") or "") or _topic(text) or str(payload.get("active_topic") or "")
            thread = _new_thread(session_id, topic or text, source_span, "active")
            threads.append(thread)
            active_id = str(thread["id"])
            visit_action = "start"
        else:
            _set_thread_state(threads, active_id, "active")
            visit_action = "continue"
        traversal.append(_visit(traversal, active_id, visit_action, source_span, text))

    for thread in threads:
        if thread["id"] == active_id:
            thread["state"] = "active"
        elif thread["state"] in {"active", "resumed"}:
            thread["state"] = "paused"

    braided = len({item.get("thread_id") for item in traversal if item.get("thread_id")}) > 1 or any(
        str(item.get("relation") or "") in {"returns_to", "depends_on", "updates"} for item in edges
    )
    thread_index = _retain_thread_index(
        threads,
        active_id=active_id,
        protected_thread_ids=protected_thread_ids,
        edges=edges,
        limit=64,
    )
    working_threads = _retain_thread_index(
        thread_index,
        active_id=active_id,
        protected_thread_ids=protected_thread_ids,
        edges=edges,
        limit=16,
    )
    retained_ids = {str(item.get("id") or "") for item in thread_index}
    retained_edges = [
        edge
        for edge in _dedupe_edges(edges)
        if str(edge.get("source_thread_id") or "") in retained_ids
        and str(edge.get("target_thread_id") or "") in retained_ids
    ][-64:]
    return _with_guards(
        {
            "status": "conversation_thread_braid_ready",
            "version": "v1_session_braided_discourse",
            "session_id": session_id,
            "threads": working_threads,
            "thread_index": thread_index,
            "thread_index_count": len(thread_index),
            "working_thread_limit": 16,
            "thread_index_limit": 64,
            "protected_thread_ids": sorted(protected_thread_ids),
            "edges": retained_edges,
            "turn_traversal": traversal,
            "active_thread_id": active_id,
            "prior_active_thread_id": prior_active_id,
            "unresolved_returns": unresolved,
            "braided": braided,
            "single_message_supported": True,
            "multi_turn_supported": True,
            "saturation_compaction": {
                "active": len(threads) > len(working_threads),
                "candidate_thread_count": len(threads),
                "working_thread_count": len(working_threads),
                "indexed_thread_count": len(thread_index),
                "discarded_thread_count": max(0, len(threads) - len(thread_index)),
                "active_thread_preserved": any(
                    str(item.get("id") or "") == active_id
                    for item in working_threads
                ) if active_id else True,
                "protected_threads_preserved": protected_thread_ids.issubset(retained_ids),
                "raw_turn_text_archived": False,
            },
            "ambiguous_relationships_are_not_invented": True,
            "session_scoped_only": True,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": THREAD_LOOM_BOUNDARY,
        }
    )


def _segments(prompt: str, units: list[dict[str, Any]], hints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if hints:
        return [
            {
                "text": truncate(str(item.get("text") or ""), 600),
                "action": str(item.get("action") or ""),
                "topic": truncate(str(item.get("topic") or ""), 240),
                "source_span": str(item.get("source_span") or f"hint_{index + 1}"),
            }
            for index, item in enumerate(hints)
            if str(item.get("text") or item.get("topic") or "").strip()
        ]
    raw_units = [str(item.get("text") or "").strip() for item in units if str(item.get("text") or "").strip()]
    if not raw_units:
        raw_units = [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+|;\s+", prompt) if item.strip()]
    segments: list[dict[str, Any]] = []
    for raw in raw_units[:16]:
        # Explicit branch/return/landing markers inside one long sentence create
        # separate visits; ordinary conjunctions do not.
        parts = re.split(
            r"(?=\b(?:then\s+)?(?:move|jump|turn|switch)\s+to\b|"
            r"\b(?:then\s+)?(?:back\s+to|return\s+to|going\s+back\s+to|finally\b|lastly\b|finish\s+(?:with|on))|"
            r"\b(?:separate|different|new)\s+(?:topic|question)\b|"
            r"\bon another topic\b|\b(?:the point about|what you said about|we discussed)\b)",
            raw,
            flags=re.IGNORECASE,
        )
        for part in parts:
            text = truncate(part.strip(" ,"), 600)
            if text:
                segments.append({"text": text, "source_span": f"segment_{len(segments) + 1}"})
    compact: list[dict[str, Any]] = []
    for segment in segments:
        marker = str(segment.get("text") or "").lower().strip(" ,:")
        if compact and marker in {"then", "next"}:
            compact[-1]["text"] = truncate(f"{compact[-1]['text']} {segment['text']}", 600)
        elif marker in {"finally", "lastly"}:
            compact.append({**segment, "join_next": True})
        elif compact and compact[-1].pop("join_next", False):
            compact[-1]["text"] = truncate(f"{compact[-1]['text']}, {segment['text']}", 600)
        else:
            compact.append(segment)
    for index, segment in enumerate(compact):
        segment["source_span"] = f"segment_{index + 1}"
        segment.pop("join_next", None)
    return compact[:20]


def _segment_action(text: str, hinted_action: str, hinted_topic: str) -> tuple[str, str]:
    if hinted_action in {"start", "continue", "branch", "resume", "land"}:
        return hinted_action, hinted_topic
    if re.match(
        r"^\s*(?:please\s+)?(?:call|name|label)\s+(?:this|it)\s+(?:the\s+)?",
        text,
        flags=re.IGNORECASE,
    ):
        return "branch", _explicit_thread_label(text)
    match = _RETURN_RE.search(text)
    if match:
        return "resume", _clean_topic(next(group for group in match.groups() if group is not None))
    match = _LAND_RE.search(text)
    if match:
        return "land", _clean_topic(next(group for group in match.groups() if group is not None))
    match = _BRANCH_RE.search(text)
    if match:
        return "branch", _explicit_thread_label(
            _clean_topic(next(group for group in match.groups() if group is not None))
        )
    if re.match(r"^\s*(?:then|next)\b", text, re.IGNORECASE):
        return "branch", _topic(text)
    return hinted_action or "continue", hinted_topic


def _explicit_thread_label(value: str) -> str:
    """Remove visible naming boilerplate before matching a thread identity.

    ``Call this the rain-scene thread`` names ``rain-scene``.  Treating words
    such as ``call``, ``this``, and ``thread`` as the topic caused otherwise
    distinct explicit labels to collapse into one session thread.
    """

    cleaned = " ".join(str(value or "").strip(" —–-,:;.!?").split())
    match = re.match(
        r"^(?:please\s+)?(?:call|name|label)\s+(?:this|it)\s+(?:the\s+)?"
        r"(.+?)(?:\s+thread)?$",
        cleaned,
        flags=re.IGNORECASE,
    )
    if match:
        cleaned = match.group(1).strip(" —–-,:;.!?")
    cleaned = re.sub(r"^(?:the\s+)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+thread$", "", cleaned, flags=re.IGNORECASE)
    return _clean_topic(cleaned)


def _resolve_thread(target: str, threads: list[dict[str, Any]], *, exclude_id: str) -> tuple[dict[str, Any] | None, bool]:
    target_terms = set(_terms(target))
    if not target_terms:
        return None, False
    scored: list[tuple[float, int, dict[str, Any]]] = []
    for index, thread in enumerate(threads):
        if str(thread.get("id") or "") == exclude_id:
            continue
        terms = set(_terms(str(thread.get("topic") or "")))
        overlap = target_terms & terms
        if overlap:
            scored.append((len(overlap) / max(len(target_terms), len(terms), 1), index, thread))
    if not scored:
        return None, False
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    ambiguous = len(scored) > 1 and scored[0][0] == scored[1][0]
    return (None, True) if ambiguous else (scored[0][2], False)


def _dependency_source(text: str, threads: list[dict[str, Any]], target_id: str, recent_id: str) -> str:
    lower = " ".join(text.lower().split())
    explicit = re.search(r"\b(?:because of|use|using|based on|in light of)\s+(?:the\s+)?(.+?)(?=[:,;.!?]|$)", lower)
    if explicit:
        thread, ambiguous = _resolve_thread(explicit.group(1), threads, exclude_id=target_id)
        if thread is not None and not ambiguous:
            return str(thread["id"])
    if recent_id and recent_id != target_id and any(cue in lower for cue in _DEPENDENCY_CUES):
        return recent_id
    return ""


def _new_thread(session_id: int, topic: str, source_span: str, state: str) -> dict[str, Any]:
    clean = _clean_topic(topic) or "current visible topic"
    digest = sha256(f"{session_id}|{clean.lower()}".encode("utf-8")).hexdigest()[:12]
    return {
        "id": f"thread_{digest}",
        "topic": truncate(clean, 240),
        "state": state,
        "opened_at": source_span,
        "scope": "current_session_only",
    }


def _visit(
    traversal: list[dict[str, Any]],
    thread_id: str,
    action: str,
    source_span: str,
    text: str,
    dependency_id: str = "",
) -> dict[str, Any]:
    return {
        "index": len(traversal) + 1,
        "thread_id": thread_id,
        "action": action,
        "source_span": source_span,
        "text": truncate(text, 600),
        "dependency_thread_id": dependency_id,
    }


def _add_edge(edges: list[dict[str, Any]], source_id: str, target_id: str, relation: str, source_span: str) -> None:
    if source_id and target_id and source_id != target_id:
        edges.append(
            {
                "source_thread_id": source_id,
                "target_thread_id": target_id,
                "relation": relation,
                "source_span": source_span,
                "confidence": "explicit_or_bounded_visible_cue",
            }
        )


def _set_thread_state(threads: list[dict[str, Any]], thread_id: str, state: str) -> None:
    for thread in threads:
        if str(thread.get("id") or "") == thread_id:
            thread["state"] = state
            return


def _normalize_thread(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or ""),
        "topic": truncate(str(item.get("topic") or ""), 240),
        "state": str(item.get("state") or "paused"),
        "opened_at": str(item.get("opened_at") or "prior_turn"),
        "scope": "current_session_only",
    }


def _normalize_edge(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_thread_id": str(item.get("source_thread_id") or ""),
        "target_thread_id": str(item.get("target_thread_id") or ""),
        "relation": str(item.get("relation") or ""),
        "source_span": str(item.get("source_span") or "prior_turn"),
        "confidence": str(item.get("confidence") or "bounded_visible_cue"),
    }


def _merge_threads(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for item in values:
        normalized = _normalize_thread(item)
        thread_id = str(normalized.get("id") or "")
        if not thread_id:
            continue
        if thread_id not in merged:
            order.append(thread_id)
        merged[thread_id] = normalized
    return [merged[thread_id] for thread_id in order]


def _retain_thread_index(
    threads: list[dict[str, Any]],
    *,
    active_id: str,
    protected_thread_ids: set[str],
    edges: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    relationship_ids = {
        str(edge.get(field) or "")
        for edge in edges
        if str(edge.get("relation") or "") in {
            "returns_to",
            "depends_on",
            "updates",
            "branches_from",
        }
        for field in ("source_thread_id", "target_thread_id")
        if str(edge.get(field) or "")
    }
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(threads):
        thread_id = str(item.get("id") or "")
        state = str(item.get("state") or "paused")
        score = (
            (1000 if thread_id == active_id else 0)
            + (700 if thread_id in protected_thread_ids else 0)
            + (300 if thread_id in relationship_ids else 0)
            + (180 if state in {"active", "resumed"} else 0)
            + (100 if state == "paused" else 0)
            + index
        )
        ranked.append((score, index, item))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    selected_ids = {
        str(item.get("id") or "") for _, _, item in ranked[: max(1, limit)]
    }
    return [item for item in threads if str(item.get("id") or "") in selected_ids]


def _dedupe_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for edge in edges:
        key = (
            str(edge.get("source_thread_id") or ""),
            str(edge.get("target_thread_id") or ""),
            str(edge.get("relation") or ""),
        )
        if all(key) and key not in seen:
            seen.add(key)
            result.append(edge)
    return result


def _clean_topic(value: str) -> str:
    clean = re.sub(r"^(?:the\s+)?(?:first|next|final)\s+(?:topic|part|item)\s*(?:is|:)?\s*", "", value.strip(), flags=re.IGNORECASE)
    clean = re.sub(r"^(?:please\s+)?(?:handle|plan|explain|discuss|address|consider|work\s+out|revise)\s+", "", clean, flags=re.IGNORECASE)
    return truncate(clean.strip(" ,.:;-"), 240)


def _topic(value: str) -> str:
    terms = _terms(_clean_topic(value))
    return " ".join(terms[:8])


def _terms(value: str) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)]
    return list(dict.fromkeys(word for word in words if word not in _TOPIC_STOP))[:20]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
