from __future__ import annotations

import re
from typing import Any

from .registry import truncate


CONTEXTUAL_CONTINUITY_BOUNDARY = (
    "source_separated_context_use_only_no_scripted_recall_profile_inference_"
    "knowledge_memory_merge_identity_personality_governance_or_authority_change"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "automatic_speech_allowed": False,
    "relationship_profile_write_allowed": False,
    "durable_preference_write": False,
    "identity_change_allowed": False,
    "personality_change_allowed": False,
    "governance_change_allowed": False,
    "remembered_wording_as_script_allowed": False,
}

_CALLBACK_CUES = (
    "remember when",
    "like before",
    "as before",
    "earlier",
    "last time",
    "that time",
    "we did this",
    "we talked about",
    "this connects",
    "same thread",
    "back to",
    "going back",
    "return to",
    "callback",
)

_PLAY_CUES = (
    "haha",
    "lol",
    "lmao",
    "xd",
    "joke",
    "joking",
    "kidding",
    "funny",
    "dark humor",
)

_TENDER_CUES = (
    "died",
    "dead",
    "death",
    "grief",
    "grieving",
    "funeral",
    "passed away",
    "lost my",
    "miss my",
    "scared",
    "afraid",
    "hospital",
    "crisis",
)


def build_contextual_continuity_plan(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Decide how separate continuity sources may shape one visible reply."""

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    lower = " ".join(prompt.lower().replace("’", "'").split())
    dialogue = (
        payload.get("dialogue_workspace")
        if isinstance(payload.get("dialogue_workspace"), dict)
        else {}
    )
    pragmatics = (
        dialogue.get("pragmatics")
        if isinstance(dialogue.get("pragmatics"), dict)
        else {}
    )
    memory = (
        payload.get("memory_context")
        if isinstance(payload.get("memory_context"), dict)
        else {}
    )
    intent = (
        payload.get("intent_decision")
        if isinstance(payload.get("intent_decision"), dict)
        else {}
    )
    events = [
        item
        for item in payload.get("current_session_events") or []
        if isinstance(item, dict)
    ][-12:]
    affect = (
        payload.get("affect_expression_guidance")
        if isinstance(payload.get("affect_expression_guidance"), dict)
        else {}
    )
    relational = (
        payload.get("relational_context")
        if isinstance(payload.get("relational_context"), dict)
        else intent.get("relational_context")
        if isinstance(intent.get("relational_context"), dict)
        else {}
    )
    conversation_continuity = (
        payload.get("conversation_continuity")
        if isinstance(payload.get("conversation_continuity"), dict)
        else {}
    )

    speaker = _speaker_scope(prompt, payload.get("speaker_context"))
    preferences = _transient_preferences(dialogue)
    callback = _callback_decision(
        lower,
        memory=memory,
        dialogue=dialogue,
        pragmatics=pragmatics,
        events=events,
        explicit_recall=intent.get("memory_recall_requested") is True,
    )
    shared_joke = _shared_joke_context(
        lower,
        memory=memory,
        events=events,
        callback=callback,
    )
    humor = _humor_decision(
        lower,
        shared_joke=shared_joke,
        affect=affect,
    )
    source_channels = _source_channels(
        memory=memory,
        events=events,
        dialogue=dialogue,
        speaker=speaker,
    )
    relationship_continuity = _relationship_continuity_receipt(
        relational=relational,
        callback=callback,
        memory=memory,
        events=events,
        speaker=speaker,
    )
    source_refs = [
        "contextual_continuity:current_turn",
        *[
            str(ref)
            for ref in memory.get("source_refs") or []
            if str(ref).strip()
        ],
    ]
    return {
        "status": "contextual_continuity_plan_ready",
        "version": "v1_source_separated_callbacks_and_transient_context",
        "source_channels": source_channels,
        "speaker_scope": speaker,
        "relationship_continuity": relationship_continuity,
        "transient_preferences": preferences,
        "callback_decision": callback,
        "conversation_continuity": conversation_continuity,
        "shared_joke_context": shared_joke,
        "humor_decision": humor,
        "expression_handoff": {
            **preferences.get("directives", {}),
            "callback_mode": callback.get("mode"),
            "continuity_mode": str(conversation_continuity.get("mode") or ""),
            "humor_posture": humor.get("posture"),
            "optional_guidance_only": True,
            "meaning_change_allowed": False,
        },
        "reviewed_memory_and_taught_knowledge_remain_separate": True,
        "current_session_events_are_durable_memory": False,
        "corrections_are_profile_updates": False,
        "speaker_identity_is_inferred_relationship_profile": False,
        "callback_is_required": False,
        "remembered_wording_may_be_used_as_script": False,
        "source_refs": list(dict.fromkeys(source_refs))[:30],
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": CONTEXTUAL_CONTINUITY_BOUNDARY,
        **GUARDS,
    }


def _transient_preferences(dialogue: dict[str, Any]) -> dict[str, Any]:
    preferences = (
        dialogue.get("preferences")
        if isinstance(dialogue.get("preferences"), dict)
        else {}
    )
    transient = (
        preferences.get("transient")
        if isinstance(preferences.get("transient"), dict)
        else {}
    )
    directives = (
        transient.get("directives")
        if transient.get("active") is True
        and isinstance(transient.get("directives"), dict)
        else {}
    )
    return {
        "active": bool(directives),
        "status": str(transient.get("status") or "not_requested"),
        "directives": {
            key: str(value)
            for key, value in directives.items()
            if key in {"response_depth", "pacing", "directness"} and str(value)
        },
        "remaining_turns": (
            max(0, int(transient.get("remaining_turns") or 0))
            if directives
            else 0
        ),
        "scope": "current_session_only",
        "expires_automatically": True,
        "durable_preference_write": False,
    }


def _callback_decision(
    lower: str,
    *,
    memory: dict[str, Any],
    dialogue: dict[str, Any],
    pragmatics: dict[str, Any],
    events: list[dict[str, Any]],
    explicit_recall: bool,
) -> dict[str, Any]:
    cue = next((item for item in _CALLBACK_CUES if item in lower), "")
    transition = (
        pragmatics.get("thread_braid")
        if isinstance(pragmatics.get("thread_braid"), dict)
        else {}
    )
    explicit_session_return = bool(cue) or any(
        str(item.get("action") or "") in {"resume", "revise_with_dependency"}
        for item in transition.get("turn_traversal") or []
        if isinstance(item, dict)
    )
    memory_available = (
        memory.get("memory_context_used") is True
        and str(memory.get("memory_source_class") or "") == "approved_memory_index"
    )
    memory_items = [
        item for item in memory.get("items") or [] if isinstance(item, dict)
    ]
    if explicit_recall and memory_available:
        source, mode, surface = "reviewed_personal_memory", "explicit_recall", True
        reason = "Aleks explicitly asked for memory recall and an approved item matched."
    elif memory_available and cue:
        source, mode, surface = "reviewed_personal_memory", "relevant_callback", True
        reason = "A visible callback cue and an approved-memory match align."
    elif explicit_session_return and events:
        source, mode, surface = "current_session_events", "relevant_callback", True
        reason = "The current turn explicitly returns to visible session context."
    elif memory_available:
        source, mode, surface = "reviewed_personal_memory", "silent_interpretive_context", False
        reason = "Relevant approved memory may inform interpretation without forcing a callback."
    else:
        source, mode, surface = "", "none", False
        reason = "No source-compatible callback is needed for this turn."
    subject = ""
    if source == "reviewed_personal_memory" and memory_items:
        subject = truncate(str(memory_items[0].get("title") or ""), 160)
    elif source == "current_session_events":
        subject = truncate(str(dialogue.get("active_topic") or ""), 160)
    return {
        "mode": mode,
        "source_channel": source,
        "surface_callback_allowed": surface,
        "silent_influence_allowed": mode == "silent_interpretive_context",
        "callback_cue": cue,
        "subject_label": subject,
        "reason": reason,
        "source_compatible": source in {
            "",
            "reviewed_personal_memory",
            "current_session_events",
        },
        "attribution_required_if_surfaced": source == "reviewed_personal_memory",
        "reconstruct_in_current_language": bool(source),
        "quote_or_repeat_remembered_wording": False,
        "callback_required": False,
    }


def _shared_joke_context(
    lower: str,
    *,
    memory: dict[str, Any],
    events: list[dict[str, Any]],
    callback: dict[str, Any],
) -> dict[str, Any]:
    play_opened = _contains_any(lower, _PLAY_CUES)
    memory_items = [
        item for item in memory.get("items") or [] if isinstance(item, dict)
    ]
    memory_play = next(
        (
            item
            for item in memory_items
            if _contains_any(
                " ".join(
                    str(item.get(key) or "").lower()
                    for key in (
                        "title",
                        "summary",
                        "memory_category",
                        "emotional_texture",
                    )
                ),
                ("joke", "humor", "playful", "laugh", "funny"),
            )
        ),
        None,
    )
    prior_play_events = [
        item
        for item in events
        if _contains_any(str(item.get("preview") or "").lower(), _PLAY_CUES)
    ]
    if memory_play and callback.get("source_channel") == "reviewed_personal_memory":
        available = True
        source = "reviewed_personal_memory"
        context_label = truncate(str(memory_play.get("title") or "shared playful context"), 160)
    elif prior_play_events and (
        callback.get("source_channel") == "current_session_events" or play_opened
    ):
        available = True
        source = "current_session_events"
        context_label = "visible current-session playful exchange"
    else:
        available = False
        source = ""
        context_label = ""
    return {
        "available": available,
        "source_channel": source,
        "context_label": context_label,
        "current_turn_opens_play": play_opened,
        "may_shape_timing": available and play_opened,
        "may_repeat_remembered_wording": False,
        "durable_joke_profile_created": False,
        "context_must_remain_attached": True,
    }


def _humor_decision(
    lower: str,
    *,
    shared_joke: dict[str, Any],
    affect: dict[str, Any],
) -> dict[str, Any]:
    explicit_humor_request = bool(
        re.search(
            r"\b(?:give|tell|make|write|share)\s+(?:me\s+)?(?:one\s+|a\s+|an\s+)?"
            r"(?:little\s+|small\s+|quick\s+|short\s+)?(?:joke|pun)\b",
            lower,
        )
        or re.search(
            r"\bgive\s+(?:the\s+)?[a-z][a-z0-9' -]{1,100}?\s+"
            r"(?:one|a|an)\s+(?:tiny\s+|little\s+|small\s+|quick\s+|short\s+)?"
            r"(?:joke|pun)\b",
            lower,
        )
    )
    user_opened_play = _contains_any(lower, _PLAY_CUES) and not bool(
        re.search(
            r"\b(?:no|not|without|avoid|skip|omit|separate|apart)\b[^.!?]{0,80}\b(?:joke|pun)\b"
            r"|\b(?:joke|pun)\b[^.!?]{0,80}\b(?:separate|apart)\b",
            lower,
        )
    )
    tender = _contains_any(lower, _TENDER_CUES)
    affect_humor = str((affect.get("dimensions") or {}).get("humor") or "")
    if tender and not user_opened_play:
        posture = "hold"
        reason = "Tender content is present and the user did not open humor."
    elif affect_humor == "contextually_held_this_turn" and not user_opened_play:
        posture = "hold"
        reason = "The current conversation context holds humor for this turn without making it generally unavailable."
    elif explicit_humor_request:
        posture = "requested_once"
        reason = "The user explicitly requested one bounded humorous aside."
    elif user_opened_play:
        posture = "available_not_required"
        reason = "The user visibly opened a playful register in this turn."
    else:
        posture = "context_only"
        reason = "Humor is not required by warmth or continuity alone."
    return {
        "posture": posture,
        "reason": reason,
        "tender_context": tender,
        "user_opened_play": user_opened_play,
        "explicit_humor_request": explicit_humor_request,
        "shared_joke_available": shared_joke.get("available") is True,
        "shared_joke_may_surface": (
            shared_joke.get("available") is True
            and user_opened_play
            and posture == "available_not_required"
        ),
        "humor_required": explicit_humor_request,
        "one_fitting_turn_then_release": True,
    }


def _source_channels(
    *,
    memory: dict[str, Any],
    events: list[dict[str, Any]],
    dialogue: dict[str, Any],
    speaker: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "channel": "reviewed_personal_memory",
            "available": (
                memory.get("memory_context_used") is True
                and str(memory.get("memory_source_class") or "")
                == "approved_memory_index"
            ),
            "use": "personal continuity context",
            "is_taught_knowledge": False,
        },
        {
            "channel": "current_session_events",
            "available": bool(events),
            "event_count": len(events),
            "use": "visible conversation continuity",
            "is_durable_memory": False,
        },
        {
            "channel": "current_session_corrections",
            "available": bool(dialogue.get("corrections")),
            "use": "active refinement",
            "is_profile_update": False,
        },
        {
            "channel": "speaker_identity",
            "available": bool(speaker.get("speaker")),
            "use": "current-turn address and source compatibility",
            "is_relationship_profile": False,
        },
        {
            "channel": "approved_taught_knowledge",
            "available": False,
            "use": "general knowledge through Comprehension, never personal callback evidence",
            "is_personal_memory": False,
        },
    ]


def _relationship_continuity_receipt(
    *,
    relational: dict[str, Any],
    callback: dict[str, Any],
    memory: dict[str, Any],
    events: list[dict[str, Any]],
    speaker: dict[str, Any],
) -> dict[str, Any]:
    active_channels: list[str] = []
    if relational.get("relational_context_present") is True:
        active_channels.append("current_turn_relational_cues")
    if events:
        active_channels.append("visible_current_session_context")
    if (
        memory.get("memory_context_used") is True
        and str(memory.get("memory_source_class") or "") == "approved_memory_index"
    ):
        active_channels.append("reviewed_personal_memory")
    callback_source = str(callback.get("source_channel") or "")
    private_turn = relational.get("private_relational_context") is True
    speaker_name = str(speaker.get("speaker") or "").strip().casefold()
    authentication = str(
        speaker.get("authentication_strength") or ""
    ).strip()
    private_scope_compatible = not private_turn or (
        speaker_name
        in {"aleks", "aleksander magi", "aleksander rani magi"}
        and authentication
        in {"local_desktop_session", "authenticated_remote_session"}
    )
    return {
        "status": (
            "relationship_continuity_available"
            if active_channels
            else "relationship_continuity_not_selected"
        ),
        "active_source_channels": active_channels,
        "current_turn_cue_types": [
            str(item) for item in relational.get("cue_types") or []
        ],
        "callback_source_channel": callback_source,
        "surface_callback_allowed": callback.get("surface_callback_allowed") is True,
        "silent_context_allowed": callback.get("silent_influence_allowed") is True,
        "reviewed_memory_privacy_gate_precedes_receipt": (
            "reviewed_personal_memory" in active_channels
        ),
        "private_current_turn_scope": private_turn,
        "private_scope_compatible": private_scope_compatible,
        "response_script_supplied": False,
        "reciprocal_emotion_claim_required": False,
        "relationship_profile_created": False,
        "current_turn_cues_are_durable_memory": False,
        "visible_session_context_is_durable_memory": False,
        "reviewed_memory_wording_may_be_repeated_as_script": False,
        "user_affect_claimed_as_selene_state": False,
        "attribution_required_if_memory_surfaces": (
            callback_source == "reviewed_personal_memory"
        ),
        "terminal_stop": (
            "source_separated_continuity_available"
            if active_channels and private_scope_compatible
            else "private_scope_incompatible"
            if active_channels
            else "no_relationship_continuity_needed"
        ),
    }


def _speaker_scope(prompt: str, supplied: Any) -> dict[str, Any]:
    if isinstance(supplied, dict) and str(
        supplied.get("speaker") or supplied.get("claimed_speaker") or ""
    ).strip():
        result = {
            "speaker": truncate(
                str(supplied.get("speaker") or supplied.get("claimed_speaker") or ""),
                80,
            ),
            "source": str(
                supplied.get("source")
                or supplied.get("envelope_source")
                or "explicit_payload"
            ),
            "inferred_relationship_profile": False,
        }
        if str(supplied.get("channel") or ""):
            result["channel"] = str(supplied["channel"])
        if str(supplied.get("authentication_strength") or ""):
            result["authentication_strength"] = str(
                supplied["authentication_strength"]
            )
        return result
    lower = prompt.lower()
    if "this is codex" in lower:
        speaker, source = "Codex", "explicit_current_turn"
    elif any(phrase in lower for phrase in ("this is aleks", "it is aleks", "it's aleks")):
        speaker, source = "Aleks", "explicit_current_turn"
    else:
        speaker, source = "session_user", "not_individually_inferred"
    return {
        "speaker": speaker,
        "source": source,
        "inferred_relationship_profile": False,
    }


def _contains_any(text: str, values: tuple[str, ...]) -> bool:
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(value)}(?![a-z0-9])", text, re.IGNORECASE)
        for value in values
    )
