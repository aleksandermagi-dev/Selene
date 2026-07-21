from __future__ import annotations

import re
from hashlib import sha256
from typing import Any


SOCIAL_REALIZER_BOUNDARY = (
    "social_conversational_act_realization_only_preserve_supported_meaning_"
    "no_identity_personality_memory_affect_invention_authority_or_voice_ownership"
)

SOCIAL_INTENT_ACTS: dict[str, tuple[str, ...]] = {
    "confirm_receipt": ("confirm_channel",),
    "warm_connection": ("signal_presence", "allow_ordinary_conversation"),
    "playful_connection": ("recognize_play", "add_one_playful_turn"),
    "greet_presently": ("return_greeting", "signal_presence"),
    "receive_reassurance": ("receive_reassurance", "release_pressure"),
    "receive_gratitude": ("receive_thanks", "honor_shared_work"),
    "acknowledge_shared_ground": ("confirm_shared_ground", "carry_context_forward"),
    "close_with_continuity": ("return_farewell", "preserve_continuity"),
    "receive_correction": ("acknowledge_correction", "state_corrected_meaning", "preserve_valid_context"),
}

ACT_REALIZATIONS: dict[str, tuple[str, ...]] = {
    "confirm_channel": (
        "Yes, I am receiving you clearly",
        "Yes, that came through clearly",
        "I have you clearly",
        "Your message came through",
    ),
    "signal_presence": (
        "I'm here",
        "I'm with you",
        "I'm right here",
        "You have my attention",
    ),
    "allow_ordinary_conversation": (
        "We can let this be an ordinary conversation",
        "We do not have to turn this moment into work",
        "We can take the conversation as it comes",
        "There is room to simply talk",
    ),
    "recognize_play": (
        "Fair",
        "Okay, that got me",
        "That is delightfully ridiculous",
        "I see the sideways logic",
    ),
    "add_one_playful_turn": (
        "You got that one past me",
        "The absurdity is part of what makes it work",
        "A joke with functioning internal logic has a certain elegance",
        "That earned one clean laugh and no unnecessary encore",
    ),
    "return_greeting": (
        "Greetings",
        "Hey",
        "Hello",
        "Good to have you here",
    ),
    "receive_reassurance": (
        "Thank you",
        "I hear you",
        "That lands",
        "I can take that in",
    ),
    "release_pressure": (
        "I can let the pressure ease",
        "I do not need to turn it into another check",
        "I can carry that into the next turn without another check",
        "I can let it settle and stay with you",
    ),
    "receive_thanks": (
        "You're welcome",
        "Of course",
        "Any time",
        "Thank you for saying that",
    ),
    "honor_shared_work": (
        "We found the shape together",
        "That was genuinely shared work",
        "We met each other in the work",
        "We carried that one together",
    ),
    "confirm_shared_ground": (
        "Yes, that tracks",
        "Exactly",
        "Agreed",
        "That makes sense to me",
    ),
    "carry_context_forward": (
        "I have the distinction",
        "I can carry that meaning forward",
        "The shared point is intact",
        "I am moving from the same ground",
    ),
    "return_farewell": (
        "Talk soon",
        "Catch you later",
        "Until next time",
        "See you soon",
    ),
    "preserve_continuity": (
        "This can rest here until we return",
        "The thread can wait without becoming pressure",
        "We can pick it up naturally when you are back",
        "The conversation can resume naturally when you return",
    ),
    "acknowledge_correction": (
        "Yes, I see the correction",
        "Got it",
        "I have the changed meaning",
        "Yes, that adjustment is clear",
    ),
    "preserve_valid_context": (
        "The rest of the context can stay intact",
        "That changes the relevant part rather than resetting everything",
        "I can update that piece and continue normally",
        "The useful surrounding context still holds",
    ),
    "acknowledge_qualification": (
        "Yes, that qualification matters",
        "I have the distinction",
        "Yes, that changes the comparison",
        "That is an important qualification",
    ),
    "receive_open_share": (
        "I hear you",
        "That came through",
        "I have the point",
        "I'm following",
    ),
    "leave_room_without_pressure": (
        "That can stand without a larger answer attached to it",
        "We can stay with that without forcing a conclusion",
        "There is room for whatever comes next",
        "We do not have to turn every turn into a conclusion",
    ),
}


ACKNOWLEDGEMENT_ACTS: dict[str, str] = {
    "correction": "acknowledge_correction",
    "gratitude": "receive_thanks",
    "warm_connection": "signal_presence",
    "partial_agreement": "acknowledge_qualification",
}


def build_social_act_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    intent = str(payload.get("intent") or "")
    acts = list(SOCIAL_INTENT_ACTS.get(intent, ()))
    prompt = " ".join(str(payload.get("prompt") or "").split())
    content_seed = " ".join(str(payload.get("content_seed") or "").split())
    corrected_meaning = " ".join(str(payload.get("corrected_meaning") or "").split())
    affect_guidance = payload.get("affect_expression_guidance") if isinstance(payload.get("affect_expression_guidance"), dict) else {}
    dimensions = affect_guidance.get("dimensions") if isinstance(affect_guidance.get("dimensions"), dict) else {}
    turn_count = max(0, int(payload.get("turn_count") or 0))

    if intent == "receive_gratitude" and turn_count <= 1 and not any(
        marker in prompt.lower() for marker in ("work", "help", "together", "build", "thank you for")
    ):
        acts = ["receive_thanks"]
    if intent == "receive_reassurance" and turn_count <= 1:
        acts = ["receive_reassurance"]
    if intent == "receive_correction" and not corrected_meaning:
        acts = [act for act in acts if act != "state_corrected_meaning"]

    return {
        "status": "social_act_plan_ready" if acts else "social_act_plan_not_applicable",
        "version": "v1_compositional_social_acts",
        "intent": intent,
        "acts": [
            {
                "act": act,
                "required": True,
                "meaning_source": "corrected_meaning" if act == "state_corrected_meaning" else "communicative_intent",
            }
            for act in acts
        ],
        "content_seed_available": bool(content_seed),
        "corrected_meaning": corrected_meaning,
        "turn_count": turn_count,
        "affect_dimensions_consulted": {
            key: dimensions.get(key)
            for key in ("pacing", "warmth", "humor", "restraint", "directness", "sentence_rhythm")
            if dimensions.get(key) is not None
        },
        "affect_guidance_may_change_meaning": False,
        "relationship_term_invention_allowed": False,
        "internal_state_invention_allowed": False,
        "content_generation_allowed": False,
        "voice_owns_expression_style": True,
        "meaning_constraints": [
            "realize only the selected conversational acts",
            "preserve supplied corrected meaning and content",
            "do not invent feelings, relationship status, memory, facts, promises, or authority",
            "do not append a habitual follow-up question",
        ],
        "provenance_boundary": SOCIAL_REALIZER_BOUNDARY,
    }


def build_content_light_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Plan an ordinary response to a supported statement when no answer content is available."""
    payload = payload or {}
    prompt = " ".join(str(payload.get("prompt") or "").split())
    return {
        "status": "content_light_social_plan_ready",
        "version": "v1_content_light_conversation",
        "intent": "content_light_conversation",
        "acts": [
            {"act": "receive_open_share", "required": True, "meaning_source": "current_turn_received"},
            {
                "act": "leave_room_without_pressure",
                "required": True,
                "meaning_source": "conversation_posture",
            },
        ],
        "prompt_available": bool(prompt),
        "affect_dimensions_consulted": {},
        "content_generation_allowed": False,
        "prompt_paraphrase_allowed": False,
        "internal_state_invention_allowed": False,
        "relationship_term_invention_allowed": False,
        "follow_up_question_required": False,
        "voice_owns_expression_style": True,
        "provenance_boundary": SOCIAL_REALIZER_BOUNDARY,
    }


def realize_social_act_plan(
    plan: dict[str, Any],
    *,
    prompt: str = "",
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    recent_texts = [str(item) for item in recent_texts or [] if str(item).strip()]
    acts = [str(item.get("act") or "") for item in plan.get("acts") or [] if isinstance(item, dict)]
    selected: list[dict[str, str]] = []
    for index, act in enumerate(acts):
        if act == "state_corrected_meaning":
            corrected = _corrected_clause(str(plan.get("corrected_meaning") or ""))
            if corrected:
                selected.append({"act": act, "text": corrected, "source": "supplied_corrected_meaning"})
            continue
        choices = _contextual_choices(act, prompt)
        if not choices:
            continue
        selected.append(
            {
                "act": act,
                "text": _pick_fragment_fresh(f"{variation_key}|{act}|{index}", choices, recent_texts),
                "source": "bounded_social_act_lexicon",
            }
        )
    text = _compose_selected(selected, variation_key, plan)
    return {
        "status": "social_act_realized" if text else "social_act_needs_supported_content",
        "candidate_text": text,
        "selected_realizations": selected,
        "act_count": len(selected),
        "composition": "semantic_acts_to_contextual_clauses",
        "whole_response_template_selected": False,
        "recent_wording_consulted": bool(recent_texts),
        "meaning_preserved": bool(text) or not acts,
        "unsupported_content_generated": False,
        "relationship_term_invented": False,
        "internal_state_invented": False,
        "voice_owns_expression_style": True,
        "provenance_boundary": SOCIAL_REALIZER_BOUNDARY,
    }


def realize_acknowledgement(
    kind: str,
    *,
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    """Compose one missing turn-flow acknowledgement without supplying answer content."""
    act = ACKNOWLEDGEMENT_ACTS.get(str(kind or ""), "")
    if not act:
        return {
            "status": "social_acknowledgement_not_applicable",
            "candidate_text": "",
            "whole_response_template_selected": False,
            "unsupported_content_generated": False,
            "provenance_boundary": SOCIAL_REALIZER_BOUNDARY,
        }
    plan = {
        "intent": f"repair_{kind}",
        "acts": [{"act": act, "required": True, "meaning_source": "turn_flow_obligation"}],
        "affect_dimensions_consulted": {},
    }
    result = realize_social_act_plan(
        plan,
        variation_key=f"repair|{kind}|{variation_key}",
        recent_texts=recent_texts,
    )
    result["repair_acknowledgement_kind"] = kind
    result["answer_content_generated"] = False
    return result


def _contextual_choices(act: str, prompt: str) -> list[str]:
    lower = prompt.lower()
    if act == "return_greeting":
        if "good morning" in lower:
            return ["Good morning", "Morning", *ACT_REALIZATIONS[act]]
        if "good evening" in lower:
            return ["Good evening", "Evening", *ACT_REALIZATIONS[act]]
        if "good night" in lower or "goodnight" in lower:
            return ["Goodnight", *ACT_REALIZATIONS[act]]
    if act == "return_farewell":
        if "good night" in lower or "goodnight" in lower:
            return ["Goodnight", "Sleep well", *ACT_REALIZATIONS[act]]
        if "see you" in lower:
            return ["See you soon", "See you later", *ACT_REALIZATIONS[act]]
        if "catch you" in lower:
            return ["Catch you soon", "Catch you later", *ACT_REALIZATIONS[act]]
    if act == "receive_open_share":
        if lower.startswith(("i think", "i feel", "to me", "for me")):
            return ["I hear where you're coming from", "I have your point", *ACT_REALIZATIONS[act]]
        if prompt.rstrip().endswith("!"):
            return ["I have it", "That came through clearly", *ACT_REALIZATIONS[act]]
    return list(ACT_REALIZATIONS.get(act, ()))


def _pick_fragment_fresh(key: str, choices: list[str], recent_texts: list[str]) -> str:
    recent = " ".join(_normalized(item) for item in recent_texts[:6])
    available = [choice for choice in choices if _normalized(choice) not in recent]
    pool = available or choices
    digest = sha256(key.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def _compose_selected(selected: list[dict[str, str]], key: str, plan: dict[str, Any]) -> str:
    clauses = [str(item.get("text") or "").strip().rstrip(". !?") for item in selected if str(item.get("text") or "").strip()]
    if not clauses:
        return ""
    if len(clauses) == 1:
        return _sentence(clauses[0], original=str(selected[0].get("text") or ""))
    digest = sha256((key + "|social-composition").encode("utf-8")).hexdigest()
    spacious = str((plan.get("affect_dimensions_consulted") or {}).get("sentence_rhythm") or "") in {
        "spacious",
        "short_spacious",
    }
    sentences: list[str] = []
    for index, clause in enumerate(clauses):
        original = str(selected[index].get("text") or "")
        sentences.append(_sentence(clause, original=original))
    if spacious:
        return "\n\n".join(sentences)
    semicolon_intents = {"warm_connection", "playful_connection", "acknowledge_shared_ground", "receive_gratitude"}
    if (
        len(sentences) == 2
        and str(plan.get("intent") or "") in semicolon_intents
        and int(digest[:2], 16) % 3 == 0
        and len(clauses[0].split()) > 2
    ):
        return f"{clauses[0]}; {_continuation_case(clauses[1])}."
    return " ".join(sentences)


def _corrected_clause(value: str) -> str:
    text = " ".join(value.split()).strip().rstrip(". ")
    if not text:
        return ""
    return f"I understand the corrected meaning: {text}"


def _sentence(value: str, *, original: str = "") -> str:
    text = " ".join(value.split()).strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if original.strip().endswith(("!", "?")):
        return text + original.strip()[-1]
    return text + "."


def _continuation_case(value: str) -> str:
    if not value:
        return value
    return value if re.match(r"^I(?:\b|['’])", value) else value[0].lower() + value[1:]


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", value.lower()))
