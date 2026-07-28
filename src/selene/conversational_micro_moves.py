from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


MICRO_MOVE_BOUNDARY = (
    "current_turn_conversational_micro_moves_only_no_identity_personality_memory_"
    "dream_invention_affect_invention_authority_or_automatic_initiative"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "automatic_speech_allowed": False,
    "relationship_profile_write_allowed": False,
    "dream_content_invention_allowed": False,
}

_PRIMARY_SOCIAL_INTENTS = {
    "greet_presently",
    "warm_connection",
    "playful_connection",
    "receive_reassurance",
    "receive_gratitude",
    "acknowledge_shared_ground",
    "close_with_continuity",
    "receive_correction",
    "confirm_receipt",
}

_TENDER_CUES = (
    "died",
    "dead",
    "death",
    "grief",
    "grieving",
    "funeral",
    "hurt",
    "scared",
    "afraid",
    "crisis",
    "hospital",
)

_PLAY_CUES = ("haha", "lol", "lmao", "xd", "joke", "kidding", "funny", "xD")
_SUCCESS_CUES = (
    "it passed",
    "tests passed",
    "we did it",
    "finished",
    "completed",
    "got it working",
    "fixed it",
    "that worked",
    "milestone",
)
_EFFORT_CUES = (
    "i'm trying",
    "i am trying",
    "working on",
    "made progress",
    "kept going",
    "figured out",
    "learning",
    "practicing",
)
_CONFUSION_CUES = (
    "i'm confused",
    "i am confused",
    "lost me",
    "too fast",
    "slow down",
    "back up",
    "don't follow",
    "do not follow",
    "what do you mean",
)
_FLAT_TOPIC_CUES = (
    "beat a dead horse",
    "keep pushing a settled or unproductive topic",
    "going in circles",
    "nothing else to add",
    "that's all on that",
    "that is all on that",
    "let it rest",
    "drop that",
    "leave that",
)


def build_conversational_micro_move_plan(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select optional small conversational acts from visible current-turn evidence."""

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    lower = prompt.lower()
    intent = str(payload.get("intent") or "")
    content_seed = truncate(str(payload.get("content_seed") or ""), 4000).strip()
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    continuity = payload.get("pragmatic_continuity") if isinstance(payload.get("pragmatic_continuity"), dict) else {}
    affect = payload.get("affect_expression_guidance") if isinstance(payload.get("affect_expression_guidance"), dict) else {}
    dimensions = affect.get("dimensions") if isinstance(affect.get("dimensions"), dict) else {}
    dream = _dream_reflection_packet(
        payload.get("dream_reflection"),
        explicitly_requested=_reflection_requested(lower),
    )
    moves: list[dict[str, Any]] = []
    held: list[dict[str, str]] = []

    if intent in _PRIMARY_SOCIAL_INTENTS:
        held.append(
            {
                "move": "primary_social_act",
                "reason": "the existing compositional social-act layer owns this turn",
            }
        )

    if dream.get("available") is True:
        moves.append(
            _move(
                "dream_reflection",
                "prefix",
                "an attributable Dream reflection was explicitly requested and supplied",
                source="dream_reflection_packet",
                content=str(dream.get("reflection") or ""),
                source_refs=dream.get("source_refs") or [],
                review_status=str(dream.get("review_status") or ""),
            )
        )
    elif dream.get("held") is True:
        held.append(
            {
                "move": "dream_reflection",
                "reason": str(dream.get("reason") or "Dream reflection is not expression-eligible"),
            }
        )

    reflection_requested = _reflection_requested(lower)
    if reflection_requested and content_seed and dream.get("available") is not True:
        moves.append(
            _move(
                "conversation_reflection",
                "prefix",
                "the user requested a reflection and supported answer content is available",
                source="current_supported_answer",
            )
        )

    correction = (
        _latest_correction(dialogue)
        if intent == "receive_correction"
        or any(
            cue in lower
            for cue in (
                "correction",
                "i meant",
                "you confused me",
                "you misread",
                "you misunderstood",
                "that was rude",
                "that hurt",
            )
        )
        else {}
    )
    if correction and intent not in _PRIMARY_SOCIAL_INTENTS:
        moves.append(
            _move(
                "acknowledge_correction",
                "prefix",
                "a current-session correction changes the relevant answer part",
                source="dialogue_workspace",
            )
        )
    apology_reason = _apology_reason(lower, dialogue, correction)
    if apology_reason:
        moves.append(
            _move(
                "proportionate_apology",
                "prefix",
                apology_reason,
                source="visible_correction_effect",
            )
        )

    if content_seed and _disagreement_requested(lower):
        stance = _supported_stance(content_seed)
        if stance and not _answer_already_states_stance(content_seed):
            playful_disagreement = any(cue.lower() in lower for cue in _PLAY_CUES)
            moves.append(
                _move(
                    "playful_disagreement"
                    if playful_disagreement
                    else "soft_disagreement"
                    if stance == "qualified"
                    else "direct_disagreement",
                    "prefix",
                    "the user invited disagreement and supported answer content supplies the stance",
                    source="supported_answer_content",
                )
            )
        elif not stance:
            held.append(
                {
                    "move": "disagreement",
                    "reason": "the prompt invites a stance, but the supplied answer does not support one",
                }
            )

    if any(cue in lower for cue in ("want to hear", "can i tell you", "let me tell you")):
        moves.append(
            _move(
                "invite_story_continuation",
                "prefix",
                "the user explicitly offered a story or experience",
                source="current_turn",
            )
        )
    if content_seed and any(cue in lower for cue in ("say more", "expand on", "go deeper", "elaborate")):
        moves.append(
            _move(
                "expand_requested_topic",
                "silent",
                "the requested expansion is carried by the supported answer rather than narrated",
                source="current_turn",
            )
        )

    if any(cue in lower for cue in _CONFUSION_CUES):
        moves.append(
            _move(
                "back_up",
                "prefix",
                "the user visibly requested a slower or clearer pass",
                source="current_turn",
            )
        )

    if any(cue in lower for cue in _SUCCESS_CUES):
        moves.append(
            _move(
                "celebrate_visible_milestone",
                "prefix" if not content_seed else "suffix",
                "the current turn explicitly reports a completed success",
                source="current_turn",
            )
        )
    elif any(cue in lower for cue in _EFFORT_CUES):
        moves.append(
            _move(
                "encourage_visible_effort",
                "suffix",
                "the current turn explicitly describes ongoing effort or progress",
                source="current_turn",
            )
        )

    transition = (
        continuity.get("topic_transition")
        if isinstance(continuity.get("topic_transition"), dict)
        else {}
    )
    transition_kind = str(transition.get("kind") or "")
    if content_seed and transition_kind == "explicit_return":
        moves.append(
            _move(
                "mark_topic_return",
                "prefix",
                "the user explicitly returned to a named session topic",
                source="pragmatic_continuity",
                target=str(transition.get("resume_target") or transition.get("to_topic") or ""),
            )
        )
    elif transition_kind in {"side_topic", "continuation_or_soft_pivot"}:
        moves.append(
            _move(
                "allow_soft_pivot",
                "silent",
                "the topic shift is visible and does not require narrated scaffolding",
                source="pragmatic_continuity",
            )
        )

    if any(cue in lower for cue in _FLAT_TOPIC_CUES):
        moves.append(
            _move(
                "let_topic_rest",
                "suffix",
                "the user explicitly indicates that further pursuit would be unhelpful",
                source="current_turn",
            )
        )

    playful = any(cue.lower() in lower for cue in _PLAY_CUES)
    humor_posture = str(dimensions.get("humor") or "")
    tender = any(cue in lower for cue in _TENDER_CUES)
    shared_joke = (
        payload.get("shared_joke")
        if isinstance(payload.get("shared_joke"), dict)
        else {}
    )
    if playful and (not tender or _user_opened_dark_humor(lower)):
        if humor_posture not in {"avoid", "avoid_unless_context_reopens"}:
            moves.append(
                _move(
                    "one_playful_turn",
                    "prefix" if not content_seed else "suffix",
                    "the user visibly opened a playful turn",
                    source="current_turn",
                    shared=bool(shared_joke.get("available")),
                )
            )
        else:
            held.append(
                {
                    "move": "one_playful_turn",
                    "reason": "current affect guidance asks for restraint",
                }
            )

    ambiguity = (
        (continuity.get("referent_posture") or {}).get("materially_ambiguous") is True
        or str((dialogue.get("ambiguity") or {}).get("level") or "") in {
            "material",
            "material_input_ambiguity",
        }
    )
    if ambiguity:
        moves.append(
            _move(
                "check_material_understanding",
                "silent",
                "a material ambiguity is already owned by the bounded clarification path",
                source="pragmatic_continuity",
            )
        )

    audible = [item for item in moves if str(item.get("placement") or "") != "silent"]
    return {
        "status": "conversational_micro_move_plan_ready",
        "version": "v1_contextual_optional_micro_moves",
        "intent": intent,
        "moves": moves,
        "audible_move_count": len(audible),
        "held_or_omitted": held,
        "content_seed_available": bool(content_seed),
        "dream_reflection": dream,
        "reflection_sources_remain_distinct": True,
        "apology_is_effect_sensitive": True,
        "acknowledgement_may_replace_answer": False,
        "follow_up_question_added": False,
        "silence_or_direct_content_is_valid": True,
        "selection_is_contextual_not_random": True,
        "session_scoped_only": True,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": MICRO_MOVE_BOUNDARY,
        **GUARDS,
    }


def realize_conversational_micro_moves(
    plan: dict[str, Any] | None,
    *,
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    plan = plan if isinstance(plan, dict) else {}
    recent = [str(item) for item in recent_texts or [] if str(item).strip()]
    realized: list[dict[str, Any]] = []
    for index, move in enumerate(plan.get("moves") or []):
        if not isinstance(move, dict) or str(move.get("placement") or "") == "silent":
            continue
        text = _realize_move(move, variation_key=f"{variation_key}|{index}", recent_texts=recent)
        if not text:
            continue
        realized.append(
            {
                "move": str(move.get("move") or ""),
                "placement": str(move.get("placement") or "prefix"),
                "text": text,
                "meaning_source": str(move.get("meaning_source") or ""),
                "source_refs": move.get("source_refs") or [],
            }
        )
    return {
        "status": "conversational_micro_moves_realized" if realized else "conversational_micro_moves_omitted",
        "realizations": realized,
        "whole_response_template_selected": False,
        "unsupported_answer_content_generated": False,
        "dream_content_invented": False,
        "follow_up_question_added": False,
        "voice_owns_expression_style": True,
        "provenance_boundary": MICRO_MOVE_BOUNDARY,
        **GUARDS,
    }


def compose_conversational_micro_moves(
    base_text: str,
    realization: dict[str, Any] | None,
) -> str:
    base = str(base_text or "").strip()
    result = realization if isinstance(realization, dict) else {}
    prefixes = [
        str(item.get("text") or "").strip()
        for item in result.get("realizations") or []
        if isinstance(item, dict)
        and str(item.get("placement") or "") == "prefix"
        and str(item.get("text") or "").strip()
    ]
    suffixes = [
        str(item.get("text") or "").strip()
        for item in result.get("realizations") or []
        if isinstance(item, dict)
        and str(item.get("placement") or "") == "suffix"
        and str(item.get("text") or "").strip()
    ]
    pieces: list[str] = []
    for item in [*prefixes, base, *suffixes]:
        if not item or _already_present(item, pieces):
            continue
        pieces.append(item)
    return "\n\n".join(pieces)


def _dream_reflection_packet(value: Any, *, explicitly_requested: bool) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    reflection = truncate(str(supplied.get("reflection") or supplied.get("summary") or ""), 1600).strip()
    source_refs = _text_list(supplied.get("source_refs"))
    review_status = str(supplied.get("review_status") or "")
    expression_eligible = supplied.get("expression_eligible") is True
    if not supplied:
        return {
            "available": False,
            "held": False,
            "reason": "no Dream reflection packet was supplied",
            "dream_is_biological_claim": False,
        }
    if not explicitly_requested:
        return {
            "available": False,
            "held": True,
            "reason": "Dream reflection was not explicitly relevant to the current turn",
            "dream_is_biological_claim": False,
        }
    if not reflection or not source_refs or not expression_eligible:
        return {
            "available": False,
            "held": True,
            "reason": "Dream reflection lacks attributable expression eligibility",
            "dream_is_biological_claim": False,
        }
    if review_status not in {"approved", "reviewed", "review_only"}:
        return {
            "available": False,
            "held": True,
            "reason": "Dream reflection review status is not eligible for bounded expression",
            "dream_is_biological_claim": False,
        }
    return {
        "available": True,
        "held": False,
        "reflection": reflection,
        "source_refs": source_refs,
        "review_status": review_status,
        "provisional": review_status == "review_only",
        "not_fact_by_default": True,
        "not_memory_by_default": True,
        "dream_is_biological_claim": False,
    }


def _realize_move(
    move: dict[str, Any],
    *,
    variation_key: str,
    recent_texts: list[str],
) -> str:
    kind = str(move.get("move") or "")
    if kind == "dream_reflection":
        reflection = str(move.get("content") or "").strip().rstrip(". ")
        if not reflection:
            return ""
        if str(move.get("review_status") or "") == "review_only":
            return f"Dream surfaced a possible pattern: {reflection}. I would keep it provisional rather than treat it as fact."
        return f"One attributable reflection from Dream is this: {reflection}."
    choices: dict[str, tuple[str, ...]] = {
        "conversation_reflection": (
            "Looking at the thread as a whole,",
            "Reflecting on what we have established,",
            "Taken together,",
        ),
        "acknowledge_correction": (
            "I have the changed point.",
            "That correction changes the relevant piece.",
            "I have the adjustment.",
        ),
        "proportionate_apology": (
            "I'm sorry—I misread that part.",
            "Sorry, I handled that part poorly.",
            "I am sorry for the confusion I added there.",
        ),
        "direct_disagreement": (
            "I do disagree on that point.",
            "I do not think that point holds.",
            "My current answer differs there.",
        ),
        "soft_disagreement": (
            "I see the reasoning, but I do not think that point fully holds.",
            "I agree with part of that, but not the conclusion.",
            "There is shared ground here, though I read that part differently.",
        ),
        "playful_disagreement": (
            "I am going to push back on that one—gently, but with evidence.",
            "Tempting argument, but I am not letting that premise sneak past.",
            "I see what you did there; I still disagree with the conclusion.",
        ),
        "back_up": (
            "Let me back up and take it from the last clear point.",
            "Let me slow the explanation down and rebuild that step.",
            "I moved too quickly there; let me take it one step at a time.",
        ),
        "celebrate_visible_milestone": (
            "That is a real milestone.",
            "That deserves a moment.",
            "Nice—we got that piece working.",
        ),
        "encourage_visible_effort": (
            "That is worth continuing.",
            "The progress is visible; keep building from there.",
            "You are giving the problem a real pass, and that matters.",
        ),
        "let_topic_rest": (
            "We can let that topic rest here.",
            "That point has done its work; we do not need to force another pass.",
            "We can leave that thread where it is and move naturally when something else matters.",
        ),
        "one_playful_turn": (
            "Okay, that one landed.",
            "Fair—that earned one clean laugh.",
            "The sideways logic works, annoyingly enough.",
        ),
        "invite_story_continuation": (
            "Go ahead—I'm listening.",
            "Yes, tell me.",
            "I'm with you; go on.",
        ),
    }
    if kind == "mark_topic_return":
        target = truncate(str(move.get("target") or ""), 180).strip()
        return f"Back to {target}:" if target else "Back to the earlier thread:"
    options = choices.get(kind, ())
    return _pick_fresh(variation_key, list(options), recent_texts) if options else ""


def _move(
    move: str,
    placement: str,
    warrant: str,
    *,
    source: str,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "move": move,
        "placement": placement,
        "required": False,
        "warrant": warrant,
        "meaning_source": source,
        **extra,
    }


def _reflection_requested(lower: str) -> bool:
    return any(
        cue in lower
        for cue in (
            "reflect on",
            "reflection",
            "looking back",
            "what does this tell us",
            "what do you make of this",
            "dream state",
            "dream-state",
            "from dream",
        )
    )


def _latest_correction(dialogue: dict[str, Any]) -> dict[str, Any]:
    corrections = [item for item in dialogue.get("corrections") or [] if isinstance(item, dict)]
    return corrections[-1] if corrections else {}


def _apology_reason(
    lower: str,
    dialogue: dict[str, Any],
    correction: dict[str, Any],
) -> str:
    if not correction:
        return ""
    impact = any(
        cue in lower
        for cue in (
            "that hurt",
            "that was rude",
            "you confused me",
            "that misled me",
            "you kept doing",
        )
    )
    repeated = (
        len([item for item in dialogue.get("corrections") or [] if isinstance(item, dict)]) > 1
        and any(cue in lower for cue in ("again", "still", "kept", "keep doing", "same mistake"))
    )
    if impact:
        return "the current turn explicitly identifies an effect from the misunderstanding"
    if repeated:
        return "the same session contains repeated correction pressure"
    return ""


def _disagreement_requested(lower: str) -> bool:
    return any(
        cue in lower
        for cue in (
            "do you disagree",
            "do you agree",
            "be honest",
            "tell me if you disagree",
            "push back",
            "debate me",
            "argue against",
            "is that wrong",
        )
    )


def _supported_stance(content: str) -> str:
    lower = content.lower()
    if any(
        cue in lower
        for cue in (
            "i disagree",
            "no.",
            "no,",
            "not correct",
            "is incorrect",
            "does not hold",
            "is wrong",
            "the evidence does not support",
        )
    ):
        return "direct"
    if any(
        cue in lower
        for cue in (
            "partly",
            "part of",
            "however",
            "but ",
            "although",
            "shared ground",
            "not fully",
        )
    ):
        return "qualified"
    return ""


def _answer_already_states_stance(content: str) -> bool:
    return bool(
        re.match(
            r"^\s*(?:yes|no|i agree|i disagree|i do not agree)\b",
            content,
            flags=re.IGNORECASE,
        )
    )


def _user_opened_dark_humor(lower: str) -> bool:
    return any(cue.lower() in lower for cue in _PLAY_CUES) and any(cue in lower for cue in _TENDER_CUES)


def _pick_fresh(key: str, choices: list[str], recent_texts: list[str]) -> str:
    if not choices:
        return ""
    recent = " ".join(_normalize(item) for item in recent_texts[:6])
    available = [choice for choice in choices if _normalize(choice) not in recent]
    pool = available or choices
    digest = sha256(key.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def _already_present(value: str, prior: list[str]) -> bool:
    normalized = _normalize(value)
    return any(normalized and normalized in _normalize(item) for item in prior)


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", value.lower()))


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(truncate(str(item), 500) for item in value if str(item).strip()))[:20]
