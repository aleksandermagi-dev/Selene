from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .supported_semantics import build_supported_semantic_packet


KNOWLEDGE_EXPRESSION_BOUNDARY = (
    "approved_knowledge_meaning_to_nlo_only_no_new_fact_memory_identity_"
    "personality_governance_authority_training_or_source_imitation"
)

FIELD_ROLES = {
    "central_claim": ("answer", "sequence"),
    "principle": ("support", "support"),
    "relationship": ("support", "support"),
    "example": ("example", "example"),
    "counterexample": ("limit", "contrast"),
    "limit": ("limit", "contrast"),
    "bounded_application": ("answer", "sequence"),
    "bounded_application_limit": ("limit", "contrast"),
}

VERB_LEMMAS = {
    "allows": "allow",
    "answers": "answer",
    "appears": "appear",
    "becomes": "become",
    "changes": "change",
    "compares": "compare",
    "connects": "connect",
    "contains": "contain",
    "depends": "depend",
    "describes": "describe",
    "explains": "explain",
    "fits": "fit",
    "gives": "give",
    "grows": "grow",
    "helps": "help",
    "includes": "include",
    "keeps": "keep",
    "makes": "make",
    "means": "mean",
    "moves": "move",
    "needs": "need",
    "offers": "offer",
    "provides": "provide",
    "records": "record",
    "remains": "remain",
    "replaces": "replace",
    "reports": "report",
    "requires": "require",
    "shows": "show",
    "specifies": "specify",
    "stores": "store",
    "supports": "support",
    "supplies": "supply",
    "tells": "tell",
    "uses": "use",
    "works": "work",
}
VERB_FORMS = {
    *VERB_LEMMAS,
    *VERB_LEMMAS.values(),
    "allow",
    "answer",
    "appear",
    "become",
    "change",
    "compare",
    "connect",
    "contain",
    "depend",
    "describe",
    "explain",
    "fit",
    "give",
    "grow",
    "help",
    "include",
    "keep",
    "make",
    "mean",
    "move",
    "need",
    "offer",
    "provide",
    "record",
    "remain",
    "replace",
    "report",
    "require",
    "show",
    "specify",
    "store",
    "support",
    "supply",
    "tell",
    "use",
    "work",
}

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "database_write_performed": False,
}


def knowledge_expression_reconstruction_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "knowledge_expression_reconstruction_ready",
            "version": "v1_meaning_first_approved_knowledge_expression",
            "normal_path": [
                "approved_source_wording",
                "understood_concept_fields",
                "current_turn_meaning_selection",
                "supported_semantic_units",
                "nlo_realization",
                "selene_voice_compatibility",
            ],
            "source_wording_is_default_visible_script": False,
            "exact_wording_available_for": [
                "attributed quotation",
                "formula or notation",
                "code or machine-readable form",
                "proper names and required technical terms",
            ],
            "meaning_change_allowed": False,
            "fact_generation_allowed": False,
        }
    )


def build_knowledge_expression_handoff(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Turn selected approved knowledge into an inspectable meaning-first NLO handoff.

    The caller remains responsible for selecting relevant approved knowledge.
    This bridge neither retrieves nor retains anything. It only decomposes the
    already-selected answer into supported units and keeps a compatibility seed
    for older consumers.
    """

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or ""), 3000).strip()
    basis = payload.get("answer_basis") if isinstance(payload.get("answer_basis"), dict) else {}
    content_seed = truncate(
        str(payload.get("content_seed") or basis.get("content_seed") or ""),
        5000,
    ).strip()
    items = [item for item in payload.get("knowledge_items") or [] if isinstance(item, dict)][:12]
    certainty = truncate(str(payload.get("certainty") or "reviewed"), 80)
    answer_kind = truncate(str(basis.get("answer_kind") or "approved_knowledge"), 120)
    refs = list(
        dict.fromkeys(
            [
                *[str(value) for value in basis.get("source_refs") or [] if str(value).strip()],
                *[
                    str(value)
                    for item in items
                    for value in item.get("source_refs") or []
                    if str(value).strip()
                ],
            ]
        )
    )[:50]
    if not content_seed or not items:
        return _locked(
            {
                "status": "knowledge_expression_reconstruction_not_needed",
                "version": "v1_meaning_first_approved_knowledge_expression",
                "active": False,
                "semantic_packet": {},
                "source_refs": refs,
                "source_wording_is_default_visible_script": False,
                "compatibility_seed": content_seed,
                "compatibility_seed_is_expression_authority": False,
            }
        )

    fields = _knowledge_fields(items)
    obligation_support = [
        item for item in basis.get("obligation_support") or [] if isinstance(item, dict)
    ]
    quote_requested = bool(
        re.search(
            r"\b(?:quote|verbatim|exact wording|word for word|exactly as written)\b",
            prompt,
            flags=re.IGNORECASE,
        )
    )
    units: list[dict[str, Any]] = []
    structured_count = 0
    exact_count = 0
    synthesized_count = 0
    for index, sentence in enumerate(_sentences(content_seed)):
        support = obligation_support[index] if index < len(obligation_support) else {}
        match = _match_field(sentence, fields, concept_id=support.get("concept_id"))
        support_field = str(support.get("support_field") or (match or {}).get("field") or "")
        role, relation = _role_relation(
            support_field,
            index,
            answer_kind=answer_kind,
        )
        obligation_ids = [str(support.get("obligation_id") or "").strip()]
        obligation_ids = [value for value in obligation_ids if value]
        unit_refs = list(
            dict.fromkeys(
                [
                    *[str(value) for value in (match or {}).get("source_refs") or [] if str(value).strip()],
                    *[str(value) for value in support.get("source_refs") or [] if str(value).strip()],
                ]
            )
        ) or refs
        exactness_reason = _exactness_reason(sentence, quote_requested=quote_requested)
        required_terms = _required_terms(sentence)
        decomposition = (
            _decompose_supported_clause(
                sentence,
                protected_terms=_protected_terms(match),
            )
            if match and not exactness_reason
            else None
        )
        base = {
            "id": f"knowledge_meaning_{index + 1}",
            "role": role,
            "relation": relation,
            "required": True,
            "supported": True,
            "source_kind": "approved_knowledge",
            "source_refs": unit_refs,
            "certainty": certainty,
            "scope": "current_question_and_approved_knowledge_limits",
            "origin_source_class": "approved_knowledge",
            "origin_concept_id": (match or {}).get("concept_id") or support.get("concept_id"),
            "origin_concept_key": str((match or {}).get("concept_key") or ""),
            "knowledge_field": support_field or "current_prompt_knowledge_synthesis",
            "obligation_ids": obligation_ids,
            "required_terms": required_terms,
            "exactness_lock": bool(exactness_reason),
            "exactness_reason": exactness_reason,
            "meaning_keys": _meaning_keys(sentence, required_terms),
            "source_wording_required": bool(exactness_reason),
        }
        if decomposition:
            units.append({**base, **decomposition, "text": ""})
            structured_count += 1
        else:
            units.append({**base, "text": sentence})
            exact_count += int(bool(exactness_reason))
            synthesized_count += int(not match)

    packet = build_supported_semantic_packet(
        {
            "answer_kind": answer_kind,
            "certainty": certainty,
            "scope": "current_question_and_approved_knowledge_limits",
            "source_refs": refs,
            "fallback_text": content_seed,
            "expression_mode": "meaning_first_reconstruction",
            "source_wording_is_surface_requirement": quote_requested,
            "original_expression_required": not quote_requested,
            "units": units,
        }
    )
    return _locked(
        {
            "status": (
                "knowledge_expression_handoff_ready"
                if units
                else "knowledge_expression_reconstruction_needs_supported_meaning"
            ),
            "version": "v1_meaning_first_approved_knowledge_expression",
            "active": bool(units),
            "answer_kind": answer_kind,
            "semantic_packet": packet,
            "unit_count": len(units),
            "structured_unit_count": structured_count,
            "text_grounded_unit_count": len(units) - structured_count,
            "prompt_synthesis_unit_count": synthesized_count,
            "exactness_lock_count": exact_count,
            "exactness_reasons": list(
                dict.fromkeys(
                    str(item.get("exactness_reason") or "")
                    for item in units
                    if str(item.get("exactness_reason") or "")
                )
            ),
            "source_refs": refs,
            "source_wording_is_default_visible_script": False,
            "source_wording_is_surface_requirement": quote_requested,
            "original_expression_required": not quote_requested,
            "compatibility_seed": content_seed,
            "compatibility_seed_is_expression_authority": False,
            "compatibility_seed_may_be_used_when_structural_realization_is_unavailable": True,
            "selection_authority_unchanged": True,
            "nlo_owns_language_structure": True,
            "voice_retains_expression_compatibility_role": True,
            "meaning_change_allowed": False,
            "fact_generation_allowed": False,
        }
    )


def _knowledge_fields(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in items:
        concept_id = item.get("id") or item.get("concept_id")
        common = {
            "concept_id": concept_id,
            "concept_key": str(item.get("concept_key") or ""),
            "title": str(item.get("title") or ""),
            "source_refs": [str(value) for value in item.get("source_refs") or [] if str(value).strip()],
        }
        values = [("central_claim", str(item.get("central_claim") or ""))]
        for field in ("principles", "relationships", "examples", "counterexamples", "limits"):
            singular = field[:-1] if field.endswith("s") else field
            values.extend((singular, str(value)) for value in item.get(field) or [])
        for field, text in values:
            normalized = _normalize(text)
            if normalized:
                result.append(
                    {
                        **common,
                        "field": field,
                        "text": truncate(" ".join(text.split()), 1200),
                        "normalized": normalized,
                        "terms": set(normalized.split()),
                    }
                )
    return result


def _match_field(
    sentence: str,
    fields: list[dict[str, Any]],
    *,
    concept_id: Any = None,
) -> dict[str, Any] | None:
    normalized = _normalize(sentence)
    candidates = [
        item
        for item in fields
        if not concept_id or str(item.get("concept_id") or "") == str(concept_id)
    ] or fields
    exact = next((item for item in candidates if item.get("normalized") == normalized), None)
    if exact:
        return exact
    terms = set(normalized.split())
    ranked: list[tuple[float, dict[str, Any]]] = []
    for item in candidates:
        field_terms = item.get("terms") or set()
        if not terms or not field_terms:
            continue
        score = len(terms & field_terms) / max(1, len(terms | field_terms))
        if score >= 0.84:
            ranked.append((score, item))
    return sorted(ranked, key=lambda value: -value[0])[0][1] if ranked else None


def _role_relation(
    field: str,
    index: int,
    *,
    answer_kind: str,
) -> tuple[str, str]:
    if answer_kind == "why_supported" and field in {"principle", "relationship"}:
        return "support", "cause"
    if field in FIELD_ROLES:
        return FIELD_ROLES[field]
    if "limit" in field or "counterexample" in field:
        return "limit", "contrast"
    if "why" in field or "reason" in field:
        return "support", "cause"
    return ("answer", "sequence") if index == 0 else ("support", "support")


def _decompose_supported_clause(
    sentence: str,
    *,
    protected_terms: set[str] | None = None,
) -> dict[str, Any] | None:
    text = sentence.strip().rstrip(". ")
    protected_terms = protected_terms or set()
    if not text or "?" in text or ":" in text or ";" in text:
        return None
    if text.lower().startswith(("if ", "when ", "unless ", "because ", "although ")):
        return None

    modal = re.match(
        r"^(?P<subject>.+?)\s+(?P<modal>can|could|may|might|must|should|will|would)\s+"
        r"(?P<negative>not\s+)?(?P<predicate>[A-Za-z][A-Za-z'-]*)"
        r"(?:\s+(?P<object>.+))?$",
        text,
        flags=re.IGNORECASE,
    )
    if modal:
        predicate = _lemma(modal.group("predicate"))
        return {
            "subject": _surface_subject(modal.group("subject"), protected_terms),
            "subject_number": _subject_number(modal.group("subject")),
            "preserve_subject_case": _preserve_subject_case(modal.group("subject"), protected_terms),
            "predicate": predicate,
            "object": modal.group("object") or "",
            "modality": modal.group("modal").lower(),
            "polarity": "negative" if modal.group("negative") else "positive",
            "tense": "present",
            "mood": "declarative",
        }

    do_support = re.match(
        r"^(?P<subject>.+?)\s+(?P<aux>do|does|did)\s+(?P<negative>not\s+)?"
        r"(?P<predicate>[A-Za-z][A-Za-z'-]*)(?:\s+(?P<object>.+))?$",
        text,
        flags=re.IGNORECASE,
    )
    if do_support:
        return {
            "subject": _surface_subject(do_support.group("subject"), protected_terms),
            "subject_number": _subject_number(do_support.group("subject")),
            "preserve_subject_case": _preserve_subject_case(do_support.group("subject"), protected_terms),
            "predicate": _lemma(do_support.group("predicate")),
            "object": do_support.group("object") or "",
            "polarity": "negative" if do_support.group("negative") else "positive",
            "tense": "past" if do_support.group("aux").lower() == "did" else "present",
            "mood": "declarative",
        }

    copula = re.match(
        r"^(?P<subject>.+?)\s+(?P<copula>is|are|was|were)\s+"
        r"(?P<negative>not\s+)?(?P<object>.+)$",
        text,
        flags=re.IGNORECASE,
    )
    if copula:
        return {
            "subject": _surface_subject(copula.group("subject"), protected_terms),
            "subject_number": _subject_number(copula.group("subject")),
            "preserve_subject_case": _preserve_subject_case(copula.group("subject"), protected_terms),
            "predicate": "be",
            "object": copula.group("object"),
            "polarity": "negative" if copula.group("negative") else "positive",
            "tense": "past" if copula.group("copula").lower() in {"was", "were"} else "present",
            "mood": "declarative",
        }

    tokens = re.findall(r"[A-Za-z][A-Za-z'-]*|[^\s]+", text)
    verb_index = next(
        (index for index, token in enumerate(tokens) if token.lower() in VERB_FORMS),
        None,
    )
    if verb_index is None:
        first = tokens[0].lower() if tokens else ""
        if first in VERB_FORMS:
            verb_index = 0
        else:
            return None
    if verb_index == 0:
        return {
            "subject": "",
            "subject_number": "",
            "preserve_subject_case": False,
            "predicate": _lemma(tokens[0]),
            "object": " ".join(tokens[1:]),
            "polarity": "positive",
            "tense": "present",
            "mood": "imperative",
        }
    if verb_index < 1 or verb_index >= len(tokens):
        return None
    return {
        "subject": _surface_subject(" ".join(tokens[:verb_index]), protected_terms),
        "subject_number": _subject_number(" ".join(tokens[:verb_index])),
        "preserve_subject_case": _preserve_subject_case(
            " ".join(tokens[:verb_index]),
            protected_terms,
        ),
        "predicate": _lemma(tokens[verb_index]),
        "object": " ".join(tokens[verb_index + 1 :]),
        "polarity": "positive",
        "tense": "present",
        "mood": "declarative",
    }


def _lemma(value: str) -> str:
    lower = value.lower()
    return VERB_LEMMAS.get(lower, lower)


def _surface_subject(value: str, protected_terms: set[str]) -> str:
    subject = " ".join(str(value or "").split())
    if not subject:
        return ""
    first, *rest = subject.split(maxsplit=1)
    if (
        first == "I"
        or first.isupper()
        or first in protected_terms
        or first.lower() in {"a", "an", "the", "this", "that", "these", "those"}
    ):
        return subject
    lowered = first[:1].lower() + first[1:]
    return " ".join([lowered, *rest])


def _preserve_subject_case(value: str, protected_terms: set[str]) -> bool:
    first = str(value or "").split(maxsplit=1)[0] if str(value or "").strip() else ""
    return bool(first == "I" or first.isupper() or first in protected_terms)


def _subject_number(value: str) -> str:
    subject = " ".join(str(value or "").lower().split())
    if subject in {"we", "they", "you", "these", "those"}:
        return "plural"
    last = subject.split()[-1] if subject else ""
    if last.endswith("s") and not last.endswith(("ss", "us", "is")):
        return "plural"
    return "singular" if subject else ""


def _protected_terms(match: dict[str, Any] | None) -> set[str]:
    if not match:
        return set()
    title = str(match.get("title") or "")
    return {
        token
        for token in re.findall(r"\b[A-Z][A-Za-z0-9'-]*\b", title)
        if token.lower() not in {"a", "an", "the"}
    }


def _exactness_reason(sentence: str, *, quote_requested: bool) -> str:
    if quote_requested:
        return "attributed_exact_wording_requested"
    if re.search(r"`[^`]+`|https?://|\b(?:SELECT|INSERT|UPDATE|DELETE)\b", sentence):
        return "code_or_machine_readable_form"
    if re.search(r"(?:^|\s)[A-Za-z0-9_()]+\s*(?:==|!=|<=|>=|=|\+|\*|/)\s*[A-Za-z0-9_.()-]+", sentence):
        return "formula_or_notation"
    return ""


def _required_terms(sentence: str) -> list[str]:
    terms = re.findall(
        r"`[^`]+`|\b\d+(?:\.\d+)?(?:\s?(?:cm|mm|m|km|g|kg|ml|l|%))?\b|"
        r"\b[A-Z]{2,}[A-Z0-9-]*\b|[\"“][^\"”]+[\"”]",
        sentence,
    )
    lower = sentence.lower()
    if re.search(r"\b(?:not|never|cannot|can't|doesn't|isn't|aren't|without)\b", lower):
        terms.append("negation")
    return list(dict.fromkeys(term.strip() for term in terms if term.strip()))[:20]


def _meaning_keys(sentence: str, required_terms: list[str]) -> list[str]:
    content = [
        term
        for term in re.findall(r"[a-z0-9']+", sentence.lower())
        if len(term) > 2 and term not in {"and", "the", "that", "this", "with", "from", "into"}
    ]
    return list(dict.fromkeys([*content[:12], *[term.lower() for term in required_terms]]))[:20]


def _sentences(value: str) -> list[str]:
    return [
        truncate(" ".join(item.split()), 1200)
        for item in re.split(r"(?<=[.!?])\s+|\n+", value.strip())
        if item.strip()
    ][:16]


def _normalize(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value).lower()))


def _locked(result: dict[str, Any]) -> dict[str, Any]:
    return {
        **result,
        **GUARDS,
        "source_change_allowed": False,
        "certainty_change_allowed": False,
        "evidence_change_allowed": False,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": KNOWLEDGE_EXPRESSION_BOUNDARY,
    }
