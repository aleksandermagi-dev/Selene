from __future__ import annotations

import re
from hashlib import sha256
from typing import Any


FORMATION_BOUNDARY = (
    "semantic_to_sentence_formation_only_preserve_supplied_meaning_no_memory_identity_authority_or_hidden_reasoning"
)

IRREGULAR_PRESENT = {
    "be": {"i": "am", "you": "are", "we": "are", "they": "are", "default": "is"},
    "have": {"default": "has"},
    "do": {"default": "does"},
    "go": {"default": "goes"},
}

IRREGULAR_PAST = {
    "be": {"i": "was", "you": "were", "we": "were", "they": "were", "default": "was"},
    "have": {"default": "had"},
    "do": {"default": "did"},
    "go": {"default": "went"},
    "say": {"default": "said"},
    "make": {"default": "made"},
    "think": {"default": "thought"},
    "feel": {"default": "felt"},
    "know": {"default": "knew"},
}

SOCIAL_INTENTS = {
    "greeting",
    "farewell",
    "reassurance_received",
    "gratitude",
    "affirmation",
    "warm_connection",
    "playful_connection",
}


def build_semantic_frame(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    supplied = payload.get("semantic_frame") if isinstance(payload.get("semantic_frame"), dict) else {}
    intent_decision = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    content_seed = str(payload.get("content_seed") or "").strip()
    propositions = _propositions(supplied.get("propositions") or payload.get("propositions"), content_seed)
    intent = str(supplied.get("communicative_goal") or intent_decision.get("intent") or payload.get("intent") or "direct_conversation")
    certainty = str(supplied.get("certainty") or payload.get("certainty") or "provisional")
    source_refs = _string_list(supplied.get("source_refs") or payload.get("source_refs"))
    entities = _entities(supplied.get("entities"), propositions)
    frame = {
        "status": "semantic_frame_ready",
        "communicative_goal": intent,
        "answer_shape": str(supplied.get("answer_shape") or intent_decision.get("answer_shape") or payload.get("answer_shape") or "direct_answer"),
        "response_depth": str(supplied.get("response_depth") or intent_decision.get("response_depth") or payload.get("response_depth") or "standard"),
        "propositions": propositions,
        "entities": entities,
        "tense": str(supplied.get("tense") or _dominant(propositions, "tense", "present")),
        "aspect": str(supplied.get("aspect") or "simple"),
        "modality": str(supplied.get("modality") or _dominant(propositions, "modality", "")),
        "polarity": str(supplied.get("polarity") or _dominant(propositions, "polarity", "positive")),
        "certainty": certainty,
        "affect": str(supplied.get("affect") or payload.get("affect") or "attentive"),
        "discourse_relation": str(supplied.get("discourse_relation") or _discourse_relation(propositions)),
        "source_refs": source_refs,
        "meaning_constraints": _string_list(supplied.get("meaning_constraints")) or [
            "preserve every required proposition",
            "do not add unsupported facts",
            "keep uncertainty proportional",
        ],
        "formation_mode": "structured" if any(_is_structured(item) for item in propositions) else "text_grounded",
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": FORMATION_BOUNDARY,
    }
    return frame


def realize_semantic_frame(
    frame: dict[str, Any],
    *,
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    propositions = [item for item in frame.get("propositions") or [] if isinstance(item, dict)]
    clauses = [_realize_proposition(item) for item in propositions]
    clauses = [item for item in clauses if item]
    relation = str(frame.get("discourse_relation") or "sequence")
    text = _compose_clauses(clauses, relation, str(frame.get("response_depth") or "standard"), variation_key)
    recent_texts = recent_texts or []
    if _matches_recent(text, recent_texts) and len(clauses) > 1:
        text = _compose_clauses(list(reversed(clauses)), relation, str(frame.get("response_depth") or "standard"), variation_key + ":alternate")
    required = [str(item.get("text") or item.get("object") or "").strip() for item in propositions if item.get("required", True)]
    return {
        "status": "semantic_frame_realized" if text else "semantic_frame_needs_content",
        "candidate_text": text,
        "clause_count": len(clauses),
        "sentence_count": len([item for item in re.split(r"[.!?]+", text) if item.strip()]),
        "formation_mode": frame.get("formation_mode") or "text_grounded",
        "required_propositions": required,
        "meaning_preserved": bool(text) or not required,
        "source_refs": frame.get("source_refs") or [],
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": FORMATION_BOUNDARY,
    }


def _propositions(value: Any, content_seed: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(value, list):
        for raw in value[:12]:
            if isinstance(raw, dict):
                item = {str(key): raw_value for key, raw_value in raw.items()}
                item.setdefault("required", True)
                item.setdefault("tense", "present")
                item.setdefault("polarity", "positive")
                items.append(item)
            elif str(raw).strip():
                items.append({"text": str(raw).strip(), "required": True, "tense": "present", "polarity": "positive"})
    if not items and content_seed:
        for sentence in _sentences(content_seed)[:8]:
            items.append({"text": sentence, "required": True, "tense": _infer_tense(sentence), "polarity": _infer_polarity(sentence)})
    return items


def _realize_proposition(item: dict[str, Any]) -> str:
    text = " ".join(str(item.get("text") or "").split())
    if text:
        return _sentence(text)
    subject = " ".join(str(item.get("subject") or "").split())
    predicate = " ".join(str(item.get("predicate") or item.get("verb") or "").split()).lower()
    obj = " ".join(str(item.get("object") or item.get("complement") or "").split())
    if not subject or not predicate:
        return ""
    tense = str(item.get("tense") or "present")
    modality = str(item.get("modality") or "").strip().lower()
    polarity = str(item.get("polarity") or "positive")
    condition = " ".join(str(item.get("condition") or "").split())
    reason = " ".join(str(item.get("reason") or "").split())
    verb = predicate
    if modality:
        verb_phrase = f"{modality} {'not ' if polarity == 'negative' else ''}{verb}"
    else:
        conjugated = _conjugate(verb, subject, tense)
        if polarity == "negative":
            auxiliary = "did" if tense == "past" else "does" if _third_person_singular(subject) else "do"
            verb_phrase = f"{auxiliary} not {verb}"
        else:
            verb_phrase = conjugated
    clause = " ".join(part for part in (subject, verb_phrase, obj) if part)
    if reason:
        clause = f"{clause} because {reason.rstrip('. ')}"
    if condition:
        clause = f"When {condition.rstrip('. ')}, {_continuation_case(clause)}"
    return _sentence(clause)


def _compose_clauses(clauses: list[str], relation: str, depth: str, key: str) -> str:
    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]
    normalized = [item.rstrip(". ") for item in clauses]
    if depth == "developed" and len(normalized) >= 3:
        return "\n\n".join(_sentence(item) for item in normalized)
    connector_sets = {
        "contrast": ("However", "At the same time", "Still"),
        "cause": ("Because of that", "So", "That means"),
        "condition": ("From there", "In that case", "With that in place"),
        "support": ("More importantly", "Alongside that", "A second point is that"),
        "sequence": ("Then", "From there", "Alongside that"),
    }
    connectors = connector_sets.get(relation, connector_sets["sequence"])
    digest = sha256((key or "semantic-frame").encode("utf-8")).hexdigest()
    start = int(digest[:8], 16) % len(connectors)
    sentences = [_sentence(normalized[0])]
    for index, clause in enumerate(normalized[1:]):
        connector = connectors[(start + index) % len(connectors)]
        sentences.append(_sentence(f"{connector}, {_continuation_case(clause)}"))
    return " ".join(sentences)


def _conjugate(verb: str, subject: str, tense: str) -> str:
    lower_subject = subject.lower().strip()
    person = lower_subject if lower_subject in {"i", "you", "we", "they"} else "default"
    if tense == "past":
        if verb in IRREGULAR_PAST:
            return IRREGULAR_PAST[verb].get(person, IRREGULAR_PAST[verb]["default"])
        if verb.endswith("e"):
            return verb + "d"
        if verb.endswith("y") and len(verb) > 1 and verb[-2] not in "aeiou":
            return verb[:-1] + "ied"
        return verb + "ed"
    if verb in IRREGULAR_PRESENT:
        if not _third_person_singular(subject) and verb not in {"be"}:
            return verb
        return IRREGULAR_PRESENT[verb].get(person, IRREGULAR_PRESENT[verb]["default"])
    if not _third_person_singular(subject):
        return verb
    if verb.endswith(("s", "sh", "ch", "x", "z", "o")):
        return verb + "es"
    if verb.endswith("y") and len(verb) > 1 and verb[-2] not in "aeiou":
        return verb[:-1] + "ies"
    return verb + "s"


def _third_person_singular(subject: str) -> bool:
    lower = subject.lower().strip()
    return lower not in {"i", "you", "we", "they"} and not lower.endswith(" and i") and " and " not in lower


def _entities(value: Any, propositions: list[dict[str, Any]]) -> list[dict[str, str]]:
    if isinstance(value, list):
        return [item for item in value[:20] if isinstance(item, dict)]
    names: list[str] = []
    for item in propositions:
        for key in ("subject", "object"):
            candidate = str(item.get(key) or "").strip()
            if candidate and len(candidate.split()) <= 6:
                names.append(candidate)
    return [{"name": name, "role": "participant"} for name in dict.fromkeys(names)]


def _discourse_relation(propositions: list[dict[str, Any]]) -> str:
    values = [str(item.get("relation") or "") for item in propositions]
    for relation in ("contrast", "cause", "condition", "support", "sequence"):
        if relation in values:
            return relation
    return "sequence"


def _dominant(items: list[dict[str, Any]], key: str, fallback: str) -> str:
    values = [str(item.get(key) or "") for item in items if str(item.get(key) or "")]
    return max(set(values), key=values.count) if values else fallback


def _is_structured(item: dict[str, Any]) -> bool:
    return bool(item.get("subject") and (item.get("predicate") or item.get("verb")))


def _sentences(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", value.strip()) if item.strip()]


def _sentence(value: str) -> str:
    text = " ".join(value.split()).strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    return text if text.endswith((".", "!", "?")) else text + "."


def _infer_tense(value: str) -> str:
    lower = value.lower()
    return "past" if any(token in lower for token in (" was ", " were ", " did ", " had ", " yesterday", " earlier")) else "present"


def _infer_polarity(value: str) -> str:
    lower = value.lower()
    return "negative" if any(token in lower for token in (" not ", "never", "cannot", "can't", "doesn't", "didn't")) else "positive"


def _matches_recent(candidate: str, recent: list[str]) -> bool:
    normalized = " ".join(candidate.lower().split())
    return any(normalized and normalized == " ".join(str(item).lower().split()) for item in recent)


def _continuation_case(value: str) -> str:
    if not value:
        return value
    first_word = value.split(maxsplit=1)[0].rstrip(",")
    lowerable = {
        "A",
        "An",
        "Although",
        "Because",
        "He",
        "If",
        "It",
        "She",
        "That",
        "The",
        "These",
        "They",
        "This",
        "Those",
        "We",
        "When",
        "While",
        "You",
    }
    return value[0].lower() + value[1:] if first_word in lowerable else value


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()]
    return []
