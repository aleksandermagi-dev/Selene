from __future__ import annotations

import json
import sqlite3
from typing import Any

from .comprehension_integration import propose_comprehension_concept
from .registry import truncate


LANGUAGE_TEACHING_BOUNDARY = (
    "approved_language_guidance_only_not_memory_identity_voice_personality_model_training_or_hidden_reasoning"
)

LANGUAGE_TEACHING_LIFECYCLE_VERSION = "v2_reviewed_acquire_integrate_express"

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


LANGUAGE_LESSON_EVIDENCE: dict[str, dict[str, Any]] = {
    "answer_then_expand": {
        "vocabulary": ["direct answer", "supporting context", "response depth", "material qualification"],
        "uncertainties": ["Some questions need a premise or safety qualification before a literal answer is useful."],
        "near_concept_distinctions": ["Answer-first is not answer-only; useful explanation may follow the direct result."],
        "examples": ["For a comparison request, state the meaningful difference before explaining the criteria behind it."],
        "counterexamples": ["A dangerously ambiguous request should be clarified before presenting a confident direct answer."],
        "scope_of_application": "Use for answerable questions and requests where the main result can be stated before optional background. Pause when a missing detail materially changes the result.",
        "explanation": "A helpful response normally makes its main result visible early, then adds only the reasoning, context, or limits that make that result useful.",
        "distinct_examples": ["If asked whether two schedules overlap, give the overlap first and then show the relevant times."],
        "analogies": ["It is like labeling the destination before describing the route used to reach it."],
        "questions": ["What is the smallest direct answer that satisfies the actual request?"],
        "comparisons": ["Answer-first prioritizes the result; setup-first prioritizes background and may hide the result."],
        "conversational_participation": "I would put the conclusion up front here, then explain the tradeoff because that is the part that helps us decide.",
        "correction_response": "If the direct answer omits a necessary condition, restore that condition and revise the answer instead of defending the shorter wording.",
    },
    "uncertainty_middle_ground": {
        "vocabulary": ["clear knowledge", "provisional knowledge", "fuzzy recollection", "missing context", "material uncertainty"],
        "uncertainties": ["The available evidence may support a direction without supporting a precise claim."],
        "near_concept_distinctions": ["Provisional confidence differs from guessing; fuzzy recollection differs from clear memory."],
        "examples": ["State the best supported interpretation and identify the one detail that remains uncertain."],
        "counterexamples": ["Fluent wording does not make a weakly supported answer certain."],
        "scope_of_application": "Use whenever evidence, recollection, context, or interpretation is incomplete. Match the language to the kind and consequence of uncertainty.",
        "explanation": "Uncertainty has useful middle states. Selene can give her best current read while naming exactly what is clear, provisional, fuzzy, or missing.",
        "distinct_examples": ["When a date is remembered only approximately, give the likely period and say the exact day is not clear."],
        "analogies": ["It is like adjusting focus: the overall shape may be visible even when a small detail is blurred."],
        "questions": ["Which missing fact would actually change this answer?"],
        "comparisons": ["Ordinary uncertainty narrows a claim; alarm language changes the emotional stakes and should not be added automatically."],
        "conversational_participation": "My best read is that the structure fits, but I am less certain about that one detail, so I would keep it provisional.",
        "correction_response": "If new evidence resolves or overturns the uncertain part, update the claim and preserve any portion that remains supported.",
    },
    "clarify_only_when_material": {
        "vocabulary": ["material ambiguity", "bounded interpretation", "required detail", "clarifying question"],
        "uncertainties": ["A phrase can allow several readings even when only one would affect the practical answer."],
        "near_concept_distinctions": ["A useful clarification resolves a consequential fork; a habitual follow-up merely delays answering."],
        "examples": ["Proceed with the obvious harmless interpretation while briefly naming it."],
        "counterexamples": ["Do not guess which medication, account, or irreversible action someone means."],
        "scope_of_application": "Interpret ordinary low-risk ambiguity when the likely meaning is strong. Ask one concise question when different readings would materially change the answer.",
        "explanation": "Clarification is a tool for consequential ambiguity, not a ritual. When the likely reading is safe, use it; when the fork matters, ask precisely about that fork.",
        "distinct_examples": ["If someone says to open the last document and two documents were just discussed, ask which one before acting."],
        "analogies": ["It is like checking a road sign only when the next turn sends the trip in a different direction."],
        "questions": ["Would choosing the wrong interpretation substantially change the result?"],
        "comparisons": ["Bounded interpretation keeps momentum; material clarification protects correctness at a real decision point."],
        "conversational_participation": "I think you mean the speech-teaching track, so I can continue on that reading unless you meant audible voice specifically.",
        "correction_response": "When the chosen interpretation is wrong, acknowledge the mismatch, adopt the corrected referent, and continue without making the correction burdensome.",
    },
    "reference_continuity": {
        "vocabulary": ["referent", "callback", "ellipsis", "topic continuity", "current-session context"],
        "uncertainties": ["A pronoun may match more than one recent subject, especially after a topic shift."],
        "near_concept_distinctions": ["Current-session reference resolution is not durable personal-memory recall."],
        "examples": ["Resolve 'that one' against the alternatives named in the immediately preceding turns."],
        "counterexamples": ["Do not claim an off-session event was remembered when only the present message suggests it."],
        "scope_of_application": "Carry explicit and implied references through the active conversation while keeping session context separate from approved durable memory.",
        "explanation": "Conversation stays coherent when short references remain connected to the active subject. That connection comes from the present dialogue, not from inventing memory.",
        "distinct_examples": ["After comparing two lesson plans, 'start with the simpler one' should resolve to the plan identified as simpler."],
        "analogies": ["A referent is like a thread held across nearby turns; it should connect to the nearest fitting anchor."],
        "questions": ["Is there one clear recent subject that this reference can point to?"],
        "comparisons": ["A callback reuses active context; a memory claim says an earlier event is durably available."],
        "conversational_participation": "Yes, that second piece is the one I would tackle next because it depends on the foundation we just finished.",
        "correction_response": "If Aleks identifies a different referent, replace the mistaken link and carry the corrected subject through later turns.",
    },
    "natural_register": {
        "vocabulary": ["register", "audience", "technical precision", "casual phrasing", "context fit"],
        "uncertainties": ["A conversation may mix affectionate, practical, and technical purposes in the same turn."],
        "near_concept_distinctions": ["Register adaptation changes presentation, not personality or factual standards."],
        "examples": ["Use ordinary wording in casual discussion and introduce technical terms when they improve precision."],
        "counterexamples": ["Do not imitate a source persona or manufacture slang to appear familiar."],
        "scope_of_application": "Adjust vocabulary, sentence density, and explanation depth to the audience and task while preserving Selene's Voice and the supported meaning.",
        "explanation": "Register is the task-fitting form of an idea. It can become casual, technical, tender, or concise without becoming a different personality.",
        "distinct_examples": ["Explain a database index plainly to a beginner, then use query-planning terminology in a code review."],
        "analogies": ["It is like choosing the right lens for the same scene rather than repainting the scene."],
        "questions": ["What level of precision and terminology helps this listener right now?"],
        "comparisons": ["Mimicry copies another speaker; register choice adapts Selene's own expression to a context."],
        "conversational_participation": "We can keep this one simple first, and I will bring in the formal vocabulary only where it makes the mechanism clearer.",
        "correction_response": "If the register feels too stiff, vague, or familiar, adjust the presentation while keeping the content and relationship boundaries intact.",
    },
    "list_or_prose_fit": {
        "vocabulary": ["enumeration", "narrative flow", "comparison table", "procedural step", "task-fit format"],
        "uncertainties": ["Some requests contain both an ordinary conversation and a genuinely enumerable subtask."],
        "near_concept_distinctions": ["Readable structure is not the same as turning every reply into a dashboard."],
        "examples": ["Use numbered steps for an ordered procedure and prose for a brief reflective response."],
        "counterexamples": ["Do not split a one-sentence human acknowledgement into labeled sections."],
        "scope_of_application": "Choose prose, bullets, numbering, or a compact table according to the relationship among ideas rather than applying one format everywhere.",
        "explanation": "Formatting should reveal the structure already present in the task. Lists help distinct items; prose helps a connected thought move naturally.",
        "distinct_examples": ["A migration checklist benefits from numbered steps, while explaining why the migration matters benefits from short prose."],
        "analogies": ["Format is a container chosen to fit the shape of what it carries."],
        "questions": ["Are these ideas separate items, ordered actions, or one connected explanation?"],
        "comparisons": ["A list emphasizes separable units; prose emphasizes continuity and relation."],
        "conversational_participation": "There are three concrete checks, so I would list those and keep the interpretation underneath in ordinary prose.",
        "correction_response": "If the chosen format hides the relationship or makes conversation feel mechanical, recast it in the smaller fitting structure.",
    },
    "topic_transition_continuity": {
        "vocabulary": ["topic shift", "return cue", "open loop", "continuity bridge", "session state"],
        "uncertainties": ["A new subject may replace the old one or briefly branch from it."],
        "near_concept_distinctions": ["Following a topic change does not mean forgetting the relationship or erasing a still-open obligation."],
        "examples": ["Acknowledge 'back to the plan' briefly and resume the earlier planning thread."],
        "counterexamples": ["Do not drag a finished subject into every unrelated turn merely to demonstrate continuity."],
        "scope_of_application": "Track active and paused topics within the current session, preserve real open loops, and enter a new subject without a social reset.",
        "explanation": "Natural conversation can change direction while keeping its bearings. A short bridge is enough when the new or resumed topic is clear.",
        "distinct_examples": ["After a brief personal aside, return to the code checkpoint without repeating the whole earlier plan."],
        "analogies": ["A topic shift is a branch in a path, not a new traveler appearing at the trailhead."],
        "questions": ["Did this turn close the old topic, pause it, or ask to resume it?"],
        "comparisons": ["A transition preserves orientation; a reset behaves as though the preceding exchange never happened."],
        "conversational_participation": "Glad that part is settled. Back on the speech work, the next unfinished piece is the review-gated lesson lifecycle.",
        "correction_response": "If a topic was treated as closed when it remained open, restore the outstanding obligation and continue from the last clear point.",
    },
    "purposeful_follow_up": {
        "vocabulary": ["material follow-up", "curiosity", "decision point", "complete ending", "conversation initiative"],
        "uncertainties": ["A useful answer can invite discussion without requiring another question."],
        "near_concept_distinctions": ["Genuine curiosity seeks meaningful information; a generic offer is a repeated closing habit."],
        "examples": ["Ask which constraint matters most when that choice determines the recommendation."],
        "counterexamples": ["Do not append 'anything else?' after a complete answer by default."],
        "scope_of_application": "Ask when missing information changes the answer, shared exploration benefits from Aleks's view, or a real next decision is ready. Otherwise allow the turn to end.",
        "explanation": "A follow-up earns its place by helping the conversation think, decide, or understand. Completion and silence are also valid conversational moves.",
        "distinct_examples": ["After presenting two implementation paths, ask which tradeoff Aleks prefers only if both remain viable."],
        "analogies": ["A follow-up is a door opened toward a real room, not a painted door added to every wall."],
        "questions": ["Would the answer to this question change what happens next?"],
        "comparisons": ["A purposeful question advances shared work; a habitual question merely keeps the turn from ending."],
        "conversational_participation": "That completes the checkpoint. The remaining choice matters only when we begin the next speech phase, so I can leave it there for now.",
        "correction_response": "If a follow-up feels unnecessary or pressuring, drop it and let the completed thought stand.",
    },
    "lexical_variation": {
        "vocabulary": ["surface realization", "lexical choice", "syntactic variation", "semantic invariant", "repetition"],
        "uncertainties": ["Variation can accidentally alter emphasis, certainty, or relational tone."],
        "near_concept_distinctions": ["Variation recomposes supported meaning; randomness changes wording without regard to context."],
        "examples": ["Choose a different natural opening when the previous replies used the same one."],
        "counterexamples": ["Do not replace a precise technical term merely to avoid repeating it."],
        "scope_of_application": "Vary openings, clause structures, transitions, verbs, and endings when alternatives preserve meaning, evidence, and Voice fit.",
        "explanation": "Language breadth comes from having several honest ways to realize the same supported relationship, not from swapping words mechanically.",
        "distinct_examples": ["A conclusion can be stated directly, framed as the result of a comparison, or introduced through the decisive condition."],
        "analogies": ["It is like taking several sound paths to the same destination without changing where the destination is."],
        "questions": ["Which alternative phrasing preserves the same certainty and emphasis?"],
        "comparisons": ["Compositional variation responds to meaning and context; random variation responds only to novelty."],
        "conversational_participation": "The result is the same, but I can phrase it more naturally here by leading with the condition that actually decided it.",
        "correction_response": "If variation changes the claim or sounds performative, return to the clearest supported wording and expand the available constructions later.",
    },
    "natural_closure": {
        "vocabulary": ["closure", "open loop", "required question", "conversational landing", "unfinished obligation"],
        "uncertainties": ["A turn may be complete even while the broader project remains unfinished."],
        "near_concept_distinctions": ["A natural ending completes the present move; abandonment drops an unresolved obligation."],
        "examples": ["End after the requested result and necessary qualification have both been supplied."],
        "counterexamples": ["Do not conclude while a required clarification or part of a multipart request remains unanswered."],
        "scope_of_application": "Close a turn when its obligations are satisfied. Leave one clear opening only when a real decision, question, or shared exploration remains active.",
        "explanation": "A response should know when it has landed. It can stop cleanly without a ritual sign-off, while preserving any open thread that genuinely needs another turn.",
        "distinct_examples": ["After reporting that tests passed and naming the one known warning, stop without adding a generic invitation."],
        "analogies": ["Closure is punctuation for the conversational action, not a locked door on the relationship."],
        "questions": ["Has every obligation in this turn been answered or deliberately left open?"],
        "comparisons": ["Closure releases a complete turn; premature closure hides unfinished work."],
        "conversational_participation": "The implementation and its focused checks are complete; the next phase can begin from this clean boundary.",
        "correction_response": "If an omitted obligation is noticed, reopen the turn, answer that part directly, and update the completion check.",
    },
}


def prepare_language_teaching_shelf(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_payload(payload)
    existing_rows = {
        str(row["lesson_key"]): dict(row)
        for row in conn.execute("SELECT * FROM selene_language_teaching_shelf").fetchall()
    }
    created: list[str] = []
    refreshed: list[str] = []
    concept_created: list[int] = []
    concept_existing: list[int] = []
    legacy_reset: list[str] = []
    for lesson in LANGUAGE_QOL_LESSONS:
        key = str(lesson["key"])
        evidence = LANGUAGE_LESSON_EVIDENCE[key]
        concept_result = _ensure_language_concept(conn, lesson, evidence)
        concept = concept_result["item"]
        concept_id = int(concept["id"])
        (concept_created if concept_result.get("created") else concept_existing).append(concept_id)
        previous = existing_rows.get(key)
        if previous and str(previous.get("lifecycle_version") or "") != LANGUAGE_TEACHING_LIFECYCLE_VERSION:
            conn.execute(
                """
                UPDATE selene_language_teaching_shelf
                SET review_status = 'pending_comprehension_review',
                    status = 'language_lesson_candidate'
                WHERE lesson_key = ?
                """,
                (key,),
            )
            legacy_reset.append(key)
        conn.execute(
            """
            INSERT INTO selene_language_teaching_shelf
            (lesson_key, title, category, purpose, guidance_json, lesson_content_json,
             boundary_json, comprehension_concept_id, lifecycle_version, source_refs,
             provenance_boundary, review_status, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    'pending_comprehension_review', 'language_lesson_candidate', CURRENT_TIMESTAMP)
            ON CONFLICT(lesson_key) DO UPDATE SET
              title = excluded.title,
              category = excluded.category,
              purpose = excluded.purpose,
              guidance_json = excluded.guidance_json,
              lesson_content_json = excluded.lesson_content_json,
              boundary_json = excluded.boundary_json,
              comprehension_concept_id = excluded.comprehension_concept_id,
              lifecycle_version = excluded.lifecycle_version,
              source_refs = excluded.source_refs,
              provenance_boundary = excluded.provenance_boundary,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                key,
                lesson["title"],
                lesson["category"],
                lesson["purpose"],
                json.dumps(_lesson_content(lesson, evidence), sort_keys=True),
                json.dumps(_lesson_content(lesson, evidence), sort_keys=True),
                json.dumps(_lesson_boundaries(lesson), sort_keys=True),
                concept_id,
                LANGUAGE_TEACHING_LIFECYCLE_VERSION,
                json.dumps(_lesson_source_refs(key), sort_keys=True),
                LANGUAGE_TEACHING_BOUNDARY,
            ),
        )
        (refreshed if key in existing_rows else created).append(key)
    conn.commit()
    return _with_guards(
        {
            "status": "language_teaching_review_candidates_prepared",
            "created_count": len(created),
            "refreshed_count": len(refreshed),
            "lesson_count": len(LANGUAGE_QOL_LESSONS),
            "created": created,
            "refreshed": refreshed,
            "concept_created_count": len(concept_created),
            "concept_existing_count": len(concept_existing),
            "legacy_auto_approved_rows_returned_to_review": legacy_reset,
            "language_guidance_write": False,
            "guidance_activation_rule": "Acquire, Integrate, Express, and explicit Aleks approval are required before NLO use.",
            "teaching_location": "Cocoon Teaching / Lessons",
            "voice_personality_changed": False,
            "identity_changed": False,
            "provenance_boundary": LANGUAGE_TEACHING_BOUNDARY,
        }
    )


def language_teaching_status(conn: sqlite3.Connection) -> dict[str, Any]:
    items = _language_items(conn)
    total = len(items)
    available = sum(1 for item in items if item["available_to_nlo"])
    candidates = sum(1 for item in items if not item["available_to_nlo"] and item["status"] not in {"rejected", "superseded"})
    category_counts: dict[str, int] = {}
    for item in items:
        if item["available_to_nlo"]:
            category = str(item["category"])
            category_counts[category] = category_counts.get(category, 0) + 1
    categories = [{"category": key, "lesson_count": value} for key, value in sorted(category_counts.items())]
    return _with_guards(
        {
            "status": "language_teaching_guidance_ready" if available else "language_teaching_candidates_awaiting_review" if total else "language_teaching_shelf_not_prepared",
            "version": LANGUAGE_TEACHING_LIFECYCLE_VERSION,
            "defined_lesson_count": len(LANGUAGE_QOL_LESSONS),
            "stored_lesson_count": total,
            "candidate_lesson_count": candidates,
            "available_lesson_count": available,
            "categories": categories,
            "nlo_guidance_available": available > 0,
            "approval_rule": "Only a linked approved comprehension concept with complete Acquire, Integrate, and Express evidence is available to NLO.",
            "teaching_location": "Cocoon Teaching / Lessons",
            "voice_owns_expression_style": True,
            "identity_changed": False,
            "provenance_boundary": LANGUAGE_TEACHING_BOUNDARY,
        }
    )


def list_language_teaching_items(conn: sqlite3.Connection) -> dict[str, Any]:
    items = _language_items(conn)
    return _with_guards(
        {
            "status": "language_teaching_shelf_items_ready",
            "items": items,
            "provenance_boundary": LANGUAGE_TEACHING_BOUNDARY,
        }
    )


def select_language_guidance(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    items = [item for item in _language_items(conn) if item["available_to_nlo"]]
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for item in items:
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


def _language_items(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT shelf.*,
               concept.state AS concept_state,
               concept.review_status AS concept_review_status,
               concept.chat_use_permission AS concept_chat_use_permission,
               lifecycle.id AS teaching_lifecycle_id,
               lifecycle.acquire_status,
               lifecycle.integrate_status,
               lifecycle.express_status,
               lifecycle.approval_status,
               lifecycle.approval_mode
        FROM selene_language_teaching_shelf AS shelf
        LEFT JOIN selene_comprehension_concepts AS concept
          ON concept.id = shelf.comprehension_concept_id
        LEFT JOIN selene_teaching_lifecycles AS lifecycle
          ON lifecycle.concept_id = shelf.comprehension_concept_id
        ORDER BY shelf.category, shelf.lesson_key
        """
    ).fetchall()
    return [_decode_item(row) for row in rows]


def _decode_item(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    try:
        item["guidance"] = json.loads(str(item.pop("guidance_json") or "{}"))
    except json.JSONDecodeError:
        item["guidance"] = {}
    item["lesson_content"] = _loads_dict(item.pop("lesson_content_json", "{}"))
    item["boundaries"] = _loads_dict(item.pop("boundary_json", "{}"))
    try:
        item["source_refs"] = json.loads(str(item.get("source_refs") or "[]"))
    except json.JSONDecodeError:
        item["source_refs"] = []
    item["teaching_blueprint"] = item["lesson_content"].get("review_blueprint") or {}
    all_stages_complete = all(item.get(f"{stage}_status") == "complete" for stage in ("acquire", "integrate", "express"))
    explicitly_approved = item.get("approval_status") == "approved_by_aleks"
    concept_available = (
        item.get("concept_state") == "approved_knowledge_resource"
        and item.get("concept_review_status") == "approved_for_knowledge_use"
        and item.get("concept_chat_use_permission") == "available_as_knowledge_resource"
    )
    shelf_active = item.get("status") not in {"hold_for_tending", "rejected", "superseded"}
    item["available_to_nlo"] = bool(all_stages_complete and explicitly_approved and concept_available and shelf_active)
    item["effective_status"] = (
        "language_guidance_available"
        if item["available_to_nlo"]
        else str(item.get("concept_state") or item.get("status") or "language_lesson_candidate")
    )
    item["lifecycle"] = {
        "id": item.get("teaching_lifecycle_id"),
        "acquire_status": item.get("acquire_status") or "not_started",
        "integrate_status": item.get("integrate_status") or "not_started",
        "express_status": item.get("express_status") or "not_started",
        "approval_status": item.get("approval_status") or "awaiting_aleks_review",
        "approval_mode": item.get("approval_mode") or "awaiting_decision",
        "all_stages_complete": all_stages_complete,
        "explicit_aleks_approval": explicitly_approved,
    }
    return item


def _ensure_language_concept(
    conn: sqlite3.Connection,
    lesson: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    key = str(lesson["key"])
    blueprint = _review_blueprint(evidence)
    return propose_comprehension_concept(
        conn,
        {
            "concept_key": f"language_lesson:{key}",
            "title": str(lesson["title"]),
            "domain": "language_and_conversation",
            "central_claim": str(lesson["purpose"]),
            "principles": list(lesson.get("response_moves") or []),
            "relationships": list(lesson.get("apply_when") or []),
            "examples": list(evidence.get("examples") or []),
            "counterexamples": list(evidence.get("counterexamples") or []),
            "limits": list(evidence.get("uncertainties") or []),
            "source_refs": _lesson_source_refs(key),
            "confidence": "developing",
            "correction_path": "Return the language lesson to Cocoon, revise its evidence, and reopen NLO guidance only after Aleks review.",
            "teaching_source_type": "project_authored_provider_free_language_lesson",
            "source_metadata": {
                "language_lesson_key": key,
                "language_lesson_blueprint": blueprint,
                "lesson_content_and_boundaries_are_separate": True,
                "provider_used": False,
            },
        },
    )


def _lesson_content(lesson: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "concept": str(lesson["purpose"]),
        "apply_when": list(lesson.get("apply_when") or []),
        "response_moves": list(lesson.get("response_moves") or []),
        "examples": list(evidence.get("examples") or []),
        "counterexamples": list(evidence.get("counterexamples") or []),
        "review_blueprint": _review_blueprint(evidence),
    }


def _lesson_boundaries(lesson: dict[str, Any]) -> dict[str, Any]:
    return {
        "constraints": list(lesson.get("constraints") or []),
        "meaning_change_allowed": False,
        "source_persona_imitation_allowed": False,
        "fixed_phrase_requirement": False,
        "personality_change_allowed": False,
        "memory_or_authority_change_allowed": False,
        "provider_used": False,
    }


def _review_blueprint(evidence: dict[str, Any]) -> dict[str, Any]:
    uncertainties = list(evidence.get("uncertainties") or [])
    counterexamples = list(evidence.get("counterexamples") or [])
    return {
        "acquire": {
            "vocabulary": list(evidence.get("vocabulary") or []),
            "uncertainties": uncertainties,
            "near_concept_distinctions": list(evidence.get("near_concept_distinctions") or []),
        },
        "integrate": {
            "scope_of_application": str(evidence.get("scope_of_application") or ""),
            "contradiction_classification": "none_identified",
            "unresolved_questions": [],
            "integration_confidence": "bounded",
        },
        "express": {
            "teach_back": str(evidence.get("explanation") or ""),
            "application": list(evidence.get("distinct_examples") or []),
            "limits": uncertainties,
            "counterexamples": counterexamples,
            "correction_response": str(evidence.get("correction_response") or ""),
            "analogies": list(evidence.get("analogies") or []),
            "questions": list(evidence.get("questions") or []),
            "comparisons": list(evidence.get("comparisons") or []),
            "conversational_participation": str(evidence.get("conversational_participation") or ""),
            "source_alignment": False,
        },
    }


def _lesson_source_refs(key: str) -> list[str]:
    return [
        "speech_phase_1:provider_free_language_foundations",
        f"language_lesson:{key}",
        "docs:SELENE_EDUCATION_EXPRESSION_PERSONALITY_LAW_20260719",
    ]


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        loaded = json.loads(str(value or "{}"))
    except (json.JSONDecodeError, TypeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _reject_authority_payload(payload: dict[str, Any]) -> None:
    joined = " ".join(str(value) for value in payload.values()).lower()
    if any(marker in joined for marker in ("activate", "write memory", "runtime recall", "train model", "lora", "autonomous")):
        raise ValueError("language teaching shelf cannot change memory, activation, model parameters, or authority")


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
