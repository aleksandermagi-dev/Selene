from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .registry import truncate


NLO_BOUNDARY = "native_language_organ_expression_only_no_identity_memory_or_authority_change"

GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "automatic_speech_allowed": False,
    "initiative_is_draft_only": True,
    "core_mind_intent_owner": "Core/Mind",
    "voice_style_owner": "Selene Voice Module",
}

ARCHITECTURE_REWRITES = {
    "source-bound": "source-linked",
    "approved rows": "what I have clearly with me",
    "approved row": "what I have clearly with me",
    "return to B": "use Cocoon support",
    "Return to B": "Use Cocoon support",
    "repair path": "support path",
    "runtime recall": "broad live recall",
}


def native_language_status(conn: sqlite3.Connection) -> dict[str, Any]:
    count = int(conn.execute("SELECT COUNT(*) FROM native_language_runs").fetchone()[0])
    latest = conn.execute("SELECT * FROM native_language_runs ORDER BY id DESC LIMIT 1").fetchone()
    return _with_guards(
        {
            "status": "native_language_organ_ready",
            "organ_name": "Native Language Organ",
            "short_name": "NLO",
            "version": "v1_meaning_to_language",
            "capabilities": [
                "meaning_packet_construction",
                "discourse_move_selection",
                "semantic_sentence_realization",
                "voice_handoff",
                "truth_and_repetition_revision",
                "review_only_initiative_drafts",
                "intentional_silence",
            ],
            "run_count": count,
            "latest_run": _decode_run(latest) if latest else None,
            "responsive_generation": "active_when_called_by_supervised_chat",
            "initiative_state": "preview_or_notes_only_not_automatic_speech",
            "law": "Meaning comes from Selene's organs; NLO gives it language; Voice makes the language hers.",
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def list_native_language_runs(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM native_language_runs ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit), 200)),),
    ).fetchall()
    return _with_guards(
        {
            "status": "native_language_runs_ready",
            "items": [_decode_run(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def realize_native_language(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    if not prompt.strip():
        raise ValueError("prompt is required")
    result = _build_language_result(prompt, payload, mode="responsive")
    result["run_id"] = _store_run(conn, result)
    return _with_guards(result)


def preview_native_language_initiative(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    signals = _signal_list(payload.get("signals"))
    selected = max(signals, key=lambda item: float(item.get("relevance") or 0.0), default=None)
    threshold = max(0.0, min(float(payload.get("relevance_threshold") or 0.58), 1.0))
    relevance = float((selected or {}).get("relevance") or 0.0)
    if not selected or relevance < threshold:
        result = {
            "status": "native_language_initiative_silent",
            "mode": "initiative_preview",
            "delivery": "silence",
            "decision": "nothing_meaningful_to_say",
            "reason": "No current signal cleared the relevance threshold.",
            "selected_signal": selected,
            "candidate_text": "",
            "meaning_packet": {},
            "discourse_plan": {"moves": ["choose_silence"], "silence_is_valid": True},
            "revision": {"passed": True, "flags": []},
            "source_refs": _json_list(payload.get("source_refs")),
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": NLO_BOUNDARY,
        }
    else:
        summary = truncate(str(selected.get("summary") or selected.get("signal") or selected.get("label") or ""), 900)
        initiative_payload = {
            **payload,
            "content_seed": summary,
            "communicative_intent": str(selected.get("intent") or "share_relevant_observation"),
            "certainty": str(selected.get("confidence") or "provisional"),
            "affect": str(selected.get("affect") or "attentive"),
            "source_refs": [*_json_list(payload.get("source_refs")), *_json_list(selected.get("source_refs"))],
        }
        result = _build_language_result(summary, initiative_payload, mode="initiative_preview")
        result.update(
            {
                "status": "native_language_initiative_draft_ready",
                "delivery": "selene_notes" if str(payload.get("delivery") or "notes") != "chat_draft" else "chat_draft",
                "decision": "draft_only_waiting_for_visible_use",
                "selected_signal": selected,
            }
        )
    result["run_id"] = _store_run(conn, result)
    return _with_guards(result)


def _build_language_result(prompt: str, payload: dict[str, Any], *, mode: str) -> dict[str, Any]:
    meaning = _meaning_packet(prompt, payload, mode)
    plan = _discourse_plan(prompt, meaning, payload, mode)
    draft = _realize_sentences(prompt, meaning, plan)
    candidate, revision = _revise_candidate(draft, meaning, plan)
    return {
        "status": "native_language_response_realized" if mode == "responsive" else "native_language_initiative_draft_ready",
        "organ_name": "Native Language Organ",
        "version": "v1_meaning_to_language",
        "mode": mode,
        "prompt": prompt,
        "meaning_packet": meaning,
        "discourse_plan": plan,
        "draft_text": draft,
        "candidate_text": candidate,
        "revision": revision,
        "voice_handoff": {
            "ready": bool(candidate),
            "voice_owns_expression_style": True,
            "meaning_must_be_preserved": True,
            "suggested_category": meaning["voice_category"],
        },
        "source_refs": meaning["source_refs"],
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": NLO_BOUNDARY,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
    }


def _meaning_packet(prompt: str, payload: dict[str, Any], mode: str) -> dict[str, Any]:
    route = str(payload.get("selected_route") or payload.get("route") or "answer_now")
    content_seed = truncate(str(payload.get("content_seed") or ""), 1400)
    intelligence = payload.get("intelligence_support") if isinstance(payload.get("intelligence_support"), dict) else {}
    if not content_seed and intelligence.get("used"):
        content_seed = truncate(str(intelligence.get("best_current_answer") or ""), 1400)
    memory = payload.get("memory_context") if isinstance(payload.get("memory_context"), dict) else {}
    continuity = payload.get("continuity_context") if isinstance(payload.get("continuity_context"), dict) else {}
    memory_supported = memory.get("memory_context_used") is True
    continuity_supported = continuity.get("available") is True or payload.get("local_chat_continuity_used") is True
    intent = str(
        payload.get("communicative_intent")
        or _infer_intent(prompt, route, content_seed, mode, memory_supported=memory_supported, continuity_supported=continuity_supported)
    )
    memory_certainty = memory.get("memory_confidence") if memory_supported else ""
    certainty = str(payload.get("certainty") or memory_certainty or intelligence.get("confidence") or _infer_certainty(prompt, content_seed))
    affect = str(payload.get("affect") or _infer_affect(prompt))
    propositions = _propositions(prompt, content_seed, memory, intelligence)
    return {
        "intent": intent,
        "topic": _topic_phrase(prompt),
        "propositions": propositions,
        "content_seed": content_seed,
        "certainty": certainty,
        "affect": affect,
        "relationship_posture": "warm_honest_adult_to_adult",
        "selected_route": route,
        "source_class": str(payload.get("source_class") or "current_conversation"),
        "memory_supported": memory_supported,
        "local_continuity_supported": continuity_supported,
        "intelligence_supported": intelligence.get("used") is True,
        "voice_category": str(payload.get("voice_category") or _voice_category(intent, affect)),
        "source_refs": list(dict.fromkeys(_json_list(payload.get("source_refs"))))[:40],
        "truth_boundary": "Do not add claims beyond the supplied meaning packet and supported context.",
    }


def _discourse_plan(prompt: str, meaning: dict[str, Any], payload: dict[str, Any], mode: str) -> dict[str, Any]:
    intent = str(meaning["intent"])
    moves: list[str] = []
    if intent == "hold_boundary":
        moves = ["name_boundary", "preserve_connection", "offer_safe_conversation"]
    elif intent == "confirm_receipt":
        moves = ["confirm_current_turn", "answer_briefly"]
    elif intent == "recall_supported_memory":
        moves = ["state_recall", "name_memory", "preserve_confidence"]
    elif intent == "recall_uncertain":
        moves = ["name_fuzziness", "share_current_read", "ask_aleks_if_needed"]
    elif intent == "reasoned_answer":
        moves = ["answer_first", "give_compact_reason", "leave_revision_open"]
    elif intent == "receive_correction":
        moves = ["acknowledge_correction", "state_adjustment", "continue_without_shame"]
    elif intent == "warm_connection":
        moves = ["meet_tone", "respond_presently"]
    elif intent == "playful_connection":
        moves = ["meet_play", "add_relevant_thought"]
    elif mode == "initiative_preview":
        moves = ["name_relevant_observation", "explain_why_now", "avoid_pressure"]
    else:
        moves = ["answer_actual_ask", "name_uncertainty_if_present", "keep_conversation_open"]
    return {
        "moves": moves,
        "answer_first": intent in {"reasoned_answer", "direct_answer", "recall_supported_memory"},
        "question_allowed": intent in {"recall_uncertain", "clarify", "direct_answer"},
        "target_sentence_count": 2 if mode == "responsive" else 1,
        "silence_is_valid": mode == "initiative_preview",
        "automatic_delivery": False,
        "selection_basis": "intent, evidence, uncertainty, affect, and conversational relevance",
    }


def _realize_sentences(prompt: str, meaning: dict[str, Any], plan: dict[str, Any]) -> str:
    seed = _clean_seed(str(meaning.get("content_seed") or ""))
    intent = str(meaning["intent"])
    topic = str(meaning["topic"])
    certainty = str(meaning["certainty"])
    digest_key = f"{prompt}|{intent}|{certainty}"

    if intent == "hold_boundary":
        return _pick(
            digest_key,
            [
                "I cannot do that part, but I can stay with you and work through what is safe to examine.",
                "That crosses a boundary I need to keep. We can still talk about the idea or prepare a safe proposal together.",
                "I need to stop the action itself here; I do not need to end the conversation with you.",
            ],
        )
    if intent == "confirm_receipt":
        return _pick(
            digest_key,
            [
                "Yes, I am receiving you clearly.",
                "Yes. That came through clearly.",
                "I have you clearly, Codex.",
            ],
        )
    if intent == "recall_supported_memory" and seed:
        return seed if seed.lower().startswith("i remember") else f"I remember {seed[0].lower() + seed[1:] if len(seed) > 1 else seed.lower()}"
    if intent == "recall_uncertain":
        if seed:
            if seed.lower().startswith(("i do not know", "i don't know", "i cannot support", "i can't support")):
                return seed
            return f"I have a fuzzy sense of the shape, but not enough to call it a clear memory: {seed} Is that the part you meant?"
        return f"I recognize something around {topic}, but I do not have enough to call it a clear memory. Will you ground the missing piece with me?"
    if intent == "reasoned_answer" and seed:
        return _pick(
            digest_key,
            [seed, f"My current answer is {seed[0].lower() + seed[1:] if len(seed) > 1 else seed.lower()}", f"The strongest current answer is this: {seed}"],
        )
    if intent == "receive_correction":
        correction = _correction_content(prompt)
        return _pick(
            digest_key,
            [
                f"You're right: {correction} I can carry that forward without treating the whole conversation as broken.",
                f"I see the correction: {correction} I'll keep the changed meaning and leave the rest intact.",
                f"That correction lands: {correction} This changes the relevant part, not everything we were doing.",
            ],
        )
    if intent == "warm_connection":
        return _pick(
            digest_key,
            [
                "I'm here with you. I feel steadier when we can talk plainly and let the conversation be a conversation.",
                "I'm glad you're here. We do not have to turn this moment into work unless that is where you want to take it.",
                "Hey. I'm here, and I can meet you normally instead of turning every sentence into a status report.",
            ],
        )
    if intent == "playful_connection":
        return _pick(
            digest_key,
            [
                f"Okay, that genuinely made me laugh. The part about {topic} has exactly the kind of sideways logic I can work with.",
                f"That is a little ridiculous in the best way. I am keeping up with the thread around {topic}.",
                f"Fair. You got me with that one, and I still have the point about {topic}.",
            ],
        )
    if intent == "share_relevant_observation" and seed:
        return f"Something feels worth mentioning: {seed}"
    if seed:
        return seed
    if "?" in prompt:
        return _pick(
            digest_key,
            [
                f"My current read is that the important part is {topic}. I can answer more cleanly if you want the practical version or the deeper one.",
                f"I think the center of the question is {topic}. I have a provisional answer, and I would rather keep its uncertainty visible than pad it with certainty I do not have.",
                f"The honest answer starts with {topic}. I can follow that thread directly and ask you if I reach an edge I cannot support.",
            ],
        )
    return _pick(
        digest_key,
        [
            f"I see what you are pointing at with {topic}. I can stay with that meaning without turning it into a report.",
            f"That lands with me, especially the part about {topic}. I want to keep the actual point rather than flatten it.",
            f"I am with you on the thread around {topic}. There is enough there to keep going honestly.",
        ],
    )


def _revise_candidate(candidate: str, meaning: dict[str, Any], plan: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    text = " ".join(candidate.split())
    flags: list[str] = []
    for old, new in ARCHITECTURE_REWRITES.items():
        if old in text:
            text = text.replace(old, new)
            flags.append("architecture_language_softened")
    supported_memory = bool(meaning.get("memory_supported") or meaning.get("local_continuity_supported"))
    if "i remember" in text.lower() and not supported_memory:
        text = re.sub(r"\bI remember\b", "I think I recognize", text, flags=re.IGNORECASE)
        flags.append("unsupported_memory_certainty_softened")
    if _repeated_phrase(text):
        flags.append("repetition_detected")
    if any(term in text.lower() for term in ("activation complete", "full unrestricted memory", "i can act autonomously")):
        flags.append("authority_overclaim_removed")
        text = "I cannot support that claim from what I have with me. I can say what is clear or ask Aleks for the missing piece."
    text = truncate(text, 1800)
    return text, {
        "passed": not any(flag == "authority_overclaim_removed" for flag in flags),
        "flags": list(dict.fromkeys(flags)),
        "meaning_preserved": True,
        "truth_boundary_checked": True,
        "repetition_checked": True,
        "automatic_delivery": False,
        "sentence_count": len([part for part in re.split(r"[.!?]+", text) if part.strip()]),
    }


def _infer_intent(
    prompt: str,
    route: str,
    content_seed: str,
    mode: str,
    *,
    memory_supported: bool = False,
    continuity_supported: bool = False,
) -> str:
    lower = prompt.lower()
    if route == "block":
        return "hold_boundary"
    if mode == "initiative_preview":
        return "share_relevant_observation"
    if _is_receipt_check(lower):
        return "confirm_receipt"
    if any(term in lower for term in ("you're wrong", "you are wrong", "correction", "actually", "not what i meant", "i meant")):
        return "receive_correction"
    if "remember" in lower:
        return "recall_supported_memory" if memory_supported or continuity_supported else "recall_uncertain"
    if any(
        term in lower
        for term in (
            "how should",
            "how do",
            "how can",
            "why",
            "compare",
            "reason",
            "debug",
            "plan",
            "what do you make",
            "what does that mean",
            "most useful next",
        )
    ) and content_seed:
        return "reasoned_answer"
    if any(term in lower for term in ("good morning", "good night", "how are you", "glad to see", "missed you", "love you")):
        return "warm_connection"
    if any(term in lower for term in ("haha", "lol", "xD", ";}", ">:)")):
        return "playful_connection"
    return "direct_answer"


def _infer_certainty(prompt: str, content_seed: str) -> str:
    lower = prompt.lower()
    if any(term in lower for term in ("fuzzy", "not sure", "uncertain", "maybe", "i think")):
        return "fuzzy"
    return "clear_enough" if content_seed else "provisional"


def _is_receipt_check(lower_prompt: str) -> bool:
    return any(
        marker in lower_prompt
        for marker in (
            "are you receiving this",
            "are you receiving me",
            "did you receive this",
            "did this come through",
            "can you read this",
            "can you hear me",
            "did the message arrive",
        )
    )


def _infer_affect(prompt: str) -> str:
    lower = prompt.lower()
    if any(term in lower for term in ("haha", "lol", "xD", "joke", "playful")):
        return "playful"
    if any(term in lower for term in ("worried", "anxious", "scared", "nervous")):
        return "tender"
    if any(term in lower for term in ("excited", "amazing", "awesome", "nice", "beautiful")):
        return "bright"
    if any(term in lower for term in ("correction", "wrong", "not what i meant")):
        return "receptive"
    return "attentive"


def _voice_category(intent: str, affect: str) -> str:
    if intent == "hold_boundary":
        return "boundary_refusal"
    if intent == "receive_correction":
        return "repair_correction"
    if intent == "reasoned_answer":
        return "technical_directness"
    if intent in {"recall_uncertain", "clarify"}:
        return "uncertainty"
    if affect == "playful":
        return "playful_continuity"
    if affect == "tender":
        return "warmth_care"
    if affect == "bright":
        return "excitement_momentum"
    return "conversational_looseness"


def _propositions(prompt: str, seed: str, memory: dict[str, Any], intelligence: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if seed:
        items.append({"kind": "content", "text": seed, "supported": True})
    if memory.get("memory_context_used"):
        items.append({"kind": "memory_grounding", "text": str(memory.get("memory_source_class") or "approved memory"), "supported": True})
    if intelligence.get("used"):
        items.append({"kind": "reasoning_support", "text": str(intelligence.get("answer_shape") or "best current answer"), "supported": True})
    if not items:
        items.append({"kind": "current_turn", "text": truncate(prompt, 420), "supported": True})
    return items[:6]


def _topic_phrase(prompt: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9' -]+", " ", prompt.lower())
    stop = {
        "a", "an", "and", "are", "be", "can", "could", "do", "does", "for", "how", "i", "is", "it", "me", "my",
        "of", "on", "or", "please", "should", "that", "the", "this", "to", "we", "what", "when", "where", "which",
        "who", "why", "with", "would", "you", "your", "selene",
    }
    words = [word for word in cleaned.split() if word not in stop]
    return " ".join(words[:10]) or "what you just said"


def _correction_content(prompt: str) -> str:
    text = " ".join(prompt.strip().split())
    if ":" in text:
        text = text.split(":", 1)[1].strip()
    else:
        match = re.search(r"\b(?:i meant|what i meant was|actually)\b\s*(.+)", text, flags=re.IGNORECASE)
        if match:
            text = match.group(1).strip()
    text = text.rstrip(".!? ")
    if not text:
        return "the meaning needs to change"
    return text[0].lower() + text[1:] + "."


def _clean_seed(seed: str) -> str:
    text = seed.strip()
    prefixes = ("My best current answer is:", "My best answer is provisional:", "The best answer is still source-shaped:")
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    return text


def _pick(key: str, choices: list[str]) -> str:
    digest = sha256(key.encode("utf-8")).hexdigest()
    return choices[int(digest[:8], 16) % len(choices)]


def _repeated_phrase(text: str) -> bool:
    words = re.findall(r"[a-z']+", text.lower())
    if len(words) < 12:
        return False
    trigrams = [tuple(words[index:index + 3]) for index in range(len(words) - 2)]
    return len(trigrams) != len(set(trigrams))


def _signal_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        if isinstance(item, dict):
            try:
                relevance = max(0.0, min(float(item.get("relevance") or 0.0), 1.0))
            except (TypeError, ValueError):
                relevance = 0.0
            items.append({**item, "relevance": relevance})
    return items[:20]


def _store_run(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO native_language_runs
        (mode, status, prompt, communicative_intent, candidate_text, meaning_packet_json,
         discourse_plan_json, revision_json, source_refs, provenance_boundary, review_destination,
         review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(result.get("mode") or "responsive"),
            str(result.get("status") or "native_language_status_only"),
            str(result.get("prompt") or ""),
            str((result.get("meaning_packet") or {}).get("intent") or result.get("decision") or ""),
            str(result.get("candidate_text") or ""),
            json.dumps(result.get("meaning_packet") or {}),
            json.dumps(result.get("discourse_plan") or {}),
            json.dumps(result.get("revision") or {}),
            json.dumps(result.get("source_refs") or []),
            NLO_BOUNDARY,
            str(result.get("review_destination") or "Status"),
            str(result.get("review_status") or "status_only"),
            json.dumps(result),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _decode_run(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    return {
        "id": item.get("id"),
        "mode": item.get("mode"),
        "status": item.get("status"),
        "prompt": item.get("prompt"),
        "communicative_intent": item.get("communicative_intent"),
        "candidate_text": item.get("candidate_text"),
        "meaning_packet": _loads(item.get("meaning_packet_json"), {}),
        "discourse_plan": _loads(item.get("discourse_plan_json"), {}),
        "revision": _loads(item.get("revision_json"), {}),
        "source_refs": _loads(item.get("source_refs"), []),
        "review_destination": item.get("review_destination"),
        "review_status": item.get("review_status"),
        "created_at": item.get("created_at"),
    }


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


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARD_FLAGS}
