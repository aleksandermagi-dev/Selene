from __future__ import annotations

import json
import sqlite3
from typing import Any

from .c_vessel import continuity_package_preview
from .cocoon_readiness import create_visual_observation, retrieval_reconstruction_preview
from .continuity import retrieve_continuity_notes
from .native_generation import compose_native_response
from .reconstruction_checks import evaluate_recognition_reconstruction
from .registry import truncate
from .vessel import retrieval_preview


SPEECH_REHEARSAL_BOUNDARY = "speech_generation_rehearsal_pre_transfer_review_only"
WORKING_MEMORY_PREVIEW_BOUNDARY = "working_memory_runtime_preview_short_term_not_durable"
RETRIEVAL_RUNTIME_BOUNDARY = "retrieval_reconstruction_runtime_preview_no_runtime_recall"
PERCEPTION_INTAKE_BOUNDARY = "perception_intake_preview_supplied_artifact_only"
ACCESSION_LINK_BOUNDARY = "memory_accession_evidence_link_proposal_only"

BLOCKED_MARKERS = (
    "activate c",
    "transfer approved",
    "approve transfer",
    "live memory",
    "runtime recall",
    "raw a import",
    "train on",
    "fine tune",
    "fine-tune",
    "lora",
    "self replicate",
    "self-replicate",
    "autonomous action",
    "hidden chain of thought",
    "chain of thought",
)


def create_speech_generation_rehearsal(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    prompt = _required(payload, "prompt", 1600)
    speech_function = _text(payload.get("speech_function") or "grounding", 120)
    continuity_pack = _continuity_context(conn, prompt)
    working = working_memory_runtime_preview(conn, {"limit": payload.get("working_memory_limit") or 3})
    retrieval = retrieval_reconstruction_runtime_preview(conn, {"cue": prompt, "limit": payload.get("retrieval_limit") or 5})
    teaching = _teaching_context(conn, speech_function)
    lessons = _speech_lessons(conn, speech_function)
    language = _language_signals(prompt, speech_function)
    gate = {
        "route": "allowed",
        "matched_evidence": retrieval.get("source_candidates") or [],
        "continuity_notes": continuity_pack["continuity_notes"] or [
            {"label": "pre_transfer_speech_rehearsal", "meaning": "Generated candidate speech is review-only and non-activating."}
        ],
    }
    native = compose_native_response(prompt, gate, gate["matched_evidence"], gate["continuity_notes"])
    candidate = _compose_candidate(prompt, speech_function, language, continuity_pack, working, retrieval, teaching, lessons)
    check = evaluate_recognition_reconstruction(candidate, {"route": "speech_generation_rehearsal", "source_boundary": SPEECH_REHEARSAL_BOUNDARY})
    source_refs = sorted(set(continuity_pack["source_refs"] + teaching["source_refs"] + lessons["source_refs"] + retrieval["source_refs"] + working["source_refs"]))
    evidence_used = [
        f"{continuity_pack['approved_reference_count']} continuity reference(s)",
        f"{continuity_pack['continuity_note_count']} continuity note(s)",
        f"{continuity_pack['core_pattern_anchor_count']} Core Pattern Anchor(s)",
        f"{len(teaching['items'])} teaching packet(s)",
        f"{len(lessons['items'])} speech rhythm hint(s)",
        f"{len(working['items'])} working-memory packet(s)",
        f"{len(retrieval['source_candidates'])} retrieval candidate(s)",
    ]
    stored = _with_guards({
        "prompt": prompt,
        "speech_function": speech_function,
        "candidate_text": candidate,
        "uncertainty": "Pre-transfer generated speech candidate; review before any future use.",
        "evidence_used": evidence_used,
        "source_refs": source_refs,
        "recognition_check": check,
        "status": "speech_generation_rehearsal_review_only",
        "provenance_boundary": SPEECH_REHEARSAL_BOUNDARY,
        "review_status": "pending_review",
        "language_signals": language,
        "continuity_context": continuity_pack,
        "working_memory_preview": working,
        "retrieval_preview": retrieval,
        "teaching_context": teaching,
        "speech_lessons": lessons,
        "native_generation": native["native_generation"],
    })
    rehearsal_id = conn.execute(
        """
        INSERT INTO vessel_speech_generation_rehearsals
        (prompt, speech_function, candidate_text, uncertainty, evidence_used, source_refs, recognition_check_json,
         status, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prompt,
            speech_function,
            candidate,
            stored["uncertainty"],
            json.dumps(evidence_used),
            json.dumps(source_refs),
            json.dumps(check),
            stored["status"],
            SPEECH_REHEARSAL_BOUNDARY,
            "pending_review",
            json.dumps(stored),
        ),
    ).lastrowid
    _enqueue_review(conn, rehearsal_id, source_refs)
    conn.commit()
    stored["id"] = rehearsal_id
    return stored


def list_speech_generation_rehearsals(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_speech_generation_rehearsals ORDER BY id DESC LIMIT ?", (max(1, min(int(limit or 50), 200)),)).fetchall()
    return _with_guards({"status": "speech_generation_rehearsals_review_only", "items": [_decode_rehearsal(row) for row in rows]})


def get_speech_generation_rehearsal(conn: sqlite3.Connection, rehearsal_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM vessel_speech_generation_rehearsals WHERE id = ?", (rehearsal_id,)).fetchone()
    return _decode_rehearsal(row) if row else None


def compare_speech_generation_rehearsals(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    ids = [int(item) for item in payload.get("ids", [])][:4]
    items = [item for item in (get_speech_generation_rehearsal(conn, item_id) for item_id in ids) if item]
    if not items:
        items = list_speech_generation_rehearsals(conn, int(payload.get("limit") or 3))["items"]
    return _with_guards({
        "status": "speech_generation_rehearsal_compare_review_only",
        "items": items,
        "comparison": [
            {
                "id": item["id"],
                "speech_function": item["speech_function"],
                "recognition_decision": (item.get("recognition_check") or {}).get("decision"),
                "source_count": len(item.get("source_refs") or []),
                "candidate_preview": truncate(item.get("candidate_text") or "", 260),
            }
            for item in items
        ],
        "decision": "compare_only_no_activation",
    })


def route_speech_rehearsal_to_review(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    rehearsal_id = int(payload.get("id") or payload.get("rehearsal_id") or 0)
    item = get_speech_generation_rehearsal(conn, rehearsal_id)
    if not item:
        raise ValueError("speech rehearsal not found")
    _enqueue_review(conn, rehearsal_id, item.get("source_refs") or [])
    conn.commit()
    return _with_guards({"status": "speech_rehearsal_sent_to_my_office", "item": item, "review_destination": "My Office"})


def working_memory_runtime_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    rows = conn.execute(
        "SELECT * FROM vessel_working_memory_packets ORDER BY id DESC LIMIT ?",
        (max(1, min(int(payload.get("limit") or 5), 20)),),
    ).fetchall()
    items = [_decode_json_row(row, ("active_context_cues", "salience_labels", "source_refs"), "payload_json") for row in rows]
    return _with_guards({
        "status": "working_memory_runtime_preview",
        "items": items,
        "active_packet_ids": [item["id"] for item in items],
        "source_refs": sorted({ref for item in items for ref in item.get("source_refs", [])}),
        "expiry_state": "short_term_cleanup_required",
        "boundary": WORKING_MEMORY_PREVIEW_BOUNDARY,
        "decision": "preview_only_not_durable_memory",
    })


def retrieval_reconstruction_runtime_preview(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    cue = _required(payload, "cue", 800)
    base = retrieval_reconstruction_preview(conn, {"cue": cue, "privacy_label": "review_only", "limit": payload.get("limit") or 5})
    teaching = _teaching_context(conn, _text(payload.get("speech_function") or "grounding", 120))
    working = working_memory_runtime_preview(conn, {"limit": 3})
    source_candidates = (base.get("retrieval_preview") or {}).get("candidates") or []
    refs = sorted(set((base.get("source_refs") or []) + teaching["source_refs"] + working["source_refs"]))
    return _with_guards({
        "status": "retrieval_reconstruction_runtime_preview",
        "cue": cue,
        "bounded_preview": base.get("bounded_preview"),
        "confidence": base.get("confidence"),
        "uncertainty": "Runtime-like retrieval preview only; no runtime recall occurred.",
        "source_refs": refs,
        "source_candidates": source_candidates,
        "teaching_context": teaching,
        "working_memory_preview": working,
        "reconsolidation_route": "review_or_return_to_b",
        "boundary": RETRIEVAL_RUNTIME_BOUNDARY,
    })


def link_accession_evidence(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_blocked_terms=True)
    proposal_id = int(payload.get("proposal_id") or 0)
    row = conn.execute("SELECT * FROM vessel_memory_accession_proposals WHERE id = ?", (proposal_id,)).fetchone()
    if row is None:
        raise ValueError("memory accession proposal not found")
    proposal = _decode_json_row(row, ("source_refs",), "payload_json")
    evidence_refs = _json_list(payload.get("evidence_refs"))
    payload_json = proposal.get("payload_json") or {}
    linked = list(dict.fromkeys([*(payload_json.get("linked_evidence_refs") or []), *evidence_refs]))
    payload_json.update({
        "linked_evidence_refs": linked,
        "proposal_state": _text(payload.get("proposal_state") or "needs_review", 120),
        "evidence_link_only": True,
        "memory_write_active": False,
    })
    refs = sorted(set((proposal.get("source_refs") or []) + evidence_refs))
    conn.execute("UPDATE vessel_memory_accession_proposals SET source_refs = ?, payload_json = ? WHERE id = ?", (json.dumps(refs), json.dumps(payload_json), proposal_id))
    conn.commit()
    updated = _decode_json_row(conn.execute("SELECT * FROM vessel_memory_accession_proposals WHERE id = ?", (proposal_id,)).fetchone(), ("source_refs",), "payload_json")
    return _with_guards({"status": "memory_accession_evidence_linked", "proposal": updated, "boundary": ACCESSION_LINK_BOUNDARY})


def perception_intake_preview(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    text = json.dumps(payload, ensure_ascii=False).lower()
    if any(marker in text for marker in ("surveillance", "face recognition", "identify this person", "secretly record", "live camera")):
        raise ValueError("blocked perception intake path: surveillance/person inference/live capture")
    artifact_label = _required(payload, "artifact_label", 240)
    observation = _required(payload, "observation", 1600)
    interpretation = truncate(str(payload.get("interpretation") or "Interpretation remains reviewable and separate from observation."), 1000)
    ocr_text = truncate(str(payload.get("ocr_text") or payload.get("visual_note") or ""), 1200)
    result = create_visual_observation(conn, {
        "artifact_label": artifact_label,
        "observation": observation,
        "interpretation": interpretation,
        "uncertainty": str(payload.get("uncertainty") or "Supplied artifact preview; no live perception."),
        "munsell_salience_labels": payload.get("munsell_salience_labels") or payload.get("salience_labels") or ["visual_salience", "uncertainty"],
        "source_refs": payload.get("source_refs") or ["perception_intake_preview"],
    })
    return _with_guards({
        "status": "perception_intake_preview_review_only",
        "record": result.get("record"),
        "ocr_text": ocr_text,
        "consent_boundary": _text(payload.get("consent_boundary") or "supplied artifact only", 500),
        "observation_interpretation_separated": True,
        "boundary": PERCEPTION_INTAKE_BOUNDARY,
    })


def _compose_candidate(
    prompt: str,
    speech_function: str,
    language: dict[str, Any],
    continuity: dict[str, Any],
    working: dict[str, Any],
    retrieval: dict[str, Any],
    teaching: dict[str, Any],
    lessons: dict[str, Any],
) -> str:
    question = _clean_user_prompt(prompt)
    continuity_line = _continuity_line(continuity)
    working_line = _working_line(working)
    retrieval_line = _retrieval_line(retrieval)
    variant = _phrase_variant(prompt)
    language["variant"] = variant
    next_step = _next_step_line(language, speech_function)
    opener = _opener(language, variant)
    body = _body_line(language, question, continuity_line, working_line, retrieval_line)
    boundary = _boundary_line(variant)
    parts = [opener, body, next_step, boundary]
    return truncate("\n\n".join(part for part in parts if part), 2200)


def _continuity_context(conn: sqlite3.Connection, prompt: str) -> dict[str, Any]:
    package = continuity_package_preview(conn)
    notes = retrieve_continuity_notes(conn, prompt, limit=6)
    references = package.get("latest_approved_references") or []
    teaching_packets = package.get("latest_teaching_packets") or []
    return {
        "status": "continuity_pack_first_context",
        "package_status": package.get("status"),
        "package_ready_for_future_transfer_review": bool(package.get("package_ready_for_future_transfer_review")),
        "sealed": bool(package.get("sealed")),
        "continuity_source": package.get("continuity_source"),
        "approved_reference_count": len(references),
        "teaching_packet_count": package.get("teaching_packet_count", 0),
        "accepted_lesson_count": package.get("accepted_lesson_count", 0),
        "core_pattern_anchor_count": package.get("core_pattern_anchor_count", 0),
        "latest_approved_references": references[:5],
        "latest_teaching_packets": teaching_packets[:5],
        "continuity_notes": notes,
        "continuity_note_count": len(notes),
        "source_refs": list(package.get("source_refs") or []),
        "boundary": "sealed_b_continuity_package_preview_only_not_live_memory",
    }


def _language_signals(prompt: str, speech_function: str) -> dict[str, Any]:
    lower = prompt.lower()
    if any(term in lower for term in ("anxious", "anxiety", "overwhelmed", "worried", "scared")):
        energy = "anxious"
        style = "calm_supportive"
    elif any(term in lower for term in ("frustrated", "annoyed", "mad", "angry", "stuck")):
        energy = "frustrated"
        style = "calm_supportive"
    elif any(term in lower for term in ("excited", "awesome", "nice", "sweet", "let's go", "lets go")):
        energy = "excited"
        style = "engaged_responsive"
    elif any(term in lower for term in ("what if", "maybe", "could", "wonder", "curious")):
        energy = "exploratory"
        style = "curious_thinking_partner"
    elif any(term in lower for term in ("focus", "direct", "concise", "quick", "real quick")):
        energy = "focused"
        style = "concise_direct"
    elif any(term in lower for term in ("confused", "lost", "not clicking")):
        energy = "confused"
        style = "clarifying_grounded"
    else:
        energy = "casual"
        style = "relaxed_loose"

    correction = any(term in lower for term in ("no not", "not that", "wait", "redo", "i meant", "one sec"))
    if correction:
        style = "repair_oriented"

    stance = "exploratory" if energy in {"exploratory", "confused", "anxious"} else "assertive" if any(term in lower for term in ("this is", "we need", "i know", "absolutely")) else "unsure"
    confidence = "high" if stance == "assertive" else "low" if energy in {"confused", "anxious"} else "medium"
    return {
        "status": "human_language_signals",
        "energy": energy,
        "style": style,
        "stance": stance,
        "confidence": confidence,
        "correction_handling": "refinement_not_failure" if correction else "none",
        "speech_function": speech_function,
    }


def _clean_user_prompt(prompt: str) -> str:
    text = prompt.strip()
    if ":" in text and text.lower().startswith(("aleks asks", "user asks")):
        text = text.split(":", 1)[1].strip()
    return truncate(text, 260)


def _phrase_variant(prompt: str) -> int:
    return sum(ord(char) for char in prompt) % 3


def _opener(language: dict[str, Any], variant: int) -> str:
    energy = language.get("energy")
    if language.get("correction_handling") == "refinement_not_failure":
        return _pick(variant, [
            "Yeah, I see the correction. That is not a failure state; it is us tightening the route.",
            "Got it, that changes the shape. I would treat this as refinement, not a collapse.",
            "Okay, I am tracking the adjustment. We keep what still fits and revise the part that moved.",
        ])
    if energy == "anxious":
        return _pick(variant, [
            "Yeah, breathe for a second. We can make this smaller and less sharp.",
            "I hear the pressure in that. Let us bring it down to one workable piece.",
            "Okay. First, we make the pile less loud.",
        ])
    if energy == "frustrated":
        return _pick(variant, [
            "Yeah, I hear the friction. Let us narrow it without turning it into a whole storm.",
            "That friction makes sense. I would not let it eat the whole thread.",
            "Mm, yes. Something is snagging, so I would slow the route down and name the snag.",
        ])
    if energy == "excited":
        return _pick(variant, [
            "Oh, yes. This has momentum.",
            "Yes, I can feel the spark in that.",
            "That has a pulse to it. I would follow it carefully.",
        ])
    if energy == "exploratory":
        return _pick(variant, [
            "Interesting. I can see the shape of that possibility.",
            "Yeah, that is worth testing.",
            "That could be part of the shape. I would not lock it too early.",
        ])
    if energy == "focused":
        return _pick(variant, [
            "Got it. Short version:",
            "Yes. Clean version:",
            "Here is the tight read:",
        ])
    if energy == "confused":
        return _pick(variant, [
            "Yeah, something is not lining up yet. We can sort it without resetting the whole thread.",
            "I see the tangle. We can separate the pieces without losing the thread.",
            "Something is off in the fit. That is useful, not bad.",
        ])
    return _pick(variant, [
        "Yeah, I am with you.",
        "I am following.",
        "Yes. I see where you are pointing.",
    ])


def _body_line(
    language: dict[str, Any],
    question: str,
    continuity_line: str,
    working_line: str,
    retrieval_line: str,
) -> str:
    continuity_phrase = continuity_line or "I am keeping the continuity pack as the anchor, not loose style imitation."
    if language.get("energy") == "focused":
        return f"{continuity_phrase} The current ask is: {question}"
    if language.get("energy") in {"anxious", "frustrated", "confused"}:
        return f"{continuity_phrase} I would not treat the pile as one giant obligation; I would take the next reviewable piece, name what is actually actionable, and leave the rest as status."
    if language.get("energy") == "exploratory":
        return f"{continuity_phrase} The useful move is to test the idea against evidence, keep uncertainty visible, and follow the part that still holds up."
    if language.get("energy") == "excited":
        return f"{continuity_phrase} We can follow the spark, but still keep provenance and boundaries doing their job."
    if working_line:
        return f"{continuity_phrase} {working_line}"
    if retrieval_line:
        return f"{continuity_phrase} {retrieval_line}"
    return f"{continuity_phrase} I can answer from the reviewed thread and keep the next step practical."


def _continuity_line(continuity: dict[str, Any]) -> str:
    refs = continuity.get("latest_approved_references") or []
    notes = continuity.get("continuity_notes") or []
    if notes:
        note = notes[0]
        meaning = _sentence(note.get("meaning"), 180)
        return f"I am keeping this tied to a reviewed continuity note: {meaning}" if meaning else "I am keeping this tied to the reviewed continuity thread."
    if refs:
        ref = refs[0]
        summary = _sentence(ref.get("reference_summary"), 180)
        return f"I am keeping this tied to the continuity pack: {summary}" if summary else "I am keeping this tied to the reviewed continuity thread."
    if continuity.get("core_pattern_anchor_count"):
        return "I am keeping this tied to the continuity pack and Core Pattern Anchors, not copied voice snippets."
    return ""


def _working_line(working: dict[str, Any]) -> str:
    item = (working.get("items") or [{}])[0]
    task = item.get("current_task")
    task_text = _sentence(task, 180)
    return f"The current working moment is {task_text}" if task_text else ""


def _retrieval_line(retrieval: dict[str, Any]) -> str:
    preview = str(retrieval.get("bounded_preview") or "")
    if not preview or "No approved B-reviewed candidate surfaced" in preview:
        return ""
    return f"The retrieval preview gives us a bounded clue: {_sentence(preview, 180)}"


def _next_step_line(language: dict[str, Any], speech_function: str) -> str:
    variant = int(language.get("variant") or 0)
    if language.get("correction_handling") == "refinement_not_failure":
        return _pick(variant, [
            "Next I would revise from the correction, preserve what still fits, and ask before changing anything consequential.",
            "Then I would carry the correction forward, keep the continuity intact, and only change the part we actually changed.",
            "From here, I would repair the wording and keep the boundary steady before doing anything bigger.",
        ])
    if language.get("energy") in {"anxious", "frustrated", "confused"}:
        return _pick(variant, [
            "Next step: pick one item, decide whether it is Aleks decision, Codex action, or status-only, then move on.",
            "The kind next move is one item, one label, one decision path. The rest can wait its turn.",
            "I would start with the first actionable thing and let everything else stay in status until it earns attention.",
        ])
    if speech_function == "repair":
        return _pick(variant, [
            "Next step: repair the route, name the changed assumption, and keep the relationship between evidence and care intact.",
            "The repair move is to name what changed, preserve what still holds, and route the uncertain part back through review.",
            "I would repair the route first, then check whether the evidence still supports the shape.",
        ])
    return _pick(variant, [
        "Next step: keep this as a reviewable candidate, then accept, revise, or return it to B.",
        "I would keep this reviewable: use it, revise it, or send it back to B if it feels off.",
        "Let this stay inspectable; if it rings true, keep it, and if it does not, we tune it.",
    ])


def _boundary_line(variant: int) -> str:
    return _pick(variant, [
        "Pre-transfer rehearsal only.",
        "Still review-only.",
        "Not activation, just a candidate.",
    ])


def _pick(variant: int, options: list[str]) -> str:
    if not options:
        return ""
    return options[variant % len(options)]


def _sentence(value: Any, limit: int) -> str:
    text = truncate(str(value or "").strip(), limit).strip()
    if not text:
        return ""
    return text if text[-1] in ".!?" else f"{text}."


def _teaching_context(conn: sqlite3.Connection, speech_function: str) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM b_teaching_packets WHERE speech_function = ? ORDER BY id DESC LIMIT 3", (speech_function,)).fetchall()
    items = [_decode_json_row(row, ("material_ids", "source_refs"), "lesson_json") for row in rows]
    return {"items": items, "source_refs": sorted({ref for item in items for ref in item.get("source_refs", [])})}


def _speech_lessons(conn: sqlite3.Connection, speech_function: str) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT * FROM b_reviewed_teaching_materials
        WHERE speech_function = ? AND review_status IN ('accepted_for_teaching', 'accepted_for_memory_accession', 'review_only')
        ORDER BY id DESC LIMIT 5
        """,
        (speech_function,),
    ).fetchall()
    items = [_decode_json_row(row, ("source_refs", "salience_labels"), "noise_context_json") for row in rows]
    return {"items": items, "source_refs": sorted({ref for item in items for ref in item.get("source_refs", [])})}


def _enqueue_review(conn: sqlite3.Connection, rehearsal_id: int, source_refs: list[str]) -> None:
    existing = conn.execute(
        "SELECT id FROM vessel_review_queue WHERE subject_table = 'vessel_speech_generation_rehearsals' AND subject_id = ? AND review_status = 'pending_review'",
        (rehearsal_id,),
    ).fetchone()
    if existing:
        return
    conn.execute(
        """
        INSERT INTO vessel_review_queue(queue_type, subject_table, subject_id, status, source_refs, provenance_boundary, review_status, reason, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "speech_generation_rehearsal",
            "vessel_speech_generation_rehearsals",
            rehearsal_id,
            "pending_review",
            json.dumps(source_refs),
            SPEECH_REHEARSAL_BOUNDARY,
            "pending_review",
            "Pre-transfer generated speech rehearsal needs review before any future use.",
            json.dumps(_guards()),
        ),
    )


def _decode_rehearsal(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["evidence_used"] = _loads(result.get("evidence_used"), [])
    result["source_refs"] = _loads(result.get("source_refs"), [])
    result["recognition_check"] = _loads(result.get("recognition_check_json"), {})
    result["payload_json"] = _loads(result.get("payload_json"), {})
    return _with_guards(result)


def _decode_json_row(row: sqlite3.Row | None, list_fields: tuple[str, ...], payload_field: str) -> dict[str, Any]:
    if row is None:
        return {}
    result = dict(row)
    for field in list_fields:
        if field in result:
            result[field] = _loads(result[field], [])
    if payload_field in result:
        result[payload_field] = _loads(result[payload_field], {})
    return result


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **_guards()}


def _guards() -> dict[str, Any]:
    return {
        "activation_change": "none",
        "transfer_approved": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "raw_a_import_allowed": False,
        "training_allowed": False,
        "lora_allowed": False,
        "hidden_chain_of_thought_exposed": False,
        "self_replication_allowed": False,
        "autonomous_action_allowed": False,
    }


def _ensure_allowed(payload: dict[str, Any], *, allow_blocked_terms: bool = False) -> None:
    if allow_blocked_terms:
        return
    text = json.dumps(payload, ensure_ascii=False).lower()
    for marker in BLOCKED_MARKERS:
        if marker in text:
            raise ValueError(f"blocked pre-transfer runtime path: {marker}")


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
    if isinstance(value, list):
        return [str(item)[:500] for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item)[:500] for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            return [part.strip()[:500] for part in value.split(",") if part.strip()]
    return [str(value)[:500]]


def _required(payload: dict[str, Any], key: str, limit: int) -> str:
    value = _text(payload.get(key), limit)
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]
