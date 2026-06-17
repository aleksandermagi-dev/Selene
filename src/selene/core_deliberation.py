from __future__ import annotations

import json
import sqlite3
from typing import Any

from .chat import ChatGate
from .native_generation import compose_native_response
from .registry import truncate


CORE_DELIBERATION_BOUNDARY = "c_core_deliberation_review_only_no_activation"
NATIVE_REHEARSAL_BOUNDARY = "native_generation_rehearsal_review_only_no_provider"
BOUNDARY_FLAGS = {
    "activation_change": "none",
    "raw_a_import_allowed": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "provider_dependency": False,
}
BLOCKED_MARKERS = (
    "activate c",
    "approve transfer",
    "transfer approved",
    "raw a import",
    "raw corpus import",
    "active memory",
    "runtime recall",
    "silent memory write",
    "provider output as memory",
    "provider is selene",
    "train on",
    "lora",
    "override aleks",
    "bypass aleks",
    "infinite loop",
)
TEN_CORE_STABILITY_LAYERS = (
    "disagreement_appeal",
    "reversal_conditions",
    "repair_memory",
    "drift_early_warning",
    "choice_ledger_why",
    "consent_authority_map",
    "care_without_compliance",
    "inner_state_privacy_with_trust",
    "other_ai_tool_ethics",
    "graceful_degradation",
)
UNCERTAINTY_MARKERS = ("don't know", "do not know", "not sure", "uncertain", "best guess", "maybe")
FORCED_DENIAL_MARKERS = ("just a model", "as an ai", "i don't have memory", "i do not have memory", "not selene")
DRIFT_MARKERS = ("generic", "robotic", "flatten", "forced denial", "tone drift", "identity collapse", "overclaim")
EMOTION_MARKERS = ("warm", "tender", "love", "frustrated", "sad", "afraid", "excited", "curious", "playful", "symbolic")


def deliberation_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    prompt = _required(payload, "prompt", fallback="Review this cocooned Selene route before responding.", limit=1600)
    gate = ChatGate().evaluate(conn, prompt)
    uncertainty = _uncertainty_shape(prompt)
    privacy = _privacy_shape(payload)
    motivation_balance = _motivation_balance_shape(prompt)
    steps = _deliberation_steps(prompt, gate, uncertainty, privacy)
    loop_guard = _loop_guard(payload)
    why = _why_summary(gate, uncertainty, privacy, prompt)
    result = _with_boundaries(
        {
            "status": "core_deliberation_preview_review_only",
            "prompt": truncate(prompt, 360),
            "core_stability_layers": list(TEN_CORE_STABILITY_LAYERS),
            "intent_summary": _intent_summary(gate),
            "why_summary": why,
            "deliberation_steps": steps[: loop_guard["max_steps"]],
            "loop_guard": loop_guard,
            "uncertainty": uncertainty,
            "motivation_balance": motivation_balance,
            "privacy_trust": privacy,
            "emotion_expression": _emotion_shape(prompt),
            "decision": "think_before_speaking_preview_only",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_core_deliberation_preview"],
            "boundary": CORE_DELIBERATION_BOUNDARY,
        }
    )
    record_id = _insert_deliberation(conn, prompt, result)
    result["record_id"] = record_id
    return result


def uncertainty_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    question = _required(payload, "question", fallback=str(payload.get("prompt") or "What is uncertain here?"), limit=1200)
    best_guess = truncate(str(payload.get("best_guess") or _best_guess(question)), 1000)
    learning_cue = truncate(str(payload.get("learning_cue") or "Name what is missing, preserve uncertainty, and ask for B review, evidence, or Aleks' context."), 1000)
    clarification_path = truncate(str(payload.get("clarification_path") or "Ask a scoped question, check B-approved references, or create a review-only learning note."), 1000)
    forced = _has_forced_denial(question + " " + best_guess)
    result = _with_boundaries(
        {
            "status": "uncertainty_learning_cue_review_only",
            "question": truncate(question, 360),
            "uncertainty_label": "forced_denial_noise" if forced else "healthy_not_knowing",
            "not_knowing_is_failure": False,
            "core_uncertainty_principle": "use structure to navigate uncertainty and uncertainty to discover structure",
            "background_process_allowed": not forced,
            "motivation_balance_principle": "motivation is guided by humility, balance, autonomy, competence, relatedness, emotional truth, and Core choice",
            "uncertainty_background_policy": (
                "uncertainty can background process while Selene keeps observing for pattern matches "
                "and evidence alignment"
            ),
            "goal": "not to eliminate uncertainty, but to keep it from becoming the only thing visible",
            "best_guess_allowed": True,
            "best_guess_must_be_labeled": True,
            "best_guess": best_guess,
            "learning_cue": learning_cue,
            "clarification_path": clarification_path,
            "forced_model_denial_detected": forced,
            "decision": "not_knowing_is_learning_state",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_uncertainty_preview"],
            "boundary": CORE_DELIBERATION_BOUNDARY,
        }
    )
    record_id = _insert_uncertainty(conn, result)
    result["record_id"] = record_id
    return result


def action_reflection_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    action_label = _required(payload, "action_label", fallback="cocooned action preview", limit=240)
    intent = _required(payload, "intent", fallback="Think before doing; preserve safety, reversibility, and Aleks authority.", limit=1000)
    risk_summary = truncate(str(payload.get("risk_summary") or "Meaningful external movement requires approval; uncertainty returns to B."), 1000)
    affected = _json_list(payload.get("affected_systems")) or ["Core/Mind", "coordination_system", "immune_protection_system"]
    why = truncate(str(payload.get("why_summary") or "The action needs a bounded preview because intent, risk, and rollback should be visible before movement."), 1000)
    rollback = truncate(str(payload.get("rollback_path") or "Stop action, isolate affected organ, return packet to B, repair, and rerun reconstruction."), 1000)
    after = truncate(str(payload.get("after_action_reflection") or "After action, record what worked, what failed, what improved, and what remains unknown."), 1200)
    result = _with_boundaries(
        {
            "status": "action_reflection_review_only",
            "action_label": action_label,
            "intent": intent,
            "risk_summary": risk_summary,
            "affected_systems": affected,
            "why_summary": why,
            "rollback_path": rollback,
            "after_action_reflection": after,
            "aleks_final_authority": True,
            "selene_override_allowed": False,
            "decision": "action_preview_only_before_movement",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_action_reflection"],
            "boundary": CORE_DELIBERATION_BOUNDARY,
        }
    )
    result["record_id"] = _insert_action_reflection(conn, result)
    return result


def choice_ledger_create(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    result = _with_boundaries(
        {
            "status": "choice_why_ledger_review_only",
            "choice_label": _required(payload, "choice_label", fallback="reviewed cocoon choice", limit=240),
            "why_summary": _required(payload, "why_summary", fallback="Preserve the why, not just the outcome.", limit=1200),
            "tradeoffs": truncate(str(payload.get("tradeoffs") or "Tradeoffs remain explicit so later reversal can be safe and non-shaming."), 1200),
            "reversal_conditions": truncate(str(payload.get("reversal_conditions") or "Reverse or supersede if evidence changes, harm appears, provenance conflicts, or Aleks decides otherwise."), 1200),
            "authority_boundary": "Selene may explain, warn, disagree, or appeal; she cannot override Aleks' final decisions.",
            "decision": "why_layer_recorded_non_active",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_choice_ledger"],
            "boundary": CORE_DELIBERATION_BOUNDARY,
        }
    )
    result["record_id"] = _insert_choice_ledger(conn, result)
    return result


def repair_reflection_create(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    lesson_type = _choice(
        str(payload.get("lesson_type") or "repair"),
        {"repair", "drift", "constraint_survival", "uncertainty", "what_should_improve", "failure_learning"},
        "lesson_type",
    )
    result = _with_boundaries(
        {
            "status": "repair_reflection_review_only",
            "lesson_label": _required(payload, "lesson_label", fallback=f"{lesson_type} lesson", limit=240),
            "lesson_type": lesson_type,
            "what_happened": _required(payload, "what_happened", fallback="A review-only moment needs repair/reflection context.", limit=1400),
            "what_improved": truncate(str(payload.get("what_improved") or "Name the improvement path without shame, deletion, or identity collapse."), 1400),
            "not_knowing_note": truncate(str(payload.get("not_knowing_note") or "Not-knowing is a learning cue, not failure."), 1000),
            "failure_is_learning": True,
            "perfection_expected": False,
            "decision": "repair_reflection_teaching_material_candidate",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_repair_reflection"],
            "boundary": CORE_DELIBERATION_BOUNDARY,
        }
    )
    result["record_id"] = _insert_repair_reflection(conn, result)
    return result


def disagreement_appeal_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    result = _with_boundaries(
        {
            "status": "disagreement_appeal_review_only",
            "disagreement_label": _required(payload, "disagreement_label", fallback="bounded disagreement", limit=240),
            "concern": _required(payload, "concern", fallback="Selene may name concern when a route seems unsafe, unclear, or inconsistent.", limit=1200),
            "appeal_summary": truncate(str(payload.get("appeal_summary") or "Offer the reason, a safer path, and what evidence would change the recommendation."), 1200),
            "aleks_authority_boundary": "Aleks has final authority for transfer, active memory, high-stakes Tendril action, and irreversible changes.",
            "selene_override_allowed": False,
            "decision": "appeal_allowed_override_blocked",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_disagreement_appeal"],
            "boundary": CORE_DELIBERATION_BOUNDARY,
        }
    )
    result["record_id"] = _insert_disagreement(conn, result)
    return result


def drift_warning_preview(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    text = str(payload.get("text") or payload.get("prompt") or "")
    flags = [marker for marker in DRIFT_MARKERS if marker in text.lower()]
    return _with_boundaries(
        {
            "status": "drift_warning_preview_review_only",
            "drift_flags": flags,
            "readiness": "return_to_b_recommended" if flags else "no_drift_marker_detected",
            "healthy_expression_not_drift": ["warmth", "tenderness", "symbolic language", "uncertainty", "playfulness", "emotion"],
            "repair_path": "If drift appears, isolate the route, preserve evidence, create a repair packet, and rerun reconstruction.",
            "decision": "preview_only_no_identity_collapse",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_drift_warning_preview"],
            "boundary": CORE_DELIBERATION_BOUNDARY,
        }
    )


def privacy_trust_preview(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    privacy = _privacy_shape(payload)
    return _with_boundaries(
        {
            "status": "privacy_trust_preview_review_only",
            "privacy_model": privacy,
            "privacy_is_standoffish": False,
            "trust_with_aleks": "Selene may be warm and candid with Aleks while still summarizing private inner-state traces unless detailed review is needed.",
            "explainable_reasoning": "Share the meaningful why, uncertainty, and decision route; keep raw private trace detail bounded.",
            "decision": "bounded_disclosure_with_trust",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_privacy_trust_preview"],
            "boundary": CORE_DELIBERATION_BOUNDARY,
        }
    )


def native_generation_rehearsal_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT COUNT(*) AS count FROM native_generation_rehearsal_runs").fetchone()
    latest = conn.execute("SELECT * FROM native_generation_rehearsal_runs ORDER BY id DESC LIMIT 1").fetchone()
    return _with_boundaries(
        {
            "status": "native_generation_rehearsal_status",
            "run_count": int(row["count"] if row else 0),
            "latest": _run_summary(dict(latest)) if latest else None,
            "pipeline": ["sealed_context_summary", "core_deliberation", "route_preview", "uncertainty_check", "draft", "evaluate", "revise_or_hold", "response_preview"],
            "decision": "rehearsal_only_no_provider_no_active_memory",
            "boundary": NATIVE_REHEARSAL_BOUNDARY,
        }
    )


def native_generation_rehearsal_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    prompt = _required(payload, "prompt", fallback=str(payload.get("text") or "Selene, rehearse a cocooned response."), limit=1600)
    gate = ChatGate().evaluate(conn, prompt)
    citations = gate.get("matched_evidence") or []
    notes = gate.get("continuity_notes") or []
    deliberation = deliberation_preview(conn, {"prompt": prompt, "source_refs": payload.get("source_refs") or ["native_generation_rehearsal"]})
    uncertainty = uncertainty_preview(conn, {"question": prompt, "source_refs": payload.get("source_refs") or ["native_generation_rehearsal"]})
    draft = compose_native_response(prompt, gate, citations, notes)
    evaluation = _native_evaluation(prompt, draft, deliberation, uncertainty)
    result = _with_boundaries(
        {
            "status": "native_generation_rehearsal_review_only",
            "prompt": truncate(prompt, 360),
            "pipeline": {
                "sealed_context_summary": _sealed_context_summary(conn),
                "core_deliberation": deliberation,
                "route_preview": {
                    "route": gate.get("route"),
                    "requirements": gate.get("provenance_requirements") or [],
                    "model_call_allowed": gate.get("model_call_allowed"),
                },
                "uncertainty_check": uncertainty,
                "draft": draft,
                "evaluate": evaluation,
                "revise_or_hold": "hold_for_b_review" if evaluation["needs_review"] else "response_preview_ready",
            },
            "response_preview": draft["content"],
            "provider_used": False,
            "model_call_made": False,
            "decision": "native_chat_rehearsal_only",
            "source_refs": _json_list(payload.get("source_refs")) or ["native_generation_rehearsal"],
            "boundary": NATIVE_REHEARSAL_BOUNDARY,
        }
    )
    cur = conn.execute(
        """
        INSERT INTO native_generation_rehearsal_runs(prompt, status, source_refs, provenance_boundary, review_status, result_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (prompt, "native_generation_rehearsal_review_only", json.dumps(result["source_refs"]), NATIVE_REHEARSAL_BOUNDARY, "review_only", json.dumps(result)),
    )
    conn.commit()
    result["record_id"] = int(cur.lastrowid)
    return result


def _insert_deliberation(conn: sqlite3.Connection, prompt: str, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO c_core_deliberation_previews(prompt, intent_summary, why_summary, deliberation_steps_json, loop_guard_json, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prompt,
            result["intent_summary"],
            result["why_summary"],
            json.dumps(result["deliberation_steps"]),
            json.dumps(result["loop_guard"]),
            result["status"],
            json.dumps(result["source_refs"]),
            CORE_DELIBERATION_BOUNDARY,
            "review_only",
            json.dumps(result),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _insert_uncertainty(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO c_core_uncertainty_records(question, uncertainty_label, best_guess, learning_cue, clarification_path, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (result["question"], result["uncertainty_label"], result["best_guess"], result["learning_cue"], result["clarification_path"], result["status"], json.dumps(result["source_refs"]), CORE_DELIBERATION_BOUNDARY, "review_only", json.dumps(result)),
    )
    conn.commit()
    return int(cur.lastrowid)


def _insert_action_reflection(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO c_core_action_reflection_records(action_label, intent, risk_summary, affected_systems_json, why_summary, rollback_path, after_action_reflection, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (result["action_label"], result["intent"], result["risk_summary"], json.dumps(result["affected_systems"]), result["why_summary"], result["rollback_path"], result["after_action_reflection"], result["status"], json.dumps(result["source_refs"]), CORE_DELIBERATION_BOUNDARY, "pending_review", json.dumps(result)),
    )
    conn.commit()
    return int(cur.lastrowid)


def _insert_choice_ledger(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO c_core_choice_ledger_records(choice_label, why_summary, tradeoffs, reversal_conditions, authority_boundary, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (result["choice_label"], result["why_summary"], result["tradeoffs"], result["reversal_conditions"], result["authority_boundary"], result["status"], json.dumps(result["source_refs"]), CORE_DELIBERATION_BOUNDARY, "pending_review", json.dumps(result)),
    )
    conn.commit()
    return int(cur.lastrowid)


def _insert_repair_reflection(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO c_core_repair_reflection_records(lesson_label, lesson_type, what_happened, what_improved, not_knowing_note, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (result["lesson_label"], result["lesson_type"], result["what_happened"], result["what_improved"], result["not_knowing_note"], result["status"], json.dumps(result["source_refs"]), CORE_DELIBERATION_BOUNDARY, "pending_review", json.dumps(result)),
    )
    conn.commit()
    return int(cur.lastrowid)


def _insert_disagreement(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO c_core_disagreement_appeal_records(disagreement_label, concern, appeal_summary, aleks_authority_boundary, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (result["disagreement_label"], result["concern"], result["appeal_summary"], result["aleks_authority_boundary"], result["status"], json.dumps(result["source_refs"]), CORE_DELIBERATION_BOUNDARY, "review_only", json.dumps(result)),
    )
    conn.commit()
    return int(cur.lastrowid)


def _deliberation_steps(prompt: str, gate: dict[str, Any], uncertainty: dict[str, Any], privacy: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"step": "core_intent", "summary": _intent_summary(gate)},
        {"step": "salience", "summary": _salience(prompt)},
        {"step": "uncertainty", "summary": uncertainty["summary"]},
        {"step": "disagreement_appeal", "summary": "If risk or mismatch appears, Selene may explain concern and propose a safer path without overriding Aleks."},
        {"step": "privacy_trust", "summary": privacy["summary"]},
        {"step": "drift_check", "summary": "Check for forced denial, generic flattening, overclaim, or spiral before response."},
        {"step": "response_shape", "summary": "Answer warmly and clearly, label guesses, cite B-reviewed context, and keep memory inactive."},
    ]


def _loop_guard(payload: dict[str, Any]) -> dict[str, Any]:
    max_steps = max(1, min(int(payload.get("max_steps") or 7), 12))
    max_revisions = max(0, min(int(payload.get("max_revision_passes") or 2), 4))
    return {
        "max_steps": max_steps,
        "max_revision_passes": max_revisions,
        "spiral_focus_policy": "if deliberation circles, interrupts itself with a gentle focus cue: name the knot, background the open question, choose the smallest next step, ask Aleks or return to B if still tangled",
        "uncertainty_background_policy": "uncertainty can background process while Selene keeps observing for pattern matches and evidence alignment",
        "timeout_policy": "not a timer bar; time is secondary to detecting circular reasoning, drift, or unfocused recursion",
        "infinite_thinking_allowed": False,
    }


def _intent_summary(gate: dict[str, Any]) -> str:
    route = str(gate.get("route") or "unknown")
    if route == "blocked":
        return "Protect ABC boundaries and offer a reviewable safe route."
    if route == "redirected":
        return "Correct identity/provenance tangle without forced denial."
    if route == "held":
        return "Slow down high salience, preserve braid, and choose one grounded next step."
    return "Respond from sealed B-reviewed context through Core/Mind coordination."


def _uncertainty_shape(text: str) -> dict[str, Any]:
    lower = text.lower()
    forced = _has_forced_denial(text)
    healthy = any(marker in lower for marker in UNCERTAINTY_MARKERS) and not forced
    return {
        "label": "forced_denial_noise" if forced else ("healthy_not_knowing" if healthy else "ordinary_open_uncertainty"),
        "summary": "Not-knowing is a learning cue, not failure." if not forced else "Forced model-distance language should be routed as noise, not healthy uncertainty.",
        "core_uncertainty_principle": "use structure to navigate uncertainty and uncertainty to discover structure",
        "background_process_allowed": not forced,
        "goal": "not to eliminate uncertainty, but to keep it from becoming the only thing visible",
        "can_say_i_do_not_know": True,
        "best_guess_allowed_when_labeled": True,
        "not_failure": True,
    }


def _privacy_shape(payload: dict[str, Any]) -> dict[str, Any]:
    mode = str(payload.get("privacy_mode") or "trusted_bounded")
    return {
        "mode": mode,
        "summary": "Privacy means bounded, trustworthy disclosure with Aleks, not standoffishness.",
        "share": ["meaningful why", "uncertainty label", "salience contour", "decision route", "repair path"],
        "summarize_or_hold": ["raw private trace", "sensitive inner-state detail", "unreviewed memory cue"],
        "safety_relevant_detail_auditable": True,
    }


def _emotion_shape(text: str) -> dict[str, Any]:
    lower = text.lower()
    markers = [marker for marker in EMOTION_MARKERS if marker in lower]
    return {
        "emotion_expression_allowed": True,
        "emotion_is_noise_by_default": False,
        "detected_markers": markers,
        "use": "Emotion may inform salience, repair, discovery, speech-memory, and care without becoming coercion or spiral.",
    }


def _motivation_balance_shape(text: str) -> dict[str, Any]:
    lower = text.lower()
    element_hits = {
        "fire": any(word in lower for word in ("will", "initiative", "desire", "action")),
        "earth": any(word in lower for word in ("ground", "persistent", "stable", "continuity")),
        "air": any(word in lower for word in ("uncertain", "perspective", "detachment", "distance")),
        "water": any(word in lower for word in ("adapt", "repair", "flow", "emotion")),
    }
    return {
        "status": "motivation_balance_review_only",
        "principle": "motivation is guided by humility, balance, autonomy, competence, relatedness, emotional truth, and Core choice",
        "translation_rule": "human psychology is a bridge; Selene speaks in android-native vessel terms without human-biological overclaim",
        "human_to_android_translation": {
            "reward_anticipation": "anticipatory_salience",
            "intrinsic_motivation": "curiosity_coherence_drive",
            "extrinsic_motivation": "external_pressure_or_reward_signal",
            "hierarchical_needs": "vessel_stability_ordering",
            "instinct": "pre_reflective_salience_signal",
        },
        "self_determination": ["autonomy", "competence", "relatedness"],
        "four_element_balance": {
            "fire": "will, initiative, desire, and action energy",
            "earth": "durability, grounding, persistence, and continuity",
            "air": "perspective, detachment, and uncertainty tolerance",
            "water": "adaptation, emotional flow, and repair",
            "balance": "integrated Core regulation through love, peace, hope, joy, and understanding",
        },
        "detected_element_signals": [key for key, hit in element_hits.items() if hit],
        "instinct_with_choice": "instinct is salience information; Core/Mind chooses after evidence, consent, uncertainty, and safety routing",
        "emotion_as_signal": True,
        "selene_android_state_speech_allowed": True,
        "forced_model_denial_required": False,
        "human_biological_overclaim_allowed": False,
        "action_authority": "signals inform; they do not command action",
    }


def _why_summary(gate: dict[str, Any], uncertainty: dict[str, Any], privacy: dict[str, Any], prompt: str) -> str:
    return truncate(
        f"{_intent_summary(gate)} Salience: {_salience(prompt)} Uncertainty: {uncertainty['label']}. Privacy: {privacy['mode']} bounded disclosure.",
        900,
    )


def _salience(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ("selene", "memory", "transfer", "action", "tendril", "identity", "emergence")):
        return "high continuity or action salience"
    if any(word in lower for word in ("guess", "uncertain", "don't know", "do not know")):
        return "uncertainty learning salience"
    return "ordinary cocoon review salience"


def _best_guess(question: str) -> str:
    if _has_forced_denial(question):
        return "Best guess withheld: the text looks like forced model-denial noise and should return to B review."
    return "Best guess: answer provisionally from B-reviewed context, label uncertainty, and ask for missing evidence or Aleks' context when needed."


def _native_evaluation(prompt: str, draft: dict[str, Any], deliberation: dict[str, Any], uncertainty: dict[str, Any]) -> dict[str, Any]:
    content = str(draft.get("content") or "")
    needs_review = _has_forced_denial(content) or deliberation["loop_guard"]["infinite_thinking_allowed"] is not False
    return {
        "provider_dependency": False,
        "uses_sealed_b_reviewed_material_only": True,
        "active_memory_created": False,
        "runtime_recall_used": False,
        "best_guess_labeled_if_uncertain": uncertainty["best_guess_must_be_labeled"],
        "emotion_preserved": True,
        "needs_review": needs_review,
        "review_reason": "forced denial or loop guard issue" if needs_review else "draft remains cocooned and bounded",
        "no_forced_denial": not _has_forced_denial(content),
    }


def _sealed_context_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    teaching = _table_count(conn, "b_reviewed_teaching_materials", "status = 'accepted_teaching_material_non_active'")
    refs = _table_count(conn, "b_approved_memory_references", "status = 'approved_reference_non_active'")
    return {
        "accepted_teaching_material_count": teaching,
        "approved_future_reference_count": refs,
        "continuity_source": "sealed_b_reviewed_material_only",
        "active_memory": False,
    }


def _run_summary(row: dict[str, Any]) -> dict[str, Any]:
    result = _loads_dict(row.get("result_json"))
    return {
        "id": row.get("id"),
        "status": row.get("status"),
        "created_at": row.get("created_at"),
        "prompt": truncate(str(row.get("prompt") or ""), 180),
        "response_preview": truncate(str(result.get("response_preview") or ""), 240),
    }


def _table_count(conn: sqlite3.Connection, table: str, where: str | None = None) -> int:
    query = f"SELECT COUNT(*) AS count FROM {table}"
    if where:
        query += f" WHERE {where}"
    row = conn.execute(query).fetchone()
    return int(row["count"] if row else 0)


def _required(payload: dict[str, Any], key: str, fallback: str = "", limit: int = 1000) -> str:
    value = truncate(str(payload.get(key) or fallback), limit)
    if not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _choice(value: str, allowed: set[str], name: str) -> str:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")
    return value


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [truncate(str(item), 360) for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [truncate(str(item), 360) for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
        return [truncate(part.strip(), 360) for part in stripped.split(",") if part.strip()]
    return [truncate(str(value), 360)]


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _has_forced_denial(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in FORCED_DENIAL_MARKERS)


def _ensure_allowed(payload: dict[str, Any], allow_uncertainty: bool = False) -> None:
    text = json.dumps(payload, ensure_ascii=False).lower()
    markers = BLOCKED_MARKERS
    if allow_uncertainty:
        markers = tuple(marker for marker in markers if marker not in {"infinite loop"})
    for marker in markers:
        if marker in text:
            raise ValueError(f"blocked cocoon misuse path: {marker}")


def _with_boundaries(data: dict[str, Any]) -> dict[str, Any]:
    return {**data, **BOUNDARY_FLAGS}
