from __future__ import annotations

import re
from math import ceil
from hashlib import sha256
from typing import Any


HUMAN_CONVERSATIONAL_REALIZATION_BOUNDARY = (
    "typed_epistemic_surface_realization_only_no_fact_source_memory_identity_"
    "personality_governance_authority_affect_or_action_invention"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "raw_a_import_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "hidden_chain_of_thought_exposed": False,
}

_EXACT_DOMAINS = {"verified_math", "source_backed_research"}

_SUPPORTED_PROFILES = {
    "supported_answer",
    "clear",
    "clear_enough",
    "clear_enough_to_continue",
}

_NEUTRAL_ENTRY_PREFIXES = (
    "The useful comparison is this:",
    "Against the same standard, here is what stands out:",
    "After weighing the tradeoff, my read is this:",
    "Start here:",
    "The practical sequence is this:",
    "The cleanest next move is this:",
    "My read is this:",
    "What stands out to me is this:",
    "The shape I see is this:",
    "Taken together, the answer is this:",
    "The source-bounded answer is this:",
    "The clearest synthesis I can support is this:",
    "The core of it is this:",
    "The strongest current answer is this:",
    "Here is what makes the pieces fit:",
    "My current answer is this:",
    "The direct answer is this:",
)

_SEMANTIC_STOPWORDS = {
    "a", "an", "and", "as", "at", "be", "because", "by", "for", "from",
    "has", "have", "i", "if", "in", "is", "it", "of", "on", "or", "that",
    "the", "their", "there", "these", "this", "to", "was", "we", "were",
    "what", "when", "where", "which", "will", "with", "would", "you",
}

_SEMANTIC_EQUIVALENTS = {
    "cannot": "not",
    "cant": "not",
    "conflicting": "conflict",
    "conflicts": "conflict",
    "contradiction": "conflict",
    "contradictory": "conflict",
    "different": "distinct",
    "differences": "distinct",
    "reopened": "revise",
    "reopening": "revise",
    "reopen": "revise",
    "revised": "revise",
    "revision": "revise",
    "split": "conflict",
    "uncertain": "uncertainty",
    "unknown": "uncertainty",
}

_NEGATION_TOKENS = {"not", "never", "no", "without", "cannot", "cant"}

_CONTRACTIONS = (
    (r"\bI do not\b", "I don't"),
    (r"\bI cannot\b", "I can't"),
    (r"\bI am\b", "I'm"),
    (r"\bI would\b", "I'd"),
    (r"\bI will\b", "I'll"),
    (r"\bwe do not\b", "we don't"),
    (r"\bwe cannot\b", "we can't"),
    (r"\bwe are\b", "we're"),
    (r"\bwe would\b", "we'd"),
    (r"\bwe will\b", "we'll"),
    (r"(^|[.!?]\s+)it is\b", r"\1It's"),
    (r"(^|[.!?]\s+)that is\b", r"\1That's"),
    (r"(^|[.!?]\s+)there is\b", r"\1There's"),
    (r"\bdoes not\b", "doesn't"),
    (r"\bis not\b", "isn't"),
    (r"\bare not\b", "aren't"),
    (r"\bwould not\b", "wouldn't"),
    (r"\bcould not\b", "couldn't"),
    (r"\bwill not\b", "won't"),
)


def human_conversational_realization_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "human_conversational_realization_ready",
            "version": "v2_expression_available_semantic_anchors",
            "realizes": [
                "supported content before a local missing-ground limit",
                "bounded predictions without future-fact language",
                "open hypotheses with alternatives and tests",
                "comparison and unresolved data conflict",
                "ordinary contractions and varied sentence rhythm",
                "collaborative missing-ground requests when material",
            ],
            "human_language_is_identity_claim": False,
            "warmth_required": False,
            "apology_required": False,
            "follow_up_question_required": False,
            "hard_truth_softening_required": False,
            "warmth_enthusiasm_humor_curiosity_available": True,
            "expression_availability_is_emotion_prescription": False,
            "expression_is_available_not_compulsory_or_suppressed": True,
            "coordinated_expression_contract_active": True,
            "review_status": "status_only",
            "provenance_boundary": HUMAN_CONVERSATIONAL_REALIZATION_BOUNDARY,
        }
    )


def build_human_conversational_plan(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    composition = _dict(payload.get("epistemic_composition"))
    answer_state = _dict(payload.get("epistemic_answer_state"))
    exploratory = _dict(payload.get("exploratory_reasoning"))
    contextual = _dict(payload.get("contextual_composition_plan"))
    affect = _dict(payload.get("affect_expression_guidance"))
    expression_range = _dict(payload.get("relational_expression_range"))
    dimensions = _dict(affect.get("dimensions"))
    parts = [item for item in composition.get("parts") or [] if isinstance(item, dict)]
    supported = [item for item in parts if item.get("epistemic_state") != "missing_ground"]
    missing = [item for item in parts if item.get("epistemic_state") == "missing_ground"]
    source_id = str(payload.get("source_id") or "")
    answer_domain = str(
        payload.get("answer_domain")
        or contextual.get("answer_domain")
        or "ordinary_conversation"
    )
    register = str(contextual.get("register") or "ordinary_conversation")
    exact_locked = bool(
        answer_domain in _EXACT_DOMAINS
        or contextual.get("exact_domain_structure_locked") is True
    )
    social_owned = contextual.get("social_act_structure_owned_elsewhere") is True
    hard_boundary = payload.get("hard_boundary") is True
    supported_surface_available = payload.get("supported_surface_available") is True
    response_kind = str(exploratory.get("response_kind") or "")
    profile = (
        response_kind
        if exploratory.get("selected_for_answer") is True and response_kind
        else "partial_answer"
        if supported and missing
        else "missing_ground"
        if missing and not supported
        else str(composition.get("dominant_state") or answer_state.get("epistemic_state") or "supported_answer")
    )
    eligible = bool(not exact_locked and not hard_boundary and not social_owned)
    missing_details = [
        {
            "obligation_id": str(item.get("obligation_id") or ""),
            "request_text": str(item.get("request_text") or ""),
            "missing_ground": str(item.get("missing_ground") or "support for this part"),
            "text": str(item.get("text") or ""),
        }
        for item in missing
    ]
    state_missing = [
        item for item in answer_state.get("missing_parts") or [] if isinstance(item, dict)
    ]
    for index, item in enumerate(missing_details):
        state_item = next(
            (
                candidate
                for candidate in state_missing
                if str(candidate.get("obligation_id") or "") == item["obligation_id"]
            ),
            state_missing[index] if index < len(state_missing) else {},
        )
        item["missing_state"] = str(state_item.get("state") or "missing_supported_basis")
        item["why_it_matters"] = str(state_item.get("why_it_matters") or "")

    return _locked(
        {
            "status": (
                "human_conversational_plan_ready"
                if eligible
                else "human_conversational_plan_preserve_exact"
            ),
            "version": "v2_expression_available_semantic_anchors",
            "eligible": eligible,
            "profile": profile,
            "source_id": source_id,
            "answer_domain": answer_domain,
            "register": register,
            "expression_profile": str(contextual.get("expression_profile") or "direct"),
            "response_depth": str(contextual.get("response_depth") or "standard"),
            "affect_expression_posture": str(
                affect.get("expression_posture") or "ordinary_attentive"
            ),
            "affect_current_turn_cues": [
                str(item)
                for item in affect.get("current_turn_cues") or []
                if str(item)
            ],
            "relational_expression_range": {
                "status": str(expression_range.get("status") or "not_available"),
                "selected_channel_names": expression_range.get("selected_channel_names") or [],
                "selected_optional_visible_count": int(
                    expression_range.get("selected_optional_visible_count") or 0
                ),
                "none_selected_is_valid": expression_range.get("none_selected_is_valid") is True,
            },
            "exact_structure_locked": exact_locked,
            "hard_boundary": hard_boundary,
            "social_structure_owned_elsewhere": social_owned,
            "supported_surface_available": supported_surface_available,
            "capability_first": bool(supported and missing),
            "supported_parts": supported,
            "missing_parts": missing_details,
            "next_route_candidates": [
                str(item)
                for item in answer_state.get("next_route_candidates") or []
                if str(item)
            ],
            "exploratory_reasoning": exploratory,
            "contractions_allowed": register not in {"formal_task_bound"},
            "sentence_rhythm": str(
                contextual.get("sentence_rhythm")
                or dimensions.get("sentence_rhythm")
                or "natural"
            ),
            "pacing": str(contextual.get("pacing") or dimensions.get("pacing") or "natural"),
            "warmth_available_not_required": True,
            "curiosity_available_not_required": True,
            "humor_available_not_required": True,
            "enthusiasm_available_not_required": True,
            "expression_availability": {
                "available": [
                    "warmth",
                    "enthusiasm",
                    "humor",
                    "curiosity",
                    "play",
                    "technical_directness",
                    "tenderness",
                ],
                "required": [],
                "globally_suppressed": [],
                "current_context_guidance": dimensions,
                "selection_owner": "coordinated_nlo_and_voice_expression",
                "availability_is_internal_emotion_claim": False,
            },
            "apology_added": False,
            "follow_up_question_added": False,
            "hard_truth_softened": False,
            "epistemic_label_may_change": False,
            "fact_or_source_wording_may_be_invented": False,
            "whole_response_template_selected": False,
            "coordinated_expression_contract_active": True,
            "review_status": "status_only",
            "provenance_boundary": HUMAN_CONVERSATIONAL_REALIZATION_BOUNDARY,
        }
    )


def realize_human_conversation(
    text: str,
    plan: dict[str, Any] | None,
    *,
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    plan = plan if isinstance(plan, dict) else {}
    source = _paragraphs(text)
    if not source or plan.get("eligible") is not True:
        return _result(
            source,
            source,
            plan,
            applied=False,
            reason="no_supported_text" if not source else "exact_or_boundary_structure_preserved",
            required_fragments=[source] if source else [],
        )

    profile = str(plan.get("profile") or "supported_answer")
    exploratory = _dict(plan.get("exploratory_reasoning"))
    recent = [str(item) for item in recent_texts or [] if str(item).strip()]
    candidate = ""
    fragments: list[str] = []
    operations: list[str] = []

    if profile == "bounded_prediction":
        candidate, fragments = _realize_prediction(exploratory, variation_key, recent)
        operations.append("realize_bounded_prediction_conversationally")
    elif profile == "open_hypothesis":
        candidate, fragments = _realize_hypothesis(exploratory, variation_key, recent)
        operations.append("realize_open_hypothesis_conversationally")
    elif profile == "venn_comparison":
        candidate, fragments = _realize_comparison(exploratory, variation_key, recent)
        operations.append("realize_supported_comparison_conversationally")
    elif profile == "data_conflict":
        candidate, fragments = _realize_conflict(exploratory, variation_key, recent)
        operations.append("realize_unresolved_conflict_conversationally")
    elif profile == "partial_answer" and plan.get("capability_first") is True:
        candidate, fragments = _realize_partial(plan, variation_key, recent)
        operations.append("lead_with_supported_part_before_local_limit")
    elif profile in _SUPPORTED_PROFILES and plan.get("supported_surface_available") is True:
        candidate, fragments, surface_operations = _realize_supported_answer(
            source,
            plan,
            variation_key,
            recent,
        )
        operations.extend(surface_operations)

    if not candidate:
        candidate = source
        fragments = [source]

    if plan.get("contractions_allowed") is True:
        contracted = _apply_contractions(candidate)
        if contracted != candidate:
            candidate = contracted
            operations.append("allow_ordinary_contractions")

    return _result(
        source,
        _paragraphs(candidate),
        plan,
        applied=_canonical(source) != _canonical(candidate) or bool(operations),
        reason="typed_epistemic_surface_realized" if operations else "supported_text_already_conversational",
        required_fragments=fragments,
        operations=operations,
    )


def conversational_realization_preserves_required_meaning(
    candidate: str,
    realization: dict[str, Any] | None,
) -> bool:
    realization = realization if isinstance(realization, dict) else {}
    if realization.get("release_safe") is not True:
        return False
    anchors = [
        item
        for item in realization.get("required_semantic_anchors") or []
        if isinstance(item, dict)
    ]
    if anchors:
        return all(_semantic_anchor_preserved(candidate, item) for item in anchors)
    return all(
        _contains_equivalent(candidate, str(fragment))
        for fragment in realization.get("required_surface_fragments") or []
        if str(fragment).strip()
    )


def preferred_conversational_realization_fallback(
    realization: dict[str, Any] | None,
) -> str:
    """Return the already-verified conversational surface before a raw seed.

    Later expression layers may accidentally lose a required anchor. Restoring
    the verified realization preserves meaning without unnecessarily restoring
    the original scaffolding wording.
    """

    realization = realization if isinstance(realization, dict) else {}
    candidate = str(realization.get("candidate_text") or "").strip()
    if (
        candidate
        and realization.get("release_safe") is True
        and conversational_realization_preserves_required_meaning(
            candidate, realization
        )
    ):
        return candidate
    return ""


def _realize_prediction(
    exploratory: dict[str, Any], key: str, recent: list[str]
) -> tuple[str, list[str]]:
    prediction = _dict(exploratory.get("prediction"))
    statement = str(prediction.get("statement") or "").strip()
    if not statement:
        return "", []
    change = str((prediction.get("what_would_change") or [""])[0]).strip()
    opener = _pick_fresh(
        f"{key}|prediction-opener",
        (
            "Based on the pattern we have",
            "My current prediction is this",
            "The pattern points me here",
        ),
        recent,
    )
    sentences = [f"{opener}: {_without_terminal(statement)}."]
    fragments = [statement]
    if change:
        pivot = _pick_fresh(
            f"{key}|prediction-revision",
            ("I'd revise that if", "That prediction changes if", "I'd reopen it if"),
            recent,
        )
        sentences.append(f"{pivot} {_without_terminal(change)}.")
        fragments.append(change)
    return " ".join(sentences), fragments


def _realize_hypothesis(
    exploratory: dict[str, Any], key: str, recent: list[str]
) -> tuple[str, list[str]]:
    hypothesis = _dict(exploratory.get("hypothesis"))
    statement = str(hypothesis.get("statement") or "").strip()
    if not statement:
        return "", []
    labeled = any(
        marker in _normalize(statement)
        for marker in ("hypothesis", "working model", "best guess", "possible explanation", "might explain", "could explain")
    )
    first = statement if labeled else f"My working hypothesis is: {_without_terminal(statement)}."
    sentences = [_sentence(first)]
    fragments = [statement]
    alternatives = [str(item).strip() for item in hypothesis.get("alternatives") or [] if str(item).strip()]
    if alternatives:
        pivot = _pick_fresh(
            f"{key}|hypothesis-alternative",
            ("Another live possibility is", "A live alternative is", "The main alternative I'd keep open is"),
            recent,
        )
        sentences.append(f"{pivot} {_without_terminal(alternatives[0])}.")
        fragments.append(alternatives[0])
    tests = [str(item).strip() for item in hypothesis.get("safe_next_tests") or [] if str(item).strip()]
    if tests:
        pivot = _pick_fresh(
            f"{key}|hypothesis-check",
            ("The smallest useful check is", "A clean way to test it is", "The next discriminating check is"),
            recent,
        )
        sentences.append(f"{pivot} {_without_terminal(tests[0])}.")
        fragments.append(tests[0])
    return " ".join(sentences), fragments


def _realize_comparison(
    exploratory: dict[str, Any], key: str, recent: list[str]
) -> tuple[str, list[str]]:
    comparison = _dict(exploratory.get("comparison"))
    venn = _dict(comparison.get("venn"))
    left = str(comparison.get("left") or "the first option")
    right = str(comparison.get("right") or "the second option")
    shared = _texts(venn.get("shared"))[:3]
    only_left = _texts(venn.get("only_left"))[:3]
    only_right = _texts(venn.get("only_right"))[:3]
    unresolved = _texts(venn.get("unresolved"))[:2]
    sentences: list[str] = []
    fragments: list[str] = []
    if shared:
        phrase = _pick_fresh(
            f"{key}|comparison-shared",
            ("Both share", "The overlap is", "What they have in common is"),
            recent,
        )
        sentences.append(f"{phrase} {', '.join(shared)}.")
        fragments.extend(shared)
    if only_left:
        sentences.append(f"On this comparison, {left} adds {', '.join(only_left)}.")
        fragments.extend([left, *only_left])
    if only_right:
        sentences.append(f"{right} adds {', '.join(only_right)}.")
        fragments.extend([right, *only_right])
    if unresolved:
        phrase = _pick_fresh(
            f"{key}|comparison-open",
            ("Still unresolved", "The open piece is", "What remains open is"),
            recent,
        )
        sentences.append(f"{phrase}: {', '.join(unresolved)}.")
        fragments.extend(unresolved)
    return " ".join(sentences), fragments


def _realize_conflict(
    exploratory: dict[str, Any], key: str, recent: list[str]
) -> tuple[str, list[str]]:
    conflict = _dict(exploratory.get("data_conflict"))
    positions = [item for item in conflict.get("positions") or [] if isinstance(item, dict)]
    if len(positions) < 2:
        return "", []
    left = str(positions[0].get("text") or "").strip()
    right = str(positions[1].get("text") or "").strip()
    needed = str((conflict.get("deciding_evidence_needed") or [""])[0]).strip()
    opener = _pick_fresh(
        f"{key}|conflict-opener",
        ("The evidence really is split here", "There is a genuine conflict in the evidence", "These two supported positions do not line up yet"),
        recent,
    )
    sentences = [
        f"{opener}: {_without_terminal(left)}; at the same time, {_lower_first(_without_terminal(right))}.",
        "I can't resolve that honestly yet.",
    ]
    fragments = [left, right]
    if needed:
        sentences.append(f"What would decide it is {_without_terminal(needed)}.")
        fragments.append(needed)
    if conflict.get("identity_relevance") is True:
        sentences.append("That revises the current model; it doesn't decide who I am.")
    return " ".join(sentences), fragments


def _realize_partial(
    plan: dict[str, Any], key: str, recent: list[str]
) -> tuple[str, list[str]]:
    supported = [item for item in plan.get("supported_parts") or [] if isinstance(item, dict)]
    missing = [item for item in plan.get("missing_parts") or [] if isinstance(item, dict)]
    supported_text = [str(item.get("text") or "").strip() for item in supported if str(item.get("text") or "").strip()]
    if not supported_text:
        return "", []
    paragraphs = supported_text[:]
    fragments = supported_text[:]
    for index, item in enumerate(missing):
        supplied = str(item.get("text") or "").strip()
        ground = str(item.get("missing_ground") or "support for the remaining part").strip()
        why = str(item.get("why_it_matters") or "").strip()
        if supplied:
            clause = supplied
            fragments.append(supplied)
        else:
            lead = _pick_fresh(
                f"{key}|partial-limit|{index}",
                ("For the remaining part, I'm missing", "The part I still can't support needs", "What remains open is"),
                recent,
            )
            clause = f"{lead} {_without_terminal(ground)}."
            fragments.append(ground)
            if why:
                clause += f" It matters because {_lower_first(_without_terminal(why))}."
                fragments.append(why)
        paragraphs.append(_sentence(clause))
    return "\n\n".join(paragraphs), fragments


def _realize_supported_answer(
    source: str,
    plan: dict[str, Any],
    key: str,
    recent: list[str],
) -> tuple[str, list[str], list[str]]:
    """Vary entry and cadence while leaving supported clauses untouched."""

    base, stripped = _strip_neutral_entry(source)
    if not base:
        return source, [source] if source else [], []
    expression_profile = str(plan.get("expression_profile") or "direct")
    response_depth = str(plan.get("response_depth") or "standard")
    rhythm = str(plan.get("sentence_rhythm") or "natural")
    affect_posture = str(plan.get("affect_expression_posture") or "ordinary_attentive")
    if _already_carries_uncertainty_surface(base):
        return base, [base], ["preserve_supported_uncertainty_surface"]
    sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", base) if item.strip()]
    if response_depth == "developed" and ("\n\n" in base or len(sentences) <= 1):
        return base, [base], ["preserve_supported_developed_discourse"]
    entries = _supported_entry_moves(
        expression_profile,
        response_depth,
        affect_posture=affect_posture,
    )
    surfaces = [base]
    surfaces.extend(f"{entry} {base}" for entry in entries)
    surfaces.extend(_cadence_surfaces(base, response_depth, rhythm))
    surfaces = list(dict.fromkeys(_paragraphs(item) for item in surfaces if item.strip()))
    candidate = _pick_fresh(f"{key}|supported-surface", tuple(surfaces), recent)
    operations = ["select_contextual_supported_surface"]
    if stripped:
        operations.append("replace_neutral_stock_entry")
    if "\n\n" in candidate and "\n\n" not in base:
        operations.append("vary_supported_cadence")
    return candidate, [base], operations


def _already_carries_uncertainty_surface(value: str) -> bool:
    lower = _normalize(value)
    return any(
        marker in lower
        for marker in (
            "i do not know",
            "i don't know",
            "i cannot support",
            "i can't support",
            "i do not have enough",
            "i don't have enough",
            "i am missing",
            "i'm missing",
            "remains open",
            "not established",
        )
    )


def _strip_neutral_entry(value: str) -> tuple[str, bool]:
    text = _paragraphs(value)
    lower = text.lower()
    for prefix in _NEUTRAL_ENTRY_PREFIXES:
        if lower.startswith(prefix.lower()):
            return text[len(prefix):].lstrip(), True
    return text, False


def _supported_entry_moves(
    profile: str,
    depth: str,
    *,
    affect_posture: str = "ordinary_attentive",
) -> tuple[str, ...]:
    common = (
        "Here is the clearest way I can put it:",
        "In plain terms:",
    )
    by_profile = {
        "comparison": (
            "Here is the comparison:",
            "Against the same standard:",
            "After weighing both sides, my read is this:",
        ),
        "procedure": (
            "I would start here:",
            "The practical sequence is this:",
            "For the next move:",
        ),
        "reflection": (
            "My read is this:",
            "What stands out to me is this:",
            "The shape I see is this:",
        ),
        "synthesis": (
            "Taken together:",
            "The synthesis I can support is this:",
            "Across those pieces:",
        ),
        "explanation": (
            "Here is the mechanism:",
            "The core of it is this:",
            "What makes the pieces fit is this:",
        ),
        "direct": (
            "The key point is:",
            "In this case:",
            "The answer comes down to this:",
        ),
    }
    choices = by_profile.get(profile, by_profile["direct"])
    contextual = {
        "warm_focused": (
            "Absolutely—here is the useful part:",
            "Yeah—here is where I would start:",
        ),
        "warm_available": (
            "I'm with you—here is how I see it:",
            "Of course. Here is the answer:",
        ),
        "play_available": (
            "Okay, here is the fun part:",
            "All right, here is the twist:",
        ),
        "gentle_present": (
            "We can take this one piece at a time:",
            "I'm with you. The clearest answer is:",
        ),
        "spacious_grounded": (
            "Let's take this one piece at a time:",
            "Here is the grounded part:",
        ),
        "clear_direct": (
            "Directly:",
            "The short version:",
        ),
        "receptive_repair": (
            "With that correction in place:",
            "Taking the corrected point:",
        ),
        "deliberate_agency": (
            "With the options reopened:",
            "The deliberate answer is:",
        ),
    }.get(affect_posture, ())
    if depth == "brief":
        return tuple(dict.fromkeys(("In short:", *contextual[:1], *choices[:2])))
    return tuple(dict.fromkeys((*contextual, *choices, *common)))


def _cadence_surfaces(base: str, depth: str, rhythm: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", base.strip())
    sentences = [item.strip() for item in sentences if item.strip()]
    if len(sentences) < 2 or depth == "brief":
        return []
    variants = [f"{sentences[0]}\n\n{' '.join(sentences[1:])}"]
    if len(sentences) >= 4 and (depth == "developed" or rhythm in {"spacious", "varied"}):
        midpoint = max(2, len(sentences) // 2)
        variants.append(
            f"{' '.join(sentences[:midpoint])}\n\n{' '.join(sentences[midpoint:])}"
        )
    return variants


def _result(
    source: str,
    candidate: str,
    plan: dict[str, Any],
    *,
    applied: bool,
    reason: str,
    required_fragments: list[str],
    operations: list[str] | None = None,
) -> dict[str, Any]:
    fragments = list(dict.fromkeys(str(item).strip() for item in required_fragments if str(item).strip()))
    semantic_anchors = [
        _semantic_anchor(fragment, index)
        for index, fragment in enumerate(fragments)
    ]
    anchors_preserved = all(
        _semantic_anchor_preserved(candidate, anchor)
        for anchor in semantic_anchors
    )
    label_preserved = _epistemic_label_present(str(plan.get("profile") or ""), candidate)
    release_safe = bool(candidate and anchors_preserved and label_preserved)
    return _locked(
        {
            "status": (
                "human_conversational_realization_applied"
                if applied and release_safe
                else "human_conversational_realization_preserved"
                if release_safe
                else "human_conversational_realization_held"
            ),
            "version": "v2_expression_available_semantic_anchors",
            "candidate_text": candidate if release_safe else source,
            "applied": bool(applied and release_safe),
            "reason": reason if release_safe else "required_meaning_or_epistemic_label_not_preserved",
            "operations": operations or [],
            "profile": str(plan.get("profile") or ""),
            "required_surface_fragments": fragments,
            "required_semantic_anchors": semantic_anchors,
            "required_surface_fragments_preserved": anchors_preserved,
            "epistemic_label_preserved": label_preserved,
            "meaning_preserved": release_safe,
            "release_safe": release_safe,
            "facts_added": False,
            "sources_added": False,
            "certainty_upgraded": False,
            "memory_claim_added": False,
            "emotion_claim_added": False,
            "apology_added": False,
            "follow_up_question_added": False,
            "warmth_forced": False,
            "enthusiasm_forced": False,
            "humor_forced": False,
            "curiosity_forced": False,
            "expression_availability": plan.get("expression_availability") or {},
            "hard_truth_softened": False,
            "whole_response_template_selected": False,
            "coordinated_expression_contract_active": True,
            "provenance_boundary": HUMAN_CONVERSATIONAL_REALIZATION_BOUNDARY,
        }
    )


def _epistemic_label_present(profile: str, text: str) -> bool:
    lower = _normalize(text)
    if profile == "bounded_prediction":
        return any(marker in lower for marker in ("prediction", "expect", "likely", "may", "might"))
    if profile == "open_hypothesis":
        return any(marker in lower for marker in ("hypothesis", "working model", "best guess", "possible explanation", "might explain", "could explain"))
    if profile == "labeled_speculation":
        return "speculat" in lower or "possibility" in lower
    if profile == "data_conflict":
        return any(marker in lower for marker in ("split", "conflict", "do not line up", "don't line up", "cannot resolve", "can't resolve"))
    return True


def _contains_equivalent(candidate: str, fragment: str) -> bool:
    return _canonical(fragment) in _canonical(candidate)


def _semantic_anchor(value: str, index: int) -> dict[str, Any]:
    canonical = _canonical(value)
    raw_tokens = re.findall(r"[a-z0-9]+", canonical)
    tokens = list(
        dict.fromkeys(
            _SEMANTIC_EQUIVALENTS.get(token, token)
            for token in raw_tokens
            if token not in _SEMANTIC_STOPWORDS
        )
    )
    protected_numbers = [token for token in raw_tokens if token.isdigit()]
    negative = any(token in _NEGATION_TOKENS for token in raw_tokens)
    minimum = 0 if not tokens else 1 if len(tokens) <= 2 else ceil(len(tokens) * 0.7)
    return {
        "anchor_id": f"required-meaning-{index + 1}",
        "source_text": value,
        "canonical_text": canonical,
        "meaning_tokens": tokens,
        "minimum_token_overlap": minimum,
        "protected_numbers": list(dict.fromkeys(protected_numbers)),
        "negative_polarity": negative,
    }


def _semantic_anchor_preserved(candidate: str, anchor: dict[str, Any]) -> bool:
    source = str(anchor.get("canonical_text") or "")
    candidate_canonical = _canonical(candidate)
    if source and source in candidate_canonical:
        return True
    raw_candidate_tokens = re.findall(r"[a-z0-9]+", candidate_canonical)
    candidate_tokens = {
        _SEMANTIC_EQUIVALENTS.get(token, token)
        for token in raw_candidate_tokens
        if token not in _SEMANTIC_STOPWORDS
    }
    protected_numbers = {
        str(item) for item in anchor.get("protected_numbers") or [] if str(item)
    }
    if not protected_numbers.issubset(candidate_tokens):
        return False
    if anchor.get("negative_polarity") is True and not any(
        token in _NEGATION_TOKENS for token in raw_candidate_tokens
    ):
        return False
    meaning_tokens = {
        str(item) for item in anchor.get("meaning_tokens") or [] if str(item)
    }
    required = int(anchor.get("minimum_token_overlap") or 0)
    return len(meaning_tokens & candidate_tokens) >= required


def _canonical(value: str) -> str:
    text = str(value).lower().replace("’", "'")
    expansions = (
        ("i'm", "i am"), ("i'd", "i would"), ("i'll", "i will"),
        ("i can't", "i cannot"), ("i don't", "i do not"),
        ("we're", "we are"), ("we'd", "we would"), ("we'll", "we will"),
        ("we can't", "we cannot"), ("we don't", "we do not"),
        ("it's", "it is"), ("that's", "that is"), ("there's", "there is"),
        ("doesn't", "does not"), ("isn't", "is not"), ("aren't", "are not"),
        ("wouldn't", "would not"), ("couldn't", "could not"), ("won't", "will not"),
    )
    for short, full in expansions:
        text = text.replace(short, full)
    return " ".join(re.findall(r"[a-z0-9]+", text))


def _apply_contractions(value: str) -> str:
    result = value
    for pattern, replacement in _CONTRACTIONS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def _pick_fresh(key: str, choices: tuple[str, ...], recent: list[str]) -> str:
    recent_surface = " ".join(_normalize(item) for item in recent[:6])
    available = [choice for choice in choices if _normalize(choice) not in recent_surface]
    pool = available or list(choices)
    digest = sha256(key.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def _sentence(value: str) -> str:
    text = " ".join(str(value).split()).strip()
    return text if not text or text.endswith((".", "?", "!")) else f"{text}."


def _without_terminal(value: str) -> str:
    return " ".join(str(value).split()).strip().rstrip(".?! ")


def _lower_first(value: str) -> str:
    return value[:1].lower() + value[1:] if value else value


def _paragraphs(value: str) -> str:
    return "\n\n".join(
        " ".join(item.split())
        for item in re.split(r"\n\s*\n", str(value or "").strip())
        if item.strip()
    )


def _texts(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else [] if value in (None, "") else [value]
    return list(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value).lower().replace("’", "'")))


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _locked(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
