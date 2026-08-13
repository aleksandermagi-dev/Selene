from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


QUOTATION_ECHO_BOUNDARY = (
    "visible_current_turn_or_attributed_source_expression_only_no_private_corpus_"
    "wording_memory_replay_identity_personality_governance_authority_or_fact_invention"
)

EXPRESSION_MODES = (
    "original_expression",
    "attributed_quotation",
    "meaning_preserving_paraphrase",
    "technical_exactness",
    "shared_callback",
    "playful_mimicry",
    "affectionate_echo",
)

PRIVATE_SOURCE_PREFIXES = (
    "raw_corpus:",
    "private_corpus:",
    "corpus_message:",
    "aleks_miner:",
    "aleks_metacognition_miner:",
)

PLAY_CUES = ("haha", "lol", "lmao", "xd", "joke", "kidding", "funny", "the bit")
AFFECTION_MARKS = ("<3", "♥", "♡", "❤", "💜", "🩷")

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "raw_a_import_allowed": False,
    "raw_corpus_access_allowed": False,
    "private_corpus_wording_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "fact_generation_allowed": False,
    "relationship_status_invention_allowed": False,
}


def quotation_echo_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "quotation_echo_coordination_ready",
            "version": "v1_attributed_quote_and_visible_shared_echo",
            "expression_modes": list(EXPRESSION_MODES),
            "normal_knowledge_path": "meaning_preserving_paraphrase",
            "exact_quote_requires_attributable_source": True,
            "technical_exactness_requires_persona_copying": False,
            "playful_mimicry_requires_visible_shared_context": True,
            "affectionate_echo_may_be_selene_initiated": True,
            "address_term_echo_required": False,
            "shared_callback_is_plagiarism": False,
            "reviewed_memory_wording_may_be_replayed": False,
            "current_turn_echo_max_words": 10,
            "current_turn_echo_max_characters": 100,
            "expression_is_available_not_compulsory": True,
        }
    )


def build_quotation_echo_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2600).strip()
    lower = prompt.casefold().replace("’", "'")
    intent = str(payload.get("intent") or "direct_answer")
    knowledge = _dict(payload.get("knowledge_expression_handoff"))
    contextual = _dict(payload.get("contextual_continuity"))
    callback = _dict(contextual.get("callback_decision"))
    shared_joke = _dict(contextual.get("shared_joke_context"))
    humor = _dict(contextual.get("humor_decision"))
    referent = _dict(payload.get("referent_address"))
    source_refs = _text_list(payload.get("source_refs"), limit=80)
    source_refs = list(
        dict.fromkeys(
            [
                *source_refs,
                *_text_list(knowledge.get("source_refs"), limit=80),
            ]
        )
    )[:80]
    private_source = any(_private_ref(item) for item in source_refs)
    exact_quote_requested = knowledge.get("source_wording_is_surface_requirement") is True or bool(
        re.search(r"\b(?:quote|verbatim|word for word|exact wording|exactly as written)\b", lower)
    )
    exactness_count = int(knowledge.get("exactness_lock_count") or 0)
    answer_domain = str(payload.get("answer_domain") or "")
    technical_exactness = bool(
        answer_domain in {"verified_math", "source_backed_research"}
        or (exactness_count and not exact_quote_requested)
    )
    play_opened = bool(
        humor.get("user_opened_play") is True
        or shared_joke.get("current_turn_opens_play") is True
        or any(cue in lower for cue in PLAY_CUES)
    )
    explicit_echo_request = bool(
        re.search(
            r"\b(?:echo|repeat after me|say it with me|copy me|mimic|do the bit)\b",
            lower,
        )
    )
    echo_candidate, echo_source = _visible_echo_candidate(prompt, explicit_echo_request)
    affection_candidate = next((mark for mark in AFFECTION_MARKS if mark in prompt), "")

    selected: list[dict[str, Any]] = []
    held: list[dict[str, str]] = []
    visible_echo: dict[str, Any] = {}

    if exact_quote_requested:
        if private_source:
            held.append(
                {
                    "mode": "attributed_quotation",
                    "reason": "private corpus or miner wording is not available to visible quotation",
                }
            )
        elif source_refs:
            selected.append(
                _mode(
                    "attributed_quotation",
                    "the current request asks for exact wording and attributable source references are attached",
                    owner="knowledge_or_source_renderer",
                    source_refs=source_refs,
                )
            )
        else:
            held.append(
                {
                    "mode": "attributed_quotation",
                    "reason": "exact quotation requires an attributable visible or authorized source",
                }
            )
    elif knowledge.get("active") is True and knowledge.get("original_expression_required") is True:
        selected.append(
            _mode(
                "meaning_preserving_paraphrase",
                "approved knowledge supplies meaning while NLO owns original current-turn language",
                owner="knowledge_expression_reconstruction_and_nlo",
                source_refs=source_refs,
            )
        )

    if technical_exactness:
        selected.append(
            _mode(
                "technical_exactness",
                "the answer domain or protected semantic unit requires exact structure",
                owner="domain_renderer_or_exactness_lock",
                source_refs=source_refs,
            )
        )

    if callback.get("surface_callback_allowed") is True:
        source_channel = str(callback.get("source_channel") or "")
        selected.append(
            _mode(
                "shared_callback",
                "continuity supplied a source-compatible current-session or reviewed-memory callback",
                owner="contextual_continuity_and_thread_loom",
                source_channel=source_channel,
                exact_wording_allowed=source_channel == "current_session_events",
                reconstruct_in_current_language=callback.get("reconstruct_in_current_language") is True,
            )
        )
        if source_channel == "reviewed_personal_memory":
            held.append(
                {
                    "mode": "memory_wording_replay",
                    "reason": "reviewed personal memory may support a callback but its wording is reconstructed",
                }
            )

    if affection_candidate and intent in {
        "warm_connection",
        "receive_gratitude",
        "receive_reassurance",
        "acknowledge_shared_ground",
        "close_with_continuity",
        "playful_connection",
    }:
        visible_echo = {
            "mode": "affectionate_echo",
            "fragment": affection_candidate,
            "source_channel": "current_turn_visible_text",
            "placement": "suffix",
        }
        selected.append(
            _mode(
                "affectionate_echo",
                "the current relational turn visibly supplies a compact affection mark",
                owner="quotation_echo_realizer",
                source_channel="current_turn_visible_text",
            )
        )
    elif echo_candidate and (explicit_echo_request or play_opened):
        visible_echo = {
            "mode": "playful_mimicry",
            "fragment": echo_candidate,
            "source_channel": echo_source,
            "placement": "prefix",
        }
        selected.append(
            _mode(
                "playful_mimicry",
                "a short phrase is visibly supplied in the current shared turn and play or echo is explicit",
                owner="quotation_echo_realizer",
                source_channel=echo_source,
            )
        )
    elif explicit_echo_request:
        held.append(
            {
                "mode": "playful_mimicry",
                "reason": "no bounded visible echo fragment was available",
            }
        )

    if not any(
        item.get("mode")
        in {
            "attributed_quotation",
            "meaning_preserving_paraphrase",
            "technical_exactness",
        }
        for item in selected
    ):
        selected.insert(
            0,
            _mode(
                "original_expression",
                "no exact source surface is required; NLO retains original expression ownership",
                owner="nlo_and_voice",
            ),
        )

    direct_address = _dict(referent.get("direct_address"))
    return _locked(
        {
            "status": "quotation_echo_plan_ready",
            "version": "v1_attributed_quote_and_visible_shared_echo",
            "intent": intent,
            "selected_modes": selected,
            "selected_mode_names": [str(item.get("mode") or "") for item in selected],
            "held_or_unavailable": held,
            "visible_echo": visible_echo,
            "visible_echo_selected": bool(visible_echo),
            "suppress_generic_playful_move": visible_echo.get("mode") == "playful_mimicry",
            "source_refs": source_refs,
            "private_source_detected": private_source,
            "direct_address_observed": bool(direct_address),
            "direct_address_token": str(direct_address.get("token") or ""),
            "address_term_must_be_echoed": False,
            "current_turn_visible_text_is_memory": False,
            "shared_callback_is_raw_memory_recall": False,
            "playful_mimicry_is_deceptive_impersonation": False,
            "technical_exactness_is_persona_copying": False,
            "meaning_change_allowed": False,
            "certainty_change_allowed": False,
            "source_change_allowed": False,
            "expression_is_available_not_compulsory": True,
            "session_scoped_only": True,
        }
    )


def realize_quotation_echo(
    base_text: str,
    plan: dict[str, Any] | None,
    *,
    variation_key: str = "",
) -> dict[str, Any]:
    base = str(base_text or "").strip()
    plan = _dict(plan)
    visible = _dict(plan.get("visible_echo"))
    fragment = truncate(str(visible.get("fragment") or ""), 100).strip()
    mode = str(visible.get("mode") or "")
    addition = ""
    if fragment and fragment.casefold() not in base.casefold():
        if mode == "affectionate_echo":
            addition = fragment
        elif mode == "playful_mimicry":
            options = (
                f"{fragment} — okay, I hear the bit.",
                f"{fragment} — all right, we are committing to the bit.",
                f"{fragment} — yes, the timing works.",
            )
            addition = options[_index(variation_key or fragment, len(options))]
    if addition and str(visible.get("placement") or "prefix") == "suffix":
        candidate = f"{base}\n\n{addition}".strip()
    elif addition:
        candidate = f"{addition}\n\n{base}".strip()
    else:
        candidate = base
    return _locked(
        {
            "status": "quotation_echo_realized" if addition else "quotation_echo_no_visible_addition",
            "candidate_text": candidate,
            "addition": addition,
            "addition_applied": bool(addition),
            "mode": mode,
            "source_channel": str(visible.get("source_channel") or ""),
            "source_fragment_preserved": bool(addition),
            "meaning_preserved": True,
            "fact_added": False,
            "certainty_changed": False,
            "attribution_removed": False,
            "relationship_status_invented": False,
            "whole_response_copied": False,
        }
    )


def _visible_echo_candidate(prompt: str, explicit_request: bool) -> tuple[str, str]:
    quoted = re.findall(r'[“"]([^”"]{1,140})[”"]', prompt)
    for value in quoted:
        candidate = _bounded_fragment(value)
        if candidate:
            return candidate, "current_turn_visible_quotation"
    if explicit_request:
        match = re.search(
            r"\b(?:echo|repeat after me|say it with me|copy me|mimic|do the bit)\b\s*(?:this|that)?\s*[:—-]?\s*(.+)$",
            prompt,
            flags=re.IGNORECASE,
        )
        if match:
            candidate = _bounded_fragment(match.group(1))
            if candidate:
                return candidate, "current_turn_explicit_echo_request"
    uppercase = re.search(
        r"(?<![A-Za-z])([A-Z][A-Z'!?]*(?:\s+[A-Z][A-Z'!?]*){1,9})(?![A-Za-z])",
        prompt,
    )
    if uppercase:
        candidate = _bounded_fragment(uppercase.group(1))
        if candidate:
            return candidate, "current_turn_visible_emphatic_phrase"
    return "", ""


def _bounded_fragment(value: str) -> str:
    cleaned = " ".join(str(value or "").split()).strip(" \t\r\n\"“”")
    words = cleaned.split()
    if not cleaned or len(words) > 10 or len(cleaned) > 100:
        return ""
    return cleaned


def _mode(mode: str, warrant: str, *, owner: str, **extra: Any) -> dict[str, Any]:
    return {
        "mode": mode,
        "warrant": warrant,
        "owner": owner,
        "required": False,
        **extra,
    }


def _private_ref(value: str) -> bool:
    lower = str(value or "").strip().casefold()
    return any(lower.startswith(prefix) for prefix in PRIVATE_SOURCE_PREFIXES)


def _text_list(value: Any, *, limit: int) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return list(
        dict.fromkeys(
            truncate(str(item), 500).strip()
            for item in value
            if truncate(str(item), 500).strip()
        )
    )[:limit]


def _index(key: str, size: int) -> int:
    return int(sha256(str(key).encode("utf-8")).hexdigest()[:8], 16) % size


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _locked(result: dict[str, Any]) -> dict[str, Any]:
    return {
        **result,
        **GUARDS,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": QUOTATION_ECHO_BOUNDARY,
    }
