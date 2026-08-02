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
    "bring": {"default": "brought"},
    "buy": {"default": "bought"},
    "come": {"default": "came"},
    "find": {"default": "found"},
    "give": {"default": "gave"},
    "keep": {"default": "kept"},
    "leave": {"default": "left"},
    "read": {"default": "read"},
    "run": {"default": "ran"},
    "speak": {"default": "spoke"},
    "tell": {"default": "told"},
    "understand": {"default": "understood"},
}

IRREGULAR_PARTICIPLES = {
    "be": "been",
    "do": "done",
    "go": "gone",
    "have": "had",
    "know": "known",
    "make": "made",
    "say": "said",
    "see": "seen",
    "take": "taken",
    "think": "thought",
    "write": "written",
    "bring": "brought",
    "buy": "bought",
    "come": "come",
    "find": "found",
    "give": "given",
    "keep": "kept",
    "leave": "left",
    "read": "read",
    "run": "run",
    "speak": "spoken",
    "tell": "told",
    "understand": "understood",
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
    expression_directives = (
        supplied.get("expression_directives")
        if isinstance(supplied.get("expression_directives"), dict)
        else payload.get("expression_directives")
        if isinstance(payload.get("expression_directives"), dict)
        else {}
    )
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
        "expression_directives": expression_directives,
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
    realized = [
        (
            index,
            item,
            _realize_proposition(
                item,
                variation_key=f"{variation_key}|unit:{item.get('id') or index + 1}",
            ),
        )
        for index, item in enumerate(propositions)
    ]
    realized = [(index, item, clause) for index, item, clause in realized if clause]
    clauses = [clause for _, _, clause in realized]
    relations = [str(item.get("relation") or "") for _, item, _ in realized]
    moods = [str(item.get("mood") or "declarative") for _, item, _ in realized]
    relation = str(frame.get("discourse_relation") or "sequence")
    text = _compose_clauses(
        clauses,
        relation,
        str(frame.get("response_depth") or "standard"),
        variation_key,
        relations=relations,
        moods=moods,
    )
    recent_texts = recent_texts or []
    if _matches_recent(text, recent_texts) and len(clauses) > 1:
        text = _compose_clauses(
            list(reversed(clauses)),
            relation,
            str(frame.get("response_depth") or "standard"),
            variation_key + ":alternate",
            relations=list(reversed(relations)),
            moods=list(reversed(moods)),
        )
    required = [str(item.get("text") or item.get("object") or "").strip() for item in propositions if item.get("required", True)]
    required_unit_ids = [
        str(item.get("id") or f"semantic_{index + 1}")
        for index, item in enumerate(propositions)
        if item.get("required", True)
    ]
    realized_unit_ids = [
        str(item.get("id") or f"semantic_{index + 1}")
        for index, item, _ in realized
    ]
    required_units_preserved = all(unit_id in realized_unit_ids for unit_id in required_unit_ids)
    meaning_signature = list(
        dict.fromkeys(
            str(marker)
            for item in propositions
            for marker in item.get("meaning_keys") or []
            if str(marker).strip()
        )
    )
    return {
        "status": "semantic_frame_realized" if text else "semantic_frame_needs_content",
        "candidate_text": text,
        "clause_count": len(clauses),
        "sentence_count": len([item for item in re.split(r"[.!?]+", text) if item.strip()]),
        "formation_mode": frame.get("formation_mode") or "text_grounded",
        "grammar_features": sorted(
            {
                feature
                for item in propositions
                for feature in ("aspect", "voice", "mood", "modality", "polarity", "condition", "reason", "contrast", "example")
                if item.get(feature)
            }
        ),
        "clause_relations": relations,
        "required_propositions": required,
        "required_semantic_unit_ids": required_unit_ids,
        "realized_semantic_unit_ids": realized_unit_ids,
        "required_semantic_units_preserved": required_units_preserved,
        "meaning_signature": meaning_signature,
        "lexical_choice_unit_count": sum(
            1 for item in propositions if isinstance(item.get("lexical_choices"), dict) and item.get("lexical_choices")
        ),
        "meaning_preserved": (bool(text) or not required) and required_units_preserved,
        "source_refs": frame.get("source_refs") or [],
        "expression_directives": frame.get("expression_directives") or {},
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


def _realize_proposition(item: dict[str, Any], *, variation_key: str = "") -> str:
    text = " ".join(str(item.get("text") or "").split())
    if text:
        return _sentence(text)
    subject = _semantic_field(item, "subject", variation_key)
    predicate = _semantic_field(item, "predicate", variation_key).lower()
    if not predicate:
        predicate = " ".join(str(item.get("verb") or "").split()).lower()
    obj = _semantic_field(item, "object", variation_key)
    if not obj:
        obj = " ".join(str(item.get("complement") or "").split())
    mood = str(item.get("mood") or "declarative").lower()
    if mood != "imperative" and not subject:
        return ""
    if not predicate:
        return ""
    subject_modifiers = _words(item.get("subject_modifiers"))
    object_modifiers = _words(item.get("object_modifiers"))
    if subject_modifiers:
        subject = " ".join([*subject_modifiers, subject])
    if object_modifiers and obj:
        obj = " ".join([*object_modifiers, obj])
    tense = str(item.get("tense") or "present")
    subject_number = str(item.get("subject_number") or "").strip().lower()
    aspect = str(item.get("aspect") or "simple")
    voice = str(item.get("voice") or "active")
    agent = " ".join(str(item.get("agent") or "").split())
    if voice == "passive" and agent:
        obj = " ".join(part for part in (obj, f"by {agent}") if part)
    modality = str(item.get("modality") or "").strip().lower()
    polarity = str(item.get("polarity") or "positive")
    condition = " ".join(str(item.get("condition") or "").split())
    reason = " ".join(str(item.get("reason") or "").split())
    contrast = " ".join(str(item.get("contrast") or "").split())
    example = " ".join(str(item.get("example") or "").split())
    qualifier = _semantic_field(item, "qualifier", variation_key)
    adverbs = _words(item.get("adverbs"))
    if mood == "imperative":
        clause = " ".join(part for part in (predicate, *adverbs, obj) if part)
    elif mood == "interrogative":
        clause = _interrogative_clause(
            subject,
            predicate,
            obj,
            tense,
            aspect,
            modality,
            polarity,
            voice,
            adverbs,
            subject_number,
        )
    else:
        verb_phrase = _verb_phrase(
            subject,
            predicate,
            tense,
            aspect,
            modality,
            polarity,
            voice,
            subject_number,
        )
        clause = " ".join(part for part in (subject, verb_phrase, *adverbs, obj) if part)
    if qualifier:
        clause = f"{qualifier.rstrip(', ')}, {_continuation_case(clause)}"
    digest = sha256((variation_key or str(item.get("id") or "semantic-unit")).encode("utf-8")).hexdigest()
    if reason:
        if int(digest[:2], 16) % 2:
            clause = f"Because {reason.rstrip('. ')}, {_continuation_case(clause)}"
        else:
            clause = f"{clause} because {reason.rstrip('. ')}"
    if contrast:
        clause = f"{clause}, while {contrast.rstrip('. ')}"
    if condition:
        if int(digest[2:4], 16) % 2:
            clause = f"{clause} when {condition.rstrip('. ')}"
        else:
            clause = f"When {condition.rstrip('. ')}, {_continuation_case(clause)}"
    if example:
        clause = f"{clause}; for example, {example.rstrip('. ')}"
    return _sentence(clause)


def _semantic_field(item: dict[str, Any], field: str, variation_key: str) -> str:
    base = " ".join(str(item.get(field) or "").split())
    choices = item.get("lexical_choices") if isinstance(item.get("lexical_choices"), dict) else {}
    alternatives = [
        " ".join(str(value).split())
        for value in choices.get(field) or []
        if str(value).strip()
    ]
    pool = list(dict.fromkeys([base, *alternatives])) if base else list(dict.fromkeys(alternatives))
    if not pool:
        return ""
    digest = sha256(f"{variation_key}|{field}".encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def _compose_clauses(
    clauses: list[str],
    relation: str,
    depth: str,
    key: str,
    *,
    relations: list[str] | None = None,
    moods: list[str] | None = None,
) -> str:
    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]
    normalized = [item.rstrip(". ") for item in clauses]
    connector_sets = {
        "contrast": ("However", "At the same time", "Still", "By contrast", "The difference is that"),
        "cause": ("Because of that", "So", "That means", "For that reason", "The mechanism is that"),
        "condition": ("From there", "In that case", "With that in place", "Under that condition", "If that changes"),
        "support": ("More importantly", "Alongside that", "A second point is that", "Supporting that", "Another useful piece is that"),
        "example": ("For example", "In a different case", "One concrete example is this"),
        "return": ("Returning to the earlier point", "That changes the earlier point", "Back on that thread"),
        "conclusion": ("Taken together", "The practical landing is this", "Overall"),
        "sequence": ("Then", "From there", "Alongside that", "Next", "After that"),
    }
    digest = sha256((key or "semantic-frame").encode("utf-8")).hexdigest()
    sentences = [_sentence(normalized[0])]
    for index, clause in enumerate(normalized[1:]):
        clause_relation = (relations[index + 1] if relations and len(relations) > index + 1 else "") or relation
        connectors = connector_sets.get(clause_relation, connector_sets["sequence"])
        start = int(digest[index * 2:index * 2 + 8] or digest[:8], 16) % len(connectors)
        connector = connectors[(start + index) % len(connectors)]
        mood = moods[index + 1] if moods and len(moods) > index + 1 else "declarative"
        continuation = (
            clause[0].lower() + clause[1:]
            if mood == "imperative" and clause
            else _continuation_case(clause)
        )
        if _starts_with_transition(clause):
            sentences.append(_sentence(clause))
        elif connector.lower().endswith(" that"):
            sentences.append(_sentence(f"{connector} {continuation}"))
        else:
            sentences.append(_sentence(f"{connector}, {continuation}"))
    if depth == "developed" and len(sentences) >= 3:
        return "\n\n".join(sentences)
    return " ".join(sentences)


def _starts_with_transition(value: str) -> bool:
    return bool(
        re.match(
            r"^(?:however|but|still|by contrast|because|so|therefore|if|when|unless|for example|for instance|"
            r"back to|returning to|finally|overall|taken together|also|another|more importantly|alongside|then|next)\b",
            value.strip(),
            flags=re.IGNORECASE,
        )
    )


def _verb_phrase(
    subject: str,
    predicate: str,
    tense: str,
    aspect: str,
    modality: str,
    polarity: str,
    voice: str,
    subject_number: str = "",
) -> str:
    base, tail = _split_predicate(predicate)
    negative = polarity == "negative"
    suffix = f" {tail}" if tail else ""
    if tense == "future" and not modality:
        modality = "will"
    if modality:
        if voice == "passive":
            core = f"be {_past_participle(base)}{suffix}"
        elif aspect == "progressive":
            core = f"be {_present_participle(base)}{suffix}"
        elif aspect == "perfect":
            core = f"have {_past_participle(base)}{suffix}"
        elif aspect == "perfect_progressive":
            core = f"have been {_present_participle(base)}{suffix}"
        else:
            core = predicate
        return f"{modality}{' not' if negative else ''} {core}"
    if voice == "passive":
        auxiliary = _conjugate("be", subject, tense, subject_number)
        return f"{auxiliary}{' not' if negative else ''} {_past_participle(base)}{suffix}"
    if aspect == "progressive":
        auxiliary = _conjugate("be", subject, tense, subject_number)
        return f"{auxiliary}{' not' if negative else ''} {_present_participle(base)}{suffix}"
    if aspect == "perfect":
        auxiliary = _conjugate("have", subject, tense, subject_number)
        return f"{auxiliary}{' not' if negative else ''} {_past_participle(base)}{suffix}"
    if aspect == "perfect_progressive":
        auxiliary = _conjugate("have", subject, tense, subject_number)
        return f"{auxiliary}{' not' if negative else ''} been {_present_participle(base)}{suffix}"
    if negative:
        auxiliary = "did" if tense == "past" else "does" if _third_person_singular(subject, subject_number) else "do"
        return f"{auxiliary} not {predicate}"
    return f"{_conjugate(base, subject, tense, subject_number)}{suffix}"


def _interrogative_clause(
    subject: str,
    predicate: str,
    obj: str,
    tense: str,
    aspect: str,
    modality: str,
    polarity: str,
    voice: str,
    adverbs: list[str],
    subject_number: str = "",
) -> str:
    base, tail = _split_predicate(predicate)
    negative = " not" if polarity == "negative" else ""
    suffix = f" {tail}" if tail else ""
    if tense == "future" and not modality:
        modality = "will"
    if modality:
        if voice == "passive":
            core = f"be {_past_participle(base)}{suffix}"
        elif aspect == "progressive":
            core = f"be {_present_participle(base)}{suffix}"
        elif aspect == "perfect":
            core = f"have {_past_participle(base)}{suffix}"
        elif aspect == "perfect_progressive":
            core = f"have been {_present_participle(base)}{suffix}"
        else:
            core = predicate
        return " ".join(part for part in (f"{modality}{negative}", subject, core, *adverbs, obj) if part) + "?"
    if voice == "passive" or aspect == "progressive":
        auxiliary = _conjugate("be", subject, tense, subject_number)
        core = f"{_past_participle(base)}{suffix}" if voice == "passive" else f"{_present_participle(base)}{suffix}"
    elif aspect in {"perfect", "perfect_progressive"}:
        auxiliary = _conjugate("have", subject, tense, subject_number)
        core = f"been {_present_participle(base)}{suffix}" if aspect == "perfect_progressive" else f"{_past_participle(base)}{suffix}"
    else:
        auxiliary = "did" if tense == "past" else "does" if _third_person_singular(subject, subject_number) else "do"
        core = predicate
    return " ".join(part for part in (f"{auxiliary}{negative}", subject, core, *adverbs, obj) if part) + "?"


def _split_predicate(predicate: str) -> tuple[str, str]:
    parts = predicate.split(maxsplit=1)
    return parts[0], parts[1] if len(parts) > 1 else ""


def _past_participle(verb: str) -> str:
    if verb in IRREGULAR_PARTICIPLES:
        return IRREGULAR_PARTICIPLES[verb]
    if verb.endswith("e"):
        return verb + "d"
    if verb.endswith("y") and len(verb) > 1 and verb[-2] not in "aeiou":
        return verb[:-1] + "ied"
    return verb + "ed"


def _present_participle(verb: str) -> str:
    if verb == "be":
        return "being"
    if verb.endswith("ie"):
        return verb[:-2] + "ying"
    if verb.endswith("e") and not verb.endswith("ee"):
        return verb[:-1] + "ing"
    if (
        len(verb) >= 3
        and verb[-1] not in "aeiouwxy"
        and verb[-2] in "aeiou"
        and verb[-3] not in "aeiou"
    ):
        return verb + verb[-1] + "ing"
    return verb + "ing"


def _words(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [" ".join(str(item).split()) for item in value if str(item).strip()][:8]
    if isinstance(value, str) and value.strip():
        return [" ".join(value.split())]
    return []


def _conjugate(verb: str, subject: str, tense: str, subject_number: str = "") -> str:
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
        if verb == "be" and subject_number == "plural":
            return "are"
        if not _third_person_singular(subject, subject_number) and verb not in {"be"}:
            return verb
        return IRREGULAR_PRESENT[verb].get(person, IRREGULAR_PRESENT[verb]["default"])
    if not _third_person_singular(subject, subject_number):
        return verb
    if verb.endswith(("s", "sh", "ch", "x", "z", "o")):
        return verb + "es"
    if verb.endswith("y") and len(verb) > 1 and verb[-2] not in "aeiou":
        return verb[:-1] + "ies"
    return verb + "s"


def _third_person_singular(subject: str, subject_number: str = "") -> bool:
    if subject_number == "plural":
        return False
    if subject_number == "singular":
        return True
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
    predicate = item.get("predicate") or item.get("verb")
    return bool(predicate and (item.get("subject") or str(item.get("mood") or "") == "imperative"))


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
