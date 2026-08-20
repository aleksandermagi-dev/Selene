from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .social_language_realizer import realize_acknowledgement


REPAIR_BOUNDARY = (
    "conversation_turn_flow_and_surface_repair_only_preserve_supported_meaning_no_memory_identity_authority_or_hidden_reasoning"
)

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

ARCHITECTURE_LEAKS = (
    "approved rows",
    "runtime recall",
    "source-bound",
    "selected route",
    "response obligation",
    "repair path",
    "evidence chain",
    "current full request",
    "reflection memory source:",
    "answer_now",
    "return_to_b",
    "create_review_packet",
    "rehearse_speech",
)


def plan_conversation_turn(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    pragmatic = payload.get("pragmatic_plan") if isinstance(payload.get("pragmatic_plan"), dict) else {}
    primary = str(intent.get("intent") or "direct_conversation")
    acts = _ordered_acts(prompt, primary, pragmatic)
    moves = _response_moves(acts, pragmatic)
    acknowledgement = _acknowledgement_kind(acts)
    return _with_guards(
        {
            "status": "conversation_turn_flow_ready",
            "version": "v2_structured_mixed_intent_turn_flow",
            "primary_intent": primary,
            "ordered_acts": acts,
            "secondary_intents": [item["act"] for item in acts if item["act"] != primary],
            "mixed_intent": len({item["act"] for item in acts}) > 1,
            "response_moves": moves,
            "obligation_sequence": [str(item.get("id") or "") for item in pragmatic.get("response_obligations") or [] if isinstance(item, dict)],
            "correction_refinement": pragmatic.get("correction_refinement") or {},
            "resolved_reference": pragmatic.get("resolved_reference"),
            "acknowledgement_kind": acknowledgement,
            "must_answer_visible_question": any(item["act"] in {"question", "reasoning_request", "direct_request"} for item in acts),
            "must_preserve_correction": any(item["act"] == "correction" for item in acts),
            "must_preserve_uncertainty": any(item["act"] == "uncertainty" for item in acts),
            "repair_scope": "surface_and_turn_flow_only",
            "meaning_may_not_be_replaced": True,
            "session_scoped_only": True,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": REPAIR_BOUNDARY,
        }
    )


def repair_conversation_candidate(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    original = _bounded_surface(str(payload.get("candidate_text") or payload.get("text") or ""), 5000)
    plan = payload.get("turn_flow_plan") if isinstance(payload.get("turn_flow_plan"), dict) else {}
    coverage = payload.get("response_coverage") if isinstance(payload.get("response_coverage"), dict) else {}
    response_agency = (
        payload.get("response_agency")
        if isinstance(payload.get("response_agency"), dict)
        else {}
    )
    recent = [str(item).strip() for item in payload.get("recent_candidates") or [] if str(item).strip()][:6]
    hard_boundary = payload.get("hard_boundary") is True or str(plan.get("primary_intent") or "") == "hard_boundary"
    repaired = _normalize(original)
    repairs: list[str] = []
    issues: list[str] = []
    attention_notes: list[str] = []

    deduped = _dedupe_adjacent_sentences(repaired)
    if deduped != repaired:
        repaired = deduped
        repairs.append("adjacent_duplicate_sentence_removed")
    paragraph_deduped = _dedupe_near_duplicate_paragraphs(repaired)
    if paragraph_deduped != repaired:
        repaired = paragraph_deduped
        repairs.append("near_duplicate_paragraph_removed")
    punctuated = _finish_punctuation(repaired)
    if punctuated != repaired:
        repaired = punctuated
        repairs.append("final_punctuation_completed")

    acknowledgement = str(plan.get("acknowledgement_kind") or "")
    if plan.get("mixed_intent") is True and acknowledgement and not hard_boundary and not _has_acknowledgement(repaired, acknowledgement):
        acknowledgement_result = realize_acknowledgement(
            acknowledgement,
            variation_key=original,
            recent_texts=recent,
        )
        prefix = str(acknowledgement_result.get("candidate_text") or "")
        if prefix:
            separator = "\n\n" if acknowledgement == "correction" else " "
            repaired = f"{prefix}{separator}{repaired}".strip()
            repairs.append(f"{acknowledgement}_acknowledgement_added")

    if not repaired:
        issues.append("empty_candidate")
    # ``unresolved_count`` also includes lexical conversation-spine alignment.
    # That is not, by itself, evidence that a visible question remains open.
    # Only a turn that actually carried a question/request obligation may use
    # the question-specific repair signal.
    if (
        plan.get("must_answer_visible_question") is True
        and int(coverage.get("unresolved_count") or 0) > 0
    ):
        attention_notes.append("visible_question_still_open")
    if _matches_recent(repaired, recent):
        issues.append("recent_response_repetition")
    if any(term in repaired.lower() for term in ARCHITECTURE_LEAKS):
        issues.append("architecture_language_visible")
    if plan.get("must_preserve_correction") is True and not _has_acknowledgement(repaired, "correction"):
        issues.append("correction_not_acknowledged")
    if plan.get("must_preserve_uncertainty") is True and not _has_uncertainty(repaired):
        issues.append("uncertainty_not_visible")

    agency_choice = (
        response_agency.get("response_choice")
        if isinstance(response_agency.get("response_choice"), dict)
        else {}
    )
    agency_choice_state = str(agency_choice.get("state") or "not_available")
    if agency_choice_state == "option_expansion_required_before_choice":
        attention_notes.append("response_agency_choice_still_pending")
    if response_agency and (
        response_agency.get("emotion_action_authority") is not False
        or agency_choice.get("emotion_silently_inherited_authority") is not False
    ):
        issues.append("emotion_authority_boundary_not_confirmed")

    needs_content_revision = any(
        note in attention_notes
        for note in (
            "visible_question_still_open",
            "response_agency_choice_still_pending",
        )
    )
    return _with_guards(
        {
            "status": (
                "conversation_candidate_needs_content_revision"
                if needs_content_revision
                else "conversation_candidate_repaired"
                if repairs
                else "conversation_candidate_checked"
            ),
            "original_candidate": original,
            "candidate_text": repaired,
            "repairs_applied": repairs,
            "issues": sorted(set(issues)),
            "attention_notes": sorted(set(attention_notes)),
            "passed": not issues,
            "needs_rephrase": any(issue in issues for issue in ("empty_candidate", "recent_response_repetition", "architecture_language_visible")),
            "needs_content_revision": needs_content_revision,
            "open_question_preserved": "visible_question_still_open" in attention_notes,
            "response_agency": {
                "observed": bool(response_agency),
                "choice_state": agency_choice_state,
                "emotion_action_authority": False,
                "meaning_rewrite_allowed": False,
                "surface_repair_cannot_choose_for_core_mind": True,
            },
            "meaning_preserved": True,
            "repair_scope": "surface_and_turn_flow_only",
            "automatic_content_generation": False,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": REPAIR_BOUNDARY,
        }
    )


def _ordered_acts(prompt: str, primary: str, pragmatic: dict[str, Any]) -> list[dict[str, Any]]:
    lower = prompt.lower().replace("’", "'")
    topic_shift = any(
        marker in lower
        for marker in ("separate question", "different question", "new question", "separate topic", "different topic", "on another topic")
    )
    found: list[tuple[int, str, str]] = []
    structured_kind_map = {
        "question": "question",
        "correction": "correction",
        "direct_request": "direct_request",
        "indirect_request": "direct_request",
        "session_preference": "session_preference",
    }
    for unit in pragmatic.get("utterance_units") or []:
        if not isinstance(unit, dict):
            continue
        kind = structured_kind_map.get(str(unit.get("kind") or ""))
        if kind:
            found.append((int(unit.get("position") or 0), kind, f"utterance:{unit.get('id') or kind}"))
    correction = pragmatic.get("correction_refinement") if isinstance(pragmatic.get("correction_refinement"), dict) else {}
    if correction.get("detected") is True:
        found.append((0, "correction", "structured_correction"))
    cue_groups = (
        ("gratitude", ("thank you", "thanks", "appreciate")),
        ("correction", (("i meant", "not what i meant", "wait,") if topic_shift else ("actually", "i meant", "not what i meant", "wait,"))),
        ("uncertainty", ("not sure", "unsure", "maybe", "i think", "fuzzy")),
        ("partial_agreement", ("okay, but", "okay but", "yes, but", "yes but", "right, but", "right but", "i agree, but", "i agree but")),
        ("warm_connection", ("glad you're", "glad you are", "missed you", "love you", "friend")),
        ("playful_connection", ("haha", "lol", "xd", ";}", ">:)")),
        ("reasoning_request", ("why", "how should", "how can", "compare", "explain", "what do you think")),
        ("direct_request", ("could you", "would you", "can you", "please")),
    )
    for act, cues in cue_groups:
        positions = [(lower.find(cue), cue) for cue in cues if cue in lower]
        if positions:
            position, cue = min(positions, key=lambda item: item[0])
            found.append((position, act, cue))
    if "?" in prompt:
        found.append((prompt.find("?"), "question", "?"))
    if not found or primary not in {item[1] for item in found}:
        found.append((-1, primary, "primary_intent"))
    ordered: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, act, cue in sorted(found, key=lambda item: (item[0], item[1])):
        if act in seen:
            continue
        ordered.append(
            {
                "act": act,
                "cue": cue,
                "position": max(0, position),
                "source": "structured_pragmatic_unit" if cue.startswith(("utterance:", "structured_")) else "current_turn_cue",
            }
        )
        seen.add(act)
    return ordered


def _response_moves(acts: list[dict[str, Any]], pragmatic: dict[str, Any]) -> list[str]:
    moves: list[str] = []
    names = [str(item.get("act") or "") for item in acts]
    if "correction" in names:
        moves.append("acknowledge_changed_meaning")
    if any(item in names for item in ("gratitude", "warm_connection", "playful_connection")):
        moves.append("meet_relational_tone_briefly")
    if "partial_agreement" in names:
        moves.append("preserve_agreement_and_answer_qualification")
    if any(item in names for item in ("question", "reasoning_request", "direct_request")):
        moves.append("answer_actual_ask")
    if "uncertainty" in names:
        moves.append("keep_uncertainty_visible")
    if pragmatic.get("response_obligations"):
        moves.append("address_each_supported_obligation")
    moves.append("leave_unsupported_parts_open")
    return list(dict.fromkeys(moves))


def _acknowledgement_kind(acts: list[dict[str, Any]]) -> str:
    names = [str(item.get("act") or "") for item in acts]
    for item in ("correction", "partial_agreement", "gratitude", "warm_connection"):
        if item in names:
            return item
    return ""


def _has_acknowledgement(value: str, kind: str) -> bool:
    lower = value.lower()
    markers = {
        "correction": (
            "correction", "you're right", "you are right", "i see",
            "i have the changed", "got it", "that changes",
        ),
        "gratitude": ("you're welcome", "you are welcome", "of course", "glad", "thank you"),
        "warm_connection": ("i'm with you", "i am with you", "glad", "here with you"),
        "partial_agreement": ("qualification matters", "i have the distinction", "yes—but", "yes, but"),
    }.get(kind, ())
    return any(marker in lower for marker in markers)


def _has_uncertainty(value: str) -> bool:
    lower = value.lower()
    return any(item in lower for item in ("i think", "maybe", "not sure", "not certain", "uncertain", "fuzzy", "current answer", "could"))


def _normalize(value: str) -> str:
    paragraphs = []
    for paragraph in re.split(r"\n+", value.replace("\r\n", "\n").strip()):
        text = " ".join(paragraph.split())
        if text:
            text = re.sub(
                r"(^|[.!?;:]\s+)i\b",
                lambda match: f"{match.group(1)}I",
                text,
            )
            paragraphs.append(text)
    return re.sub(r"([.!?])\s+([\"'])", r"\1\2", "\n\n".join(paragraphs))


def _bounded_surface(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _dedupe_adjacent_sentences(value: str) -> str:
    paragraphs: list[str] = []
    for paragraph in value.split("\n\n"):
        sentences = [item.strip() for item in re.findall(r"[^.!?]+[.!?]?", paragraph) if item.strip()]
        kept: list[str] = []
        prior = ""
        for sentence in sentences:
            normalized = " ".join(re.findall(r"[a-z0-9']+", sentence.lower()))
            if normalized and normalized == prior:
                continue
            kept.append(sentence)
            prior = normalized
        paragraphs.append(" ".join(kept))
    text = "\n\n".join(item for item in paragraphs if item)
    return re.sub(r"([.!?])\s+([\"'])", r"\1\2", text)


def _dedupe_near_duplicate_paragraphs(value: str) -> str:
    """Remove repeated paraphrases without merging distinct sourced claims."""

    kept: list[str] = []
    term_sets: list[set[str]] = []
    for paragraph in [item.strip() for item in value.split("\n\n") if item.strip()]:
        terms = set(re.findall(r"[a-z0-9']+", paragraph.lower()))
        duplicate = False
        if len(terms) >= 10 and "[" not in paragraph and "http" not in paragraph.lower():
            for prior in term_sets:
                if len(prior) < 10:
                    continue
                containment = len(terms & prior) / min(len(terms), len(prior))
                if containment >= 0.85:
                    duplicate = True
                    break
        if duplicate:
            continue
        kept.append(paragraph)
        term_sets.append(terms)
    return "\n\n".join(kept)


def _finish_punctuation(value: str) -> str:
    if not value or value.endswith((".", "!", "?", "…")):
        return value
    return value + "." if value[-1].isalnum() or value[-1] in ("'", '"', ")") else value


def _matches_recent(candidate: str, recent: list[str]) -> bool:
    words = re.findall(r"[a-z0-9']+", candidate.lower())
    if not words:
        return False
    normalized = " ".join(words)
    for item in recent:
        recent_words = re.findall(r"[a-z0-9']+", item.lower())
        if normalized == " ".join(recent_words):
            return True
        shared = min(10, len(words), len(recent_words))
        if shared >= 7 and words[:shared] == recent_words[:shared]:
            return True
    return False


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
