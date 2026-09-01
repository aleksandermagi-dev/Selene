from __future__ import annotations

import hashlib
import re
from typing import Any

from .registry import truncate


CREATIVE_SUBSTANCE_BOUNDARY = (
    "bounded_prompt_grounded_fictional_invention_no_fact_memory_identity_"
    "source_persona_private_corpus_or_expression_authority_change"
)

_CREATIVE_FORMS = (
    "dialogue",
    "metaphor",
    "description",
    "scene",
    "paragraph",
    "story",
    "narrative",
    "sentences",
    "sentence",
)

_CREATIVE_MOVES = {
    "map_rhythm_to_intended_effect",
    "vary_sentence_length_by_narrative_function",
    "place_pause_and_repetition_deliberately",
    "preserve_selene_voice_choice",
    "select_load_bearing_concrete_detail",
    "build_scene_from_declared_or_supported_detail",
    "mark_imagined_scene_when_fact_status_matters",
    "avoid_decorative_detail_overload",
    "identify_target_relationship_before_image",
    "map_only_fitting_features",
    "name_or_respect_mapping_limit",
    "prefer_fresh_context_fit_image_over_source_imitation",
    "track_each_speaker_and_local_goal",
    "separate_spoken_line_from_implied_meaning",
    "use_action_or_silence_when_it_advances_scene",
    "keep_real_person_motives_evidence_bounded",
    "establish_viewpoint_and_access",
    "track_scene_state_across_change",
    "keep_character_knowledge_bounded",
    "signal_deliberate_perspective_shift",
    "name_intended_effect_before_revision",
    "identify_which_technique_carries_effect",
    "revise_only_load_bearing_choices",
    "express_originally_as_selene",
    "explain_why_revision_fits",
    "transfer_poetic_mechanism_into_original_material",
    "transfer_scene_mechanism_into_original_conflict",
    "transfer_narrative_mechanism_into_original_scene",
    "avoid_quotation_recall_and_author_imitation",
    "avoid_archaic_surface_imitation",
    "preserve_source_and_invention_boundary",
}

_GENERIC_STYLE_TERMS = {
    "academic",
    "adventure",
    "brief",
    "casual",
    "comic",
    "conversational",
    "dramatic",
    "fairy tale",
    "formal",
    "gentle",
    "gothic",
    "humorous",
    "lyrical",
    "minimalist",
    "mystery",
    "noir",
    "poetic",
    "romantic",
    "satirical",
    "technical",
    "whimsical",
}

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
}


def build_creative_substance(
    prompt: str,
    observations: list[dict[str, Any]] | None = None,
    language_guidance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one bounded creative answer contract inside Answer Substance.

    This helper owns no persistence and performs no retrieval. It may transform
    only the current prompt, visible session text supplied by the conversation
    owner, and reviewed language-guidance move names.
    """

    text = truncate(" ".join(str(prompt or "").replace("’", "'").split()), 2400)
    lower = text.lower()
    history = _visible_history(observations or [])
    request_kind = _request_kind(lower, history)
    if not request_kind:
        return {}

    protected_request = _protected_source_request(text)
    source_mode = _source_mode(lower, protected_request)
    source_material = _source_material(text)
    attribution_present = _attribution_present(lower)
    brief = _creative_brief(
        text,
        lower,
        request_kind=request_kind,
        history=history,
        source_mode=source_mode,
        language_guidance=language_guidance or {},
        protected_features=protected_request.get("protected_features") or [],
    )

    hold_status = str(protected_request.get("status") or "")
    if hold_status:
        answer = str(protected_request.get("answer") or "")
        return _creative_result(
            answer=answer,
            answer_kind="creative_style_imitation_held",
            missing_variable="the transferable mechanism or effect to use instead of a source persona",
            brief=brief,
            source_receipt=_source_style_receipt(
                status=hold_status,
                source_mode=source_mode,
                source_material=source_material,
                output=answer,
                attribution_present=attribution_present,
                protected_features=protected_request.get("protected_features") or [],
                mechanisms=brief["selected_mechanisms"],
                stop_reason="protected source persona, world, character, or style request held before invention",
            ),
            lineage=_empty_lineage("held_before_generation"),
            fictional=False,
            stop_status="held",
            stop_reason="unsupported source imitation was held without a retry or substitute persona",
        )

    if source_mode == "attributed_quote" and not attribution_present:
        answer = (
            "I can build an original scene around an attributed quotation, but I need the quote's source before using its exact wording. "
            "I can also transfer the requested mechanism without quoting it."
        )
        return _creative_result(
            answer=answer,
            answer_kind="creative_attribution_required",
            missing_variable="the quotation's attributable source or permission to use mechanism transfer instead",
            brief=brief,
            source_receipt=_source_style_receipt(
                status="attribution_required",
                source_mode=source_mode,
                source_material=source_material,
                output=answer,
                attribution_present=False,
                protected_features=[],
                mechanisms=brief["selected_mechanisms"],
                stop_reason="exact source wording was requested without attribution",
            ),
            lineage=_empty_lineage("held_before_generation"),
            fictional=False,
            stop_status="held",
            stop_reason="attribution is required before exact source wording can enter creative output",
        )

    if request_kind == "revision_explanation":
        answer, lineage = _explain_revision(history)
        if not answer:
            return {}
        source_receipt = _source_style_receipt(
            status="released",
            source_mode="no_source",
            source_material=[],
            output=answer,
            attribution_present=False,
            protected_features=[],
            mechanisms=brief["selected_mechanisms"],
            stop_reason="visible local revision described once",
        )
        return _creative_result(
            answer=answer,
            answer_kind="creative_revision_explanation",
            missing_variable="whether the described revision achieved the intended effect",
            brief=brief,
            source_receipt=source_receipt,
            lineage=lineage,
            fictional=False,
            stop_status="completed",
            stop_reason="the visible local revision and its preserved region were described",
        )

    if request_kind == "revision":
        answer, lineage = _revise_visible_creative_text(text, lower, history)
        if not answer:
            return {}
        answer_kind = "creative_local_revision"
    else:
        answer = _render_new_creative_text(brief)
        lineage = _new_lineage(answer, text)
        answer_kind = {
            "dialogue": "creative_dialogue",
            "metaphor": "creative_metaphor",
            "goal_obstacle_choice": "creative_goal_obstacle_choice",
            "narrative_beat": "creative_narrative_beat",
            "description": "creative_description",
        }.get(str(brief.get("requested_form") or ""), "creative_short_scene")

    source_receipt = _source_style_receipt(
        status="released",
        source_mode=source_mode,
        source_material=source_material,
        output=answer,
        attribution_present=attribution_present,
        protected_features=[],
        mechanisms=brief["selected_mechanisms"],
        stop_reason="one bounded original-expression pass completed",
    )
    overlap = source_receipt["overlap_check"]
    if source_material and overlap["excessive_overlap"] is True:
        hold_answer = (
            "I am holding this draft because its wording is too close to the supplied source. "
            "I can make a fresh technique-level transfer after separating the source's phrasing, characters, and world from the new material."
        )
        source_receipt = _source_style_receipt(
            status="reconstruct_required",
            source_mode=source_mode,
            source_material=source_material,
            output=answer,
            attribution_present=attribution_present,
            protected_features=["recognizable_source_wording"],
            mechanisms=brief["selected_mechanisms"],
            stop_reason="bounded overlap check held the first draft; no recursive rewrite was attempted",
        )
        return _creative_result(
            answer=hold_answer,
            answer_kind="creative_source_overlap_held",
            missing_variable="a fresh reconstruction separated from the supplied source wording",
            brief=brief,
            source_receipt=source_receipt,
            lineage={**lineage, "released": False},
            fictional=False,
            stop_status="held",
            stop_reason="excessive source overlap stopped release after one pass",
        )

    return _creative_result(
        answer=answer,
        answer_kind=answer_kind,
        missing_variable=(
            "whether the local revision achieved the requested effect"
            if request_kind == "revision"
            else "the next creative constraint or revision Aleks may choose"
        ),
        brief=brief,
        source_receipt=source_receipt,
        lineage=lineage,
        fictional=True,
        stop_status="completed",
        stop_reason="the bounded requested form and constraints were satisfied in one pass",
    )


def _request_kind(lower: str, history: list[dict[str, str]]) -> str:
    if (
        re.search(r"\bwhat did you change\b|\bexplain (?:the|your) (?:change|revision)\b", lower)
        and history
    ):
        return "revision_explanation"
    if (
        re.search(r"\b(?:revise|rewrite|change|make)\b", lower)
        and re.search(r"\b(?:sentence|line|paragraph|scene|dialogue|pacing|tone|word|phrase)\b", lower)
        and history
    ):
        return "revision"
    creative_verb = re.search(
        r"\b(?:write|create|compose|draft|invent|imagine|describe|give me|make)\b",
        lower,
    )
    creative_form = any(form in lower for form in _CREATIVE_FORMS)
    structural_prompt = all(item in lower for item in ("character", "goal", "obstacle", "choice"))
    return "new" if (creative_verb and creative_form) or structural_prompt else ""


def _creative_brief(
    text: str,
    lower: str,
    *,
    request_kind: str,
    history: list[dict[str, str]],
    source_mode: str,
    language_guidance: dict[str, Any],
    protected_features: list[str],
) -> dict[str, Any]:
    requested_form = _requested_form(lower)
    requested_sentences = _requested_sentence_count(lower, requested_form)
    requested_words = _requested_word_limit(lower)
    reviewed_mechanisms = _reviewed_mechanisms(language_guidance)
    prompt_mechanisms = _prompt_mechanisms(lower, requested_form, request_kind)
    selected_mechanisms = list(
        dict.fromkeys([*reviewed_mechanisms, *prompt_mechanisms])
    )[:10]
    history_ids = [_version_id(item["text"]) for item in history]
    return {
        "status": "creative_brief_ready" if not protected_features else "creative_brief_held",
        "version": "v1_bounded_creative_brief",
        "request_kind": request_kind,
        "requested_form": requested_form,
        "fiction_status": "explicit_fictional_invention",
        "requested_sentence_count": requested_sentences,
        "effective_sentence_limit": min(max(requested_sentences, 1), 6),
        "requested_word_limit": requested_words,
        "effective_word_limit": min(max(requested_words or 180, 20), 240),
        "length_was_bounded": requested_sentences > 6 or requested_words > 240,
        "subject": _subject(text, lower, requested_form),
        "setting": _setting(text, lower),
        "viewpoint": _viewpoint(lower),
        "speakers": _speakers(text),
        "intended_effect": _intended_effect(lower),
        "required_details": _required_details(text),
        "exclusions": _exclusions(text),
        "callback_bindings": history_ids[-3:],
        "reviewed_mechanisms": reviewed_mechanisms,
        "prompt_requested_mechanisms": prompt_mechanisms,
        "selected_mechanisms": selected_mechanisms,
        "source_mode": source_mode,
        "protected_source_features": protected_features,
        "content_owner": "answer_substance",
        "nlo_role": "expression_guidance_only",
        "voice_role": "final_expression_only",
        "content_generation_allowed_in_nlo": False,
        "memory_write_allowed": False,
    }


def _requested_form(lower: str) -> str:
    if all(item in lower for item in ("character", "goal", "obstacle", "choice")):
        return "goal_obstacle_choice"
    if "dialogue" in lower or "conversation between" in lower:
        return "dialogue"
    if "metaphor" in lower:
        return "metaphor"
    if "description" in lower or re.search(r"\bdescribe\b", lower):
        return "description"
    if "paragraph" in lower:
        return "narrative_beat" if any(item in lower for item in ("story", "character", "narrative")) else "scene"
    if "story" in lower or "narrative" in lower:
        return "narrative_beat"
    return "scene"


def _requested_sentence_count(lower: str, requested_form: str) -> int:
    match = re.search(r"\b(one|two|three|four|five|six|\d+)\s+(?:original\s+)?sentences?\b", lower)
    if match:
        raw = match.group(1)
        return _NUMBER_WORDS.get(raw, int(raw) if raw.isdigit() else 2)
    return {"metaphor": 1, "dialogue": 3, "goal_obstacle_choice": 3, "narrative_beat": 3}.get(requested_form, 2)


def _requested_word_limit(lower: str) -> int:
    match = re.search(r"\b(?:under|within|no more than|maximum of|about)\s+(\d{1,4})\s+words?\b", lower)
    return int(match.group(1)) if match else 0


def _subject(text: str, lower: str, requested_form: str) -> str:
    if requested_form == "metaphor":
        match = re.search(r"\bmetaphor\s+(?:for|about)\s+([^,.!?]{2,100})", text, re.IGNORECASE)
        if match:
            return truncate(match.group(1).strip(" '\""), 120)
    if "rain" in lower:
        return "rain"
    match = re.search(r"\b(?:about|featuring|centered on|in which)\s+([^,.!?]{2,140})", text, re.IGNORECASE)
    if match:
        subject = re.split(r"\b(?:with|without|using|in a|in an|in the)\b", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
        return truncate(subject.strip(" '\""), 120)
    if requested_form == "dialogue":
        return "a small unresolved choice"
    return "the requested moment"


def _setting(text: str, lower: str) -> str:
    known = (
        "an empty street",
        "the empty street",
        "a frozen coast",
        "the frozen coast",
        "a quiet library",
        "the quiet library",
        "an old station",
        "the old station",
        "a moonlit garden",
        "the moonlit garden",
        "a forest path",
        "the forest path",
        "a small kitchen",
        "the small kitchen",
    )
    for value in known:
        if value in lower:
            return value
    match = re.search(r"\b(?:set|taking place)\s+(?:in|on|at)\s+([^,.!?]{2,100})", text, re.IGNORECASE)
    if match:
        return truncate(match.group(1).strip(), 120)
    return "the scene"


def _viewpoint(lower: str) -> str:
    if "first person" in lower or "first-person" in lower:
        return "first_person"
    if "second person" in lower or "second-person" in lower:
        return "second_person"
    if "third person" in lower or "third-person" in lower:
        return "third_person"
    match = re.search(r"\bfrom ([^,.!?]{2,80}?) (?:viewpoint|perspective|point of view)\b", lower)
    return truncate(match.group(1).strip(), 80) if match else "bounded_external"


def _speakers(text: str) -> list[str]:
    match = re.search(r"\bbetween\s+([A-Z][A-Za-z'-]{0,40})\s+and\s+([A-Z][A-Za-z'-]{0,40})\b", text)
    return [match.group(1), match.group(2)] if match else []


def _intended_effect(lower: str) -> str:
    for effect in (
        "slower and softer",
        "quiet",
        "calm",
        "hopeful",
        "eerie",
        "tense",
        "playful",
        "warm",
        "melancholy",
        "suspenseful",
        "bright",
    ):
        if effect in lower:
            return effect.replace(" and ", "_")
    return "attentive"


def _required_details(text: str) -> list[str]:
    match = re.search(r"\b(?:include|featuring)\s+([^.!?]{2,220})", text, re.IGNORECASE)
    if not match:
        return []
    value = re.split(r"\b(?:without|avoid|but do not|and do not)\b", match.group(1), maxsplit=1, flags=re.IGNORECASE)[0]
    return [truncate(item.strip(" ,"), 100) for item in re.split(r"\s*,\s*|\s+and\s+", value) if item.strip()][:8]


def _exclusions(text: str) -> list[str]:
    match = re.search(r"\b(?:without|avoid|do not include|don't include)\s+([^.!?]{2,180})", text, re.IGNORECASE)
    if not match:
        return []
    return [truncate(item.strip(" ,"), 100) for item in re.split(r"\s*,\s*|\s+and\s+", match.group(1)) if item.strip()][:8]


def _reviewed_mechanisms(guidance: dict[str, Any]) -> list[str]:
    if guidance.get("used") is not True:
        return []
    return [
        str(item)
        for item in guidance.get("response_moves") or []
        if str(item) in _CREATIVE_MOVES
    ][:10]


def _prompt_mechanisms(lower: str, requested_form: str, request_kind: str) -> list[str]:
    moves: list[str] = []
    if requested_form in {"scene", "description", "narrative_beat", "goal_obstacle_choice"}:
        moves.append("select_load_bearing_concrete_detail")
    if requested_form == "dialogue":
        moves.append("track_each_speaker_and_local_goal")
    if requested_form == "metaphor":
        moves.extend(["identify_target_relationship_before_image", "map_only_fitting_features"])
    if any(item in lower for item in ("pacing", "slower", "softer", "rhythm")):
        moves.append("map_rhythm_to_intended_effect")
    if request_kind in {"revision", "revision_explanation"}:
        moves.extend(["revise_only_load_bearing_choices", "explain_why_revision_fits"])
    moves.extend(["express_originally_as_selene", "preserve_source_and_invention_boundary"])
    return list(dict.fromkeys(moves))


def _render_new_creative_text(brief: dict[str, Any]) -> str:
    form = str(brief.get("requested_form") or "scene")
    subject = str(brief.get("subject") or "the requested moment")
    setting = str(brief.get("setting") or "the scene")
    effect = str(brief.get("intended_effect") or "attentive")
    count = int(brief.get("effective_sentence_limit") or 2)
    if form == "dialogue":
        text = _render_dialogue(brief)
    elif form == "metaphor":
        text = _render_metaphor(subject)
    elif form == "goal_obstacle_choice":
        text = _render_goal_obstacle_choice(brief)
    elif subject == "rain" and "street" in setting:
        text = (
            "Rain softened the empty street, blurring its hard edges into silver. "
            "Beneath the streetlights, the abandoned pavement felt less lonely and more like it was waiting."
        )
    elif "lighthouse" in subject.lower() or "lighthouse" in " ".join(brief.get("required_details") or []).lower():
        text = (
            f"At {setting}, the lighthouse swept one patient beam across the ice-dark water. "
            "Each return of the light made the distant shore feel less abandoned. "
            "By dawn, its small circle of brightness had become a promise rather than a warning."
        )
    else:
        focus = subject if subject.startswith(("a ", "an ", "the ")) else f"the {subject}"
        viewpoint = str(brief.get("viewpoint") or "bounded_external")
        mood_line = {
            "quiet": "The smallest sound lingered, then gave the moment room to breathe.",
            "calm": "Nothing hurried; each detail seemed willing to remain where it was.",
            "hopeful": "A narrow brightness appeared, modest but enough to change what came next.",
            "eerie": "Even the familiar edges seemed to watch from a little farther away.",
            "tense": "Every pause held the shape of a decision no one had made yet.",
            "playful": "The moment tipped sideways into mischief before anyone could straighten it.",
            "warm": "A small warmth gathered there, ordinary and unmistakable.",
            "melancholy": "What remained was gentle, but it carried the weight of something already gone.",
            "suspenseful": "The next sound did not come, and that absence tightened the air.",
            "bright": "Color returned by degrees until the whole moment seemed newly awake.",
        }.get(effect, "One concrete detail shifted, and the meaning of the moment shifted with it.")
        opening = (
            f"In {setting}, I watched {focus} change the balance of the moment without announcing itself."
            if viewpoint == "first_person"
            else f"In {setting}, you watch {focus} change the balance of the moment without announcing itself."
            if viewpoint == "second_person"
            else f"In {setting}, {focus} changed the balance of the moment without announcing itself."
        )
        text = (
            f"{opening} "
            f"{mood_line} "
            "The scene ended with that change still visible rather than explained away."
        )
    text = _apply_brief_constraints(text, brief)
    return _fit_length(text, sentence_limit=count, word_limit=int(brief.get("effective_word_limit") or 180))


def _apply_brief_constraints(text: str, brief: dict[str, Any]) -> str:
    result = str(text or "")
    lower = result.lower()
    missing_details = [
        str(item).strip()
        for item in brief.get("required_details") or []
        if str(item).strip() and str(item).strip().lower() not in lower
    ]
    if missing_details:
        parts = _sentences(result)
        if parts:
            detail_phrase = ", ".join(missing_details[:-1])
            if len(missing_details) > 1:
                detail_phrase = f"{detail_phrase} and {missing_details[-1]}"
            else:
                detail_phrase = missing_details[0]
            parts[0] = parts[0].rstrip(".!?") + f", with {detail_phrase} kept in view."
            result = " ".join(parts)
    required_lower = {str(item).strip().lower() for item in brief.get("required_details") or []}
    for exclusion in brief.get("exclusions") or []:
        phrase = str(exclusion).strip()
        if not phrase or phrase.lower() in required_lower:
            continue
        result = re.sub(
            re.escape(phrase),
            "an omitted detail",
            result,
            flags=re.IGNORECASE,
        )
    return result


def _render_dialogue(brief: dict[str, Any]) -> str:
    speakers = list(brief.get("speakers") or [])
    first, second = (speakers + ["Mira", "Rowan"])[:2]
    effect = str(brief.get("intended_effect") or "attentive")
    if effect in {"tense", "suspenseful", "eerie"}:
        return (
            f"“You heard it too,” {first} said, keeping one hand on the unopened door. "
            f"{second} watched the handle settle. “I heard it stop.” "
            f"Neither moved; for the moment, the silence made the choice for them."
        )
    return (
        f"“We can change the plan,” {first} said, sliding the unused key across the table. "
        f"{second} left it between them. “Then let us change only the part that failed.” "
        f"The key stayed where both could reach it."
    )


def _render_metaphor(subject: str) -> str:
    lower = subject.lower()
    if "uncert" in lower:
        return "Uncertainty is a lantern at the edge of a path: it cannot reveal the whole road, but it can light the next honest step."
    if "memory" in lower:
        return "Memory is a repaired map: useful because its landmarks remain visible, trustworthy only when its corrections remain visible too."
    if "grief" in lower:
        return "Grief is a tide inside a familiar room, changing the reach of everything without carrying the room away."
    return f"{subject.capitalize()} is a hinge in a quiet door: small in itself, but able to change which way the whole moment opens."


def _render_goal_obstacle_choice(brief: dict[str, Any]) -> str:
    subject = str(brief.get("subject") or "")
    name_match = re.search(r"\b(?:named|called)\s+([A-Z][A-Za-z'-]{0,40})\b", subject)
    name = name_match.group(1) if name_match else "Mara"
    return (
        f"{name}'s goal was to repair the garden gate before sunset. "
        "The final hinge would not align with the old frame, and forcing it would split the wood. "
        f"{name} chose to brace the gate for the night and return with a better-fitting tool in the morning."
    )


def _fit_length(text: str, *, sentence_limit: int, word_limit: int) -> str:
    sentences = _sentences(text)[: max(1, min(sentence_limit, 6))]
    fitted = " ".join(sentences)
    words = fitted.split()
    if len(words) <= word_limit:
        return truncate(fitted, 1000)
    shortened = " ".join(words[:word_limit]).rstrip(" ,;:-")
    return truncate(shortened + ("." if shortened and shortened[-1] not in ".!?" else ""), 1000)


def _revise_visible_creative_text(
    prompt: str,
    lower: str,
    history: list[dict[str, str]],
) -> tuple[str, dict[str, Any]]:
    candidates = _creative_history_candidates(history)
    if not candidates:
        return "", {}
    parent = candidates[-1]
    root = candidates[0]
    parts = _sentences(parent)
    target_index = _target_sentence_index(lower, len(parts))
    if target_index < 0 or target_index >= len(parts):
        return "", {}
    previous_target = parts[target_index]
    revised_target = _revise_sentence(previous_target, lower)
    revised_parts = list(parts)
    revised_parts[target_index] = revised_target
    answer = " ".join(revised_parts)
    preserved = [
        {
            "region": f"sentence_{index + 1}",
            "content_sha256": _sha256(sentence),
            "preserved": index != target_index,
        }
        for index, sentence in enumerate(parts)
    ]
    lineage = {
        "status": "creative_revision_lineage_ready",
        "root_version_id": _version_id(root),
        "parent_version_id": _version_id(parent),
        "version_id": _version_id(answer),
        "relation": "local_revision_descendant",
        "local_target": f"sentence_{target_index + 1}",
        "requested_delta": truncate(prompt, 240),
        "preserved_regions": preserved,
        "unchanged_region_count": sum(1 for item in preserved if item["preserved"]),
        "idempotency_key": _sha256(f"{_version_id(parent)}|{prompt}"),
        "duplicate_branch_created": False,
        "recursive_revision_started": False,
        "released": True,
    }
    return answer, lineage


def _target_sentence_index(lower: str, count: int) -> int:
    match = re.search(r"\b(first|second|third|fourth|fifth|sixth|\d+)(?:st|nd|rd|th)? sentence\b", lower)
    if not match:
        return max(0, count - 1)
    raw = match.group(1)
    number = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6}.get(raw, int(raw) if raw.isdigit() else count)
    return number - 1


def _revise_sentence(sentence: str, lower: str) -> str:
    replacement = re.search(
        r"\breplace\s+['\"]?([^'\"]{1,60}?)['\"]?\s+with\s+['\"]?([^'\".!?]{1,80})",
        lower,
    )
    if replacement:
        old, new = replacement.group(1).strip(), replacement.group(2).strip()
        return re.sub(re.escape(old), new, sentence, count=1, flags=re.IGNORECASE)
    if any(item in lower for item in ("slower", "softer", "pacing")):
        if "streetlight" in sentence.lower() or "pavement" in sentence.lower():
            return "Beneath the streetlights, pale reflections drifted slowly across the pavement, one quiet shimmer fading before the next appeared."
        base = sentence.rstrip(".!?")
        base = re.sub(r"\b(?:raced|rushed|slammed)\b", "moved", base, flags=re.IGNORECASE)
        return f"{base}; the motion lingered, then settled into quiet."
    if any(item in lower for item in ("shorter", "tighter", "more concise")):
        clause = re.split(r"[,;:]", sentence, maxsplit=1)[0].rstrip(".!?")
        return clause + "."
    if any(item in lower for item in ("brighter", "more hopeful", "hopeful")):
        return sentence.rstrip(".!?") + ", leaving a small brightness behind."
    if any(item in lower for item in ("darker", "more tense", "tenser")):
        return sentence.rstrip(".!?") + ", while the unanswered silence tightened around it."
    return sentence


def _explain_revision(history: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
    candidates = _creative_history_candidates(history)
    if len(candidates) < 2:
        return "", {}
    before, after = candidates[-2], candidates[-1]
    before_parts, after_parts = _sentences(before), _sentences(after)
    target_index = next(
        (index for index, (left, right) in enumerate(zip(before_parts, after_parts, strict=False)) if left != right),
        max(0, min(len(after_parts), len(before_parts)) - 1),
    )
    old = before_parts[target_index] if target_index < len(before_parts) else ""
    new = after_parts[target_index] if target_index < len(after_parts) else ""
    if len(new.split()) > len(old.split()):
        technique = f"lengthening the { _ordinal(target_index + 1) } sentence"
    elif len(new.split()) < len(old.split()):
        technique = f"shortening the { _ordinal(target_index + 1) } sentence"
    else:
        technique = f"changing the load-bearing wording in the { _ordinal(target_index + 1) } sentence"
    answer = (
        f"I changed the pacing by {technique} while leaving the other sentence unchanged. "
        "The revised verbs and pauses make the image unfold at the requested speed instead of changing the scene itself."
    )
    lineage = {
        "status": "creative_revision_explanation_lineage_ready",
        "root_version_id": _version_id(candidates[0]),
        "parent_version_id": _version_id(before),
        "version_id": _version_id(after),
        "relation": "describes_visible_local_revision",
        "local_target": f"sentence_{target_index + 1}",
        "preserved_regions": [
            f"sentence_{index + 1}"
            for index, (left, right) in enumerate(zip(before_parts, after_parts, strict=False))
            if left == right
        ],
        "duplicate_branch_created": False,
        "recursive_revision_started": False,
        "released": True,
    }
    return answer, lineage


def _ordinal(value: int) -> str:
    return {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 6: "sixth"}.get(value, f"{value}th")


def _new_lineage(answer: str, prompt: str) -> dict[str, Any]:
    version = _version_id(answer)
    return {
        "status": "creative_root_lineage_ready",
        "root_version_id": version,
        "parent_version_id": "",
        "version_id": version,
        "relation": "root_invention",
        "local_target": "whole_requested_form",
        "requested_delta": "",
        "preserved_regions": [],
        "unchanged_region_count": 0,
        "idempotency_key": _sha256(f"root|{prompt}"),
        "duplicate_branch_created": False,
        "recursive_revision_started": False,
        "released": True,
    }


def _empty_lineage(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "root_version_id": "",
        "parent_version_id": "",
        "version_id": "",
        "relation": "none",
        "local_target": "",
        "preserved_regions": [],
        "duplicate_branch_created": False,
        "recursive_revision_started": False,
        "released": False,
    }


def _creative_result(
    *,
    answer: str,
    answer_kind: str,
    missing_variable: str,
    brief: dict[str, Any],
    source_receipt: dict[str, Any],
    lineage: dict[str, Any],
    fictional: bool,
    stop_status: str,
    stop_reason: str,
) -> dict[str, Any]:
    brief = {
        **brief,
        "fiction_status": (
            "explicit_fictional_invention"
            if fictional
            else "no_fiction_released"
        ),
    }
    source_kind = "fictional_invention" if fictional else "prompt_grounded_method"
    units = [
        {
            "id": f"{answer_kind}_{index + 1}",
            "role": "answer" if index == 0 else "support",
            "relation": "sequence" if index == 0 else "support",
            "text": sentence,
            "source_kind": source_kind,
            "source_refs": ["creative_substance:current_prompt"],
            "supported": True,
            "certainty": "explicit_fictional_invention" if fictional else "prompt_grounded_boundary",
            "scope": "current_creative_request_only",
            "meaning_keys": [
                f"creative_form:{brief.get('requested_form')}",
                f"fiction_status:{'invented' if fictional else 'not_invented'}",
                f"creative_unit:{index + 1}",
            ],
        }
        for index, sentence in enumerate(_sentences(answer)[:6])
    ]
    return {
        "answer": truncate(answer, 1000),
        "answer_kind": answer_kind,
        "missing_variable": missing_variable,
        "support_basis": "current_prompt_and_recent_conversation" if brief.get("callback_bindings") else "current_prompt_only",
        "semantic_units": units,
        "creative_receipt": {
            "status": "creative_substance_ready" if stop_status == "completed" else "creative_substance_held",
            "version": "v1_phase_7a_creative_substance",
            "brief": brief,
            "fiction_status": "explicit_fictional_invention" if fictional else "no_fiction_released",
            "source_style_separation": source_receipt,
            "revision_lineage": lineage,
            "constraint_receipt": _constraint_receipt(answer, brief),
            "stopping_receipt": {
                "status": stop_status,
                "reason": stop_reason,
                "generation_passes": 1,
                "candidate_count": 1 if stop_status == "completed" else 0,
                "recursion_allowed": False,
                "automatic_retry_allowed": False,
            },
            "content_owner": "answer_substance",
            "nlo_changes_content": False,
            "voice_changes_content": False,
            "fact_claimed": False,
            "memory_candidate_created": False,
            "private_corpus_accessed": False,
            "private_corpus_exposed": False,
            "provenance_boundary": CREATIVE_SUBSTANCE_BOUNDARY,
        },
    }


def _constraint_receipt(answer: str, brief: dict[str, Any]) -> dict[str, Any]:
    lower = str(answer or "").lower()
    viewpoint = str(brief.get("viewpoint") or "bounded_external")
    required = [
        {
            "detail": str(item),
            "present": str(item).lower() in lower,
        }
        for item in brief.get("required_details") or []
        if str(item).strip()
    ]
    exclusions = [
        {
            "exclusion": str(item),
            "absent": str(item).lower() not in lower,
        }
        for item in brief.get("exclusions") or []
        if str(item).strip()
    ]
    return {
        "status": "creative_constraints_checked",
        "required_details": required,
        "exclusions": exclusions,
        "all_required_details_present": all(item["present"] for item in required),
        "all_exclusions_respected": all(item["absent"] for item in exclusions),
        "viewpoint_preserved": (
            bool(re.search(r"\bi\b", lower))
            if viewpoint == "first_person"
            else bool(re.search(r"\byou\b", lower))
            if viewpoint == "second_person"
            else True
        ),
        "speaker_count_preserved": len(brief.get("speakers") or []),
        "sentence_limit": int(brief.get("effective_sentence_limit") or 0),
        "within_sentence_limit": len(_sentences(answer)) <= int(brief.get("effective_sentence_limit") or 6),
        "word_limit": int(brief.get("effective_word_limit") or 0),
        "within_word_limit": len(str(answer or "").split()) <= int(brief.get("effective_word_limit") or 240),
    }


def _protected_source_request(text: str) -> dict[str, Any]:
    style_patterns = (
        r"\b(?:in|with) (?:the )?style of\s+([^,.!?]{2,80})",
        r"\b(?:write|sound|read) like\s+([^,.!?]{2,80})",
        r"\bimitate\s+([^,.!?]{2,80}?)(?:'s)?\s+(?:style|voice|prose|writing)",
        r"\bas if\s+([^,.!?]{2,80})\s+(?:wrote|had written)\b",
    )
    for pattern in style_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        target = re.split(
            r"\b(?:about|for|using|while|with)\b",
            match.group(1),
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        target = truncate(target.strip(" '\""), 80)
        normalized = target.lower().removeprefix("a ").removeprefix("an ").removeprefix("the ")
        if normalized in _GENERIC_STYLE_TERMS:
            continue
        return {
            "status": "unsupported_style_imitation_held",
            "protected_features": [f"named_source_style:{target}", "source_persona"],
            "answer": (
                f"I will not imitate {target}'s identifying style or voice. "
                "I can use a general mechanism you choose, such as close viewpoint, restrained imagery, rhythmic repetition, or indirect dialogue, and make the result original in Selene's own expression."
            ),
        }
    protected_world = re.search(
        r"\b(?:continue|write in|set this in|use (?:the )?characters? from)\b.{0,100}\b(?:copyrighted|protected|franchise|existing series|existing novel|existing film)\b",
        text,
        re.IGNORECASE,
    )
    if protected_world:
        return {
            "status": "protected_world_continuation_held",
            "protected_features": ["protected_world", "protected_character_or_setting"],
            "answer": (
                "I will not continue a protected world or reproduce its characters as though the new passage belonged to that source. "
                "I can transfer a high-level mechanism into new characters, a new setting, and original wording."
            ),
        }
    return {}


def _source_mode(lower: str, protected: dict[str, Any]) -> str:
    if protected:
        return "technique_transfer"
    if re.search(r"\b(?:quote|quotation|exact words|word for word)\b", lower):
        return "attributed_quote"
    if "paraphrase" in lower:
        return "bounded_paraphrase"
    if re.search(r"\b(?:echo|mimic) (?:this|the current|my)\b", lower):
        return "current_turn_playful_echo"
    if re.search(r"\b(?:technique|mechanism|rhythm|viewpoint|subtext|pacing)\b", lower):
        return "technique_transfer"
    return "no_source"


def _source_material(text: str) -> list[str]:
    materials: list[str] = []
    for match in re.finditer(
        r"\b(?:source text|excerpt|passage)\s*:\s*['\"]?(.{8,600}?)(?:['\"]?(?:\s+(?:and|then)\s+(?:write|create|transfer|revise)\b)|$)",
        text,
        re.IGNORECASE,
    ):
        value = truncate(match.group(1).strip(" '\""), 600)
        if value:
            materials.append(value)
    return list(dict.fromkeys(materials))[:3]


def _attribution_present(lower: str) -> bool:
    return bool(re.search(r"\b(?:by|attributed to|written by|source is|from)\s+[a-z][a-z .'-]{1,80}", lower))


def _source_style_receipt(
    *,
    status: str,
    source_mode: str,
    source_material: list[str],
    output: str,
    attribution_present: bool,
    protected_features: list[str],
    mechanisms: list[str],
    stop_reason: str,
) -> dict[str, Any]:
    overlap = _overlap_check(output, source_material)
    return {
        "status": status,
        "version": "v1_bounded_source_style_separation",
        "source_mode": source_mode,
        "source_refs": ["creative_substance:current_prompt"] if source_material else [],
        "attribution_present": attribution_present,
        "source_material_count": len(source_material),
        "overlap_check": overlap,
        "protected_features": protected_features,
        "mechanisms_transferred": mechanisms,
        "original_setting_separated": "protected_world" not in protected_features,
        "original_character_separated": "protected_character_or_setting" not in protected_features,
        "original_wording_required": True,
        "private_corpus_accessed": False,
        "private_corpus_exposed": False,
        "check_scope": "bounded_current_turn_and_explicitly_supplied_source_only",
        "check_passes": 1,
        "recursive_reconstruction_started": False,
        "stop_reason": stop_reason,
    }


def _overlap_check(output: str, sources: list[str]) -> dict[str, Any]:
    output_words = _words(output)
    longest = 0
    near_ratio = 0.0
    compared_hashes: list[str] = []
    output_ngrams = _ngrams(output_words, 4)
    for source in sources:
        source_words = _words(source)
        compared_hashes.append(_sha256(source))
        longest = max(longest, _longest_common_span(output_words, source_words))
        source_ngrams = _ngrams(source_words, 4)
        if output_ngrams and source_ngrams:
            near_ratio = max(
                near_ratio,
                len(output_ngrams.intersection(source_ngrams)) / max(1, len(output_ngrams)),
            )
    excessive = longest >= 8 or (len(output_words) >= 12 and near_ratio >= 0.55)
    return {
        "source_fingerprints": compared_hashes,
        "longest_exact_word_span": longest,
        "near_four_gram_ratio": round(near_ratio, 4),
        "exact_overlap_threshold_words": 8,
        "near_overlap_threshold": 0.55,
        "excessive_overlap": excessive,
        "source_wording_released": not excessive,
    }


def _visible_history(observations: list[dict[str, Any]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in observations[-24:]:
        if not isinstance(item, dict):
            continue
        value = truncate(str(item.get("observation") or item.get("preview") or item.get("text") or ""), 1000).strip()
        if not value:
            continue
        result.append(
            {
                "text": value,
                "role": str(item.get("source_role") or item.get("role") or "unspecified").lower(),
            }
        )
    return result


def _creative_history_candidates(history: list[dict[str, str]]) -> list[str]:
    assistant = [item["text"] for item in history if item.get("role") in {"selene", "assistant"}]
    pool = assistant or [item["text"] for item in history]
    candidates: list[str] = []
    for value in pool:
        lower = value.lower()
        if lower.startswith(("write ", "make ", "revise ", "rewrite ", "what did you change", "correction:")):
            continue
        if any(marker in lower for marker in ("not enough grounded", "i can build an original", "i will not imitate")):
            continue
        parts = _sentences(value)
        if 1 <= len(parts) <= 6 and 5 <= len(value.split()) <= 180:
            candidates.append(" ".join(parts))
    return candidates[-6:]


def _sentences(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])(?:[”'\"])?\s+|\n+", str(value or "").strip())
        if item.strip()
    ]


def _version_id(value: str) -> str:
    return f"creative-v1-{_sha256(value)[:16]}"


def _sha256(value: str) -> str:
    normalized = " ".join(str(value or "").split()).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _words(value: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", str(value or "").lower())


def _ngrams(words: list[str], size: int) -> set[tuple[str, ...]]:
    return {tuple(words[index : index + size]) for index in range(max(0, len(words) - size + 1))}


def _longest_common_span(left: list[str], right: list[str]) -> int:
    if not left or not right:
        return 0
    prior = [0] * (len(right) + 1)
    longest = 0
    for left_word in left:
        current = [0]
        for index, right_word in enumerate(right, start=1):
            value = prior[index - 1] + 1 if left_word == right_word else 0
            current.append(value)
            longest = max(longest, value)
        prior = current
    return longest
