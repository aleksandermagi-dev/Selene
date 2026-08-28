from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


CURRENT_TURN_FACT_LEDGER_BOUNDARY = (
    "visible_current_turn_fact_and_owner_input_coordination_only_no_truth_decision_"
    "memory_identity_personality_governance_authority_training_or_action"
)

FACT_KINDS = frozenset(
    {
        "entity",
        "quantity",
        "option",
        "criterion",
        "observation",
        "claim",
        "relation",
        "condition",
        "constraint",
        "correction",
        "sequence",
    }
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

_STOP = {
    "a", "about", "an", "and", "are", "as", "at", "be", "because", "but",
    "by", "can", "could", "did", "do", "does", "for", "from", "had", "has",
    "have", "how", "i", "if", "in", "is", "it", "me", "my", "of", "on",
    "or", "our", "please", "should", "so", "that", "the", "then", "there",
    "these", "this", "those", "to", "too", "us", "was", "we", "were", "what",
    "when", "where", "which", "who", "why", "will", "with", "would", "you",
    "your",
}

_REQUEST_START = re.compile(
    r"^(?:please\s+)?(?:ask|calculate|choose|compare|contrast|describe|explain|give|"
    r"identify|list|name|pick|plan|predict|recommend|say|show|state|summarize|tell|"
    r"what|when|where|which|who|why|how|do you|could you|can you|would you)\b",
    re.IGNORECASE,
)

_NUMBER = (
    r"(?:-?\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?|zero|one|two|three|four|five|six|"
    r"seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|"
    r"eighty|ninety|hundred)"
)

_OPERATION_FACT_KINDS: dict[str, set[str]] = {
    "comparison": {"entity", "option", "criterion", "observation", "relation", "quantity", "condition", "constraint"},
    "choice": {"entity", "option", "criterion", "observation", "relation", "quantity", "condition", "constraint"},
    "prediction": {"quantity", "observation", "relation", "condition", "claim"},
    "hypothesis": {"observation", "relation", "condition", "claim"},
    "disagreement": {"claim", "observation", "relation", "condition", "quantity"},
    "correction": {"correction", "claim", "relation", "quantity"},
    "reopening": {"correction", "claim", "relation", "quantity"},
    "method": {"constraint", "sequence", "criterion", "condition", "quantity", "observation", "relation"},
    "action_scope": {"constraint", "sequence", "criterion", "condition", "quantity", "observation", "relation"},
    "reason": {"observation", "relation", "condition", "claim"},
    "summary": set(FACT_KINDS),
    "session_summary": set(FACT_KINDS),
}


def current_turn_fact_ledger_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "current_turn_fact_ledger_ready",
            "version": "v1_typed_visible_turn_facts",
            "scope": "one_visible_current_turn_only",
            "fact_kinds": sorted(FACT_KINDS),
            "owner_inputs_are_answers": False,
            "user_statements_are_independently_verified": False,
            "current_turn_facts_precede_optional_retrieval": True,
            "review_status": "status_only",
            "provenance_boundary": CURRENT_TURN_FACT_LEDGER_BOUNDARY,
        }
    )


def build_current_turn_fact_ledger(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build typed, attributable facts and owner inputs from one visible turn.

    The ledger preserves what the speaker supplied. It does not decide whether
    a claim is true, solve an operation, retain a memory, or generate speech.
    """

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 4000).strip()
    if not prompt:
        raise ValueError("current-turn prompt is required")
    interpreted = truncate(str(payload.get("interpreted_text") or prompt), 4000).strip()
    session_id = int(payload.get("session_id") or 0)
    obligations = [
        dict(item)
        for item in payload.get("obligations") or []
        if isinstance(item, dict)
    ][:24]
    correction = (
        payload.get("correction_refinement")
        if isinstance(payload.get("correction_refinement"), dict)
        else {}
    )
    revision = (
        payload.get("epistemic_revision")
        if isinstance(payload.get("epistemic_revision"), dict)
        else {}
    )
    clauses = _clauses(interpreted)
    facts: list[dict[str, Any]] = []
    for clause_index, clause in enumerate(clauses):
        facts.extend(
            _facts_from_clause(
                clause,
                clause_index=clause_index,
                session_id=session_id,
                prompt=interpreted,
            )
        )
    facts.extend(
        _correction_facts(
            correction,
            revision,
            clause_index=len(clauses),
            session_id=session_id,
            prompt=interpreted,
        )
    )
    facts = _deduplicate(facts)[:64]
    facts = _bind_facts_to_obligations(facts, obligations)
    owner_inputs = [_owner_input(obligation, facts) for obligation in obligations]
    by_kind = {
        kind: [fact["id"] for fact in facts if fact.get("kind") == kind]
        for kind in sorted(FACT_KINDS)
        if any(fact.get("kind") == kind for fact in facts)
    }
    turn_key = sha256(f"{session_id}|{interpreted}".encode("utf-8")).hexdigest()[:16]
    return _with_guards(
        {
            "status": "current_turn_fact_ledger_ready",
            "version": "v1_typed_visible_turn_facts",
            "ledger_id": f"current-turn-facts-{turn_key}",
            "session_id": session_id,
            "literal_prompt": prompt,
            "interpreted_prompt": interpreted,
            "clauses": clauses,
            "facts": facts,
            "fact_count": len(facts),
            "facts_by_kind": by_kind,
            "owner_inputs": owner_inputs,
            "owner_input_count": len(owner_inputs),
            "current_turn_precedence": True,
            "facts_are_user_supplied_not_independently_verified": True,
            "facts_are_durable_memory": False,
            "owner_inputs_are_answers": False,
            "downstream_missing_input_must_account_for_supplied_fields": True,
            "review_status": "status_only",
            "provenance_boundary": CURRENT_TURN_FACT_LEDGER_BOUNDARY,
        }
    )


def owner_input_for_obligation(
    ledger: dict[str, Any] | None,
    obligation_id: str,
) -> dict[str, Any]:
    ledger = ledger if isinstance(ledger, dict) else {}
    return next(
        (
            dict(item)
            for item in ledger.get("owner_inputs") or []
            if isinstance(item, dict)
            and str(item.get("obligation_id") or "") == str(obligation_id or "")
        ),
        {},
    )


def _facts_from_clause(
    clause: str,
    *,
    clause_index: int,
    session_id: int,
    prompt: str,
) -> list[dict[str, Any]]:
    clean = truncate(" ".join(clause.split()), 1200).strip(" ,;:")
    lower = clean.lower().replace("’", "'")
    if not clean:
        return []
    facts: list[dict[str, Any]] = []

    for value, unit in re.findall(
        rf"\b({_NUMBER})\s*(%|percent|percentage|seconds?|minutes?|hours?|days?|"
        r"feet|foot|ft|inches?|meters?|kilometers?|miles?|grams?|kilograms?|"
        r"pounds?|lbs?|dollars?|cents?|volts?|amps?|watts?|degrees?)?\b",
        lower,
        flags=re.IGNORECASE,
    ):
        if not unit and value in {"one", "two", "three"} and not re.search(
            rf"\b{re.escape(value)}\s+(?:options?|choices?|items?|boxes?|hours?|minutes?|times?)\b",
            lower,
        ):
            continue
        facts.append(
            _fact(
                "quantity",
                clean,
                clause_index,
                session_id,
                prompt,
                value=value,
                unit=unit or "count",
            )
        )

    options = _options(clean)
    for option in options:
        facts.append(
            _fact(
                "option",
                option,
                clause_index,
                session_id,
                prompt,
                value=option,
            )
        )

    relation = re.match(
        r"^(?P<subject>(?:the\s+)?[A-Za-z0-9][A-Za-z0-9_' -]{0,70}?)\s+"
        r"(?P<predicate>is|are|was|were|has|have|costs?|weighs?|holds?|uses?|"
        r"contains?|dropped?|drops?|rose|rises?|changed?|stayed?|remained?)\s+"
        r"(?P<object>[^?]{1,220}?)(?:[.!]|$)",
        clean,
        flags=re.IGNORECASE,
    )
    if relation and not _REQUEST_START.match(clean):
        subject = relation.group("subject").strip()
        predicate = relation.group("predicate").strip()
        obj = relation.group("object").strip(" ,.;")
        facts.append(
            _fact(
                "relation",
                clean,
                clause_index,
                session_id,
                prompt,
                subject=subject,
                predicate=predicate,
                object=obj,
            )
        )
        facts.append(
            _fact(
                "entity",
                subject,
                clause_index,
                session_id,
                prompt,
                value=subject,
            )
        )

    criterion = ""
    criterion_match = re.search(
        r"\b(?P<criterion>[^.!?;]{2,140}?)\s+(?:matters?|counts?)\s+more\b|"
        r"\b(?:criterion|priority|deciding factor)\s+(?:is|will be|should be)\s+(?P<named>[^.!?;]{2,140})|"
        r"\bbecause\s+(?P<because>[^.!?;]{2,160})",
        clean,
        flags=re.IGNORECASE,
    )
    if criterion_match:
        criterion = next(
            (
                value.strip(" ,.;")
                for value in criterion_match.groupdict().values()
                if value
            ),
            "",
        )
    if criterion:
        facts.append(
            _fact(
                "criterion",
                criterion,
                clause_index,
                session_id,
                prompt,
                value=criterion,
            )
        )

    if re.search(r"\b(?:if|when|whenever|unless|provided that|given that)\b", lower):
        facts.append(_fact("condition", clean, clause_index, session_id, prompt))
    if re.search(
        r"\b(?:must|need to|needs to|only|cannot|can't|do not|don't|without|keep|"
        r"required?|limited to|at most|at least)\b",
        lower,
    ):
        facts.append(_fact("constraint", clean, clause_index, session_id, prompt))
    if re.search(r"\b(?:first|then|next|after that|return to|go back to|finally|last)\b", lower):
        facts.append(_fact("sequence", clean, clause_index, session_id, prompt))
    if re.search(r"\b(?:i noticed|i observed|i saw|we noticed|we observed|the data|the report|the result)\b", lower):
        facts.append(_fact("observation", clean, clause_index, session_id, prompt))
    elif not _REQUEST_START.match(clean) and relation:
        facts.append(_fact("observation", clean, clause_index, session_id, prompt))
    if re.search(r"\b(?:i think|i believe|my claim|the claim|according to|report says|report shows)\b", lower):
        facts.append(_fact("claim", clean, clause_index, session_id, prompt))
    return facts


def _correction_facts(
    correction: dict[str, Any],
    revision: dict[str, Any],
    *,
    clause_index: int,
    session_id: int,
    prompt: str,
) -> list[dict[str, Any]]:
    direct_match = re.search(
        r"\b(?:actually[, ]+)?(?:i\s+)?meant\s+(?P<corrected>.+?)\s*,?\s+not\s+"
        r"(?P<replaced>.+?)(?:[.!?]|$)",
        prompt,
        flags=re.IGNORECASE,
    )
    inverse_match = re.search(
        r"\bnot\s+(?P<replaced>.+?)[,;]\s*(?:but|rather)\s+"
        r"(?P<corrected>.+?)(?:[.!?]|$)",
        prompt,
        flags=re.IGNORECASE,
    )
    textual_match = direct_match or inverse_match
    detected = bool(
        correction.get("detected") is True
        or revision.get("detected") is True
        or textual_match
    )
    if not detected:
        return []
    corrected = truncate(
        str(
            correction.get("corrected_meaning")
            or revision.get("revised_claim")
            or (textual_match.group("corrected") if textual_match else "")
        ),
        800,
    ).strip(" ,.;")
    replaced = truncate(
        str(
            correction.get("replaced_meaning")
            or revision.get("prior_claim")
            or (textual_match.group("replaced") if textual_match else "")
        ),
        800,
    ).strip(" ,.;")
    text = corrected or truncate(str(correction.get("summary") or prompt), 800)
    return [
        _fact(
            "correction",
            text,
            clause_index,
            session_id,
            prompt,
            value=corrected,
            replaced_value=replaced,
        )
    ]


def _owner_input(
    obligation: dict[str, Any],
    facts: list[dict[str, Any]],
) -> dict[str, Any]:
    obligation_id = str(obligation.get("id") or "")
    bound = [
        fact for fact in facts if obligation_id in (fact.get("obligation_ids") or [])
    ]
    functions = [
        str(item).strip().lower()
        for item in obligation.get("requested_response_functions") or []
        if str(item).strip()
    ]
    values = lambda kind: [
        str(fact.get("value") or fact.get("text") or "")
        for fact in bound
        if fact.get("kind") == kind
        and str(fact.get("value") or fact.get("text") or "").strip()
    ]
    relation_subjects = [
        str(fact.get("subject") or "")
        for fact in bound
        if fact.get("kind") == "relation" and str(fact.get("subject") or "")
    ]
    explicit_options = _unique(values("option"))
    options = (
        explicit_options
        if len(explicit_options) >= 2
        else _unique([*explicit_options, *relation_subjects])
    )
    fields = {
        "entities": values("entity"),
        "quantities": [fact for fact in bound if fact.get("kind") == "quantity"],
        "options": options,
        "criteria": values("criterion"),
        "observations": values("observation"),
        "claims": values("claim"),
        "relations": [fact for fact in bound if fact.get("kind") == "relation"],
        "conditions": values("condition"),
        "constraints": values("constraint"),
        "corrections": [fact for fact in bound if fact.get("kind") == "correction"],
        "sequence": values("sequence"),
    }
    supplied = [key for key, value in fields.items() if value]
    return {
        "obligation_id": obligation_id,
        "answer_act": str(obligation.get("answer_act") or ""),
        "responsible_owner": str(obligation.get("responsible_owner") or ""),
        "requested_response_functions": functions,
        "fact_ids": [str(fact.get("id") or "") for fact in bound],
        "fact_count": len(bound),
        "supplied_fields": fields,
        "supplied_field_names": supplied,
        "has_current_turn_support": bool(bound),
        "missing_input_report_must_name_only_unsupplied_fields": True,
        "owner_must_consume_before_missing_input": True,
        "current_turn_precedence": True,
    }


def _bind_facts_to_obligations(
    facts: list[dict[str, Any]],
    obligations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for fact in facts:
        fact_terms = set(fact.get("terms") or [])
        bound: list[str] = []
        for obligation in obligations:
            obligation_id = str(obligation.get("id") or "")
            if not obligation_id:
                continue
            text = " ".join(
                str(value or "")
                for value in (
                    obligation.get("source_text"),
                    obligation.get("parent_source_text"),
                    obligation.get("topic"),
                )
            )
            obligation_terms = set(_terms(text))
            functions = {
                str(item).strip().lower()
                for item in obligation.get("requested_response_functions") or []
                if str(item).strip()
            }
            compatible_kinds = set().union(
                *(_OPERATION_FACT_KINDS.get(function, set()) for function in functions),
            ) if functions else set()
            if fact_terms & obligation_terms or str(fact.get("kind") or "") in compatible_kinds:
                bound.append(obligation_id)
        result.append({**fact, "obligation_ids": list(dict.fromkeys(bound))})
    return result


def _fact(
    kind: str,
    text: str,
    clause_index: int,
    session_id: int,
    prompt: str,
    **fields: Any,
) -> dict[str, Any]:
    normalized = " ".join(str(text or "").lower().split())
    distinguishing_fields = "|".join(
        " ".join(str(fields.get(name) or "").lower().split())
        for name in (
            "value",
            "unit",
            "subject",
            "predicate",
            "object",
            "replaced_value",
        )
    )
    identifier = sha256(
        f"{session_id}|{clause_index}|{kind}|{normalized}|{distinguishing_fields}".encode(
            "utf-8"
        )
    ).hexdigest()[:16]
    return {
        "id": f"current-turn-fact-{identifier}",
        "kind": kind if kind in FACT_KINDS else "observation",
        "text": truncate(str(text or ""), 1200),
        "clause_index": clause_index,
        "terms": _terms(str(text or "")),
        "source": "current_visible_user_turn",
        "source_ref": f"current_turn:{sha256(prompt.encode('utf-8')).hexdigest()[:12]}",
        "reported_not_independently_verified": True,
        "durable_memory": False,
        **fields,
    }


def _options(text: str) -> list[str]:
    patterns = (
        r"\b(?:choose|pick|decide)\s+between\s+(.{1,90}?)\s+and\s+(.{1,90}?)(?:[,.;?]|$)",
        r"\b(?:compare|contrast)\s+(.{1,90}?)\s+(?:and|with|versus|vs\.?)\s+(.{1,90}?)(?:[,.;?]|$)",
        r"\bwhich(?:\s+would\s+you\s+(?:choose|pick|prefer))?[, :]?\s*(.{1,70}?)\s+or\s+(.{1,70}?)(?:[,.;?]|$)",
        r"\b(?:options?|choices?)\s+(?:are|include)\s+(.{1,90}?)\s+(?:and|or)\s+(.{1,90}?)(?:[,.;?]|$)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        return _unique([_clean_option(match.group(1)), _clean_option(match.group(2))])
    return []


def _clean_option(value: str) -> str:
    value = re.sub(r"^(?:the|a|an)\s+", "", value.strip(" ,.;:?"), flags=re.IGNORECASE)
    value = re.split(r"\b(?:and then|then|because|so that|while)\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    value = re.sub(
        r"\s+(?:as|in)\s+(?:a\s+)?(?:venn\s+diagram|table|list|chart|matrix)$",
        "",
        value,
        flags=re.IGNORECASE,
    )
    return truncate(value.strip(" ,.;:?"), 140)


def _clauses(text: str) -> list[str]:
    clauses: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+|;\s*", text.strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        pieces = re.split(
            r",\s+(?=(?:and\s+)?(?:ask|calculate|choose|compare|contrast|explain|"
            r"give|identify|pick|plan|predict|recommend|show|state|summarize|tell|"
            r"what|which|why|how)\b)",
            sentence,
            flags=re.IGNORECASE,
        )
        clauses.extend(piece.strip(" ,") for piece in pieces if piece.strip(" ,"))
    return clauses[:32]


def _terms(value: str) -> list[str]:
    return list(
        dict.fromkeys(
            item
            for item in re.findall(r"[a-z0-9][a-z0-9_'/-]{1,}", value.lower())
            if item not in _STOP
        )
    )[:40]


def _deduplicate(facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for fact in facts:
        key = (
            str(fact.get("kind") or ""),
            " ".join(str(fact.get("text") or "").lower().split()),
            str(fact.get("value") or "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(fact)
    return result


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = str(value or "").strip()
        key = " ".join(clean.casefold().split())
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(clean)
    return result[:12]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
