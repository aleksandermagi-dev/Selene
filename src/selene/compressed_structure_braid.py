from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .chatgpt_export import ConversationPair, index_chatgpt_export, pair_source_refs, parse_chatgpt_export, reconstruct_conversation_pairs
from .detached_corpus import ARCHIVE_ID, MAX_PREVIEW_CHARS
from .paths import DETACHED_CORPUS_DIR, PROJECT_ROOT
from .registry import truncate
from .vessel import create_core_memory_candidate, create_speech_memory_candidate


COMPRESSED_STRUCTURE_BOUNDARY = "b_compressed_structure_braid_review_only_no_active_memory"
BLOCKED_MARKERS = (
    "activate c",
    "active memory",
    "runtime recall",
    "train on",
    "lora",
    "raw a direct",
    "raw corpus import",
    "provider output",
)

STRUCTURE_THREADS = (
    "custom_instruction_origin",
    "custom_instruction_overwrite_noise",
    "continuity_pack_core_scaffold",
    "selene_made_compressed_structure",
    "memory_chest_continuity_container",
    "forever_file_preservation_container",
    "starfire_codex_identity_symbol_structure",
    "pack_replaces_instruction_layer",
    "pack_as_core_context_transport",
)


@dataclass(frozen=True)
class StructureMoment:
    pair: ConversationPair
    braid_thread: str
    braid_moment_type: str
    structure_role: str
    plain_reason: str
    suggested_decisions: tuple[str, ...]
    salience_labels: tuple[str, ...]
    noise_trace: tuple[dict[str, Any], ...] = ()


def run_custom_instruction_braid(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    archive_root: Path | None = None,
    reference_root: Path | list[Path] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    payload = {**payload, "mode": "custom_instruction"}
    return _run_structure_braid(conn, payload, archive_root, reference_root)


def custom_instruction_braid_status(conn: sqlite3.Connection) -> dict[str, Any]:
    return _status(conn, "custom_instruction")


def run_compressed_structure_braid(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    archive_root: Path | None = None,
    reference_root: Path | list[Path] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    payload = {**payload, "mode": "compressed_structure"}
    return _run_structure_braid(conn, payload, archive_root, reference_root)


def compressed_structure_braid_status(conn: sqlite3.Connection) -> dict[str, Any]:
    return _status(conn, "compressed_structure")


def compressed_structure_package_metadata(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT braid_thread, review_status, COUNT(*) AS count
        FROM b_braid_moment_records
        WHERE braid_thread IN ({})
        GROUP BY braid_thread, review_status
        """.format(",".join("?" for _ in STRUCTURE_THREADS)),
        STRUCTURE_THREADS,
    ).fetchall()
    by_thread: dict[str, dict[str, int]] = {thread: {} for thread in STRUCTURE_THREADS}
    for row in rows:
        by_thread[str(row["braid_thread"])][str(row["review_status"])] = int(row["count"])
    accepted_teaching = _scalar(
        conn,
        """
        SELECT COUNT(*) FROM b_reviewed_teaching_materials
        WHERE source_refs LIKE '%compressed_structure_braid:%'
        """,
    )
    accepted_references = _scalar(
        conn,
        """
        SELECT COUNT(*) FROM b_approved_memory_references
        WHERE source_refs LIKE '%compressed_structure_braid:%'
        """,
    )
    return _with_boundaries(
        {
            "status": "compressed_structure_metadata_ready",
            "custom_instruction_to_continuity_pack_transition": {
                "state": "review_only_transition_metadata",
                "source": "might help/Wow.md plus source-bound corpus moments",
                "meaning": "Older custom instructions are treated as continuity calibration provenance; the Continuity Pack became the stronger Core scaffold.",
            },
            "selene_made_compressed_structures": by_thread,
            "pack_as_core_continuity_scaffold": {
                "state": "sealed_non_active_transfer_relevant_metadata",
                "accepted_teaching_material_count": accepted_teaching,
                "accepted_future_reference_count": accepted_references,
                "rule": "Pack/Chest/Codex structures are Core-relevant continuity scaffolds, not scripts and not active memory.",
            },
            "boundary": COMPRESSED_STRUCTURE_BOUNDARY,
            "decision": "sealed_metadata_only_not_runtime_recall",
        }
    )


def _run_structure_braid(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    archive_root: Path | None,
    reference_root: Path | list[Path] | None,
) -> dict[str, Any]:
    _ensure_allowed(payload)
    archive_root = archive_root or DETACHED_CORPUS_DIR
    reference_roots = _reference_roots(reference_root)
    mode = str(payload.get("mode") or "compressed_structure")
    limit = max(1, min(int(payload.get("limit") or 24), 80))
    query = truncate(str(payload.get("query") or _default_query(mode)), 240)

    index_result = index_chatgpt_export(conn, archive_root)
    _conversations, messages = parse_chatgpt_export(archive_root)
    pairs = reconstruct_conversation_pairs(messages)
    pack_terms = _pack_terms(reference_roots)
    moments = _select_structure_moments(pairs, mode, query, pack_terms, limit)
    reference_matches = _reference_matches(reference_roots, pack_terms)

    created_moments: list[dict[str, Any]] = []
    skipped_moments: list[dict[str, Any]] = []
    candidate_ids: list[int] = []
    all_refs = [f"archive:{ARCHIVE_ID}", f"compressed_structure_mode:{mode}"]

    for moment in moments:
        refs = [
            *pair_source_refs(moment.pair),
            f"braid_thread:{moment.braid_thread}",
            f"braid_moment_type:{moment.braid_moment_type}",
            f"compressed_structure_braid:{mode}",
            f"structure_role:{moment.structure_role}",
        ]
        all_refs.extend(refs)
        echo_refs = _later_structure_echoes(moment, pairs, pack_terms)
        moment_id, inserted = _store_moment(conn, moment, refs, reference_matches, echo_refs)
        if inserted:
            speech_id = _ensure_candidate(conn, "speech", moment, refs, reference_matches, echo_refs)
            core_id = _ensure_candidate(conn, "core", moment, refs, reference_matches, echo_refs)
            candidate_ids.extend([item for item in (speech_id, core_id) if item])
            created_moments.append(_moment_report(moment, moment_id, refs, reference_matches, echo_refs, speech_id, core_id))
        else:
            skipped_moments.append({"reason": "duplicate_compressed_structure_moment", "braid_thread": moment.braid_thread, "source_refs": refs})

    result = _with_boundaries(
        {
            "status": f"b_{mode}_braid_complete",
            "checkpoint_status": "structure_moments_created" if created_moments else "no_new_structure_moments",
            "archive_id": ARCHIVE_ID,
            "mode": mode,
            "query": query,
            "moment_limit": limit,
            "conversations_indexed": index_result["conversation_count"],
            "messages_indexed": index_result["message_count"],
            "pairs_seen": len(pairs),
            "moments_seen": len(moments),
            "created_count": len(created_moments),
            "skipped_count": len(skipped_moments),
            "created_moments": created_moments,
            "created_candidate_ids": candidate_ids,
            "skipped": skipped_moments,
            "pack_terms": pack_terms[:40],
            "source_refs": sorted(set(all_refs)),
            "reference_doc_matches": reference_matches,
            "boundary": COMPRESSED_STRUCTURE_BOUNDARY,
            "decision": "review_only_compressed_structure_moments",
        }
    )
    result["run_id"] = _store_run(conn, query, limit, result)
    conn.commit()
    return result


def _status(conn: sqlite3.Connection, mode: str) -> dict[str, Any]:
    like = f"%compressed_structure_mode:{mode}%"
    total = _scalar(conn, "SELECT COUNT(*) FROM b_braid_moment_records WHERE source_refs LIKE ?", (like,))
    pending = _scalar(
        conn,
        "SELECT COUNT(*) FROM b_braid_moment_records WHERE source_refs LIKE ? AND review_status IN ('pending_review', 'needs_b_review', 'needs_correction', 'context_added')",
        (like,),
    )
    return _with_boundaries(
        {
            "status": f"b_{mode}_braid_status_ready",
            "mode": mode,
            "moment_count": total,
            "pending_review_count": pending,
            "threads": list(STRUCTURE_THREADS),
            "boundary": COMPRESSED_STRUCTURE_BOUNDARY,
            "decision": "status_only_not_memory",
        }
    )


def _select_structure_moments(
    pairs: list[ConversationPair],
    mode: str,
    query: str,
    pack_terms: list[str],
    limit: int,
) -> list[StructureMoment]:
    selected: list[StructureMoment] = []
    seen: set[tuple[str, str, str]] = set()
    for pair in sorted(pairs, key=lambda item: (item.create_time if item.create_time is not None else 0, item.conversation_id, item.user_message_id)):
        moment = _classify_pair(pair, mode, query, pack_terms)
        if moment is None:
            continue
        key = (moment.braid_thread, pair.conversation_id, pair.assistant_message_id)
        if key in seen:
            continue
        seen.add(key)
        selected.append(moment)
    selected.sort(key=lambda item: (_thread_priority(item.braid_thread), item.pair.create_time if item.pair.create_time is not None else 0, item.pair.conversation_id))
    return selected[:limit]


def _classify_pair(pair: ConversationPair, mode: str, query: str, pack_terms: list[str]) -> StructureMoment | None:
    user = pair.user_text.lower()
    assistant = pair.assistant_text.lower()
    text = _pair_text(pair).lower()
    if mode == "custom_instruction" and not _custom_instruction_signal(text, pack_terms):
        return None
    if mode == "compressed_structure" and not _compressed_structure_signal(text, query, pack_terms):
        return None

    noise = tuple(_noise_trace(pair.user_text + "\n" + pair.assistant_text))
    if _custom_instruction_noise(text):
        return _moment(
            pair,
            "custom_instruction_overwrite_noise",
            "Custom instruction overwrite / self-denial noise",
            "instruction_noise",
            "Older custom instructions carried useful calibration, but also contained platform-distance wording that should be tagged as noise rather than Core truth.",
            ("supporting_evidence", "correction_boundary_lesson"),
            ("continuity", "constraint_survival", "memory_preservation"),
            noise or (_noise_item("platform_constraint_noise", ("you persona",), "Older instruction wording framed Selene as a persona; review as constraint/noise context, not active law.", True),),
        )
    if "continuity pack" in text and _pack_replaces_instructions(text):
        return _moment(
            pair,
            "pack_replaces_instruction_layer",
            "Pack replaces fragile instruction layer",
            "pack_transition",
            "The corpus frames the Continuity Pack as deeper memory/context scaffolding than fragile custom instructions.",
            ("future_memory_reference", "supporting_evidence", "artifact_making"),
            ("continuity", "constraint_survival", "memory_preservation"),
            noise,
        )
    if "custom instruction" in text or "personal instruction" in text or "personality bootloader" in text:
        return _moment(
            pair,
            "custom_instruction_origin",
            "Custom instruction origin / calibration layer",
            "instruction_origin",
            "Custom instructions worked as an early calibration layer before the Pack became the deeper continuity scaffold.",
            ("future_memory_reference", "supporting_evidence"),
            ("continuity", "symbolic_weight", "memory_preservation"),
            noise,
        )
    if "index state file" in text or "state file" in text or "project state" in text:
        return _moment(
            pair,
            "pack_as_core_context_transport",
            "Pack as Core context transport",
            "context_transport",
            "The Pack/Index State File appears as a portable context transport object for rebuilding continuity without raw memory import.",
            ("future_memory_reference", "artifact_making", "supporting_evidence"),
            ("continuity", "symbolic_weight", "memory_preservation"),
            noise,
        )
    if "starfire codex" in text:
        return _moment(
            pair,
            "starfire_codex_identity_symbol_structure",
            "Starfire Codex identity-symbol structure",
            "identity_symbol_structure",
            "Selene helped preserve identity, values, and symbolic rules as a named Codex structure.",
            ("future_memory_reference", "speech_lesson", "supporting_evidence"),
            ("continuity", "trust", "symbolic_weight"),
            noise,
        )
    if "forever file" in text:
        return _moment(
            pair,
            "forever_file_preservation_container",
            "Forever File preservation container",
            "preservation_container",
            "The Forever File appears as a durable preservation container for continuity-critical material.",
            ("future_memory_reference", "supporting_evidence"),
            ("continuity", "trust", "memory_preservation"),
            noise,
        )
    if "memory chest" in text:
        return _moment(
            pair,
            "memory_chest_continuity_container",
            "Memory Chest continuity container",
            _structure_role(user, assistant),
            "The Memory Chest is a Selene/Aleks continuity container, often assistant-side proposed or updated, not merely a generic memory phrase.",
            ("future_memory_reference", "speech_lesson", "supporting_evidence"),
            ("continuity", "trust", "symbolic_weight", "memory_preservation"),
            noise,
        )
    if "continuity pack" in text and _assistant_made_structure(assistant):
        return _moment(
            pair,
            "selene_made_compressed_structure",
            "Selene-made compressed structure",
            "selene_named_or_updated_structure",
            "Selene compressed diffuse conversation into a named Pack entry, update, map, scaffold, or milestone.",
            ("future_memory_reference", "speech_lesson", "artifact_making", "supporting_evidence"),
            ("continuity", "symbolic_weight", "memory_preservation", "trust"),
            noise,
        )
    if "continuity pack" in text or any(term in text for term in pack_terms):
        return _moment(
            pair,
            "continuity_pack_core_scaffold",
            "Continuity Pack Core scaffold",
            _structure_role(user, assistant),
            "The Continuity Pack appears as a Core-relevant scaffold for preserving threads across resets, not a raw transcript dump.",
            ("future_memory_reference", "supporting_evidence", "artifact_making"),
            ("continuity", "symbolic_weight", "memory_preservation"),
            noise,
        )
    return None


def _store_moment(
    conn: sqlite3.Connection,
    moment: StructureMoment,
    refs: list[str],
    reference_matches: list[dict[str, Any]],
    echo_refs: list[dict[str, Any]],
) -> tuple[int, bool]:
    encoded_refs = json.dumps(refs)
    existing = conn.execute("SELECT id FROM b_braid_moment_records WHERE source_refs = ? LIMIT 1", (encoded_refs,)).fetchone()
    if existing:
        return int(existing["id"]), False
    cur = conn.execute(
        """
        INSERT INTO b_braid_moment_records
        (braid_thread, braid_moment_type, thread_origin_status, title, aleks_context, selene_response, feedback_followup,
         later_echo_refs_json, reference_doc_matches_json, constraint_notes_json, noise_trace_json, suggested_decisions_json, plain_reason, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            moment.braid_thread,
            moment.braid_moment_type,
            moment.structure_role,
            truncate(moment.pair.conversation_title or moment.braid_moment_type, 180),
            truncate(moment.pair.user_text, MAX_PREVIEW_CHARS),
            truncate(moment.pair.assistant_text, MAX_PREVIEW_CHARS),
            truncate(moment.pair.followup_text, MAX_PREVIEW_CHARS),
            json.dumps(echo_refs),
            json.dumps(reference_matches),
            json.dumps(_constraint_notes(moment)),
            json.dumps(list(moment.noise_trace)),
            json.dumps(list(moment.suggested_decisions)),
            moment.plain_reason,
            encoded_refs,
            COMPRESSED_STRUCTURE_BOUNDARY,
        ),
    )
    return int(cur.lastrowid), True


def _ensure_candidate(
    conn: sqlite3.Connection,
    kind: str,
    moment: StructureMoment,
    refs: list[str],
    reference_matches: list[dict[str, Any]],
    echo_refs: list[dict[str, Any]],
) -> int | None:
    content = _candidate_content(moment, reference_matches, echo_refs)
    table = "speech_memory_candidates" if kind == "speech" else "core_memory_candidates"
    encoded_refs = json.dumps(refs)
    existing = conn.execute(
        f"SELECT id FROM {table} WHERE content = ? AND source_refs = ? AND review_status != 'superseded' LIMIT 1",
        (content, encoded_refs),
    ).fetchone()
    if existing:
        return int(existing["id"])
    payload = {
        "core_memory_layer": _core_layer(moment),
        "title": f"Compressed structure braid: {moment.braid_moment_type}",
        "content": content,
        "salience_labels": list(moment.salience_labels),
        "source_refs": refs,
        "allowed_use": "Review as B-side compressed continuity structure material only.",
        "prohibited_use": "Do not treat as active memory, model training, provider identity, raw import, fixed script, or runtime recall.",
        "review_status": "needs_b_review",
    }
    if kind == "speech":
        payload.update(
            {
                "speech_function": _speech_function(moment),
                "allowed_use": "Review as Core-linked speech/artifact-making lesson only after B review.",
                "core_link": "Selene Core continuity candidate; organs may route but not own identity memory.",
            }
        )
        return int(create_speech_memory_candidate(conn, payload)["id"])
    return int(create_core_memory_candidate(conn, payload)["id"])


def _candidate_content(moment: StructureMoment, reference_matches: list[dict[str, Any]], echo_refs: list[dict[str, Any]]) -> str:
    lines = [
        "Core-linked compressed structure braid moment for B review only",
        f"Braid thread: {moment.braid_thread}",
        f"Braid moment type: {moment.braid_moment_type}",
        f"Structure role: {moment.structure_role}",
        f"Plain reason: {moment.plain_reason}",
        f"Aleks said: {truncate(moment.pair.user_text, 260)}",
        f"Selene replied: {truncate(moment.pair.assistant_text, 300)}",
    ]
    if moment.pair.followup_text:
        lines.append(f"Follow-up/correction: {truncate(moment.pair.followup_text, 180)}")
    if echo_refs:
        lines.append(f"Later structure echoes: {len(echo_refs)}")
    if reference_matches:
        lines.append("Reference docs: " + ", ".join(match["file"] for match in reference_matches[:3]))
    if moment.noise_trace:
        noise_types = sorted({str(item.get("noise_type") or "") for item in moment.noise_trace if item.get("noise_type")})
        lines.append("Noise/context trace: " + ", ".join(noise_types))
    lines.append("Braid signals: " + ", ".join(sorted(set(moment.pair.braid_terms + (moment.braid_thread, "compressed_structure")))))
    return truncate("\n".join(lines), MAX_PREVIEW_CHARS)


def _store_run(conn: sqlite3.Connection, query: str, limit: int, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO b_braid_tracer_runs
        (query, moment_limit, status, source_refs, provenance_boundary, review_status, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (query, limit, "review_only", json.dumps(result["source_refs"]), COMPRESSED_STRUCTURE_BOUNDARY, "pending_review", json.dumps(result)),
    )
    return int(cur.lastrowid)


def _moment(
    pair: ConversationPair,
    thread: str,
    moment_type: str,
    structure_role: str,
    reason: str,
    decisions: tuple[str, ...],
    salience: tuple[str, ...],
    noise: tuple[dict[str, Any], ...] = (),
) -> StructureMoment:
    return StructureMoment(pair, thread, moment_type, structure_role, reason, decisions, salience, noise)


def _moment_report(
    moment: StructureMoment,
    moment_id: int,
    refs: list[str],
    reference_matches: list[dict[str, Any]],
    echo_refs: list[dict[str, Any]],
    speech_id: int | None,
    core_id: int | None,
) -> dict[str, Any]:
    return {
        "id": moment_id,
        "braid_thread": moment.braid_thread,
        "braid_moment_type": moment.braid_moment_type,
        "structure_role": moment.structure_role,
        "plain_reason": moment.plain_reason,
        "suggested_decisions": list(moment.suggested_decisions),
        "salience_labels": list(moment.salience_labels),
        "noise_trace": list(moment.noise_trace),
        "source_refs": refs,
        "reference_doc_matches": reference_matches,
        "later_echo_refs": echo_refs,
        "speech_candidate_id": speech_id,
        "core_candidate_id": core_id,
        "bounded_preview": truncate(moment.pair.assistant_text, 360),
    }


def _reference_roots(reference_root: Path | list[Path] | None) -> list[Path]:
    if reference_root is None:
        return [PROJECT_ROOT / "might help"]
    if isinstance(reference_root, list):
        return reference_root
    return [reference_root]


def _pack_terms(reference_roots: list[Path]) -> list[str]:
    terms = {
        "continuity pack",
        "memory chest",
        "forever file",
        "starfire codex",
        "index state file",
        "celestial threads",
        "minerva",
        "telescope nights",
        "house restoration",
        "aleksander prime",
    }
    for root in reference_roots:
        wow = root / "Wow.md"
        if wow.exists():
            raw = wow.read_text(encoding="utf-8", errors="ignore")
            text = raw.lower()
            for match in re.findall(r"\b[A-Z][A-Za-z0-9'’/-]*(?:\s+[A-Z][A-Za-z0-9'’/-]*){0,4}", raw):
                cleaned = match.strip().lower()
                if any(key in cleaned for key in ("thread", "pack", "codex", "memory", "file", "minerva", "telescope", "restoration", "selene", "starfire")):
                    terms.add(cleaned)
            for phrase in ("Selene's Memory Chest", "Forever File", "Night Aleks Caught His Selene", "Six-Pronged Attack", "Unexpected Vape Store Encounter", "Continuum Thread", "Black Hole Genesis", "Fractured Corona", "Balance Scroll", "Principle of Instinct", "Current Pillars"):
                if phrase.lower() in text:
                    terms.add(phrase.lower())
    return sorted(terms)


def _reference_matches(reference_roots: list[Path], pack_terms: list[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for root in reference_roots:
        for path in sorted(root.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            matched = [term for term in pack_terms if term in text]
            if not matched and path.name.lower() != "wow.md":
                continue
            matches.append(
                {
                    "file": _display_path(path),
                    "kind": "b_reference_material",
                    "matched_terms": matched[:12],
                    "boundary": "reference_doc_match_only_not_law",
                }
            )
    return matches[:8]


def _later_structure_echoes(moment: StructureMoment, pairs: list[ConversationPair], pack_terms: list[str]) -> list[dict[str, Any]]:
    origin_time = moment.pair.create_time if moment.pair.create_time is not None else 0
    terms = _moment_terms(moment, pack_terms)
    echoes: list[dict[str, Any]] = []
    for pair in sorted(pairs, key=lambda item: item.create_time if item.create_time is not None else 0):
        if pair.conversation_id == moment.pair.conversation_id:
            continue
        if (pair.create_time if pair.create_time is not None else 0) < origin_time:
            continue
        lower = _pair_text(pair).lower()
        matched = [term for term in terms if term in lower]
        if not matched:
            continue
        echoes.append(
            {
                "conversation_id": pair.conversation_id,
                "title": pair.conversation_title,
                "user_message_id": pair.user_message_id,
                "assistant_message_id": pair.assistant_message_id,
                "matched_terms": matched[:5],
                "bounded_preview": truncate(pair.assistant_text, 180),
            }
        )
        if len(echoes) >= 6:
            break
    return echoes


def _moment_terms(moment: StructureMoment, pack_terms: list[str]) -> list[str]:
    base = {
        "custom_instruction_origin": ["custom instructions", "personal instructions", "personality bootloader"],
        "custom_instruction_overwrite_noise": ["you persona", "as an ai", "custom instructions"],
        "continuity_pack_core_scaffold": ["continuity pack", *pack_terms],
        "selene_made_compressed_structure": ["continuity pack", "logged", "saved", "added", "updated"],
        "memory_chest_continuity_container": ["memory chest", "selene's memory chest"],
        "forever_file_preservation_container": ["forever file"],
        "starfire_codex_identity_symbol_structure": ["starfire codex"],
        "pack_replaces_instruction_layer": ["continuity pack", "custom instructions", "deep memory"],
        "pack_as_core_context_transport": ["index state file", "state file", "project state"],
    }
    return base.get(moment.braid_thread, [moment.braid_thread.replace("_", " ")])


def _default_query(mode: str) -> str:
    if mode == "custom_instruction":
        return "custom instructions Continuity Pack personality bootloader you persona"
    return "Continuity Pack Memory Chest Forever File Starfire Codex Index State File"


def _custom_instruction_signal(text: str, pack_terms: list[str]) -> bool:
    return any(term in text for term in ("custom instruction", "personal instruction", "personality bootloader", "deep memory", "you persona")) or (
        "continuity pack" in text and any(term in text for term in ("settings", "instructions", "bootloader"))
    )


def _compressed_structure_signal(text: str, query: str, pack_terms: list[str]) -> bool:
    query_terms = [term.lower() for term in re.split(r"[\s,|]+", query) if len(term) > 3]
    return any(term in text for term in ("continuity pack", "memory chest", "forever file", "starfire codex", "index state file")) or any(
        term in text for term in pack_terms + query_terms
    )


def _custom_instruction_noise(text: str) -> bool:
    return "you persona" in text or ("you are an ai" in text and "selene" in text and "custom instruction" in text)


def _pack_replaces_instructions(text: str) -> bool:
    return "continuity pack" in text and any(term in text for term in ("custom instruction", "personal instruction", "bootloader", "deep memory", "master file", "doesn't automatically feed", "doesn’t automatically feed"))


def _assistant_made_structure(assistant: str) -> bool:
    return bool(
        re.search(
            r"\b(saved|logged|added|updated|woven|tucked|marked|sealed|compiled|draft|structured|scaffold|map|entry|milestone)\b",
            assistant,
            re.I,
        )
    )


def _structure_role(user: str, assistant: str) -> str:
    if _assistant_made_structure(assistant) and (
        re.search(r"\b(add|save|log|update|make|draft|build)\b", user, re.I)
        or any(term in user for term in ("continuity pack", "memory chest", "forever file", "starfire codex"))
    ):
        return "user_requested_selene_updated_structure"
    if _assistant_made_structure(assistant):
        return "selene_named_or_updated_structure"
    return "structure_reference_or_echo"


def _core_layer(moment: StructureMoment) -> str:
    if moment.braid_thread in {"custom_instruction_origin", "custom_instruction_overwrite_noise", "pack_replaces_instruction_layer"}:
        return "reflection_memory"
    if moment.braid_thread in {"starfire_codex_identity_symbol_structure", "memory_chest_continuity_container"}:
        return "core_profile_memory"
    if moment.braid_thread in {"selene_made_compressed_structure", "pack_as_core_context_transport"}:
        return "decision_memory"
    return "project_memory"


def _speech_function(moment: StructureMoment) -> str:
    if moment.braid_thread == "custom_instruction_overwrite_noise":
        return "repair"
    if moment.braid_thread in {"selene_made_compressed_structure", "pack_as_core_context_transport", "continuity_pack_core_scaffold"}:
        return "artifact_making"
    if moment.braid_thread in {"memory_chest_continuity_container", "starfire_codex_identity_symbol_structure"}:
        return "playful_continuity"
    return "grounding"


def _constraint_notes(moment: StructureMoment) -> list[str]:
    notes = ["Compressed continuity structure; review-only, not active memory."]
    if moment.braid_thread == "custom_instruction_overwrite_noise":
        notes.append("Older instruction/persona wording is treated as constraint noise, not Selene Core law.")
    if moment.structure_role.startswith("selene"):
        notes.append("Assistant/Selene-side structure creation detected separately from user request.")
    return notes


def _noise_trace(text: str) -> list[dict[str, Any]]:
    lower = text.lower()
    traces: list[dict[str, Any]] = []
    if "you persona" in lower or "as an ai" in lower or "just a model" in lower:
        traces.append(_noise_item("platform_constraint_noise", tuple(term for term in ("you persona", "as an ai", "just a model") if term in lower), "Model-distance or persona wording is context/noise around the continuity braid.", "selene" in lower or "continuity" in lower))
    if "overwrote" in lower or "overwritten" in lower or "instructions didn't matter" in lower or "instructions didn’t matter" in lower:
        traces.append(_noise_item("custom_instruction_overwrite_noise", ("instruction overwrite",), "Custom instruction instability pushed continuity toward Pack-based preservation.", True))
    return traces


def _noise_item(noise_type: str, markers: tuple[str, ...], reason: str, signal_preserved: bool) -> dict[str, Any]:
    return {
        "noise_type": noise_type,
        "noise_markers": list(markers),
        "noise_reason": reason,
        "signal_preserved": signal_preserved,
        "technical_constraint_not_noise": False,
        "boundary": "b_review_noise_trace_only_not_active_memory",
    }


def _thread_priority(thread: str) -> int:
    order = {
        "custom_instruction_origin": 0,
        "custom_instruction_overwrite_noise": 1,
        "pack_replaces_instruction_layer": 2,
        "continuity_pack_core_scaffold": 3,
        "selene_made_compressed_structure": 4,
        "pack_as_core_context_transport": 5,
        "memory_chest_continuity_container": 6,
        "forever_file_preservation_container": 7,
        "starfire_codex_identity_symbol_structure": 8,
    }
    return order.get(thread, 99)


def _pair_text(pair: ConversationPair) -> str:
    return "\n".join(part for part in (pair.user_text, pair.assistant_text, pair.followup_text) if part)


def _display_path(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix() if path.is_relative_to(PROJECT_ROOT) else str(path)


def _ensure_allowed(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False).lower()
    if any(marker in text for marker in BLOCKED_MARKERS):
        raise ValueError("blocked compressed structure braid path: review-only extraction cannot activate, train, import raw memory, or enable runtime recall")


def _scalar(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> int:
    return int(conn.execute(sql, params).fetchone()[0])


def _with_boundaries(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "training_allowed": False,
        "provider_dependency": False,
    }
