from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from typing import Any

from .comprehension_integration import propose_comprehension_concept
from .language_formation import build_semantic_frame, realize_semantic_frame
from .metacognition import inspect_metacognition
from .native_language_organ import realize_native_language
from .registry import truncate
from .voice_module import generate_voice_preview


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
NOTE_KINDS = {"notice", "connection", "idea", "uncertainty", "revisit"}
CLARIFICATION_STATES = {
    "not_needed",
    "unclear",
    "question_forming",
    "question_ready",
    "answered",
    "clarified_for_now",
    "reopened",
}
CLARIFICATION_ACTIONS = {
    "needs_clarification",
    "develop_question",
    "form_question",
    "clarified_for_now",
    "reopen",
}
LEARNING_COMPASS_STATES = {
    "ready_to_explore",
    "exploring",
    "question_ready",
    "answer_received",
    "integrating",
    "still_unclear",
    "connected_for_now",
    "reopened",
    "needs_representation",
    "needs_prerequisite",
    "return_later",
}
LEARNING_COMPASS_ACTIONS = {
    "ready_to_explore",
    "integrating",
    "still_unclear",
    "connected_for_now",
    "reopen",
    "needs_representation",
    "needs_prerequisite",
    "return_later",
}
PONDERING_STATES = {
    "active",
    "needs_representation",
    "needs_prerequisite",
    "question_forming",
    "waiting_for_answer",
    "return_later",
    "integrated_for_now",
    "reopened",
}
OPEN_PONDERING_STATES = PONDERING_STATES - {"integrated_for_now"}
REPRESENTATION_KINDS = {
    "objects",
    "tallies",
    "groups",
    "place_value",
    "spatial_object",
    "sentence_roles",
    "sentence_transform",
}

LANGUAGE_FOUNDATION_COMPASS_GOALS: tuple[dict[str, Any], ...] = (
    {
        "goal_key": "language_foundation_sentence_scene_20260801",
        "display_order": 1,
        "title": "L1 · See the meaning roles inside a sentence",
        "curriculum_band": "Language foundation",
        "subject_domains": ["sentence formation", "meaning roles"],
        "concept_keys": ["language_lesson:sentence_core_from_meaning_roles"],
        "already_connected": (
            "The reviewed foundation separates who or what a clause concerns from the action, state, description, or relationship being expressed."
        ),
        "next_connection": (
            "Build a short sentence from visible role cards, then reconstruct the same supported scene in a different word order only when the meaning still fits."
        ),
        "why_it_matters": (
            "A visible meaning map gives grammar something stable to organize and makes awkward wording easier to repair without changing the idea."
        ),
        "suggested_activity": (
            "Place one participant, one action or state, and an optional affected object into role cards; read the resulting sentence and name only what each card contributes."
        ),
    },
    {
        "goal_key": "language_foundation_number_time_negation_20260801",
        "display_order": 2,
        "title": "L2 · Change form while tracking number, time, and negation",
        "curriculum_band": "Language foundation",
        "subject_domains": ["agreement", "tense", "negation"],
        "concept_keys": [
            "language_lesson:noun_verb_number_agreement",
            "language_lesson:tense_tracks_time_relation",
            "language_lesson:negation_preserves_scope",
        ],
        "already_connected": (
            "The reviewed foundation keeps the participant and action visible while grammatical form tracks singular or plural, event time, and exactly what is denied."
        ),
        "next_connection": (
            "Compare two visible forms of one supplied sentence and identify which feature changed, which meaning stayed, and whether the new form makes a different claim."
        ),
        "why_it_matters": (
            "This supports correction, recall, planning, and ordinary conversation without letting tense or negation silently distort the supported content."
        ),
        "suggested_activity": (
            "Start with a short present statement, then deliberately choose one change—plural, past, future, or negative—and inspect the before and after forms."
        ),
    },
    {
        "goal_key": "language_foundation_detail_relation_word_fit_20260801",
        "display_order": 3,
        "title": "L3 · Add detail and relationships without drifting",
        "curriculum_band": "Language foundation",
        "subject_domains": ["modifiers", "conjunctions", "word fit"],
        "concept_keys": [
            "language_lesson:modifier_attachment_and_specificity",
            "language_lesson:conjunction_matches_relation",
            "language_lesson:lexical_sense_and_word_pair_fit",
        ],
        "already_connected": (
            "The reviewed foundation treats descriptions, connectors, and word choices as meaning-bearing decisions rather than decoration."
        ),
        "next_connection": (
            "Attach one supported detail to its intended role and connect a second clause with the relationship that actually holds."
        ),
        "why_it_matters": (
            "This is the bridge from correct sentence cores to natural, precise language that can explain and connect ideas without source parroting."
        ),
        "suggested_activity": (
            "Add one modifier or a second clause to a short sentence, compare the result with the original, and remove anything the supplied scene does not support."
        ),
    },
)

PRIOR_F1_LEA_GOALS: tuple[dict[str, Any], ...] = (
    {
        "goal_key": "f1_lea_place_value_comparison_subtraction_20260801",
        "display_order": 1,
        "title": "Connect place value, comparison, and subtraction",
        "curriculum_band": "F1",
        "subject_domains": ["number sense", "operations"],
        "prompt_fragment": "A box contains 34 beads. Another box contains 29 beads.",
        "concept_keys": [
            "curriculum_f1_base_ten_place_value_v1",
            "curriculum_f1_number_representation_comparison_v1",
            "curriculum_f1_subtraction_relationship_v1",
            "curriculum_f1_equality_inverse_operations_v1",
        ],
        "already_connected": (
            "Selene recalled that ten ones compose one ten and that a digit's value depends on its place."
        ),
        "next_connection": (
            "Use tens and ones to compare 34 and 29, state which quantity is larger, and verify the difference with subtraction."
        ),
        "why_it_matters": (
            "This connects number representation to comparison, exact arithmetic, and later multi-step reasoning."
        ),
        "suggested_activity": (
            "Use two small quantities represented as tens and ones, compare them aloud, then check the comparison by subtraction."
        ),
        "lea_observation": (
            "The response supplied relevant base-ten knowledge but did not apply it to the requested comparison or subtraction check."
        ),
    },
    {
        "goal_key": "f1_lea_equal_shares_ordered_steps_20260801",
        "display_order": 2,
        "title": "Explain equal shares through reasoning and ordered steps",
        "curriculum_band": "F1",
        "subject_domains": ["fractions", "ordered procedures"],
        "prompt_fragment": "A square sandwich must be shared equally among four people.",
        "concept_keys": [
            "curriculum_f1_equal_shares_whole_v1",
            "curriculum_f1_ordered_algorithm_v1",
        ],
        "already_connected": (
            "Selene identified equal size as the reason four pieces can be called fourths of the same whole."
        ),
        "next_connection": (
            "Describe the four equal shares and give a clear sequence another person could follow to make them."
        ),
        "why_it_matters": (
            "This joins fraction meaning to reproducible instructions, spatial reasoning, and later algorithms."
        ),
        "suggested_activity": (
            "Describe two cuts of a square sandwich, then explain how the result can be checked for four equal shares."
        ),
        "lea_observation": (
            "The fraction principle appeared, but the requested ordered procedure and full application remained incomplete."
        ),
    },
    {
        "goal_key": "f1_lea_capacity_contained_amount_20260801",
        "display_order": 3,
        "title": "Distinguish container capacity from the amount currently inside",
        "curriculum_band": "F1",
        "subject_domains": ["equal groups", "measurement", "capacity"],
        "prompt_fragment": "Three shelves hold four jars each. One jar contains 250 milliliters.",
        "concept_keys": [
            "curriculum_f1_equal_groups_repeated_addition_v1",
            "curriculum_f1_capacity_contained_volume_v1",
            "curriculum_f1_liter_milliliter_scale_v1",
        ],
        "already_connected": (
            "Selene recalled that capacity belongs to the container under a stated fill boundary."
        ),
        "next_connection": (
            "Solve the equal-groups total while keeping jar capacity separate from the liquid amount currently inside one jar."
        ),
        "why_it_matters": (
            "This supports mixed mathematical and measurement questions without collapsing distinct quantities into one answer."
        ),
        "suggested_activity": (
            "Count jars in equal groups, then compare a jar's maximum capacity with a smaller measured amount placed inside it."
        ),
        "lea_observation": (
            "The response named capacity but did not complete the jar total or explicitly distinguish capacity from current contents."
        ),
    },
    {
        "goal_key": "f1_lea_graph_evidence_fair_rule_20260801",
        "display_order": 4,
        "title": "Use graph evidence to reconsider a rule fairly",
        "curriculum_band": "F1",
        "subject_domains": ["data literacy", "fairness", "civic reasoning"],
        "prompt_fragment": "A class graph says seven students chose apples and four chose oranges.",
        "concept_keys": [
            "curriculum_f1_categorical_graph_representation_v1",
            "curriculum_f1_graph_interpretation_answerability_v1",
            "curriculum_f1_rules_purpose_context_v1",
            "curriculum_f1_fairness_consistent_relevance_v1",
            "curriculum_f1_respectful_disagreement_rule_revision_v1",
        ],
        "already_connected": (
            "Selene recalled that rules, laws, customs, and agreements have different meanings and sources of authority."
        ),
        "next_connection": (
            "State what the graph supports, what it cannot establish, and why group size alone does not justify silencing the smaller group."
        ),
        "why_it_matters": (
            "This joins evidence limits to fair participation, reasoned disagreement, and later historical or civic source analysis."
        ),
        "suggested_activity": (
            "Use a small preference graph, list only its supported claims, then examine a proposed classroom rule against its purpose and effects."
        ),
        "lea_observation": (
            "The response gave generic authority definitions rather than applying the graph evidence and fairness principles to the rule."
        ),
    },
)


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
    note_count = int(conn.execute("SELECT COUNT(*) FROM selene_study_notes").fetchone()[0])
    clarification_count = int(
        conn.execute(
            "SELECT COUNT(*) FROM selene_study_notes WHERE clarification_state IN ('unclear', 'question_forming', 'question_ready', 'reopened')"
        ).fetchone()[0]
    )
    pondering_count = int(conn.execute("SELECT COUNT(*) FROM selene_study_pondering_threads").fetchone()[0])
    open_pondering_count = int(
        conn.execute(
            "SELECT COUNT(*) FROM selene_study_pondering_threads WHERE state != 'integrated_for_now'"
        ).fetchone()[0]
    )
    representation_attempt_count = int(
        conn.execute("SELECT COUNT(*) FROM selene_study_representation_attempts").fetchone()[0]
    )
    compass_row = conn.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN state = 'connected_for_now' THEN 1 ELSE 0 END) AS connected,
               SUM(CASE WHEN state != 'connected_for_now' THEN 1 ELSE 0 END) AS open
        FROM selene_learning_compass_goals
        """
    ).fetchone()
    eligible_materials = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM selene_comprehension_concepts
            WHERE state = 'approved_knowledge_resource'
              AND review_status = 'approved_for_knowledge_use'
              AND chat_use_permission = 'available_as_knowledge_resource'
            """
        ).fetchone()[0]
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
            "note_count": note_count,
            "open_clarification_count": clarification_count,
            "pondering_thread_count": pondering_count,
            "open_pondering_count": open_pondering_count,
            "representation_attempt_count": representation_attempt_count,
            "learning_compass_goal_count": int(compass_row["total"] or 0),
            "learning_compass_open_count": int(compass_row["open"] or 0),
            "learning_compass_connected_count": int(compass_row["connected"] or 0),
            "eligible_material_count": eligible_materials,
            "question_answer_rule": (
                "Aleks's answer is attributable session knowledge immediately and becomes a source-labeled "
                "teaching update candidate for durable use."
            ),
            "durable_use_rule": "Durable Chat use still follows the inspectable comprehension and teaching lifecycle.",
            "pondering_rule": (
                "Confusion may remain open, change representation, identify a prerequisite, or return later without becoming a failure."
            ),
            "simulation_rule": "Representation attempts are bounded visible learning artifacts, not hidden reasoning or world action.",
            "review_status": "status_only",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def list_open_study_attention(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 100), 300))
    note_rows = conn.execute(
        """
        SELECT notes.*, sessions.title AS session_title, sessions.status AS session_status,
               questions.question_text AS linked_question_text,
               questions.status AS linked_question_status
        FROM selene_study_notes notes
        JOIN selene_study_sessions sessions ON sessions.id = notes.session_id
        LEFT JOIN selene_study_questions questions ON questions.id = notes.linked_question_id
        WHERE notes.clarification_state IN ('unclear', 'question_forming', 'question_ready', 'reopened')
        ORDER BY notes.updated_at DESC, notes.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    question_rows = conn.execute(
        """
        SELECT questions.*, sessions.title AS session_title, sessions.status AS session_status
        FROM selene_study_questions questions
        JOIN selene_study_sessions sessions ON sessions.id = questions.session_id
        WHERE questions.status = 'open'
          AND NOT EXISTS (
            SELECT 1 FROM selene_study_notes notes WHERE notes.linked_question_id = questions.id
          )
        ORDER BY questions.updated_at DESC, questions.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    pondering_rows = conn.execute(
        """
        SELECT threads.*, sessions.title AS session_title, sessions.status AS session_status
        FROM selene_study_pondering_threads threads
        JOIN selene_study_sessions sessions ON sessions.id = threads.session_id
        WHERE threads.state != 'integrated_for_now'
        ORDER BY threads.updated_at DESC, threads.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    items = [
        {**_decode_note(row), "attention_type": "clarification_note"}
        for row in note_rows
    ]
    items.extend(
        {**_decode_question(row), "attention_type": "direct_question"}
        for row in question_rows
    )
    items.extend(
        {**_decode_pondering_thread(row), "attention_type": "pondering_thread"}
        for row in pondering_rows
    )
    items.sort(key=lambda item: (str(item.get("updated_at") or ""), int(item.get("id") or 0)), reverse=True)
    items = items[:limit]
    return _with_guards(
        {
            "status": "open_study_attention_ready",
            "items": items,
            "open_count": len(items),
            "persistence_rule": "Open clarification remains visible until answered or explicitly clear for now.",
            "answered_items_remain_in_session_history": True,
            "review_status": "status_only",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def list_learning_compass(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 100), 300))
    rows = conn.execute(
        """
        SELECT goals.*, sessions.title AS linked_session_title,
               questions.question_text AS latest_question_text,
               questions.status AS latest_question_status
        FROM selene_learning_compass_goals goals
        LEFT JOIN selene_study_sessions sessions ON sessions.id = goals.linked_session_id
        LEFT JOIN selene_study_questions questions ON questions.id = goals.latest_question_id
        ORDER BY CASE WHEN goals.state = 'connected_for_now' THEN 1 ELSE 0 END ASC,
                 goals.display_order ASC, goals.id ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    items = [_decode_learning_compass_goal(row) for row in rows]
    return _with_guards(
        {
            "status": "selene_learning_compass_ready",
            "items": items,
            "goal_count": len(items),
            "open_count": sum(item["state"] != "connected_for_now" for item in items),
            "connected_count": sum(item["state"] == "connected_for_now" for item in items),
            "governing_rule": (
                "An answer is teaching input. Understanding is shown by connection, application, and honest "
                "reflection, not by performed agreement."
            ),
            "connection_rule": (
                "Connections are recorded only when noticed; an empty connection field is never displayed as a deficiency."
            ),
            "grading_used": False,
            "deadlines_used": False,
            "performance_required": False,
            "review_status": "descriptive_learning_guidance",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def seed_prior_f1_lea_learning_compass(
    conn: sqlite3.Connection, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    del payload
    created: list[str] = []
    already_present: list[str] = []
    unavailable: list[dict[str, Any]] = []
    for specification in PRIOR_F1_LEA_GOALS:
        existing = conn.execute(
            "SELECT id FROM selene_learning_compass_goals WHERE goal_key = ?",
            (specification["goal_key"],),
        ).fetchone()
        if existing:
            already_present.append(str(specification["goal_key"]))
            continue

        evidence_row = conn.execute(
            """
            SELECT messages.id AS message_id, messages.session_id, messages.content,
                   sessions.title AS session_title
            FROM selene_chat_messages messages
            JOIN selene_chat_sessions sessions ON sessions.id = messages.session_id
            WHERE messages.role = 'user' AND messages.content LIKE ?
            ORDER BY messages.id DESC
            LIMIT 1
            """,
            (f"%{specification['prompt_fragment']}%",),
        ).fetchone()
        if not evidence_row:
            unavailable.append({"goal_key": specification["goal_key"], "reason": "LEA source turn not found"})
            continue
        response_row = conn.execute(
            """
            SELECT id, content FROM selene_chat_messages
            WHERE session_id = ? AND role = 'selene' AND id > ?
            ORDER BY id ASC LIMIT 1
            """,
            (int(evidence_row["session_id"]), int(evidence_row["message_id"])),
        ).fetchone()
        if not response_row:
            unavailable.append({"goal_key": specification["goal_key"], "reason": "LEA response not found"})
            continue

        concept_rows = conn.execute(
            f"""
            SELECT id, concept_key FROM selene_comprehension_concepts
            WHERE concept_key IN ({','.join('?' for _ in specification['concept_keys'])})
              AND state = 'approved_knowledge_resource'
              AND review_status = 'approved_for_knowledge_use'
              AND chat_use_permission = 'available_as_knowledge_resource'
            """,
            tuple(specification["concept_keys"]),
        ).fetchall()
        concept_by_key = {str(row["concept_key"]): int(row["id"]) for row in concept_rows}
        concept_ids = [concept_by_key[key] for key in specification["concept_keys"] if key in concept_by_key]
        if len(concept_ids) != len(specification["concept_keys"]):
            unavailable.append({"goal_key": specification["goal_key"], "reason": "approved prerequisites not available"})
            continue

        source_refs = [
            "learning_evidence_activity:2026-08-01:f1",
            f"selene_chat_session:{int(evidence_row['session_id'])}",
            f"selene_chat_message:{int(evidence_row['message_id'])}",
            f"selene_chat_message:{int(response_row['id'])}",
        ]
        evidence = {
            "activity_date": "2026-08-01",
            "activity_kind": "gentle_learning_evidence_activity",
            "observation": specification["lea_observation"],
            "interpretation": "This is a next useful connection, not a failure or grade.",
            "source_session_title": str(evidence_row["session_title"] or ""),
            "pass_fail_judgment": False,
            "anxiety_or_performance_pressure_intended": False,
        }
        conn.execute(
            """
            INSERT INTO selene_learning_compass_goals
            (goal_key, display_order, title, curriculum_band, subject_domains_json,
             state, already_connected, next_connection, why_it_matters,
             suggested_activity, concept_ids_json, source_refs, evidence_json,
             source_kind, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, 'ready_to_explore', ?, ?, ?, ?, ?, ?, ?,
                    'learning_evidence_activity', ?)
            """,
            (
                specification["goal_key"],
                int(specification["display_order"]),
                specification["title"],
                specification["curriculum_band"],
                json.dumps(specification["subject_domains"]),
                specification["already_connected"],
                specification["next_connection"],
                specification["why_it_matters"],
                specification["suggested_activity"],
                json.dumps(concept_ids),
                json.dumps(source_refs),
                json.dumps(evidence),
                STUDY_BOUNDARY,
            ),
        )
        created.append(str(specification["goal_key"]))
    conn.commit()
    result = list_learning_compass(conn)
    result.update(
        {
            "status": "prior_f1_lea_learning_compass_seeded",
            "created": created,
            "already_present": already_present,
            "unavailable": unavailable,
            "idempotent": True,
        }
    )
    return result


def seed_language_foundation_learning_compass(
    conn: sqlite3.Connection, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Prepare prerequisite-first language directions from already reviewed guidance.

    These are guided Study directions, not conclusions drawn from a live test.
    Their source concepts must already have completed the language teaching
    lifecycle and be available as reviewed resources.
    """
    del payload
    created: list[str] = []
    already_present: list[str] = []
    unavailable: list[dict[str, Any]] = []
    reordered_existing_goal_count = int(
        conn.execute(
            """
            UPDATE selene_learning_compass_goals
            SET display_order = display_order + 10, updated_at = CURRENT_TIMESTAMP
            WHERE source_kind = 'learning_evidence_activity' AND display_order < 10
            """
        ).rowcount
    )
    for specification in LANGUAGE_FOUNDATION_COMPASS_GOALS:
        existing = conn.execute(
            "SELECT id FROM selene_learning_compass_goals WHERE goal_key = ?",
            (specification["goal_key"],),
        ).fetchone()
        if existing:
            already_present.append(str(specification["goal_key"]))
            continue

        concept_rows = conn.execute(
            f"""
            SELECT id, concept_key, source_refs FROM selene_comprehension_concepts
            WHERE concept_key IN ({','.join('?' for _ in specification['concept_keys'])})
              AND state = 'approved_knowledge_resource'
              AND review_status = 'approved_for_knowledge_use'
              AND chat_use_permission = 'available_as_knowledge_resource'
            """,
            tuple(specification["concept_keys"]),
        ).fetchall()
        concept_by_key = {str(row["concept_key"]): row for row in concept_rows}
        if any(key not in concept_by_key for key in specification["concept_keys"]):
            unavailable.append(
                {
                    "goal_key": specification["goal_key"],
                    "reason": "reviewed language prerequisites not available",
                }
            )
            continue
        concept_ids = [int(concept_by_key[key]["id"]) for key in specification["concept_keys"]]
        source_refs = list(
            dict.fromkeys(
                [
                    "guided_study_activity:language_foundations:2026-08-01",
                    *[
                        source
                        for key in specification["concept_keys"]
                        for source in _loads(concept_by_key[key]["source_refs"], [])
                        if str(source)
                    ],
                ]
            )
        )[:100]
        evidence = {
            "activity_date": "2026-08-01",
            "activity_kind": "gentle_guided_language_foundation",
            "observation": (
                "This direction comes from the reviewed prerequisite sequence. It is prepared for exploration, "
                "not inferred from a performance score."
            ),
            "interpretation": (
                "Visible reconstruction or transformation may offer learning evidence later; needing another form "
                "or prerequisite remains a normal study state."
            ),
            "pass_fail_judgment": False,
            "anxiety_or_performance_pressure_intended": False,
            "synthetic_check_only": True,
        }
        conn.execute(
            """
            INSERT INTO selene_learning_compass_goals
            (goal_key, display_order, title, curriculum_band, subject_domains_json,
             state, already_connected, next_connection, why_it_matters,
             suggested_activity, concept_ids_json, source_refs, evidence_json,
             source_kind, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, 'ready_to_explore', ?, ?, ?, ?, ?, ?, ?,
                    'guided_language_foundation', ?)
            """,
            (
                specification["goal_key"],
                int(specification["display_order"]),
                specification["title"],
                specification["curriculum_band"],
                json.dumps(specification["subject_domains"]),
                specification["already_connected"],
                specification["next_connection"],
                specification["why_it_matters"],
                specification["suggested_activity"],
                json.dumps(concept_ids),
                json.dumps(source_refs),
                json.dumps(evidence),
                STUDY_BOUNDARY,
            ),
        )
        created.append(str(specification["goal_key"]))
    conn.commit()
    result = list_learning_compass(conn)
    result.update(
        {
            "status": "language_foundation_learning_compass_seeded",
            "created": created,
            "already_present": already_present,
            "unavailable": unavailable,
            "reordered_existing_goal_count": reordered_existing_goal_count,
            "idempotent": True,
            "live_assessment_performed": False,
            "teaching_material_mutated": False,
        }
    )
    return result


def start_learning_compass_goal(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    goal_id = _positive_id((payload or {}).get("goal_id"), "goal_id")
    row = conn.execute("SELECT * FROM selene_learning_compass_goals WHERE id = ?", (goal_id,)).fetchone()
    if not row:
        raise ValueError("learning compass goal not found")
    goal = _decode_learning_compass_goal(row)
    concept_ids = _int_list(goal.get("concept_ids"))
    if not concept_ids:
        raise ValueError("learning compass goal has no approved study material")
    session = start_study_session(
        conn,
        {
            "concept_ids": concept_ids,
            "title": f"Learning Compass: {goal['title']}",
            "focus": goal["next_connection"],
            "compass_goal_id": goal_id,
        },
    )
    session_id = int(session["item"]["id"])
    state = "reopened" if goal["state"] == "connected_for_now" else "exploring"
    _update_learning_compass_row(
        conn,
        goal_id,
        state=state,
        linked_session_id=session_id,
        event="study_session_opened_from_learning_compass",
        event_detail="A normal Study session was opened for this visible learning goal.",
    )
    conn.commit()
    result = list_learning_compass(conn)
    result.update({"status": "learning_compass_study_started", "session": get_study_session(conn, {"session_id": session_id})})
    return result


def update_learning_compass_goal(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    goal_id = _positive_id(payload.get("goal_id"), "goal_id")
    action = str(payload.get("action") or "").strip()
    if action not in LEARNING_COMPASS_ACTIONS:
        raise ValueError("unsupported learning compass action")
    row = conn.execute("SELECT * FROM selene_learning_compass_goals WHERE id = ?", (goal_id,)).fetchone()
    if not row:
        raise ValueError("learning compass goal not found")
    goal = _decode_learning_compass_goal(row)
    reflection = truncate(str(payload.get("reflection") or ""), 4000).strip()
    remaining = truncate(str(payload.get("remaining_unclear") or ""), 4000).strip()
    question_without_words = payload.get("question_without_words") is True

    if action == "connected_for_now" and not reflection:
        raise ValueError("a visible reflection is required before marking a goal connected for now")
    if action == "still_unclear" and not remaining and not question_without_words:
        raise ValueError("say what remains unclear or mark that the question has no words yet")

    state = "reopened" if action == "reopen" else action
    if question_without_words and not remaining:
        remaining = "Something still does not fit yet, but the question does not have words yet."
    values: dict[str, Any] = {"state": state}
    if reflection:
        values["selene_reflection"] = reflection
    if action == "connected_for_now":
        values["remaining_unclear"] = ""
    elif remaining:
        values["remaining_unclear"] = remaining
    _update_learning_compass_row(
        conn,
        goal_id,
        event=f"learning_compass_{state}",
        event_detail=(reflection or remaining or "The goal state was deliberately updated without a performance judgment."),
        **values,
    )
    conn.commit()
    result = list_learning_compass(conn)
    result.update({"status": "learning_compass_goal_updated", "updated_goal_id": goal_id})
    return result


def create_pondering_thread(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    session_id = _positive_id(payload.get("session_id"), "session_id")
    session = conn.execute("SELECT * FROM selene_study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        raise ValueError("study session not found")
    state = str(payload.get("state") or "active").strip()
    if state not in PONDERING_STATES:
        raise ValueError("unsupported pondering state")
    title = truncate(str(payload.get("title") or session["focus"] or session["title"]), 300).strip()
    if not title:
        raise ValueError("a visible pondering-thread title is required")
    compass_goal_id = int(payload.get("compass_goal_id") or session["compass_goal_id"] or 0) or None
    if compass_goal_id is not None and not conn.execute(
        "SELECT 1 FROM selene_learning_compass_goals WHERE id = ?", (compass_goal_id,)
    ).fetchone():
        raise ValueError("learning compass goal not found")
    question_id = int(payload.get("question_id") or 0) or None
    if question_id is not None and not conn.execute(
        "SELECT 1 FROM selene_study_questions WHERE id = ? AND session_id = ?", (question_id, session_id)
    ).fetchone():
        raise ValueError("pondering question must belong to this study session")
    current_fit = truncate(str(payload.get("current_fit") or ""), 4000).strip()
    missing_bridge = truncate(str(payload.get("missing_bridge") or ""), 4000).strip()
    prerequisite_needed = truncate(str(payload.get("prerequisite_needed") or ""), 2000).strip()
    revisit_cue = truncate(str(payload.get("revisit_cue") or ""), 2000).strip()
    preferences = [item for item in _text_list(payload.get("representation_preferences")) if item in REPRESENTATION_KINDS]
    if state == "integrated_for_now" and not current_fit:
        raise ValueError("a visible reflection is required before connecting a pondering thread for now")
    source_refs = list(dict.fromkeys([
        *_loads(session["source_refs"], []),
        f"selene_study_session:{session_id}",
        *([f"selene_learning_compass_goal:{compass_goal_id}"] if compass_goal_id else []),
        *([f"selene_study_question:{question_id}"] if question_id else []),
    ]))[:100]
    thread_key = "ponder-" + sha256(f"{session_id}|{compass_goal_id}|{question_id}|{title}".encode("utf-8")).hexdigest()[:20]
    conn.execute(
        """
        INSERT INTO selene_study_pondering_threads
        (thread_key, session_id, compass_goal_id, question_id, title, state, current_fit,
         missing_bridge, prerequisite_needed, representation_preferences_json, revisit_cue,
         source_refs, provenance_boundary, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(thread_key) DO UPDATE SET
          state = excluded.state, current_fit = excluded.current_fit,
          missing_bridge = excluded.missing_bridge,
          prerequisite_needed = excluded.prerequisite_needed,
          representation_preferences_json = excluded.representation_preferences_json,
          revisit_cue = excluded.revisit_cue, updated_at = CURRENT_TIMESTAMP
        """,
        (
            thread_key, session_id, compass_goal_id, question_id, title, state, current_fit,
            missing_bridge, prerequisite_needed, json.dumps(preferences), revisit_cue,
            json.dumps(source_refs), STUDY_BOUNDARY, json.dumps({"visible_deliberation": True}),
        ),
    )
    thread_id = int(conn.execute(
        "SELECT id FROM selene_study_pondering_threads WHERE thread_key = ?", (thread_key,)
    ).fetchone()[0])
    _record_evidence(
        conn, session_id, "pondering_thread_held",
        "Selene kept a visible learning thread open without treating incompleteness as failure.",
        {"thread_id": thread_id, "state": state, "missing_bridge": missing_bridge}, source_refs,
    )
    if compass_goal_id and state in {"needs_representation", "needs_prerequisite", "return_later"}:
        _update_learning_compass_row(
            conn, compass_goal_id, state=state,
            remaining_unclear=(missing_bridge or prerequisite_needed or revisit_cue),
            event=f"learning_compass_{state}",
            event_detail="The activity remains available while its learning conditions are adjusted.",
        )
    conn.commit()
    result = get_study_session(conn, {"session_id": session_id})
    result.update({"status": "study_pondering_thread_ready", "updated_thread_id": thread_id})
    return result


def update_pondering_thread(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    thread_id = _positive_id(payload.get("thread_id"), "thread_id")
    row = conn.execute("SELECT * FROM selene_study_pondering_threads WHERE id = ?", (thread_id,)).fetchone()
    if not row:
        raise ValueError("pondering thread not found")
    state = str(payload.get("state") or row["state"]).strip()
    if state not in PONDERING_STATES:
        raise ValueError("unsupported pondering state")
    current_fit = truncate(str(payload.get("current_fit", row["current_fit"]) or ""), 4000).strip()
    missing_bridge = truncate(str(payload.get("missing_bridge", row["missing_bridge"]) or ""), 4000).strip()
    prerequisite_needed = truncate(
        str(payload.get("prerequisite_needed", row["prerequisite_needed"]) or ""), 2000
    ).strip()
    revisit_cue = truncate(str(payload.get("revisit_cue", row["revisit_cue"]) or ""), 2000).strip()
    preferences = (
        [item for item in _text_list(payload.get("representation_preferences")) if item in REPRESENTATION_KINDS]
        if "representation_preferences" in payload else _loads(row["representation_preferences_json"], [])
    )
    if state == "integrated_for_now" and not current_fit:
        raise ValueError("a visible reflection is required before connecting a pondering thread for now")
    conn.execute(
        """
        UPDATE selene_study_pondering_threads
        SET state = ?, current_fit = ?, missing_bridge = ?, prerequisite_needed = ?,
            representation_preferences_json = ?, revisit_cue = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (state, current_fit, missing_bridge, prerequisite_needed, json.dumps(preferences), revisit_cue, thread_id),
    )
    session_id = int(row["session_id"])
    _record_evidence(
        conn, session_id, "pondering_thread_updated",
        "The open learning thread changed state through visible reflection.",
        {"thread_id": thread_id, "state": state, "current_fit": current_fit, "missing_bridge": missing_bridge},
        _loads(row["source_refs"], []),
    )
    compass_goal_id = int(row["compass_goal_id"] or 0)
    if compass_goal_id:
        compass_state = (
            "connected_for_now" if state == "integrated_for_now"
            else "reopened" if state == "active"
            else state
        )
        if compass_state in LEARNING_COMPASS_STATES:
            values: dict[str, Any] = {"state": compass_state}
            if current_fit:
                values["selene_reflection"] = current_fit
            if state == "integrated_for_now":
                values["remaining_unclear"] = ""
            else:
                values["remaining_unclear"] = missing_bridge or prerequisite_needed or revisit_cue
            _update_learning_compass_row(
                conn, compass_goal_id, event=f"pondering_thread_{state}",
                event_detail="A visible pondering thread updated this learning direction.", **values,
            )
    conn.commit()
    result = get_study_session(conn, {"session_id": session_id})
    result.update({"status": "study_pondering_thread_updated", "updated_thread_id": thread_id})
    return result


def try_study_representation(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    thread_id = _positive_id(payload.get("thread_id"), "thread_id")
    thread = conn.execute("SELECT * FROM selene_study_pondering_threads WHERE id = ?", (thread_id,)).fetchone()
    if not thread:
        raise ValueError("pondering thread not found")
    kind = str(payload.get("representation_kind") or "").strip()
    if kind not in REPRESENTATION_KINDS:
        raise ValueError("unsupported representation kind")
    input_state, operations, output_state = _simulate_representation(kind, payload)
    observation = truncate(str(payload.get("observation") or ""), 3000).strip()
    source_refs = list(dict.fromkeys([
        *_loads(thread["source_refs"], []), f"selene_study_pondering_thread:{thread_id}"
    ]))[:100]
    cursor = conn.execute(
        """
        INSERT INTO selene_study_representation_attempts
        (thread_id, session_id, representation_kind, input_json, operations_json,
         output_json, observation, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            thread_id, int(thread["session_id"]), kind, json.dumps(input_state), json.dumps(operations),
            json.dumps(output_state), observation, json.dumps(source_refs), STUDY_BOUNDARY,
        ),
    )
    attempt_id = int(cursor.lastrowid)
    preferences = list(dict.fromkeys([*_loads(thread["representation_preferences_json"], []), kind]))
    conn.execute(
        "UPDATE selene_study_pondering_threads SET representation_preferences_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(preferences), thread_id),
    )
    _record_evidence(
        conn, int(thread["session_id"]), "representation_attempted",
        "Selene tried a bounded visible representation to inspect the concept from another form.",
        {"thread_id": thread_id, "attempt_id": attempt_id, "representation_kind": kind}, source_refs,
    )
    conn.commit()
    result = get_study_session(conn, {"session_id": int(thread["session_id"])})
    result.update({"status": "study_representation_attempt_ready", "attempt_id": attempt_id})
    return result


def list_study_materials(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 200), 500))
    rows = conn.execute(
        """
        SELECT id, title, domain, central_claim, confidence, source_refs, updated_at
        FROM selene_comprehension_concepts
        WHERE state = 'approved_knowledge_resource'
          AND review_status = 'approved_for_knowledge_use'
          AND chat_use_permission = 'available_as_knowledge_resource'
        ORDER BY domain ASC, title ASC, id ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["source_refs"] = _loads(item.get("source_refs"), [])
        item["study_eligible"] = True
        items.append(item)
    return _with_guards(
        {
            "status": "selene_study_materials_ready",
            "items": items,
            "eligible_count": len(items),
            "eligibility_rule": "approved, Chat-eligible knowledge only",
            "review_status": "status_only",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def list_study_sessions(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 50), 200))
    rows = conn.execute(
        """
        SELECT sessions.*,
               (
                 SELECT COUNT(*)
                 FROM selene_study_questions questions
                 WHERE questions.session_id = sessions.id AND questions.status = 'open'
               ) AS open_question_count
             , (
                 SELECT COUNT(*)
                 FROM selene_study_notes notes
                 WHERE notes.session_id = sessions.id
                   AND notes.clarification_state IN ('unclear', 'question_forming', 'question_ready', 'reopened')
               ) AS open_clarification_count
        FROM selene_study_sessions sessions
        ORDER BY sessions.updated_at DESC, sessions.id DESC
        LIMIT ?
        """,
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
    note_rows = conn.execute(
        "SELECT * FROM selene_study_notes WHERE session_id = ? ORDER BY id ASC", (session_id,)
    ).fetchall()
    pondering_rows = conn.execute(
        "SELECT * FROM selene_study_pondering_threads WHERE session_id = ? ORDER BY id ASC", (session_id,)
    ).fetchall()
    pondering_threads = []
    for pondering_row in pondering_rows:
        thread = _decode_pondering_thread(pondering_row)
        attempt_rows = conn.execute(
            "SELECT * FROM selene_study_representation_attempts WHERE thread_id = ? ORDER BY id ASC",
            (int(pondering_row["id"]),),
        ).fetchall()
        thread["representation_attempts"] = [_decode_representation_attempt(item) for item in attempt_rows]
        pondering_threads.append(thread)
    session = _decode_session(row)
    session["concepts"] = _concept_summaries(conn, session["concept_ids"])
    return _with_guards(
        {
            "status": "selene_study_session_ready",
            "item": session,
            "questions": [_decode_question(item) for item in question_rows],
            "notes": [_decode_note(item) for item in note_rows],
            "pondering_threads": pondering_threads,
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
    compass_goal_id = int(payload.get("compass_goal_id") or 0) or None
    if compass_goal_id is not None and not conn.execute(
        "SELECT 1 FROM selene_learning_compass_goals WHERE id = ?", (compass_goal_id,)
    ).fetchone():
        raise ValueError("learning compass goal not found")
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
        (session_key, title, focus, status, concept_ids_json, source_refs, provenance_boundary,
         payload_json, compass_goal_id)
        VALUES (?, ?, ?, 'active', ?, ?, ?, ?, ?)
        ON CONFLICT(session_key) DO UPDATE SET
          status = 'active', focus = excluded.focus, compass_goal_id = excluded.compass_goal_id,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            key,
            title,
            focus,
            json.dumps(concept_ids),
            json.dumps(source_refs),
            STUDY_BOUNDARY,
            json.dumps({}),
            compass_goal_id,
        ),
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
        {"concept_ids": concept_ids, "focus": focus, "compass_goal_id": compass_goal_id},
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
    compass_goal_id = int(current["compass_goal_id"] or 0)
    if compass_goal_id:
        compass_values: dict[str, Any] = {}
        if understanding:
            compass_values["selene_reflection"] = understanding
        if uncertainties:
            compass_values["state"] = "still_unclear"
            compass_values["remaining_unclear"] = "\n".join(uncertainties)
        elif status == "active":
            compass_values["state"] = "integrating"
        if connections:
            goal_row = conn.execute(
                "SELECT noticed_connections_json FROM selene_learning_compass_goals WHERE id = ?",
                (compass_goal_id,),
            ).fetchone()
            previous_connections = _loads(goal_row[0], []) if goal_row else []
            compass_values["noticed_connections_json"] = list(
                dict.fromkeys([*_text_list(previous_connections), *_text_list(connections)])
            )[:100]
        if compass_values:
            _update_learning_compass_row(
                conn,
                compass_goal_id,
                event="learning_compass_study_reflection_updated",
                event_detail="Selene's visible Study reflection updated this goal without grading it.",
                **compass_values,
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
    compass_goal_id = int(session["compass_goal_id"] or 0)
    if compass_goal_id:
        _update_learning_compass_row(
            conn,
            compass_goal_id,
            state="question_ready",
            latest_question_id=question_id,
            remaining_unclear=(uncertainty or question),
            event="learning_compass_question_formed",
            event_detail=(question or "A question is present but does not have words yet."),
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
    conn.execute(
        """
        UPDATE selene_study_notes
        SET clarification_state = 'answered', updated_at = CURRENT_TIMESTAMP
        WHERE linked_question_id = ?
        """,
        (question_id,),
    )
    compass_goal_id = int(session["compass_goal_id"] or 0)
    if compass_goal_id:
        _update_learning_compass_row(
            conn,
            compass_goal_id,
            state="answer_received",
            latest_question_id=question_id,
            event="learning_compass_answer_received",
            event_detail=(
                "Aleks answered the linked Study question. The answer is teaching input; understanding is not assumed."
            ),
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


def form_study_note(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    session_id = _positive_id(payload.get("session_id"), "session_id")
    session_row = conn.execute("SELECT * FROM selene_study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session_row:
        raise ValueError("study session not found")
    session = _decode_session(session_row)
    concept_id = int(payload.get("concept_id") or (session["concept_ids"][0] if session["concept_ids"] else 0))
    concepts = _approved_concepts(conn, [concept_id]) if concept_id else []
    if not concepts or concept_id not in set(session["concept_ids"]):
        raise ValueError("study note concept_id must be approved and belong to this study session")
    concept = _decode_study_concept(concepts[0])
    attention_mode = str(payload.get("attention_mode") or "anything").strip()
    if attention_mode not in {"anything", "clarification"}:
        raise ValueError("attention_mode must be anything or clarification")

    existing = {
        str(row[0])
        for row in conn.execute(
            "SELECT meaning_summary FROM selene_study_notes WHERE session_id = ?",
            (session_id,),
        ).fetchall()
    }
    candidates = _study_attention_candidates(session, concept)
    if attention_mode == "clarification":
        candidates = [item for item in candidates if item["clarification_state"] == "unclear"]
    selected = next((item for item in candidates if item["meaning_summary"] not in existing), None)
    if not selected:
        return _with_guards(
            {
                "status": (
                    "study_clarification_signal_not_present"
                    if attention_mode == "clarification"
                    else "no_new_study_note_signal"
                ),
                "created": False,
                "message": (
                    "No explicit uncertainty is recorded yet; Selene will not invent one."
                    if attention_mode == "clarification"
                    else "Everything currently available on this material is already represented in the notepad."
                ),
                "item": None,
                "session": get_study_session(conn, {"session_id": session_id}),
                "review_status": "status_only",
                "provenance_boundary": STUDY_BOUNDARY,
            }
        )

    source_refs = list(
        dict.fromkeys(
            [
                *_text_list(session.get("source_refs")),
                *_text_list(concept.get("source_refs")),
                f"selene_study_session:{session_id}",
                f"selene_comprehension_concept:{concept_id}",
            ]
        )
    )[:100]
    clarification_needed = selected["clarification_state"] == "unclear"
    metacognition = inspect_metacognition(
        conn,
        {
            "prompt": selected["meaning_summary"],
            "candidate_text": selected["meaning_summary"],
            "comprehension_context": {
                "understanding_state": "developing" if clarification_needed else "approved_material_under_study",
                "comprehension_handshake": {"required": clarification_needed},
                "knowledge_context": {"concept_id": concept_id, "title": concept.get("title")},
            },
            "unknowns": [selected["source_text"]] if clarification_needed else [],
            "source_refs": source_refs,
        },
        record_run=True,
        commit=False,
    )
    nlo = realize_native_language(
        conn,
        {
            "prompt": (
                f"What needs clarification while studying {concept.get('title')}?"
                if clarification_needed
                else f"What stands out while studying {concept.get('title')}?"
            ),
            "content_seed": selected["meaning_summary"],
            "communicative_intent": "reflection",
            "certainty": "developing" if clarification_needed else "grounded_in_approved_material",
            "affect": "curious" if selected["note_kind"] in {"connection", "uncertainty"} else "attentive",
            "response_depth": "short",
            "source_refs": source_refs,
        },
    )
    voice = generate_voice_preview(
        conn,
        {
            "prompt": f"Study note about {concept.get('title')}",
            "route": "ask_aleks" if clarification_needed else "answer_now",
            "meaning_text": nlo.get("candidate_text") or selected["meaning_summary"],
            "voice_category": (nlo.get("voice_handoff") or {}).get("suggested_category") or "",
            "context_summary": f"Selene is deliberately studying {concept.get('title')}.",
            "expression_guidance": {
                "study_note": True,
                "meaning_must_be_preserved": True,
                "expression_guidance_changes_meaning": False,
            },
        },
    )
    note_text = truncate(
        str(voice.get("candidate_text") or nlo.get("candidate_text") or selected["meaning_summary"]),
        4000,
    ).strip()
    cursor = conn.execute(
        """
        INSERT INTO selene_study_notes
        (session_id, concept_id, note_kind, meaning_summary, note_text, source_field,
         clarification_state, metacognition_json, language_json, voice_json,
         source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            concept_id,
            selected["note_kind"],
            selected["meaning_summary"],
            note_text,
            selected["source_field"],
            selected["clarification_state"],
            json.dumps(_visible_metacognition(metacognition)),
            json.dumps(_visible_language(nlo)),
            json.dumps(_visible_voice(voice)),
            json.dumps(source_refs),
            STUDY_BOUNDARY,
        ),
    )
    note_id = int(cursor.lastrowid)
    _record_evidence(
        conn,
        session_id,
        "study_note_formed",
        "Selene formed a visible source-linked Study note.",
        {
            "note_id": note_id,
            "note_kind": selected["note_kind"],
            "clarification_state": selected["clarification_state"],
            "source_field": selected["source_field"],
            "memory_write": False,
        },
        source_refs,
    )
    conn.commit()
    return _with_guards(
        {
            "status": "selene_study_note_formed",
            "created": True,
            "item": _decode_note(conn.execute("SELECT * FROM selene_study_notes WHERE id = ?", (note_id,)).fetchone()),
            "session": get_study_session(conn, {"session_id": session_id}),
            "review_status": "selene_owned_working_study_note",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def update_study_note_clarification(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    note_id = _positive_id(payload.get("note_id"), "note_id")
    action = str(payload.get("action") or "").strip()
    if action not in CLARIFICATION_ACTIONS:
        raise ValueError("unsupported study note clarification action")
    row = conn.execute("SELECT * FROM selene_study_notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        raise ValueError("study note not found")
    note = _decode_note(row)
    current_state = str(note["clarification_state"])
    target_state = {
        "needs_clarification": "unclear",
        "develop_question": "question_forming",
        "form_question": "question_ready",
        "clarified_for_now": "clarified_for_now",
        "reopen": "reopened",
    }[action]
    allowed_from = {
        "needs_clarification": {"not_needed", "clarified_for_now"},
        "develop_question": {"unclear", "reopened"},
        "form_question": {"unclear", "question_forming", "reopened"},
        "clarified_for_now": {"unclear", "question_forming", "question_ready", "reopened"},
        "reopen": {"answered", "clarified_for_now"},
    }[action]
    if current_state not in allowed_from:
        raise ValueError(f"cannot {action.replace('_', ' ')} from {current_state}")

    linked_question_id = note.get("linked_question_id")
    if action == "form_question":
        formation_state = str(payload.get("formation_state") or "ready")
        asked = ask_study_question(
            conn,
            {
                "session_id": note["session_id"],
                "concept_id": note.get("concept_id"),
                "question_text": payload.get("question_text") or "",
                "uncertainty_context": payload.get("uncertainty_context") or note["meaning_summary"],
                "formation_state": formation_state,
            },
        )
        linked_question_id = max(int(item["id"]) for item in asked["questions"])

    conn.execute(
        """
        UPDATE selene_study_notes
        SET clarification_state = ?, linked_question_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (target_state, linked_question_id, note_id),
    )
    _record_evidence(
        conn,
        int(note["session_id"]),
        "study_clarification_state_changed",
        "A Study note moved through Selene's visible clarification path.",
        {
            "note_id": note_id,
            "from": current_state,
            "to": target_state,
            "linked_question_id": linked_question_id,
        },
        _text_list(note.get("source_refs")),
    )
    conn.commit()
    return _with_guards(
        {
            "status": "study_note_clarification_updated",
            "item": _decode_note(conn.execute("SELECT * FROM selene_study_notes WHERE id = ?", (note_id,)).fetchone()),
            "session": get_study_session(conn, {"session_id": int(note["session_id"])}),
            "review_status": "selene_owned_working_study_note",
            "provenance_boundary": STUDY_BOUNDARY,
        }
    )


def _study_attention_candidates(session: dict[str, Any], concept: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    def add(
        note_kind: str,
        source_field: str,
        source_text: Any,
        lead: str,
        *,
        clarification_state: str = "not_needed",
        relevance: float,
    ) -> None:
        value = truncate(str(source_text or ""), 2200).strip()
        if not value:
            return
        candidates.append(
            {
                "note_kind": note_kind if note_kind in NOTE_KINDS else "notice",
                "source_field": source_field,
                "source_text": value,
                "meaning_summary": truncate(f"{lead}: {value}", 2600),
                "clarification_state": (
                    clarification_state if clarification_state in CLARIFICATION_STATES else "not_needed"
                ),
                "relevance": max(0.0, min(float(relevance), 1.0)),
            }
        )

    for value in _text_list(session.get("uncertainties")):
        add(
            "uncertainty",
            "session_uncertainty",
            value,
            "Something here still feels unresolved",
            clarification_state="unclear",
            relevance=0.98,
        )
    for value in _text_list(session.get("connections")):
        add("connection", "session_connection", value, "I keep connecting this to", relevance=0.95)
    for value in _text_list(concept.get("relationships")):
        add("connection", "relationship", value, "This connection stands out", relevance=0.92)
    for value in _text_list(concept.get("limits")):
        add("revisit", "limit", value, "This boundary feels worth keeping visible", relevance=0.88)
    for value in _text_list(concept.get("counterexamples")):
        add("notice", "counterexample", value, "This contrast catches my attention", relevance=0.84)
    for value in _text_list(concept.get("principles")):
        add("notice", "principle", value, "This principle feels central", relevance=0.80)
    for value in _text_list(concept.get("examples")):
        add("connection", "example", value, "This example makes the idea concrete", relevance=0.76)
    add("notice", "central_claim", concept.get("central_claim"), "This is the center of it", relevance=0.72)
    return candidates


def _decode_study_concept(item: dict[str, Any]) -> dict[str, Any]:
    decoded = dict(item)
    for key in ("principles_json", "relationships_json", "examples_json", "counterexamples_json", "limits_json"):
        decoded[key.removesuffix("_json")] = _loads(decoded.get(key), [])
    decoded["source_refs"] = _loads(decoded.get("source_refs"), [])
    decoded["payload"] = _loads(decoded.get("payload_json"), {})
    return decoded


def _visible_metacognition(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": result.get("run_id"),
        "status": result.get("status"),
        "fit_state": result.get("fit_state"),
        "recommended_action": result.get("recommended_action"),
        "sufficiency_state": result.get("sufficiency_state"),
        "observations": result.get("observations") or [],
        "hidden_chain_of_thought_exposed": False,
    }


def _visible_language(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": result.get("run_id"),
        "status": result.get("status"),
        "mode": result.get("mode"),
        "delivery": result.get("delivery") or "selene_study_notepad",
        "decision": result.get("decision") or "visible_after_deliberate_study_invitation",
        "revision": result.get("revision") or {},
        "suggested_voice_category": (result.get("voice_handoff") or {}).get("suggested_category"),
        "hidden_chain_of_thought_exposed": False,
    }


def _visible_voice(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "voice_category": result.get("voice_category"),
        "voice_confidence": result.get("voice_confidence"),
        "generation_source": result.get("generation_source"),
        "nlo_meaning_preserved": result.get("nlo_meaning_preserved") is True,
    }


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


def _update_learning_compass_row(
    conn: sqlite3.Connection,
    goal_id: int,
    *,
    event: str,
    event_detail: str,
    **values: Any,
) -> None:
    row = conn.execute(
        "SELECT evidence_json FROM selene_learning_compass_goals WHERE id = ?",
        (goal_id,),
    ).fetchone()
    if not row:
        raise ValueError("learning compass goal not found")
    allowed = {
        "state",
        "selene_reflection",
        "remaining_unclear",
        "noticed_connections_json",
        "linked_session_id",
        "latest_question_id",
    }
    updates = {key: value for key, value in values.items() if key in allowed}
    if "state" in updates and str(updates["state"]) not in LEARNING_COMPASS_STATES:
        raise ValueError("unsupported learning compass state")
    if "noticed_connections_json" in updates and not isinstance(updates["noticed_connections_json"], str):
        updates["noticed_connections_json"] = json.dumps(updates["noticed_connections_json"])

    evidence = _loads(row["evidence_json"], {})
    history = evidence.get("updates") if isinstance(evidence.get("updates"), list) else []
    history.append(
        {
            "event": truncate(event, 160),
            "detail": truncate(event_detail, 1200),
            "performance_judgment": False,
        }
    )
    evidence["updates"] = history[-100:]
    updates["evidence_json"] = json.dumps(evidence)
    assignments = ", ".join(f"{key} = ?" for key in updates)
    conn.execute(
        f"UPDATE selene_learning_compass_goals SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (*updates.values(), goal_id),
    )


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


def _decode_learning_compass_goal(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["subject_domains"] = _loads(item.pop("subject_domains_json", "[]"), [])
    item["noticed_connections"] = _loads(item.pop("noticed_connections_json", "[]"), [])
    item["concept_ids"] = _loads(item.pop("concept_ids_json", "[]"), [])
    item["source_refs"] = _loads(item.get("source_refs"), [])
    item["evidence"] = _loads(item.pop("evidence_json", "{}"), {})
    return item


def _decode_pondering_thread(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["representation_preferences"] = _loads(item.pop("representation_preferences_json", "[]"), [])
    item["source_refs"] = _loads(item.get("source_refs"), [])
    item["payload"] = _loads(item.pop("payload_json", "{}"), {})
    return item


def _decode_representation_attempt(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["input"] = _loads(item.pop("input_json", "{}"), {})
    item["operations"] = _loads(item.pop("operations_json", "[]"), [])
    item["output"] = _loads(item.pop("output_json", "{}"), {})
    item["source_refs"] = _loads(item.get("source_refs"), [])
    return item


def _decode_question(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["answer_source_refs"] = _loads(item.get("answer_source_refs"), [])
    item["payload"] = _loads(item.pop("payload_json", "{}"), {})
    return item


def _simulate_representation(kind: str, payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    if kind in {"sentence_roles", "sentence_transform"}:
        return _simulate_sentence_representation(kind, payload)
    if kind in {"objects", "tallies", "groups", "place_value"}:
        quantity = _bounded_integer(payload.get("quantity"), "quantity", 0, 200)
    if kind == "objects":
        shape = str(payload.get("shape") or "circle").strip()
        if shape not in {"circle", "square", "triangle"}:
            raise ValueError("object shape must be circle, square, or triangle")
        items = [
            {"id": index + 1, "shape": shape, "x": 3 + (index % 20) * 5, "y": 8 + (index // 20) * 10}
            for index in range(quantity)
        ]
        return {"quantity": quantity, "shape": shape}, [{"operation": "arrange", "columns": 20}], {
            "quantity": quantity, "items": items, "description": f"{quantity} visible {shape} objects"
        }
    if kind == "tallies":
        groups = ["||||/" for _ in range(quantity // 5)]
        if quantity % 5:
            groups.append("|" * (quantity % 5))
        return {"quantity": quantity}, [{"operation": "group_tallies", "size": 5}], {
            "quantity": quantity, "groups": groups, "full_groups": quantity // 5, "remainder": quantity % 5
        }
    if kind == "groups":
        group_size = _bounded_integer(payload.get("group_size"), "group_size", 1, 50)
        full_groups, remainder = divmod(quantity, group_size)
        return {"quantity": quantity, "group_size": group_size}, [{"operation": "partition_equal_groups"}], {
            "quantity": quantity,
            "group_size": group_size,
            "groups": [group_size for _ in range(full_groups)],
            "remainder": remainder,
            "equal_partition_complete": remainder == 0,
        }
    if kind == "place_value":
        hundreds, remainder = divmod(quantity, 100)
        tens, ones = divmod(remainder, 10)
        return {"quantity": quantity}, [{"operation": "decompose_base_ten"}], {
            "quantity": quantity, "hundreds": hundreds, "tens": tens, "ones": ones,
            "expanded": f"{hundreds * 100} + {tens * 10} + {ones}",
        }

    label = truncate(str(payload.get("label") or "object"), 80).strip() or "object"
    shape = str(payload.get("shape") or "arrow").strip()
    if shape not in {"arrow", "rectangle", "square", "triangle"}:
        raise ValueError("spatial shape must be arrow, rectangle, square, or triangle")
    x = _bounded_number(payload.get("x", 50), "x", 0, 100)
    y = _bounded_number(payload.get("y", 50), "y", 0, 100)
    rotation = _bounded_number(payload.get("rotation", 0), "rotation", -3600, 3600)
    move_x = _bounded_number(payload.get("move_x", 0), "move_x", -100, 100)
    move_y = _bounded_number(payload.get("move_y", 0), "move_y", -100, 100)
    rotate_degrees = _bounded_number(payload.get("rotate_degrees", 0), "rotate_degrees", -360, 360)
    output_x = max(0.0, min(100.0, x + move_x))
    output_y = max(0.0, min(100.0, y + move_y))
    output_rotation = (rotation + rotate_degrees) % 360
    operations = []
    if move_x or move_y:
        operations.append({"operation": "move", "x": move_x, "y": move_y})
    if rotate_degrees:
        operations.append({"operation": "rotate", "degrees": rotate_degrees})
    if not operations:
        operations.append({"operation": "observe_orientation"})
    return (
        {"label": label, "shape": shape, "x": x, "y": y, "rotation": rotation % 360},
        operations,
        {"label": label, "shape": shape, "x": output_x, "y": output_y, "rotation": output_rotation},
    )


def _simulate_sentence_representation(
    kind: str, payload: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    subject = truncate(" ".join(str(payload.get("subject") or "").split()), 160).strip()
    predicate = truncate(" ".join(str(payload.get("predicate") or "").split()), 160).strip()
    obj = truncate(" ".join(str(payload.get("object") or "").split()), 240).strip()
    if not subject or not predicate:
        raise ValueError("sentence representations require a visible subject and predicate")
    subject_number = str(payload.get("subject_number") or "singular").strip().lower()
    if subject_number not in {"singular", "plural"}:
        raise ValueError("subject number must be singular or plural")

    base_proposition: dict[str, Any] = {
        "id": "sentence_core",
        "subject": subject,
        "subject_number": subject_number,
        "predicate": predicate,
        "object": obj,
        "tense": "present",
        "polarity": "positive",
        "required": True,
        "meaning_keys": ["subject", "predicate", *( ["object"] if obj else [] )],
    }
    base_frame = build_semantic_frame(
        {"semantic_frame": {"response_depth": "short", "propositions": [base_proposition]}}
    )
    base_result = realize_semantic_frame(base_frame, variation_key="study-sentence-base")
    roles = [
        {"role": "subject", "label": "Who or what", "value": subject},
        {"role": "predicate", "label": "Action, state, or relation", "value": predicate},
    ]
    if obj:
        roles.append({"role": "object", "label": "Affected or completing part", "value": obj})
    input_state = {
        "roles": roles,
        "sentence": base_result["candidate_text"],
        "subject_number": subject_number,
        "tense": "present",
        "polarity": "positive",
    }
    if kind == "sentence_roles":
        return (
            input_state,
            [{"operation": "map_visible_meaning_roles"}, {"operation": "form_sentence_core"}],
            {
                **input_state,
                "required_semantic_units_preserved": base_result["required_semantic_units_preserved"],
                "meaning_preserved": base_result["meaning_preserved"],
                "hidden_chain_of_thought_exposed": False,
                "description": "Visible meaning-role cards arranged as one sentence core",
            },
        )

    tense = str(payload.get("tense") or "present").strip().lower()
    polarity = str(payload.get("polarity") or "positive").strip().lower()
    if tense not in {"present", "past", "future"}:
        raise ValueError("sentence tense must be present, past, or future")
    if polarity not in {"positive", "negative"}:
        raise ValueError("sentence polarity must be positive or negative")
    subject_modifier = truncate(" ".join(str(payload.get("subject_modifier") or "").split()), 120).strip()
    object_modifier = truncate(" ".join(str(payload.get("object_modifier") or "").split()), 120).strip()
    relation = str(payload.get("relation") or "").strip().lower()
    if relation not in {"", "support", "contrast", "cause", "sequence"}:
        raise ValueError("sentence relation must be support, contrast, cause, sequence, or empty")

    transformed = {
        **base_proposition,
        "tense": tense,
        "polarity": polarity,
        "subject_modifiers": [subject_modifier] if subject_modifier else [],
        "object_modifiers": [object_modifier] if object_modifier else [],
    }
    propositions = [transformed]
    second_subject = truncate(" ".join(str(payload.get("second_subject") or "").split()), 160).strip()
    second_predicate = truncate(" ".join(str(payload.get("second_predicate") or "").split()), 160).strip()
    second_object = truncate(" ".join(str(payload.get("second_object") or "").split()), 240).strip()
    if relation:
        if not second_subject or not second_predicate:
            raise ValueError("a visible second subject and predicate are required for a clause relationship")
        propositions.append(
            {
                "id": "related_clause",
                "subject": second_subject,
                "predicate": second_predicate,
                "object": second_object,
                "tense": tense,
                "polarity": "positive",
                "relation": relation,
                "required": True,
                "meaning_keys": ["second_subject", "second_predicate", *( ["second_object"] if second_object else [] )],
            }
        )
    elif second_subject or second_predicate or second_object:
        raise ValueError("choose a clause relationship before supplying a second clause")

    operations: list[dict[str, Any]] = []
    if tense != "present":
        operations.append({"operation": "change_tense", "from": "present", "to": tense})
    if polarity != "positive":
        operations.append({"operation": "change_polarity", "from": "positive", "to": polarity})
    if subject_modifier:
        operations.append({"operation": "attach_subject_modifier", "value": subject_modifier})
    if object_modifier:
        operations.append({"operation": "attach_object_modifier", "value": object_modifier})
    if relation:
        operations.append({"operation": "connect_supplied_clause", "relation": relation})
    if not operations:
        operations.append({"operation": "observe_stable_sentence_core"})
    transformed_frame = build_semantic_frame(
        {
            "semantic_frame": {
                "response_depth": "standard",
                "discourse_relation": relation or "sequence",
                "propositions": propositions,
                "meaning_constraints": [
                    "use only the visible supplied roles",
                    "preserve every required proposition",
                    "do not add unsupported participants or relationships",
                ],
            }
        }
    )
    transformed_result = realize_semantic_frame(
        transformed_frame,
        variation_key=f"study-sentence-transform|{tense}|{polarity}|{relation}",
    )
    original_claim_unchanged = not any(
        (tense != "present", polarity != "positive", subject_modifier, object_modifier, relation)
    )
    return (
        input_state,
        operations,
        {
            "before_sentence": base_result["candidate_text"],
            "sentence": transformed_result["candidate_text"],
            "roles": roles,
            "tense": tense,
            "polarity": polarity,
            "subject_number": subject_number,
            "subject_modifier": subject_modifier,
            "object_modifier": object_modifier,
            "relation": relation,
            "required_semantic_units_preserved": transformed_result["required_semantic_units_preserved"],
            "meaning_preserved_within_explicit_transformation": transformed_result["meaning_preserved"],
            "original_claim_unchanged": original_claim_unchanged,
            "claim_change_is_visible_and_requested": not original_claim_unchanged,
            "transformation_source": "visible_supplied_controls",
            "unsupported_content_added": False,
            "hidden_chain_of_thought_exposed": False,
        },
    )


def _bounded_integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if result < minimum or result > maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}")
    return result


def _bounded_number(value: Any, label: str, minimum: float, maximum: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number") from exc
    if result < minimum or result > maximum:
        raise ValueError(f"{label} must be between {minimum:g} and {maximum:g}")
    return round(result, 4)


def _decode_note(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["metacognition"] = _loads(item.pop("metacognition_json", "{}"), {})
    item["language"] = _loads(item.pop("language_json", "{}"), {})
    item["voice"] = _loads(item.pop("voice_json", "{}"), {})
    item["source_refs"] = _loads(item.get("source_refs"), [])
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
