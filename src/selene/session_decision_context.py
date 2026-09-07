from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


SESSION_DECISION_BOUNDARY = (
    "visible_current_session_decision_reconstruction_only_no_durable_memory_"
    "identity_personality_governance_authority_training_or_action"
)

GUARDS: dict[str, Any] = {
    "writes_state": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "expression_authority": False,
}


def build_session_decision_context(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reconstruct one small decision from visible turns in the current chat.

    This is connective tissue between the Conversation Spine and existing answer
    owners. It does not decide external truth. It preserves the options,
    priorities, and reported outcomes that the speaker supplied so a comparison
    can be revised without turning each follow-up into an unrelated question.
    """

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400).strip()
    events = [item for item in payload.get("conversation_events") or [] if isinstance(item, dict)][-20:]
    user_turns = [
        truncate(str(item.get("preview") or ""), 1800).strip()
        for item in events
        if str(item.get("role") or "").lower() == "user"
        and str(item.get("preview") or "").strip()
    ]
    if prompt and (not user_turns or _normalize(user_turns[-1]) != _normalize(prompt)):
        user_turns.append(prompt)

    options: list[dict[str, Any]] = []
    subject = "option"
    for text in user_turns:
        extracted, extracted_subject = _extract_options(text)
        if len(extracted) >= 2:
            options = extracted
            subject = extracted_subject or subject

    priorities = _extract_priorities(user_turns)
    evidence_updates = _extract_evidence_updates(user_turns, options)
    constraint_updates = _extract_constraint_updates(user_turns)
    stated_preference = _extract_stated_preference(user_turns, options)
    mode = _request_mode(prompt)
    active_evidence_updates = [
        item for item in evidence_updates if item.get("hypothetical") is not True
    ]
    if mode == "revision" and _is_hypothetical_evidence(prompt):
        active_evidence_updates = evidence_updates
    recommendation = _choose_option(
        options,
        priorities=priorities,
        evidence_updates=active_evidence_updates,
        constraint_updates=constraint_updates,
    )
    response_seed, supported_operations, operation_fields = _response(
        prompt,
        mode=mode,
        options=options,
        subject=subject,
        priorities=priorities,
        evidence_updates=active_evidence_updates,
        constraint_updates=constraint_updates,
        stated_preference=stated_preference,
        recommendation=recommendation,
    )
    available = bool(len(options) >= 2 and response_seed)
    context_id = sha256(
        "|".join([str(payload.get("session_id") or 0), *user_turns]).encode("utf-8")
    ).hexdigest()[:16]
    return _with_guards(
        {
            "status": (
                "session_decision_response_ready"
                if available
                else "session_decision_context_available"
                if len(options) >= 2
                else "session_decision_context_not_material"
            ),
            "version": "v1_visible_option_priority_revision",
            "context_id": f"session-decision-{context_id}",
            "mode": mode,
            "options": options,
            "subject": subject,
            "priorities": priorities,
            "constraint_updates": constraint_updates,
            "evidence_updates": evidence_updates,
            "active_evidence_updates": active_evidence_updates,
            "stated_preference": stated_preference,
            "recommendation": recommendation,
            "response_seed": response_seed if available else "",
            "supported_operations": supported_operations if available else [],
            "operation_fields": operation_fields if available else {},
            "available": available,
            "current_session_only": True,
            "reported_premises_are_external_facts": False,
            "recommendation_is_revisable": True,
            "source_refs": ["conversation_spine:visible_session_decision"],
            "review_status": "status_only",
            "provenance_boundary": SESSION_DECISION_BOUNDARY,
        }
    )


def _extract_options(text: str) -> tuple[list[dict[str, Any]], str]:
    normalized = " ".join(str(text or "").replace("’", "'").split())
    container = re.search(
        r"\b(?:have|consider|compare|between)\s+(?:two|three|four|several|some|\d+)?\s*"
        r"(?P<subject>plans?|options?|choices?|approaches?|routes?|designs?|candidates?)\s*:\s*"
        r"(?P<body>[^.?!]{4,900})",
        normalized,
        flags=re.IGNORECASE,
    )
    if not container:
        return [], ""
    subject = _singular_subject(container.group("subject"))
    body = container.group("body")
    parts = re.split(
        r"\s*,\s*(?:and\s+)?(?=(?:one|a|an|the)\s+)|\s+and\s+(?=(?:one|a|an|the)\s+)",
        body,
        flags=re.IGNORECASE,
    )
    options: list[dict[str, Any]] = []
    for index, raw in enumerate(parts[:6]):
        value = re.sub(r"^(?:one|a|an|the)\s+", "", raw.strip(" ,;:"), flags=re.IGNORECASE)
        value = re.split(r"\b(?:compare|recommend|choose|which)\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
        value = value.strip(" ,;:.")
        if not value:
            continue
        properties = [
            item.strip(" ,;:.").lower()
            for item in re.split(r"\s+(?:but|and|yet|while)\s+", value, flags=re.IGNORECASE)
            if item.strip(" ,;:.")
        ][:4]
        label = f"{value.lower()} {subject}".strip()
        aliases = list(
            dict.fromkeys(
                [label, value.lower(), *[f"{item} {subject}" for item in properties], *properties]
            )
        )
        options.append(
            {
                "id": f"session-option-{index + 1}",
                "label": label,
                "descriptor": value.lower(),
                "properties": properties or [value.lower()],
                "aliases": aliases,
                "source": "visible_user_turn",
            }
        )
    return (options, subject) if len(options) >= 2 else ([], "")


def _extract_priorities(turns: list[str]) -> list[str]:
    result: list[str] = []
    patterns = (
        r"\b(?P<value>[a-z][a-z -]{1,80}?)\s+(?:still\s+)?matters?\s+(?:the\s+)?most\b",
        r"\b(?:top|main|highest)\s+priority\s+(?:is|remains)\s+(?P<value>[^.?!;]{2,100})",
        r"\bprioriti[sz]e\s+(?P<value>[^.?!;]{2,100})",
    )
    for text in turns:
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = re.sub(r"^(?:but|and|while)\s+", "", match.group("value").strip(" ,;:."), flags=re.IGNORECASE)
                if value and value.lower() not in {item.lower() for item in result}:
                    result.append(value.lower())
    return result[-4:]


def _extract_constraint_updates(turns: list[str]) -> list[str]:
    result: list[str] = []
    for text in turns:
        for clause in re.split(r"[.;?!]|\s*,\s*(?:but|and)\s+", text):
            clean = re.sub(
                r"^(?:actually|now|so)\s*,?\s+",
                "",
                clause.strip(" ,;:."),
                flags=re.IGNORECASE,
            )
            if re.search(
                r"\b(?:deadline|budget|time|capacity|staffing|risk|cost|requirement|constraint)\b"
                r".{0,80}\b(?:moved|changed|increased|decreased|closer|shorter|longer|tighter|looser)\b",
                clean,
                flags=re.IGNORECASE,
            ):
                result.append(clean)
    return list(dict.fromkeys(result))[-6:]


def _extract_evidence_updates(turns: list[str], options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for text in turns:
        lower = _normalize(text)
        if not re.search(r"\b(?:evidence|data|result|showed|shows|failed|fails|succeeded|succeeds)\b", lower):
            continue
        for option in options:
            alias = _matched_alias(lower, option)
            if not alias:
                continue
            negative = bool(re.search(rf"\b{re.escape(alias)}\b.{{0,60}}\b(?:fail|fails|failed|worse|less reliable|breaks?)\b", lower))
            positive = bool(re.search(rf"\b{re.escape(alias)}\b.{{0,60}}\b(?:succeed|succeeds|worked|works|better|more reliable)\b", lower))
            if negative or positive:
                result.append(
                    {
                        "option_id": option["id"],
                        "option_label": option["label"],
                        "text": truncate(text, 700),
                        "direction": "against" if negative else "supports",
                        "hypothetical": _is_hypothetical_evidence(text),
                        "source": (
                            "visible_user_hypothetical_not_observed"
                            if _is_hypothetical_evidence(text)
                            else "visible_user_report_not_independently_verified"
                        ),
                    }
                )
    return result[-8:]


def _extract_stated_preference(turns: list[str], options: list[dict[str, Any]]) -> dict[str, Any]:
    for text in reversed(turns):
        lower = _normalize(text)
        if not re.search(r"\b(?:i think|i believe|my best guess|i would choose|i prefer)\b", lower):
            continue
        for option in options:
            alias = _matched_alias(lower, option)
            if alias and re.search(r"\b(?:best|wins?|choose|prefer|recommend)\b", lower):
                return {
                    "option_id": option["id"],
                    "option_label": option["label"],
                    "text": truncate(text, 500),
                    "source": "visible_user_stance",
                }
    return {}


def _choose_option(
    options: list[dict[str, Any]],
    *,
    priorities: list[str],
    evidence_updates: list[dict[str, Any]],
    constraint_updates: list[str],
) -> dict[str, Any]:
    if len(options) < 2:
        return {}
    priority_terms = set(_terms(" ".join(priorities)))
    deadline_tightened = any(
        re.search(r"\bdeadline\b.*\b(?:closer|shorter|tighter|moved)\b", item, re.IGNORECASE)
        for item in constraint_updates
    )
    scores: list[tuple[int, int, dict[str, Any], list[str]]] = []
    for index, option in enumerate(options):
        terms = set(_terms(" ".join([option["label"], *option["properties"]])))
        score = 0
        reasons: list[str] = []
        overlap = sorted(priority_terms & terms)
        if overlap:
            score += 5
            reasons.append(f"it directly matches the stated priority of {priorities[-1]}")
        if not priorities and "balanced" in terms:
            score += 2
            reasons.append("it is the middle-ground default when no priority dominates")
        if deadline_tightened and {"fast", "speed", "quick"} & terms:
            score += 1
            reasons.append("the closer deadline gives speed more weight")
        against = [item for item in evidence_updates if item["option_id"] == option["id"] and item["direction"] == "against"]
        support = [item for item in evidence_updates if item["option_id"] == option["id"] and item["direction"] == "supports"]
        if against:
            score -= 6
            reasons.append("the reported outcome evidence weighs against it")
        if support:
            score += 3
            reasons.append("the reported outcome evidence supports it")
        scores.append((score, -index, option, reasons))
    score, _, selected, reasons = max(scores, key=lambda item: (item[0], item[1]))
    return {
        "option_id": selected["id"],
        "option_label": selected["label"],
        "score": score,
        "basis": reasons or ["it is the least-assumptive default from the visible descriptions"],
        "epistemic_state": "revisable_current_session_recommendation",
    }


def _request_mode(prompt: str) -> str:
    lower = _normalize(prompt)
    if re.search(r"\b(?:best prediction|predict|what do you expect|most likely)\b", lower):
        return "prediction"
    if re.search(r"\b(?:do you disagree|do you agree|agree or disagree|your stance)\b", lower):
        return "disagreement"
    if re.search(r"\b(?:what changes|what would you update|how does that change|revise|update)\b", lower):
        return "revision"
    if re.search(r"\bcompare\b|\bcontrast\b", lower):
        return "comparison_and_choice" if re.search(r"\b(?:recommend|choose|pick|prefer)\b", lower) else "comparison"
    if re.search(r"\b(?:recommend|choose|pick|prefer)\b", lower):
        return "choice"
    return "none"


def _response(
    prompt: str,
    *,
    mode: str,
    options: list[dict[str, Any]],
    subject: str,
    priorities: list[str],
    evidence_updates: list[dict[str, Any]],
    constraint_updates: list[str],
    stated_preference: dict[str, Any],
    recommendation: dict[str, Any],
) -> tuple[str, list[str], dict[str, Any]]:
    if len(options) < 2 or mode == "none" or not recommendation:
        return "", [], {}
    chosen = str(recommendation.get("option_label") or "")
    comparison_sentences = [_describe_option(item, subject) for item in options]
    comparison_fields = {
        "candidates": [str(item.get("label") or "") for item in options],
        "findings": comparison_sentences,
        "comparison_basis": "visible option descriptions under the same current-session priorities",
    }
    choice_fields = {
        "selected_option": chosen,
        "criteria": recommendation.get("basis") or [],
        "revision_conditions": ["the stated priority changes", "new outcome evidence changes the tradeoff"],
    }
    priority = priorities[-1] if priorities else ""
    latest_evidence = evidence_updates[-1] if evidence_updates else {}

    if mode in {"comparison", "comparison_and_choice"}:
        text = " ".join(comparison_sentences)
        operations = ["comparison"]
        fields: dict[str, Any] = {"comparison": comparison_fields}
        if mode == "comparison_and_choice":
            reason = f"it best matches the stated priority of {priority}" if priority else str((recommendation.get("basis") or [""])[0])
            text += f" I would start with the {chosen} because {reason}."
            text += " I would revise that choice if the priority or the outcome evidence changed."
            operations.append("choice")
            fields["choice"] = choice_fields
        return text, operations, fields

    if mode == "revision":
        if latest_evidence:
            changed = str(latest_evidence.get("text") or "the latest reported result")
            text = (
                f"If that evidence held, it would change the recommendation: it would weigh {latest_evidence['direction']} "
                f"the {latest_evidence['option_label']}."
                if latest_evidence.get("hypothetical") is True
                else (
                    f"That evidence changes the recommendation: it weighs {latest_evidence['direction']} "
                    f"the {latest_evidence['option_label']}."
                )
            )
        else:
            changed = constraint_updates[-1] if constraint_updates else "the latest condition changed"
            text = f"That changes the weighting: {changed.rstrip('.')}"
            text += f", but {priority} remains the controlling priority." if priority else "."
        text += f" I would update the recommendation to the {chosen}."
        if not latest_evidence and priority and re.search(r"\bdeadline\b", changed, flags=re.IGNORECASE):
            text += " The tighter deadline makes the tradeoff closer; it does not erase the priority you kept."
        return text, ["correction", "choice"], {
            "correction": {
                "corrected_input": changed,
                "affected_result": "current_session_recommendation",
                "recompute_required": True,
                "current_application": text,
            },
            "choice": choice_fields,
        }

    if mode == "disagreement":
        preference_label = str(stated_preference.get("option_label") or "")
        disagree = bool(preference_label and preference_label != chosen)
        if disagree:
            text = f"I do disagree, based on the priorities we have set. The {preference_label} remains a workable tradeoff, but the {chosen} fits the current evidence better."
        else:
            text = f"I agree with that current choice: the {chosen} fits the priorities and evidence we have."
        text += " I would change my stance if those premises changed."
        return text, ["disagreement"], {
            "disagreement": {
                "stance": "disagreement" if disagree else "agreement",
                "claim_evaluated": str(stated_preference.get("text") or prompt),
                "premises": [*priorities, *[str(item.get("text") or "") for item in evidence_updates]]
                or recommendation.get("basis")
                or ["the visible option descriptions"],
            }
        }

    if mode == "prediction":
        basis = [*priorities, *[str(item.get("text") or "") for item in evidence_updates]]
        text = f"My best prediction from what we have is the {chosen}."
        if latest_evidence:
            text += f" The latest reported evidence weighs {latest_evidence['direction']} the {latest_evidence['option_label']}."
        elif priority:
            text += f" That follows from {priority} being the current priority."
        text += " It is a revisable prediction, not a guaranteed outcome; I would update it if the premises or results changed."
        return text, ["prediction"], {
            "prediction": {
                "predicted_change": chosen,
                "basis": basis or recommendation.get("basis") or ["the visible current-session comparison"],
                "revision_conditions": ["the premises or results changed"],
            }
        }

    if mode == "choice":
        reason = str((recommendation.get("basis") or [""])[0])
        return (
            f"I would choose the {chosen} because {reason}. I would revise that choice if the priority or outcome evidence changed.",
            ["choice"],
            {"choice": choice_fields},
        )
    return "", [], {}


def _describe_option(option: dict[str, Any], subject: str) -> str:
    properties = [str(item) for item in option.get("properties") or [] if str(item)]
    label = str(option.get("label") or f"unnamed {subject}")
    terms = set(_terms(" ".join(properties)))
    if {"fast", "fragile"} <= terms:
        return f"The {label} offers speed, with fragility as its tradeoff."
    if {"slow", "reliable"} <= terms:
        return f"The {label} favors reliability at a slower pace."
    if "balanced" in terms:
        return f"The {label} keeps the tradeoff closer to the middle."
    if len(properties) > 1:
        return f"The {label} combines {', '.join(properties[:-1])} and {properties[-1]}."
    return f"The {label} is defined here by {properties[0] if properties else label}."


def _matched_alias(text: str, option: dict[str, Any]) -> str:
    aliases = sorted([str(item) for item in option.get("aliases") or [] if str(item)], key=len, reverse=True)
    return next((alias for alias in aliases if re.search(rf"\b{re.escape(alias)}\b", text)), "")


def _terms(value: str) -> list[str]:
    aliases = {
        "reliability": "reliable",
        "speed": "fast",
        "quick": "fast",
        "quickly": "fast",
        "slower": "slow",
        "fragility": "fragile",
    }
    result = []
    for item in re.findall(r"[a-z][a-z0-9_-]{1,}", _normalize(value)):
        term = aliases.get(item, item)
        if term not in result:
            result.append(term)
    return result


def _normalize(value: str) -> str:
    return " ".join(str(value or "").lower().replace("’", "'").split())


def _singular_subject(value: str) -> str:
    normalized = str(value or "").lower()
    return {
        "plans": "plan",
        "options": "option",
        "choices": "choice",
        "approaches": "approach",
        "routes": "route",
        "designs": "design",
        "candidates": "candidate",
    }.get(normalized, normalized)


def _is_hypothetical_evidence(value: str) -> bool:
    return bool(
        re.search(
            r"(?:^|[.!?]\s+)if\s+(?:the\s+)?(?:evidence|data|results?)\b|"
            r"\bif\s+.+?\b(?:showed|shows|failed|fails|succeeded|succeeds)\b",
            str(value or ""),
            flags=re.IGNORECASE,
        )
    )


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
