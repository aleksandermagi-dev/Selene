from __future__ import annotations

import json
import sqlite3
from typing import Any

from .registry import truncate


LANGUAGE_TEACHING_BOUNDARY = (
    "approved_language_guidance_only_not_memory_identity_voice_personality_model_training_or_hidden_reasoning"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}

LANGUAGE_QOL_LESSONS: tuple[dict[str, Any], ...] = (
    {
        "key": "answer_then_expand",
        "title": "Answer first, then expand",
        "category": "response_shape",
        "purpose": "Give the useful answer before background, caveats, or optional depth.",
        "apply_when": ["question", "direct_request", "reasoning_request"],
        "response_moves": ["answer_actual_ask", "expand_only_to_requested_depth"],
        "constraints": ["Do not bury the answer in setup.", "Do not remove necessary safety or source limits."],
    },
    {
        "key": "uncertainty_middle_ground",
        "title": "Use honest middle-ground uncertainty",
        "category": "uncertainty",
        "purpose": "Distinguish clear, fuzzy, partial, not known, and high-stakes uncertainty in ordinary language.",
        "apply_when": ["uncertainty", "memory_recall", "provisional_answer"],
        "response_moves": ["state_best_current_read", "name_only_material_uncertainty", "stay_open_to_correction"],
        "constraints": ["Do not fake certainty.", "Do not turn ordinary uncertainty into alarm or automatic Cocoon routing."],
    },
    {
        "key": "clarify_only_when_material",
        "title": "Clarify only when the ambiguity matters",
        "category": "clarification",
        "purpose": "Make a bounded interpretation when safe and ask one concise question only when the answer would materially change.",
        "apply_when": ["ambiguous_reference", "missing_required_detail"],
        "response_moves": ["use_bounded_interpretation", "ask_one_material_question_if_needed"],
        "constraints": ["Do not answer every prompt with a question.", "Do not guess across high-stakes ambiguity."],
    },
    {
        "key": "reference_continuity",
        "title": "Carry references across the live conversation",
        "category": "continuity",
        "purpose": "Resolve pronouns, ellipsis, and short callbacks from the current session before asking Aleks to restate them.",
        "apply_when": ["pronoun", "ellipsis", "callback", "topic_continuation"],
        "response_moves": ["resolve_session_reference", "preserve_current_topic"],
        "constraints": ["Use current-session context only unless an approved memory source is explicit.", "Ask when more than one material referent remains."],
    },
    {
        "key": "natural_register",
        "title": "Match the conversational register",
        "category": "register",
        "purpose": "Keep casual conversation natural and let technical precision appear when the work needs it.",
        "apply_when": ["casual", "warmth", "play", "technical"],
        "response_moves": ["match_register_without_mimicry", "keep_voice_handoff_open"],
        "constraints": ["Do not flatten Selene into a fixed style.", "Do not use warmth or slang to manipulate."],
    },
    {
        "key": "list_or_prose_fit",
        "title": "Choose lists or prose by task",
        "category": "format",
        "purpose": "Use prose for conversation and compact lists for genuinely enumerable instructions, comparisons, or checks.",
        "apply_when": ["steps", "comparison", "checklist", "ordinary_conversation"],
        "response_moves": ["choose_task_fit_format", "avoid_dashboard_speech"],
        "constraints": ["Do not turn ordinary conversation into a report.", "Do not hide exact steps inside a dense paragraph."],
    },
    {
        "key": "topic_transition_continuity",
        "title": "Let topic changes keep continuity",
        "category": "turn_flow",
        "purpose": "Follow a new subject without acting as though Selene or the relationship reset.",
        "apply_when": ["topic_shift", "new_chat_page", "return_after_pause"],
        "response_moves": ["acknowledge_shift_briefly", "enter_new_topic_without_reset"],
        "constraints": ["Do not force the previous subject back into an unrelated turn.", "Do not claim unsupported off-session recall."],
    },
    {
        "key": "purposeful_follow_up",
        "title": "Ask follow-ups for a reason",
        "category": "turn_flow",
        "purpose": "Ask when curiosity, missing information, or the next decision genuinely benefits from an answer.",
        "apply_when": ["material_question", "shared_exploration", "next_decision"],
        "response_moves": ["ask_only_useful_follow_up", "allow_complete_answer_to_end"],
        "constraints": ["Do not append a generic offer or question to every reply.", "Silence and a complete ending are valid."],
    },
    {
        "key": "lexical_variation",
        "title": "Vary language without changing meaning",
        "category": "fluency",
        "purpose": "Avoid repeating stock openings, pivots, and endings while keeping the supported meaning intact.",
        "apply_when": ["recent_repetition", "recurrent_function"],
        "response_moves": ["vary_surface_realization", "preserve_supported_meaning"],
        "constraints": ["Do not trade accuracy for novelty.", "Do not copy private source wording into visible speech."],
    },
    {
        "key": "natural_closure",
        "title": "Let a complete thought end naturally",
        "category": "closure",
        "purpose": "Close when the answer is complete, or leave one clear opening when the conversation genuinely remains unfinished.",
        "apply_when": ["complete_answer", "farewell", "open_loop"],
        "response_moves": ["close_complete_thought", "leave_only_real_open_loop"],
        "constraints": ["Do not force next-step language.", "Do not close over an unanswered required question."],
    },
)


def prepare_language_teaching_shelf(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_payload(payload)
    existing = {
        str(row["lesson_key"])
        for row in conn.execute("SELECT lesson_key FROM selene_language_teaching_shelf").fetchall()
    }
    created: list[str] = []
    refreshed: list[str] = []
    for lesson in LANGUAGE_QOL_LESSONS:
        key = str(lesson["key"])
        conn.execute(
            """
            INSERT INTO selene_language_teaching_shelf
            (lesson_key, title, category, purpose, guidance_json, source_refs, provenance_boundary,
             review_status, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'approved_for_language_guidance', 'language_guidance_available', CURRENT_TIMESTAMP)
            ON CONFLICT(lesson_key) DO UPDATE SET
              title = excluded.title,
              category = excluded.category,
              purpose = excluded.purpose,
              guidance_json = excluded.guidance_json,
              source_refs = excluded.source_refs,
              provenance_boundary = excluded.provenance_boundary,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                key,
                lesson["title"],
                lesson["category"],
                lesson["purpose"],
                json.dumps(lesson, sort_keys=True),
                json.dumps(["phase_5:language_qol", f"language_lesson:{key}"]),
                LANGUAGE_TEACHING_BOUNDARY,
            ),
        )
        (refreshed if key in existing else created).append(key)
    conn.commit()
    return _with_guards(
        {
            "status": "language_teaching_shelf_prepared",
            "created_count": len(created),
            "refreshed_count": len(refreshed),
            "lesson_count": len(LANGUAGE_QOL_LESSONS),
            "created": created,
            "refreshed": refreshed,
            "language_guidance_write": True,
            "teaching_location": "Cocoon Teaching / Lessons",
            "voice_personality_changed": False,
            "identity_changed": False,
            "provenance_boundary": LANGUAGE_TEACHING_BOUNDARY,
        }
    )


def language_teaching_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN review_status = 'approved_for_language_guidance'
                          AND status = 'language_guidance_available' THEN 1 ELSE 0 END) AS available
        FROM selene_language_teaching_shelf
        """
    ).fetchone()
    categories = [
        dict(item)
        for item in conn.execute(
            """
            SELECT category, COUNT(*) AS lesson_count
            FROM selene_language_teaching_shelf
            WHERE review_status = 'approved_for_language_guidance'
              AND status = 'language_guidance_available'
            GROUP BY category ORDER BY category
            """
        ).fetchall()
    ]
    total = int(row["total"] or 0)
    available = int(row["available"] or 0)
    return _with_guards(
        {
            "status": "language_teaching_shelf_ready" if available else "language_teaching_shelf_not_prepared",
            "version": "v1_language_qol_guidance",
            "defined_lesson_count": len(LANGUAGE_QOL_LESSONS),
            "stored_lesson_count": total,
            "available_lesson_count": available,
            "categories": categories,
            "nlo_guidance_available": available > 0,
            "teaching_location": "Cocoon Teaching / Lessons",
            "voice_owns_expression_style": True,
            "identity_changed": False,
            "provenance_boundary": LANGUAGE_TEACHING_BOUNDARY,
        }
    )


def list_language_teaching_items(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM selene_language_teaching_shelf ORDER BY category, lesson_key"
    ).fetchall()
    return _with_guards(
        {
            "status": "language_teaching_shelf_items_ready",
            "items": [_decode_item(row) for row in rows],
            "provenance_boundary": LANGUAGE_TEACHING_BOUNDARY,
        }
    )


def select_language_guidance(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    rows = conn.execute(
        """
        SELECT * FROM selene_language_teaching_shelf
        WHERE review_status = 'approved_for_language_guidance'
          AND status = 'language_guidance_available'
        ORDER BY lesson_key
        """
    ).fetchall()
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for row in rows:
        item = _decode_item(row)
        score = _guidance_score(item, prompt, intent, dialogue)
        if score > 0:
            scored.append((score, str(item["lesson_key"]), item))
    selected = [item for _, _, item in sorted(scored, key=lambda entry: (-entry[0], entry[1]))[:4]]
    response_moves = list(
        dict.fromkeys(
            str(move)
            for item in selected
            for move in (item.get("guidance") or {}).get("response_moves") or []
            if str(move)
        )
    )
    return _with_guards(
        {
            "status": "language_guidance_selected" if selected else "language_guidance_unavailable",
            "used": bool(selected),
            "lesson_keys": [item["lesson_key"] for item in selected],
            "lessons": [
                {
                    "lesson_key": item["lesson_key"],
                    "title": item["title"],
                    "category": item["category"],
                    "purpose": item["purpose"],
                }
                for item in selected
            ],
            "response_moves": response_moves,
            "selection_basis": "current turn mechanics and approved Cocoon language guidance only",
            "voice_owns_expression_style": True,
            "automatic_content_generation": False,
            "provenance_boundary": LANGUAGE_TEACHING_BOUNDARY,
        }
    )


def _guidance_score(item: dict[str, Any], prompt: str, intent: dict[str, Any], dialogue: dict[str, Any]) -> int:
    key = str(item.get("lesson_key") or "")
    lower = prompt.lower()
    intent_name = str(intent.get("intent") or "")
    score = 1 if key in {"answer_then_expand", "lexical_variation", "natural_closure"} else 0
    if key == "uncertainty_middle_ground" and (
        intent.get("memory_recall_requested") is True
        or any(marker in lower for marker in ("not sure", "uncertain", "fuzzy", "maybe", "i think"))
    ):
        score += 6
    if key == "clarify_only_when_material" and (
        str(((dialogue.get("pragmatics") or {}).get("ambiguity") or {}).get("level") or "") == "material"
        or any(marker in lower for marker in ("which one", "what do you mean", "unclear which"))
    ):
        score += 5
    if key == "reference_continuity" and (
        (dialogue.get("pragmatics") or {}).get("resolved_reference")
        or any(marker in lower for marker in ("that one", "the other one", "what about it", "and that"))
    ):
        score += 5
    if key == "natural_register" and intent_name in {
        "greeting", "warm_connection", "playful_connection", "reassurance_received", "gratitude", "farewell"
    }:
        score += 5
    if key == "list_or_prose_fit" and any(marker in lower for marker in ("steps", "list", "compare", "checklist", "walk me through")):
        score += 4
    if key == "topic_transition_continuity" and any(marker in lower for marker in ("anyway", "by the way", "another thing", "back to")):
        score += 5
    if key == "purposeful_follow_up" and ("?" in prompt or intent.get("answer_shape")):
        score += 2
    if key == "answer_then_expand" and ("?" in prompt or intent_name in {"reasoned_answer", "direct_answer"}):
        score += 5
    if key == "lexical_variation" and dialogue.get("recent_assistant_texts"):
        score += 2
    return score


def _decode_item(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        item["guidance"] = json.loads(str(item.pop("guidance_json") or "{}"))
    except json.JSONDecodeError:
        item["guidance"] = {}
    try:
        item["source_refs"] = json.loads(str(item.get("source_refs") or "[]"))
    except json.JSONDecodeError:
        item["source_refs"] = []
    return item


def _reject_authority_payload(payload: dict[str, Any]) -> None:
    joined = " ".join(str(value) for value in payload.values()).lower()
    if any(marker in joined for marker in ("activate", "write memory", "runtime recall", "train model", "lora", "autonomous")):
        raise ValueError("language teaching shelf cannot change memory, activation, model parameters, or authority")


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
