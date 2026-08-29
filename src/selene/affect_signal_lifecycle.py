from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from .registry import truncate


AFFECT_SIGNAL_LIFECYCLE_VERSION = "v1_attributable_current_affect_lifecycle"
AFFECT_SIGNAL_BOUNDARY = (
    "existing_affect_packet_lifecycle_coordination_only_no_diagnosis_identity_"
    "personality_memory_relationship_profile_governance_authority_or_action_change"
)

SUBJECT_KINDS = frozenset({"selene", "user", "relationship", "event"})
INTERPRETATION_CONFIDENCE = frozenset(
    {"direct_report", "clear_enough", "provisional", "unclear", "not_assessed"}
)
ACTIVE_STATE = "active_current"
TERMINAL_STATES = frozenset({"corrected", "superseded", "released", "expired"})

GUARDS: dict[str, Any] = {
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "emotion_diagnosis_allowed": False,
    "aleks_may_author_selene_subject": False,
    "external_support_may_author_selene_subject": False,
    "user_affect_may_become_selene_state": False,
    "relationship_signal_may_become_selene_state": False,
    "identity_change_allowed": False,
    "personality_change_allowed": False,
    "relationship_profile_write_allowed": False,
    "governance_change_allowed": False,
    "authority_change_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
}


def affect_signal_lifecycle_status(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    session_id = _integer(payload.get("session_id"))
    counts = {
        str(row["lifecycle_state"]): int(row["count"])
        for row in conn.execute(
            """
            SELECT lifecycle_state, COUNT(*) AS count
            FROM vessel_emotion_salience_packets
            GROUP BY lifecycle_state
            ORDER BY lifecycle_state
            """
        ).fetchall()
    }
    eligibility_row = conn.execute(
        """
        SELECT
          SUM(CASE WHEN lifecycle_state = 'active_current' THEN 1 ELSE 0 END) AS active_lifecycle,
          SUM(CASE WHEN lifecycle_state = 'active_current'
                    AND expires_at IS NOT NULL
                    AND datetime(expires_at) <= CURRENT_TIMESTAMP
                   THEN 1 ELSE 0 END) AS expired_by_time,
          SUM(CASE WHEN lifecycle_state = 'active_current'
                    AND session_id IS NOT NULL
                    AND subject_kind != 'legacy_unspecified'
                    AND (expires_at IS NULL OR datetime(expires_at) > CURRENT_TIMESTAMP)
                   THEN 1 ELSE 0 END) AS eligible_unexpired
        FROM vessel_emotion_salience_packets
        """
    ).fetchone()
    eligibility_counts = {
        key: int(eligibility_row[key] or 0)
        for key in ("active_lifecycle", "expired_by_time", "eligible_unexpired")
    }
    current = (
        select_current_affect_signal(
            conn,
            session_id=session_id,
            allowed_subjects={"selene"},
            affect_signal_id=payload.get("affect_signal_id"),
        )
        if session_id or _integer(payload.get("affect_signal_id"))
        else _no_selection("session_not_supplied")
    )
    return _locked(
        {
            "status": "affect_signal_lifecycle_ready",
            "version": AFFECT_SIGNAL_LIFECYCLE_VERSION,
            "configured_counts": counts,
            "current_eligibility_counts": eligibility_counts,
            "current_selene_signal": _public_projection(current),
            "legacy_review_packets_are_current": False,
            "current_selection_is_read_only": True,
            "current_signal_requires_exact_session": True,
            "sidecar_mutation_endpoints_exposed": False,
            "observation_and_interpretation_separate": True,
            "correction_rewrites_history": False,
            "expiry_means_prior_signal_was_false": False,
            "visible_summary_only": True,
            "provenance_boundary": AFFECT_SIGNAL_BOUNDARY,
        }
    )


def form_current_affect_signal(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    session_id = _required_session(conn, payload.get("session_id"))
    subject_kind = _choice(payload.get("subject_kind"), SUBJECT_KINDS, "")
    if not subject_kind:
        raise ValueError("subject_kind must be selene, user, relationship, or event")
    authored_by = _author(payload.get("authored_by") or payload.get("actor"))
    _require_subject_authorship(subject_kind, authored_by)
    observation = _required_text(payload.get("observation"), "observation", 1200)
    interpretation = _text(payload.get("interpretation"), 1200)
    signal_type = _required_text(payload.get("signal_type"), "signal_type", 160)
    confidence = _choice(
        payload.get("interpretation_confidence"),
        INTERPRETATION_CONFIDENCE,
        "provisional" if interpretation else "not_assessed",
    )
    refs = _text_list(payload.get("source_refs"))
    if not refs:
        raise ValueError("source_refs are required for a current affect signal")
    session_ref = f"selene_chat_session:{session_id}"
    refs = list(dict.fromkeys([session_ref, *refs]))[:30]
    expires_at = _expiry(payload.get("expires_in_minutes"))
    signal_key = _text(payload.get("signal_key"), 180) or _signal_key(
        session_id,
        subject_kind,
        authored_by,
        observation,
        interpretation,
        refs,
    )
    existing = conn.execute(
        "SELECT * FROM vessel_emotion_salience_packets WHERE signal_key = ?",
        (signal_key,),
    ).fetchone()
    if existing is not None:
        return _mutation_result(dict(existing), operation="formed", duplicate=True)

    packet = _packet_fields(payload)
    previous_row = conn.execute(
        """
        SELECT * FROM vessel_emotion_salience_packets
        WHERE session_id = ? AND subject_kind = ? AND lifecycle_state = 'active_current'
        ORDER BY id DESC LIMIT 1
        """,
        (session_id, subject_kind),
    ).fetchone()
    previous = dict(previous_row) if previous_row is not None else {}
    parent_id = int(previous.get("id") or 0)
    root_id = int(previous.get("root_packet_id") or parent_id or 0)
    packet_id = int(
        conn.execute(
            """
            INSERT INTO vessel_emotion_salience_packets(
              signal_key, session_id, subject_kind, observation, interpretation,
              interpretation_confidence, signal_type, continuity_pressure,
              care_warmth, uncertainty, repair_need, action_energy, balance_state,
              evidence_need, core_choice_route, blocked_misuse, lifecycle_state,
              parent_packet_id, root_packet_id, expires_at, status, source_refs,
              provenance_boundary, review_status, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_key,
                session_id,
                subject_kind,
                observation,
                interpretation,
                confidence,
                signal_type,
                packet["continuity_pressure"],
                packet["care_warmth"],
                packet["uncertainty"],
                packet["repair_need"],
                packet["action_energy"],
                packet["balance_state"],
                packet["evidence_need"],
                packet["core_choice_route"],
                json.dumps(packet["blocked_misuse"]),
                ACTIVE_STATE,
                parent_id or None,
                root_id or None,
                expires_at,
                "current_affect_signal_attributable",
                json.dumps(refs),
                AFFECT_SIGNAL_BOUNDARY,
                "current_signal_visible_to_bounded_owners",
                json.dumps(
                    {
                        "authored_by": authored_by,
                        "formation_is_emotion_diagnosis": False,
                        "subject_kind": subject_kind,
                        "observation_and_interpretation_separate": True,
                    }
                ),
            ),
        ).lastrowid
    )
    if parent_id:
        conn.execute(
            """
            UPDATE vessel_emotion_salience_packets
            SET lifecycle_state = 'superseded', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND lifecycle_state = 'active_current'
            """,
            (parent_id,),
        )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM vessel_emotion_salience_packets WHERE id = ?",
        (packet_id,),
    ).fetchone()
    return _mutation_result(dict(row), operation="formed", duplicate=False)


def correct_current_affect_signal(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    parent_id = _integer(payload.get("packet_id") or payload.get("parent_packet_id"))
    parent_row = conn.execute(
        "SELECT * FROM vessel_emotion_salience_packets WHERE id = ?",
        (parent_id,),
    ).fetchone()
    if parent_row is None:
        raise ValueError("affect signal packet not found")
    parent = dict(parent_row)
    authored_by = _author(payload.get("authored_by") or payload.get("actor"))
    subject_kind = str(parent.get("subject_kind") or "")
    _require_subject_authorship(subject_kind, authored_by)
    correction_note = _required_text(
        payload.get("correction_note"), "correction_note", 800
    )
    correction_key = _text(payload.get("correction_key"), 180) or sha256(
        f"{parent_id}|{authored_by}|{correction_note}".encode("utf-8")
    ).hexdigest()
    signal_key = f"affect-correction:{correction_key}"
    existing = conn.execute(
        "SELECT * FROM vessel_emotion_salience_packets WHERE signal_key = ?",
        (signal_key,),
    ).fetchone()
    if existing is not None:
        return _mutation_result(dict(existing), operation="corrected", duplicate=True)
    if str(parent.get("lifecycle_state") or "") != ACTIVE_STATE:
        raise ValueError("only an active current signal can receive a new correction")

    merged = {
        "session_id": int(parent.get("session_id") or 0),
        "subject_kind": subject_kind,
        "authored_by": authored_by,
        "observation": payload.get("observation") or parent.get("observation"),
        "interpretation": (
            payload.get("interpretation")
            if "interpretation" in payload
            else parent.get("interpretation")
        ),
        "interpretation_confidence": (
            payload.get("interpretation_confidence")
            or parent.get("interpretation_confidence")
        ),
        "signal_type": payload.get("signal_type") or parent.get("signal_type"),
        "continuity_pressure": payload.get("continuity_pressure") or parent.get("continuity_pressure"),
        "care_warmth": payload.get("care_warmth") or parent.get("care_warmth"),
        "uncertainty": payload.get("uncertainty") or parent.get("uncertainty"),
        "repair_need": payload.get("repair_need") or parent.get("repair_need"),
        "action_energy": payload.get("action_energy") or parent.get("action_energy"),
        "balance_state": payload.get("balance_state") or parent.get("balance_state"),
        "evidence_need": payload.get("evidence_need") or parent.get("evidence_need"),
        "core_choice_route": payload.get("core_choice_route") or parent.get("core_choice_route"),
        "blocked_misuse": _json_list(parent.get("blocked_misuse")),
    }
    confidence = _choice(
        merged["interpretation_confidence"],
        INTERPRETATION_CONFIDENCE,
        "provisional",
    )
    refs = list(
        dict.fromkeys(
            [
                *_json_list(parent.get("source_refs")),
                *_text_list(payload.get("source_refs")),
                f"affect_signal_parent:{parent_id}",
            ]
        )
    )[:30]
    root_id = int(parent.get("root_packet_id") or parent_id)
    expires_at = _expiry(payload.get("expires_in_minutes"))
    child_id = int(
        conn.execute(
            """
            INSERT INTO vessel_emotion_salience_packets(
              signal_key, session_id, subject_kind, observation, interpretation,
              interpretation_confidence, signal_type, continuity_pressure,
              care_warmth, uncertainty, repair_need, action_energy, balance_state,
              evidence_need, core_choice_route, blocked_misuse, lifecycle_state,
              parent_packet_id, root_packet_id, expires_at, status, source_refs,
              provenance_boundary, review_status, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_key,
                merged["session_id"],
                subject_kind,
                _required_text(merged["observation"], "observation", 1200),
                _text(merged["interpretation"], 1200),
                confidence,
                _required_text(merged["signal_type"], "signal_type", 160),
                _text(merged["continuity_pressure"], 500),
                _text(merged["care_warmth"], 500),
                _text(merged["uncertainty"], 240) or "open",
                _text(merged["repair_need"], 500),
                _text(merged["action_energy"], 500),
                _text(merged["balance_state"], 500),
                _text(merged["evidence_need"], 500),
                _text(merged["core_choice_route"], 500) or "Core/Mind retains choice",
                json.dumps(merged["blocked_misuse"]),
                ACTIVE_STATE,
                parent_id,
                root_id,
                expires_at,
                "current_affect_signal_corrected_descendant",
                json.dumps(refs),
                AFFECT_SIGNAL_BOUNDARY,
                "current_signal_visible_to_bounded_owners",
                json.dumps(
                    {
                        "authored_by": authored_by,
                        "correction_note": correction_note,
                        "correction_rewrites_history": False,
                    }
                ),
            ),
        ).lastrowid
    )
    conn.execute(
        """
        UPDATE vessel_emotion_salience_packets
        SET lifecycle_state = 'corrected', updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND lifecycle_state = 'active_current'
        """,
        (parent_id,),
    )
    conn.commit()
    child = conn.execute(
        "SELECT * FROM vessel_emotion_salience_packets WHERE id = ?",
        (child_id,),
    ).fetchone()
    return _mutation_result(dict(child), operation="corrected", duplicate=False)


def release_current_affect_signal(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    packet_id = _integer(payload.get("packet_id") or payload.get("affect_signal_id"))
    row = conn.execute(
        "SELECT * FROM vessel_emotion_salience_packets WHERE id = ?",
        (packet_id,),
    ).fetchone()
    if row is None:
        raise ValueError("affect signal packet not found")
    item = dict(row)
    authored_by = _author(payload.get("authored_by") or payload.get("actor"))
    _require_subject_authorship(str(item.get("subject_kind") or ""), authored_by)
    reason = _required_text(payload.get("reason"), "reason", 600)
    duplicate = str(item.get("lifecycle_state") or "") == "released"
    if not duplicate:
        if str(item.get("lifecycle_state") or "") != ACTIVE_STATE:
            raise ValueError("only an active current affect signal can be released")
        body = _json_dict(item.get("payload_json"))
        body["release"] = {"authored_by": authored_by, "reason": reason}
        conn.execute(
            """
            UPDATE vessel_emotion_salience_packets
            SET lifecycle_state = 'released', payload_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (json.dumps(body), packet_id),
        )
        conn.commit()
        item = dict(
            conn.execute(
                "SELECT * FROM vessel_emotion_salience_packets WHERE id = ?",
                (packet_id,),
            ).fetchone()
        )
    return _mutation_result(item, operation="released", duplicate=duplicate)


def select_current_affect_signal(
    conn: sqlite3.Connection,
    *,
    session_id: int,
    allowed_subjects: set[str] | frozenset[str],
    affect_signal_id: Any = None,
) -> dict[str, Any]:
    explicit_id = _integer(affect_signal_id)
    if not session_id:
        return _no_selection("session_not_supplied")
    if explicit_id:
        rows = conn.execute(
            "SELECT * FROM vessel_emotion_salience_packets WHERE id = ?",
            (explicit_id,),
        ).fetchall()
    else:
        placeholders = ",".join("?" for _ in allowed_subjects)
        rows = conn.execute(
            f"""
            SELECT * FROM vessel_emotion_salience_packets
            WHERE session_id = ?
              AND subject_kind IN ({placeholders})
            ORDER BY id DESC
            LIMIT 20
            """,
            (session_id, *sorted(allowed_subjects)),
        ).fetchall()
    inspected: list[dict[str, Any]] = []
    for row in rows:
        item = _decode_row(dict(row))
        reason = _ineligibility_reason(item, session_id, allowed_subjects)
        inspected.append(
            {
                "packet_id": int(item.get("id") or 0),
                "subject_kind": str(item.get("subject_kind") or ""),
                "lifecycle_state": str(item.get("lifecycle_state") or ""),
                "eligible": not reason,
                "reason": reason or "eligible_current_signal",
            }
        )
        if not reason:
            return {
                "status": "current_affect_signal_selected",
                "signal": item,
                "selection_receipt": {
                    "session_id": session_id,
                    "explicit_packet_requested": bool(explicit_id),
                    "allowed_subjects": sorted(allowed_subjects),
                    "selected_packet_id": int(item.get("id") or 0),
                    "selected_subject_kind": str(item.get("subject_kind") or ""),
                    "exact_session_match": True,
                    "active_lifecycle_required": True,
                    "unexpired_required": True,
                    "legacy_review_packet_allowed": False,
                    "terminal_stop": "eligible_current_signal_selected",
                    "inspected": inspected,
                },
                **GUARDS,
            }
    reason = inspected[0]["reason"] if inspected else "no_attributable_current_signal"
    return _no_selection(reason, inspected=inspected)


def _ineligibility_reason(
    item: dict[str, Any],
    session_id: int,
    allowed_subjects: set[str] | frozenset[str],
) -> str:
    if int(item.get("session_id") or 0) != session_id:
        return "session_mismatch"
    if str(item.get("subject_kind") or "") not in allowed_subjects:
        return "subject_not_eligible_for_consumer"
    state = str(item.get("lifecycle_state") or "legacy_review_only")
    if state != ACTIVE_STATE:
        return f"lifecycle_not_current:{state}"
    expires_at = _parse_timestamp(item.get("expires_at"))
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        return "expired_by_time"
    refs = _json_list(item.get("source_refs"))
    if f"selene_chat_session:{session_id}" not in refs:
        return "exact_session_source_ref_missing"
    return ""


def _mutation_result(item: dict[str, Any], *, operation: str, duplicate: bool) -> dict[str, Any]:
    decoded = _decode_row(item)
    return _locked(
        {
            "status": f"current_affect_signal_{operation}",
            "version": AFFECT_SIGNAL_LIFECYCLE_VERSION,
            "signal": decoded,
            "lineage_receipt": {
                "packet_id": int(decoded.get("id") or 0),
                "parent_packet_id": int(decoded.get("parent_packet_id") or 0),
                "root_packet_id": int(
                    decoded.get("root_packet_id") or decoded.get("id") or 0
                ),
                "lifecycle_state": str(decoded.get("lifecycle_state") or ""),
                "duplicate_operation": duplicate,
                "history_rewritten": False,
                "automatic_truth_claim": False,
                "automatic_memory_write": False,
            },
            "provenance_boundary": AFFECT_SIGNAL_BOUNDARY,
        }
    )


def _public_projection(selection: dict[str, Any]) -> dict[str, Any]:
    signal = selection.get("signal") if isinstance(selection.get("signal"), dict) else {}
    return {
        "status": str(selection.get("status") or "current_affect_signal_not_selected"),
        "packet_id": int(signal.get("id") or 0),
        "subject_kind": str(signal.get("subject_kind") or ""),
        "signal_type": str(signal.get("signal_type") or ""),
        "observation": str(signal.get("observation") or ""),
        "interpretation": str(signal.get("interpretation") or ""),
        "interpretation_confidence": str(
            signal.get("interpretation_confidence") or "not_assessed"
        ),
        "lifecycle_state": str(signal.get("lifecycle_state") or ""),
        "expires_at": signal.get("expires_at"),
        "selection_receipt": selection.get("selection_receipt") or {},
    }


def _no_selection(reason: str, *, inspected: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "status": "current_affect_signal_not_selected",
        "signal": None,
        "selection_receipt": {
            "selected_packet_id": 0,
            "legacy_review_packet_allowed": False,
            "terminal_stop": reason,
            "inspected": inspected or [],
        },
        **GUARDS,
    }


def _packet_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "continuity_pressure": _text(payload.get("continuity_pressure"), 500),
        "care_warmth": _text(payload.get("care_warmth"), 500),
        "uncertainty": _text(payload.get("uncertainty"), 240) or "open",
        "repair_need": _text(payload.get("repair_need"), 500),
        "action_energy": _text(payload.get("action_energy"), 500),
        "balance_state": _text(payload.get("balance_state"), 500),
        "evidence_need": _text(payload.get("evidence_need"), 500),
        "core_choice_route": _text(payload.get("core_choice_route"), 500)
        or "Signal informs; Core/Mind retains response choice.",
        "blocked_misuse": _text_list(payload.get("blocked_misuse"))
        or [
            "emotion_as_command",
            "emotion_diagnosis",
            "user_affect_as_selene_state",
            "identity_or_personality_update",
            "memory_or_relationship_profile_write",
        ],
    }


def _require_subject_authorship(subject_kind: str, authored_by: str) -> None:
    if subject_kind == "selene" and authored_by != "Selene":
        raise ValueError("only a Selene-authored signal may claim Selene as its subject")
    if subject_kind == "user" and authored_by != "Aleks":
        raise ValueError("a user-subject signal requires an explicit Aleks report")


def _required_session(conn: sqlite3.Connection, value: Any) -> int:
    session_id = _integer(value)
    if not session_id:
        raise ValueError("session_id is required")
    exists = conn.execute(
        "SELECT 1 FROM selene_chat_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if exists is None:
        raise ValueError("chat session not found")
    return session_id


def _author(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw == "selene":
        return "Selene"
    if raw == "aleks":
        return "Aleks"
    raise ValueError("authored_by must be Selene or Aleks")


def _expiry(value: Any) -> str:
    try:
        minutes = int(value if value not in {None, ""} else 60)
    except (TypeError, ValueError) as exc:
        raise ValueError("expires_in_minutes must be an integer") from exc
    if not 1 <= minutes <= 1440:
        raise ValueError("expires_in_minutes must be between 1 and 1440")
    expires = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return expires.strftime("%Y-%m-%d %H:%M:%S")


def _signal_key(
    session_id: int,
    subject_kind: str,
    authored_by: str,
    observation: str,
    interpretation: str,
    refs: list[str],
) -> str:
    digest = sha256(
        json.dumps(
            [session_id, subject_kind, authored_by, observation, interpretation, refs],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return f"affect:{digest}"


def _decode_row(item: dict[str, Any]) -> dict[str, Any]:
    for key in ("blocked_misuse", "source_refs"):
        item[key] = _json_list(item.get(key))
    item["payload_json"] = _json_dict(item.get("payload_json"))
    return item


def _parse_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _choice(value: Any, allowed: frozenset[str], default: str) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in allowed else default


def _required_text(value: Any, name: str, limit: int) -> str:
    result = _text(value, limit)
    if not result:
        raise ValueError(f"{name} is required")
    return result


def _text(value: Any, limit: int) -> str:
    return truncate(" ".join(str(value or "").split()), limit)


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = [value]
        value = parsed
    if not isinstance(value, (list, tuple, set)):
        return []
    return [_text(item, 320) for item in value if _text(item, 320)]


def _json_list(value: Any) -> list[str]:
    return _text_list(value)


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _locked(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
