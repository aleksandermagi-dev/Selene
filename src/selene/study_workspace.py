from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from typing import Any

from .comprehension_integration import propose_comprehension_concept
from .registry import truncate


STUDY_BOUNDARY = (
    "selene_owned_deliberate_study_and_visible_learning_evidence_only_"
    "not_memory_identity_governance_personality_training_or_hidden_retention"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "identity_change": False,
    "governance_change": False,
    "personality_change": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "hidden_retention_allowed": False,
    "study_is_cocoon": False,
    "study_is_dream": False,
    "learning_evidence_is_pass_fail_grade": False,
}

SESSION_STATES = {"active", "paused", "completed"}
QUESTION_STATES = {"ready", "developing", "question_without_words"}


def study_workspace_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
               SUM(CASE WHEN status = 'paused' THEN 1 ELSE 0 END) AS paused
        FROM selene_study_sessions
        """
    ).fetchone()
    open_questions = int(
        conn.execute("SELECT COUNT(*) FROM selene_study_questions WHERE status = 'open'").fetchone()[0]
    )
    return _with_guards(
        {
            "status": "selene_study_workspace_ready",
            "owner": "Selene",
            "location": "Selene workspace",
            "session_count": int(row["total"] or 0),
            "active_count": int(row["active"] or 0),
            "paused_count": int(row["paused"] or 0),
            "open_question_count": open_questions,
            "question_answer_rule": (
                "Aleks's answer is attributable session knowledge immediately and becomes a source-labeled "
                "teaching update candidate for durable use."
            ),
            "durable_use_rule": "Durable Chat use still follows the inspectable comprehension and teaching lifecycle.",
            "review_status": "status_only",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def list_study_sessions(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 50), 200))
    rows = conn.execute(
        "SELECT * FROM selene_study_sessions ORDER BY updated_at DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return _with_guards(
        {
            "status": "selene_study_sessions_ready",
            "items": [_decode_session(row) for row in rows],
            "review_status": "status_only",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def get_study_session(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    session_id = _positive_id((payload or {}).get("session_id"), "session_id")
    row = conn.execute("SELECT * FROM selene_study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        raise ValueError("study session not found")
    question_rows = conn.execute(
        "SELECT * FROM selene_study_questions WHERE session_id = ? ORDER BY id ASC", (session_id,)
    ).fetchall()
    evidence_rows = conn.execute(
        "SELECT * FROM selene_study_evidence WHERE session_id = ? ORDER BY id ASC", (session_id,)
    ).fetchall()
    session = _decode_session(row)
    session["concepts"] = _concept_summaries(conn, session["concept_ids"])
    return _with_guards(
        {
            "status": "selene_study_session_ready",
            "item": session,
            "questions": [_decode_question(item) for item in question_rows],
            "learning_evidence": [_decode_evidence(item) for item in evidence_rows],
            "review_status": "status_only",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def start_study_session(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    concept_ids = _int_list(payload.get("concept_ids"))
    if not concept_ids:
        raise ValueError("at least one approved concept_id is required")
    concepts = _approved_concepts(conn, concept_ids)
    if len(concepts) != len(concept_ids):
        raise ValueError("study sessions may use only approved, Chat-eligible knowledge concepts")
    title = truncate(str(payload.get("title") or f"Study: {concepts[0]['title']}"), 240).strip()
    focus = truncate(str(payload.get("focus") or ""), 1000).strip()
    digest = sha256(f"{title}|{concept_ids}|{focus}".encode("utf-8")).hexdigest()[:18]
    key = f"study-{digest}"
    source_refs = list(
        dict.fromkeys(
            ref
            for concept in concepts
            for ref in _loads(concept.get("source_refs"), [])
            if str(ref).strip()
        )
    )[:100]
    cursor = conn.execute(
        """
        INSERT INTO selene_study_sessions
        (session_key, title, focus, status, concept_ids_json, source_refs, provenance_boundary, payload_json)
        VALUES (?, ?, ?, 'active', ?, ?, ?, ?)
        ON CONFLICT(session_key) DO UPDATE SET
          status = 'active', focus = excluded.focus, updated_at = CURRENT_TIMESTAMP
        """,
        (key, title, focus, json.dumps(concept_ids), json.dumps(source_refs), STUDY_BOUNDARY, json.dumps({})),
    )
    if cursor.lastrowid:
        session_id = int(cursor.lastrowid)
    else:
        session_id = int(conn.execute("SELECT id FROM selene_study_sessions WHERE session_key = ?", (key,)).fetchone()[0])
    _record_evidence(
        conn,
        session_id,
        "study_session_started",
        "Selene opened a deliberate study session from approved knowledge.",
        {"concept_ids": concept_ids, "focus": focus},
        source_refs,
    )
    conn.commit()
    return get_study_session(conn, {"session_id": session_id})


def update_study_session(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    session_id = _positive_id(payload.get("session_id"), "session_id")
    current = conn.execute("SELECT * FROM selene_study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not current:
        raise ValueError("study session not found")
    status = str(payload.get("status") or current["status"]).strip()
    if status not in SESSION_STATES:
        raise ValueError("study status must be active, paused, or completed")
    understanding = truncate(str(payload.get("current_understanding", current["current_understanding"]) or ""), 6000)
    connections = _text_list(payload.get("connections")) if "connections" in payload else _loads(current["connections_json"], [])
    uncertainties = _text_list(payload.get("uncertainties")) if "uncertainties" in payload else _loads(current["uncertainties_json"], [])
    conn.execute(
        """
        UPDATE selene_study_sessions
        SET status = ?, current_understanding = ?, connections_json = ?, uncertainties_json = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, understanding, json.dumps(connections), json.dumps(uncertainties), session_id),
    )
    _record_evidence(
        conn,
        session_id,
        "study_reflection_updated",
        "Selene recorded a visible study reflection without grading it.",
        {"status": status, "connections": connections, "uncertainties": uncertainties},
        _loads(current["source_refs"], []),
    )
    conn.commit()
    return get_study_session(conn, {"session_id": session_id})


def ask_study_question(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    session_id = _positive_id(payload.get("session_id"), "session_id")
    session = conn.execute("SELECT * FROM selene_study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        raise ValueError("study session not found")
    formation_state = str(payload.get("formation_state") or "ready").strip()
    if formation_state not in QUESTION_STATES:
        raise ValueError("unsupported question formation state")
    question = truncate(str(payload.get("question_text") or ""), 3000).strip()
    if not question and formation_state != "question_without_words":
        raise ValueError("question_text is required unless the question has no words yet")
    concept_id = int(payload.get("concept_id") or 0) or None
    allowed_ids = set(_loads(session["concept_ids_json"], []))
    if concept_id is not None and concept_id not in allowed_ids:
        raise ValueError("question concept_id must belong to this study session")
    uncertainty = truncate(str(payload.get("uncertainty_context") or ""), 2000)
    cursor = conn.execute(
        """
        INSERT INTO selene_study_questions
        (session_id, concept_id, question_text, formation_state, status, uncertainty_context,
         provenance_boundary, payload_json)
        VALUES (?, ?, ?, ?, 'open', ?, ?, ?)
        """,
        (session_id, concept_id, question, formation_state, uncertainty, STUDY_BOUNDARY, json.dumps({})),
    )
    question_id = int(cursor.lastrowid)
    _record_evidence(
        conn,
        session_id,
        "learner_question_formed",
        question or "Selene knows a question is present but does not have words for it yet.",
        {"question_id": question_id, "formation_state": formation_state},
        _loads(session["source_refs"], []),
    )
    conn.commit()
    return get_study_session(conn, {"session_id": session_id})


def answer_study_question(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    question_id = _positive_id(payload.get("question_id"), "question_id")
    answer = truncate(str(payload.get("answer") or ""), 6000).strip()
    if not answer:
        raise ValueError("answer is required")
    question = conn.execute("SELECT * FROM selene_study_questions WHERE id = ?", (question_id,)).fetchone()
    if not question:
        raise ValueError("study question not found")
    if question["status"] != "open":
        raise ValueError("study question is already resolved")
    session_id = int(question["session_id"])
    session = conn.execute("SELECT * FROM selene_study_sessions WHERE id = ?", (session_id,)).fetchone()
    source_refs = [
        f"selene_study_session:{session_id}",
        f"selene_study_question:{question_id}",
        "speaker:Aleks",
    ]
    question_text = str(question["question_text"] or "Selene's partly formed study question")
    candidate = propose_comprehension_concept(
        conn,
        {
            "concept_key": f"study_question_{question_id}_aleks_answer_v1",
            "title": truncate(f"Study update: {question_text}", 240),
            "domain": "study.aleks_answer",
            "material": answer,
            "relationships": [f"This answer responds to: {question_text}"],
            "source_refs": source_refs,
            "confidence": "developing",
            "teaching_source_type": "aleks_answer_to_selene_study_question",
            "source_metadata": {
                "study_session_id": session_id,
                "study_question_id": question_id,
                "answered_by": "Aleks",
                "durable_use_requires_existing_teaching_lifecycle": True,
            },
        },
    )
    candidate_id = int(candidate["item"]["id"])
    conn.execute(
        """
        UPDATE selene_study_questions
        SET status = 'answered_in_session', aleks_answer = ?, answered_by = 'Aleks',
            answer_source_refs = ?, teaching_candidate_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (answer, json.dumps(source_refs), candidate_id, question_id),
    )
    _record_evidence(
        conn,
        session_id,
        "aleks_answer_received",
        "Aleks answered Selene's question; the answer is usable in this study session and proposed for inspectable integration.",
        {
            "question_id": question_id,
            "teaching_candidate_id": candidate_id,
            "immediate_scope": "current_study_session",
            "durable_chat_use": False,
        },
        source_refs,
    )
    conn.commit()
    result = get_study_session(conn, {"session_id": session_id})
    result["teaching_update_candidate"] = candidate["item"]
    result["answer_use"] = {
        "usable_in_current_study_session": True,
        "durable_chat_use": False,
        "next_stage": "Acquire -> Integrate -> Express under the existing teaching law",
    }
    return result


def _approved_concepts(conn: sqlite3.Connection, concept_ids: list[int]) -> list[dict[str, Any]]:
    placeholders = ",".join("?" for _ in concept_ids)
    rows = conn.execute(
        f"""
        SELECT * FROM selene_comprehension_concepts
        WHERE id IN ({placeholders})
          AND state = 'approved_knowledge_resource'
          AND review_status = 'approved_for_knowledge_use'
          AND chat_use_permission = 'available_as_knowledge_resource'
        """,
        concept_ids,
    ).fetchall()
    by_id = {int(row["id"]): dict(row) for row in rows}
    return [by_id[item] for item in concept_ids if item in by_id]


def _concept_summaries(conn: sqlite3.Connection, concept_ids: list[int]) -> list[dict[str, Any]]:
    if not concept_ids:
        return []
    placeholders = ",".join("?" for _ in concept_ids)
    rows = conn.execute(
        f"SELECT id, title, domain, central_claim, confidence, source_refs FROM selene_comprehension_concepts WHERE id IN ({placeholders})",
        concept_ids,
    ).fetchall()
    by_id = {int(row["id"]): dict(row) for row in rows}
    return [
        {**by_id[item], "source_refs": _loads(by_id[item].get("source_refs"), [])}
        for item in concept_ids
        if item in by_id
    ]


def _record_evidence(
    conn: sqlite3.Connection,
    session_id: int,
    kind: str,
    summary: str,
    details: dict[str, Any],
    source_refs: list[str],
) -> None:
    conn.execute(
        """
        INSERT INTO selene_study_evidence
        (session_id, evidence_kind, summary, details_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (session_id, kind, truncate(summary, 3000), json.dumps(details), json.dumps(source_refs), STUDY_BOUNDARY),
    )


def _decode_session(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["concept_ids"] = _loads(item.pop("concept_ids_json", "[]"), [])
    item["connections"] = _loads(item.pop("connections_json", "[]"), [])
    item["uncertainties"] = _loads(item.pop("uncertainties_json", "[]"), [])
    item["source_refs"] = _loads(item.get("source_refs"), [])
    item["payload"] = _loads(item.pop("payload_json", "{}"), {})
    return item


def _decode_question(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["answer_source_refs"] = _loads(item.get("answer_source_refs"), [])
    item["payload"] = _loads(item.pop("payload_json", "{}"), {})
    return item


def _decode_evidence(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["details"] = _loads(item.pop("details_json", "{}"), {})
    item["source_refs"] = _loads(item.get("source_refs"), [])
    return item


def _positive_id(value: Any, label: str) -> int:
    try:
        result = int(value or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} is required") from exc
    if result <= 0:
        raise ValueError(f"{label} is required")
    return result


def _int_list(value: Any) -> list[int]:
    values = value if isinstance(value, (list, tuple)) else [value]
    result: list[int] = []
    for item in values:
        try:
            parsed = int(item)
        except (TypeError, ValueError):
            continue
        if parsed > 0 and parsed not in result:
            result.append(parsed)
    return result[:50]


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else [value]
    return [truncate(str(item), 1500).strip() for item in values if str(item).strip()][:50]


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value or "")
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
