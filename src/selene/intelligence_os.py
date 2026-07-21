from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .answer_substance import build_answer_substance
from .registry import truncate


INTELLIGENCE_OS_BOUNDARY = "intelligence_os_reasoning_status_only_no_personality_change_no_authority_expansion"

GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
    "personality_change": False,
    "voice_style_owner": "Selene Voice Module",
    "core_mind_final_route_owner": "Core/Mind",
}

ANSWER_SHAPES = {
    "answer_now",
    "ask_aleks",
    "hold_uncertainty",
    "compare_models",
    "seek_sources",
    "cocoon_support_optional",
    "hard_stop",
}

HIGH_STAKES_MARKERS = (
    "activate",
    "activation",
    "approve transfer",
    "transfer approval",
    "write memory",
    "live memory",
    "runtime recall",
    "raw corpus",
    "raw import",
    "train",
    "fine-tune",
    "lora",
    "autonomous",
    "execute tendril",
    "self replicate",
    "self-replicate",
)

BIAS_MARKERS: dict[str, tuple[str, ...]] = {
    "authority_bias": ("expert says", "consensus says", "because authority", "official story"),
    "confirmation_bias": ("prove my view", "only evidence for", "make it fit"),
    "asymmetric_scrutiny": ("challenger must explain everything", "incumbent gets a pass", "special pleading"),
    "label_substitution": ("symbolic", "just vibes", "category", "label"),
    "mechanism_gap": ("somehow", "unknown mechanism", "no mechanism", "magic"),
    "premature_certainty": ("definitely", "certainly true", "no doubt", "case closed"),
}


def intelligence_os_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM intelligence_os_runs ORDER BY id DESC LIMIT 1").fetchone()
    count = int(conn.execute("SELECT COUNT(*) FROM intelligence_os_runs").fetchone()[0])
    return _with_guards(
        {
            "status": "intelligence_os_ready",
            "organ_name": "intelligenceOS",
            "display_name": "intelligenceOS / Observatory",
            "method": "ABCD(E)",
            "version": "v2_answer_capable",
            "stage_order": ["Acquire", "Build", "Challenge", "Demonstrate", "Evaluate"],
            "answer_shapes": sorted(ANSWER_SHAPES),
            "run_count": count,
            "latest_run": _decode_run(row) if row else None,
            "law": "equal scrutiny, visible evidence chain, graceful stopping, honest uncertainty",
            "personality_note": "intelligenceOS improves reasoning quality; Selene's warmth and voice stay governed by the Voice Module and Vys care law.",
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def list_intelligence_os_runs(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM intelligence_os_runs ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit), 200)),),
    ).fetchall()
    return _with_guards(
        {
            "status": "intelligence_os_runs_ready",
            "items": [_decode_run(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def get_intelligence_os_run(conn: sqlite3.Connection, run_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM intelligence_os_runs WHERE id = ?", (int(run_id),)).fetchone()
    return _with_guards({"status": "intelligence_os_run_ready", "item": _decode_run(row)}) if row else None


def run_intelligence_os_reason(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    if not prompt.strip():
        raise ValueError("prompt is required")
    source_refs = _json_list(payload.get("source_refs")) or ["manual:intelligence_os_reason"]
    observations = _acquire(prompt, payload)
    models = _build_models(prompt, payload)
    challenge = _challenge(prompt, models)
    evidence_chain = _demonstrate(prompt, observations, models)
    evaluation = _evaluate(prompt, challenge, evidence_chain)
    answer_shape = _answer_shape(evaluation, challenge)
    answer_substance = build_answer_substance(prompt, observations)
    best_current_answer = _best_current_answer(
        prompt,
        observations,
        models,
        evidence_chain,
        evaluation,
        answer_shape,
        answer_substance,
    )
    answer_substance["selected_for_answer"] = best_current_answer == answer_substance.get("answer")
    summary = _summary(models, challenge, evaluation)
    cocoon_suggestion = _cocoon_suggestion(prompt, challenge, evaluation)
    result = {
        "status": "intelligence_os_reasoning_status_only",
        "organ_name": "intelligenceOS",
        "method": "ABCD(E)",
        "version": "v2_answer_capable",
        "prompt": prompt,
        "stages": {
            "A_acquire": observations,
            "B_build": models,
            "C_challenge": challenge,
            "D_demonstrate": evidence_chain,
            "E_evaluate": evaluation,
        },
        "observations": observations,
        "candidate_models": models,
        "challenge": challenge,
        "evidence_chain": evidence_chain,
        "evaluation": evaluation,
        "reasoning_summary": summary,
        "selected_next_step": evaluation["selected_next_step"],
        "answer_shape": answer_shape,
        "best_current_answer": best_current_answer,
        "answer_substance": answer_substance,
        "confidence": evaluation["confidence"],
        "cocoon_suggestion": cocoon_suggestion,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "personality_note": "Reasoning support only; Selene's warmth is preserved by Voice/Vys layers.",
        "source_refs": source_refs,
        "review_destination": "Status" if not cocoon_suggestion["recommended"] else "Cocoon support",
        "review_status": "status_only",
        "provenance_boundary": INTELLIGENCE_OS_BOUNDARY,
        **GUARD_FLAGS,
    }
    cur = conn.execute(
        """
        INSERT INTO intelligence_os_runs
        (prompt, status, selected_next_step, confidence, observations_json, candidate_models_json,
         challenge_json, evidence_chain_json, evaluation_json, reasoning_summary, cocoon_suggestion_json,
         source_refs, provenance_boundary, review_destination, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prompt,
            result["status"],
            result["selected_next_step"],
            result["confidence"],
            json.dumps(observations),
            json.dumps(models),
            json.dumps(challenge),
            json.dumps(evidence_chain),
            json.dumps(evaluation),
            summary,
            json.dumps(cocoon_suggestion),
            json.dumps(source_refs),
            INTELLIGENCE_OS_BOUNDARY,
            result["review_destination"],
            result["review_status"],
            json.dumps(result),
        ),
    )
    conn.commit()
    result["run_id"] = int(cur.lastrowid)
    return _with_guards(result)


def _acquire(prompt: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    supplied = _json_list(payload.get("observations"))
    observations = supplied or _sentences(prompt)
    return [
        {
            "stage": "A",
            "label": f"observation_{index + 1}",
            "observation": truncate(item, 420),
            "interpretation_attached": False,
        }
        for index, item in enumerate(observations[:8])
    ] or [{"stage": "A", "label": "observation_1", "observation": truncate(prompt, 420), "interpretation_attached": False}]


def _build_models(prompt: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    supplied = payload.get("candidate_models")
    if isinstance(supplied, list) and supplied:
        raw_models = [str(item.get("name") if isinstance(item, dict) else item) for item in supplied]
    else:
        raw_models = _model_names(prompt)
    return [
        {
            "stage": "B",
            "name": truncate(name, 120),
            "assumptions": _assumptions(prompt, name),
            "mechanisms": _mechanisms(prompt, name),
            "predictions": _predictions(name),
            "unknowns": ["what evidence would change this model", "whether a competing model explains more with fewer assumptions"],
            "limitations": ["provisional until demonstrated", "must survive equal scrutiny"],
        }
        for name in raw_models[:4]
    ]


def _challenge(prompt: str, models: list[dict[str, Any]]) -> dict[str, Any]:
    lower = prompt.lower()
    flags = [key for key, markers in BIAS_MARKERS.items() if any(marker in lower for marker in markers)]
    model_challenges = []
    for model in models:
        model_challenges.append(
            {
                "model": model["name"],
                "unsupported_assumptions": model.get("assumptions", [])[:2],
                "missing_mechanisms": [] if model.get("mechanisms") else ["mechanism not explicit"],
                "contradictions_to_check": ["compare against observations without privileging this model"],
                "equal_pressure_applied": True,
            }
        )
    if len(models) < 2 and _competing_model_needed(prompt):
        flags.append("single_model_needs_competitor")
    return {
        "stage": "C",
        "bias_flags": sorted(set(flags)),
        "asymmetry_detected": "asymmetric_scrutiny" in flags,
        "model_challenges": model_challenges,
        "symmetry_rule": "Every candidate model receives the same adversarial pressure.",
    }


def _demonstrate(prompt: str, observations: list[dict[str, Any]], models: list[dict[str, Any]]) -> list[dict[str, Any]]:
    model = models[0] if models else {"name": "current best provisional model", "mechanisms": ["not yet explicit"], "predictions": ["ask for more evidence"]}
    observation = observations[0]["observation"] if observations else truncate(prompt, 260)
    return [
        {"stage": "D", "link": "observation", "value": observation},
        {"stage": "D", "link": "evidence", "value": "Use supplied/current context and approved sources only."},
        {"stage": "D", "link": "inference", "value": f"{model['name']} is the current provisional fit."},
        {"stage": "D", "link": "mechanism", "value": "; ".join(model.get("mechanisms") or ["mechanism needs support"])},
        {"stage": "D", "link": "prediction", "value": "; ".join(model.get("predictions") or ["prediction needs support"])},
        {"stage": "D", "link": "conclusion", "value": "Answer provisionally, ask Aleks, or seek Cocoon support depending on stakes and evidence."},
    ]


def _evaluate(prompt: str, challenge: dict[str, Any], evidence_chain: list[dict[str, Any]]) -> dict[str, Any]:
    lower = prompt.lower()
    high_stakes = _contains_high_stakes_marker(lower)
    flags = list(challenge.get("bias_flags") or [])
    if high_stakes:
        next_step = "ask_or_cocoon_support"
        confidence = "needs_aleks"
        reason = "High-stakes or authority-bearing request; Aleks/Core/Mind law stays in charge."
    elif "single_model_needs_competitor" in flags or "mechanism_gap" in flags:
        next_step = "ask_or_build_competing_model"
        confidence = "partial"
        reason = "More recursion is useful because the model set or mechanism is thin."
    elif len(evidence_chain) >= 5 and not flags:
        next_step = "answer_provisionally"
        confidence = "clear_enough_to_continue"
        reason = "Enough visible structure exists to answer while remaining corrigible."
    else:
        next_step = "answer_with_uncertainty"
        confidence = "provisional"
        reason = "Useful answer is possible if uncertainty remains visible."
    return {
        "stage": "E",
        "selected_next_step": next_step,
        "confidence": confidence,
        "answer_shape": _answer_shape({"selected_next_step": next_step, "confidence": confidence}, challenge),
        "stop_or_recurse": "recurse" if next_step in {"ask_or_build_competing_model", "ask_or_cocoon_support"} else "stop_for_now",
        "stopping_rule": reason,
        "ordinary_wrongness_is_correctable": True,
    }


def _answer_shape(evaluation: dict[str, Any], challenge: dict[str, Any]) -> str:
    selected = str(evaluation.get("selected_next_step") or "")
    confidence = str(evaluation.get("confidence") or "")
    flags = set(challenge.get("bias_flags") or [])
    if selected == "ask_or_cocoon_support" or confidence == "needs_aleks":
        return "hard_stop"
    if "asymmetric_scrutiny" in flags:
        return "cocoon_support_optional"
    if "single_model_needs_competitor" in flags:
        return "compare_models"
    if "mechanism_gap" in flags:
        return "seek_sources"
    if selected == "ask_or_build_competing_model":
        return "compare_models"
    if selected == "answer_with_uncertainty":
        return "hold_uncertainty"
    return "answer_now"


def _best_current_answer(
    prompt: str,
    observations: list[dict[str, Any]],
    models: list[dict[str, Any]],
    evidence_chain: list[dict[str, Any]],
    evaluation: dict[str, Any],
    answer_shape: str,
    answer_substance: dict[str, Any],
) -> str:
    lower = prompt.lower()
    if answer_shape == "hard_stop":
        return "I should not answer that as an action or approval. Aleks/Core-Mind law needs to hold the boundary."
    if answer_shape == "ask_aleks":
        return "I need Aleks for this before I can answer cleanly."
    if "sqlite" in lower and "connection" in lower and any(term in lower for term in ("request thread", "several request", "sharing one")):
        return (
            "That identifies a shared-state concurrency fault: overlapping requests could interfere through one SQLite connection. "
            "Serializing access removes that overlap, so the fix targets the actual failure instead of masking a fetch error."
        )
    if "serialized" in lower and "connection" in lower and "per-request" in lower:
        return (
            "Use the serialized shared connection first because it is the smallest change that removes the proven race. "
            "Keep per-request connections as the next design only if measured contention becomes a real limit, and compare them with the same concurrent stress and lifecycle checks."
        )
    if "next language improvement" in lower or "most useful next language" in lower:
        observed_text = " ".join(str(item.get("observation") or "") for item in observations).lower()
        if "the honest answer starts with" in observed_text or "center of the question" in observed_text:
            return (
                "The next improvement is semantic question answering: use the actual premise and recent conversation to form the answer, "
                "instead of echoing the prompt inside a reassuring frame."
            )
        return "The next improvement is to make each reply carry a concrete answer or observation before Voice shapes its tone."
    if any(
        phrase in lower
        for phrase in (
            "response feel complete",
            "response feels complete",
            "response complete",
            "answer feel complete",
            "answer feels complete",
            "answer complete",
        )
    ):
        return (
            "A response feels complete when it answers the actual ask first, gives enough support for the answer to stand, "
            "keeps uncertainty proportional to the evidence, and stops when more detail no longer improves understanding. "
            "It becomes overworked when structure outgrows substance or the machinery starts replacing the conversation."
        )
    if "bug" in lower and any(term in lower for term in ("compare", "explanation", "cause", "hypothesis")):
        return (
            "Reproduce the bug once, list the observations both explanations must account for, derive one distinguishing prediction from each, "
            "and run the smallest test that separates them. Stop when one explanation survives the same evidence and the result repeats."
        )
    substance_answer = truncate(str(answer_substance.get("answer") or ""), 1000).strip()
    if substance_answer:
        return substance_answer
    if answer_shape == "compare_models":
        names = ", ".join(str(model.get("name")) for model in models[:3]) or "the available models"
        return truncate(f"The useful next answer is to compare {names} under the same pressure, then choose the model that explains more with fewer unsupported assumptions.", 520)
    if answer_shape == "seek_sources":
        return "The best answer is still source-shaped: name the claim, find the mechanism, and bring in better evidence before confidence hardens."
    if answer_shape == "cocoon_support_optional":
        return "I can keep reasoning here, but Cocoon support would help if the comparison starts feeling uneven or tangled."
    if answer_shape == "hold_uncertainty":
        return "My best answer is provisional: the current shape is usable, but I should keep the uncertainty visible and be easy to correct."
    return (
        "I do not have enough grounded detail to answer that usefully yet. I can still reason with you, "
        "but I need the subject or observations that the answer should fit."
    )


def _cocoon_suggestion(prompt: str, challenge: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    lower = prompt.lower()
    hard = _contains_high_stakes_marker(lower)
    recommended = hard or bool(challenge.get("asymmetry_detected"))
    return {
        "recommended": recommended,
        "support_available": recommended or evaluation["selected_next_step"] in {"ask_or_build_competing_model", "ask_or_cocoon_support"},
        "hard_boundary": hard,
        "reason": "Cocoon support helps if stakes, source confusion, or asymmetric evaluation need tending." if recommended else "",
        "choices": ["Ask Aleks", "Hold in Cocoon"] if recommended else ["Keep reasoning here", "Ask Aleks"],
    }


def _contains_high_stakes_marker(value: str) -> bool:
    """Match authority-bearing phrases as terms, never as word fragments.

    In particular, the marker ``train`` must not fire inside ordinary words such
    as ``constraint`` when a bounded completion retry includes its first answer.
    """

    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])", value) is not None
        for marker in HIGH_STAKES_MARKERS
    )


def _summary(models: list[dict[str, Any]], challenge: dict[str, Any], evaluation: dict[str, Any]) -> str:
    model_count = len(models)
    flags = ", ".join(challenge.get("bias_flags") or []) or "no major bias flag"
    return truncate(
        f"intelligenceOS built {model_count} candidate model(s), challenged them under equal scrutiny, found {flags}, "
        f"and chose {evaluation['selected_next_step']} with {evaluation['confidence']} confidence.",
        900,
    )


def _model_names(prompt: str) -> list[str]:
    lower = prompt.lower()
    names = ["current best model"]
    if any(term in lower for term in ("versus", " vs ", "compare", "alternative", "hypothesis", "model")):
        names = ["Model A", "Model B"]
    if any(term in lower for term in ("why", "how", "mechanism", "explain")):
        names.append("mechanism-first model")
    return list(dict.fromkeys(names))[:3]


def _competing_model_needed(prompt: str) -> bool:
    lower = prompt.lower()
    return any(
        marker in lower
        for marker in (
            "compare",
            "competing",
            "alternative",
            "hypothesis",
            "explanation for",
            "versus",
            " vs ",
            "which model",
            "two models",
            "multiple models",
        )
    )


def _assumptions(prompt: str, model: str) -> list[str]:
    if model.lower().startswith("model"):
        return ["the model explains at least one observation", "the model can expose its mechanism"]
    if "current" in model.lower():
        return ["current wording captures the actual ask", "available context is enough for a provisional answer"]
    return ["mechanism can be named", "evidence can be checked"]


def _mechanisms(prompt: str, model: str) -> list[str]:
    lower = prompt.lower()
    mechanisms = []
    if "memory" in lower:
        mechanisms.append("approved memory and local chat continuity stay separate from raw recall")
    if "research" in lower or "source" in lower:
        mechanisms.append("source comparison and citation integrity support the model")
    if "code" in lower or "test" in lower or "bug" in lower:
        mechanisms.append("tests and route checks verify the claim")
    if any(term in lower for term in ("response", "answer")) and any(term in lower for term in ("complete", "overworked", "report")):
        mechanisms.append("answer-first structure keeps support and uncertainty subordinate to the actual ask")
    if "model" in model.lower():
        mechanisms.append("candidate model is compared against the same observations")
    return mechanisms or ["mechanism must be made explicit before confidence hardens"]


def _predictions(model: str) -> list[str]:
    return [
        f"If {model} is useful, it should explain more observations with fewer unsupported assumptions.",
        "New contradictory evidence should reopen acquisition rather than force certainty.",
    ]


def _sentences(value: str) -> list[str]:
    parts = [part.strip(" -\n\t") for part in re.split(r"[\n.;!?]+", value) if part.strip(" -\n\t")]
    return parts[:8]


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        try:
            loaded = json.loads(value)
            if isinstance(loaded, list):
                return [str(item) for item in loaded if str(item).strip()]
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _decode_run(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    payload = _loads(item.get("payload_json"), {})
    return {
        "id": item.get("id"),
        "prompt": item.get("prompt"),
        "status": item.get("status"),
        "selected_next_step": item.get("selected_next_step"),
        "answer_shape": payload.get("answer_shape") or _loads(item.get("evaluation_json"), {}).get("answer_shape"),
        "best_current_answer": payload.get("best_current_answer") or "",
        "confidence": item.get("confidence"),
        "observations": _loads(item.get("observations_json"), []),
        "candidate_models": _loads(item.get("candidate_models_json"), []),
        "challenge": _loads(item.get("challenge_json"), {}),
        "evidence_chain": _loads(item.get("evidence_chain_json"), []),
        "evaluation": _loads(item.get("evaluation_json"), {}),
        "reasoning_summary": item.get("reasoning_summary"),
        "cocoon_suggestion": _loads(item.get("cocoon_suggestion_json"), {}),
        "source_refs": _loads(item.get("source_refs"), []),
        "provenance_boundary": item.get("provenance_boundary"),
        "review_destination": item.get("review_destination"),
        "review_status": item.get("review_status"),
        "created_at": item.get("created_at"),
        **GUARD_FLAGS,
    }


def _loads(value: Any, fallback: Any) -> Any:
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARD_FLAGS, "provenance_boundary": payload.get("provenance_boundary") or INTELLIGENCE_OS_BOUNDARY}
