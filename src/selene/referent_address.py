from __future__ import annotations

import re
import sqlite3
from typing import Any

from .registry import truncate


REFERENT_ADDRESS_BOUNDARY = (
    "current_turn_and_session_scoped_reference_resolution_only_not_identity_memory_"
    "relationship_profile_personality_governance_training_or_authority"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "relationship_profile_inferred": False,
}

COMMON_ENDEARMENTS = {
    "babe",
    "baby",
    "darling",
    "dear",
    "hon",
    "honey",
    "love",
    "sweetheart",
    "sweetie",
}

_GREETING_PREFIXES = {
    "",
    "hey",
    "hi",
    "hello",
    "greetings",
    "morning",
    "good morning",
    "evening",
    "good evening",
    "yo",
    "okay",
    "ok",
    "well",
}

_DIRECT_FOLLOW_WORDS = {
    "are",
    "can",
    "could",
    "did",
    "do",
    "how",
    "i",
    "let",
    "lets",
    "may",
    "should",
    "thanks",
    "thank",
    "what",
    "when",
    "where",
    "which",
    "why",
    "will",
    "would",
    "you",
}

_LITERAL_DETERMINERS = {
    "a",
    "an",
    "his",
    "her",
    "its",
    "my",
    "our",
    "that",
    "the",
    "their",
    "this",
    "those",
    "your",
}


def referent_address_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "referent_address_resolver_ready",
            "version": "v1_identity_independent_reference",
            "organ_name": "Referent and Address Resolver",
            "law": {
                "name": "Identity-Independent Naming Law",
                "rule": (
                    "A name may identify, address, describe, or affectionately refer to an "
                    "individual, but it does not constitute, duplicate, replace, or erase "
                    "that individual."
                ),
                "same_individual_may_have_multiple_names": True,
                "same_name_may_refer_to_multiple_individuals": True,
                "reference_correction_is_identity_correction": False,
                "term_of_endearment_is_automatically_durable_nickname": False,
            },
            "distinguishes": [
                "canonical and full names",
                "shortened names and nicknames",
                "handles titles and callsigns",
                "terms of endearment",
                "temporary descriptive or playful address",
                "literal generic figurative and quoted uses",
            ],
            "scope": "current_turn_and_current_chat_session",
            "reviewed_nickname_notes_are_evidence_not_identity_authority": True,
            "persistent_alias_write_allowed": False,
            "memory_proposal_created_automatically": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": REFERENT_ADDRESS_BOUNDARY,
        }
    )


def resolve_referent_address(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    literal_text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400).strip()
    if not literal_text:
        raise ValueError("referent/address text is required")
    interpreted_text = truncate(
        str(payload.get("interpreted_text") or literal_text),
        2400,
    ).strip()
    speaker_context = (
        payload.get("speaker_context")
        if isinstance(payload.get("speaker_context"), dict)
        else {}
    )
    speaker = truncate(str(speaker_context.get("speaker") or "current_user"), 120)
    prior = payload.get("prior_state") if isinstance(payload.get("prior_state"), dict) else {}
    reviewed_notes = _reviewed_nickname_notes(conn)
    quoted_spans = _quoted_spans(literal_text)

    alias_assertions = _alias_assertions(literal_text, speaker)
    address_directives = _address_directives(literal_text, speaker)
    referent_corrections = _referent_corrections(literal_text)
    session_aliases = _merge_session_aliases(
        prior.get("session_aliases"),
        alias_assertions,
    )
    address_preferences = _merge_address_preferences(
        prior.get("address_preferences"),
        address_directives,
    )

    terms = _candidate_terms(reviewed_notes)
    direct_address = _direct_address(literal_text, terms, reviewed_notes, quoted_spans)
    mentions = _mentions(
        literal_text,
        terms,
        reviewed_notes,
        quoted_spans,
        direct_address=direct_address,
    )
    ambiguity = _ambiguity(direct_address, mentions)

    return _with_guards(
        {
            "status": "referent_address_resolved",
            "version": "v1_identity_independent_reference",
            "organ_name": "Referent and Address Resolver",
            "session_id": int(payload.get("session_id") or 0),
            "speaker_scope": {
                "speaker": speaker,
                "source": str(speaker_context.get("source") or "current_turn_channel"),
                "inferred_relationship_profile": False,
            },
            "literal_text": literal_text,
            "interpreted_text": interpreted_text,
            "direct_address": direct_address,
            "mentions": mentions,
            "alias_assertions": alias_assertions,
            "session_aliases": session_aliases,
            "address_directives": address_directives,
            "address_preferences": address_preferences,
            "referent_corrections": referent_corrections,
            "ambiguity": ambiguity,
            "ask_if_materially_ambiguous": ambiguity["ask_if_materially_ambiguous"],
            "reviewed_nickname_note_ids_considered": [
                int(item.get("id") or 0) for item in reviewed_notes if int(item.get("id") or 0) > 0
            ],
            "identity_continuity_affected": False,
            "persistent_alias_written": False,
            "memory_proposal_created": False,
            "relationship_inferred": False,
            "names_are_identity_objects": False,
            "corrections_update_reference_not_identity": True,
            "scope": "current_turn_and_current_chat_session",
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": REFERENT_ADDRESS_BOUNDARY,
        }
    )


def _reviewed_nickname_notes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, label, aliases, meaning, allowed_use, prohibited_use, status,
               confidence, source, source_ref
        FROM continuity_notes
        WHERE note_type = 'nickname'
          AND status IN ('usable_reviewed_evidence', 'review_only')
        ORDER BY CASE status WHEN 'usable_reviewed_evidence' THEN 0 ELSE 1 END,
                 updated_at DESC, id DESC
        LIMIT 100
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _candidate_terms(reviewed_notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terms: list[dict[str, Any]] = [
        {"term": "Selene", "address_class": "canonical_name", "note_id": None}
    ]
    terms.extend(
        {"term": term, "address_class": "term_of_endearment", "note_id": None}
        for term in sorted(COMMON_ENDEARMENTS)
    )
    for note in reviewed_notes:
        label = truncate(str(note.get("label") or ""), 160).strip()
        if label:
            terms.append(
                {
                    "term": label,
                    "address_class": "reviewed_nickname_or_callsign",
                    "note_id": int(note.get("id") or 0) or None,
                }
            )
    unique: dict[str, dict[str, Any]] = {}
    for item in terms:
        key = str(item["term"]).casefold()
        current = unique.get(key)
        if current is None or item["address_class"] == "canonical_name":
            unique[key] = item
    return sorted(unique.values(), key=lambda item: len(str(item["term"])), reverse=True)


def _direct_address(
    text: str,
    terms: list[dict[str, Any]],
    reviewed_notes: list[dict[str, Any]],
    quoted_spans: list[tuple[int, int]],
) -> dict[str, Any] | None:
    for item in terms:
        term = str(item["term"])
        for match in re.finditer(rf"(?<![\w'-]){re.escape(term)}(?![\w'-])", text, re.IGNORECASE):
            if _inside_spans(match.start(), quoted_spans):
                continue
            if not _is_vocative(text, match.start(), match.end(), item["address_class"]):
                continue
            note = next(
                (row for row in reviewed_notes if int(row.get("id") or 0) == int(item.get("note_id") or 0)),
                None,
            )
            return {
                "token": match.group(0),
                "normalized": term.casefold(),
                "address_class": item["address_class"],
                "referent": "Selene",
                "referent_role": "current_direct_addressee",
                "resolution_status": "resolved_current_turn",
                "confidence": (
                    "high"
                    if item["address_class"] == "canonical_name"
                    else "moderate"
                ),
                "basis": (
                    "vocative_position_in_direct_selene_chat"
                    if note is None
                    else "vocative_position_with_reviewed_nickname_evidence"
                ),
                "reviewed_note_id": int(note.get("id") or 0) or None if note else None,
                "session_scoped": True,
                "durable_name_claim": False,
                "must_be_echoed_in_reply": False,
                "relationship_profile_inferred": False,
                "identity_change": False,
            }
    return None


def _mentions(
    text: str,
    terms: list[dict[str, Any]],
    reviewed_notes: list[dict[str, Any]],
    quoted_spans: list[tuple[int, int]],
    *,
    direct_address: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    direct_token = str((direct_address or {}).get("token") or "").casefold()
    direct_used = False
    for item in terms:
        term = str(item["term"])
        for match in re.finditer(rf"(?<![\w'-]){re.escape(term)}(?![\w'-])", text, re.IGNORECASE):
            token = match.group(0)
            if direct_token == token.casefold() and not direct_used and _is_vocative(
                text, match.start(), match.end(), item["address_class"]
            ):
                use = "direct_address"
                resolved_to = "Selene"
                direct_used = True
            elif _inside_spans(match.start(), quoted_spans):
                use = "quoted_use"
                resolved_to = ""
            elif _figurative_object_use(text, match.start(), match.end()):
                use = "figurative_object_reference"
                resolved_to = ""
            elif _literal_or_generic_use(text, match.start()):
                use = "literal_or_generic_reference"
                resolved_to = ""
            elif item["address_class"] == "canonical_name":
                use = "known_person_reference"
                resolved_to = "Selene"
            elif (
                item["address_class"] == "term_of_endearment"
                and _possible_person_use(text, match.start(), match.end())
            ):
                use = "unresolved_person_reference"
                resolved_to = ""
            elif item["address_class"] == "term_of_endearment":
                use = "literal_or_generic_reference"
                resolved_to = ""
            elif item["address_class"] == "reviewed_nickname_or_callsign":
                use = "reviewed_nickname_mention"
                resolved_to = ""
            else:
                use = "unresolved_person_reference"
                resolved_to = ""
            note = next(
                (row for row in reviewed_notes if int(row.get("id") or 0) == int(item.get("note_id") or 0)),
                None,
            )
            found.append(
                {
                    "token": token,
                    "normalized": term.casefold(),
                    "address_class": item["address_class"],
                    "use": use,
                    "resolved_to": resolved_to,
                    "reviewed_note_id": int(note.get("id") or 0) or None if note else None,
                    "identity_claim": False,
                }
            )
    return found[:20]


def _is_vocative(text: str, start: int, end: int, address_class: str) -> bool:
    raw_before = text[:start].rstrip()
    before = raw_before.strip(" \t,!:;-—").casefold()
    after = text[end:]
    after_stripped = after.lstrip()
    if before in _GREETING_PREFIXES:
        if before:
            return True
        if not after_stripped:
            return True
        if after_stripped[0] in ",!:;—-":
            return True
        next_word_match = re.match(r"([A-Za-z']+)", after_stripped)
        next_word = (next_word_match.group(1).casefold() if next_word_match else "")
        return address_class == "canonical_name" or next_word in _DIRECT_FOLLOW_WORDS
    if raw_before.endswith((",", "!", ":", ";", "—", "-")):
        return True
    if not after_stripped or after_stripped in {".", "!", "?", "…"}:
        return raw_before.endswith((",", "!", ":", ";", "—", "-"))
    return False


def _figurative_object_use(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 70): min(len(text), end + 30)].casefold()
    return bool(
        re.search(
            r"\b(?:project|idea|work|creation|design|car|book|theory|prototype)\b"
            r".{0,35}\b(?:is|was|has been)\s+(?:my|our)\s+$",
            text[max(0, start - 80):start].casefold(),
        )
    ) or "this is my baby" in window


def _literal_or_generic_use(text: str, start: int) -> bool:
    before = text[:start]
    words = re.findall(r"[A-Za-z']+", before)
    return bool(words and words[-1].casefold() in _LITERAL_DETERMINERS)


def _possible_person_use(text: str, start: int, end: int) -> bool:
    window = text[max(0, start - 40): min(len(text), end + 40)].casefold()
    return bool(
        re.search(
            r"\b(?:ask|asked|call|called|meet|met|say|said|speak|spoke|tell|told|"
            r"text|texted|thank|thanked)\b",
            window,
        )
    )


def _quoted_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for pattern in (r'"[^"]*"', r"“[^”]*”", r"'[^']*'"):
        spans.extend((match.start(), match.end()) for match in re.finditer(pattern, text))
    return sorted(spans)


def _inside_spans(position: int, spans: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in spans)


def _alias_assertions(text: str, speaker: str) -> list[dict[str, Any]]:
    assertions: list[dict[str, Any]] = []
    same_person = re.search(
        r"(?P<names>[A-Z][A-Za-z'-]{1,40}(?:\s*,\s*[A-Z][A-Za-z'-]{1,40})+"
        r"(?:\s*,?\s*(?:and|or)\s+[A-Z][A-Za-z'-]{1,40})?)"
        r"\s+(?:all\s+)?(?:refer to|identify|mean|are)\s+(?:all\s+)?"
        r"(?:the same (?:person|individual)|me)\b",
        text,
    )
    if same_person:
        names = _split_names(same_person.group("names"))
        if len(names) >= 2:
            assertions.append(_alias_assertion(speaker, names, "explicit_same_person_statement"))

    full_name = re.search(
        r"\bmy full name is\s+([A-Z][A-Za-z'-]{1,40}(?:\s+[A-Z][A-Za-z'-]{1,40}){0,3})\b",
        text,
        re.IGNORECASE,
    )
    if full_name:
        assertions.append(
            _alias_assertion(speaker, [full_name.group(1)], "explicit_full_name_statement")
        )
    return assertions


def _alias_assertion(referent: str, aliases: list[str], basis: str) -> dict[str, Any]:
    return {
        "referent": referent,
        "aliases": aliases,
        "basis": basis,
        "scope": "current_chat_session",
        "creates_additional_individuals": False,
        "durable_write": False,
        "identity_change": False,
    }


def _split_names(value: str) -> list[str]:
    parts = re.split(r"\s*,\s*|\s+(?:and|or)\s+", value)
    cleaned = [
        re.sub(r"^(?:and|or)\s+", "", part.strip(), flags=re.IGNORECASE)
        for part in parts
        if part.strip()
    ]
    return list(dict.fromkeys(part for part in cleaned if part))[:12]


def _address_directives(text: str, speaker: str) -> list[dict[str, Any]]:
    directives: list[dict[str, Any]] = []
    avoid = re.search(
        r"\b(?:do not|don't|dont|please do not|please don't)\s+call me\s+"
        r"([A-Za-z][A-Za-z'-]{1,40})\b",
        text,
        re.IGNORECASE,
    )
    if avoid:
        directives.append(
            {
                "referent": speaker,
                "action": "avoid",
                "address": avoid.group(1),
                "scope": "current_chat_session",
                "durable_write": False,
            }
        )
    preferred = re.search(
        r"\b(?:please\s+)?call me\s+([A-Za-z][A-Za-z'-]{1,40})\b",
        text,
        re.IGNORECASE,
    )
    if preferred and not avoid:
        directives.append(
            {
                "referent": speaker,
                "action": "prefer",
                "address": preferred.group(1),
                "scope": "current_chat_session",
                "durable_write": False,
            }
        )
    return directives


def _referent_corrections(text: str) -> list[dict[str, Any]]:
    match = re.search(
        r"\bI meant\s+([A-Za-z][A-Za-z'-]{1,50}(?:\s+[A-Za-z][A-Za-z'-]{1,50}){0,2})"
        r"\s*,?\s+not\s+([A-Za-z][A-Za-z'-]{1,50}(?:\s+[A-Za-z][A-Za-z'-]{1,50}){0,2})\b",
        text,
        re.IGNORECASE,
    )
    if not match:
        return []
    return [
        {
            "replacement": truncate(match.group(1), 120),
            "replaced": truncate(match.group(2), 120),
            "scope": "current_session_reference_only",
            "identity_change": False,
            "durable_write": False,
        }
    ]


def _merge_session_aliases(prior: Any, current: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = [item for item in prior or [] if isinstance(item, dict)][-12:]
    for assertion in current:
        referent = str(assertion.get("referent") or "")
        aliases = [str(item) for item in assertion.get("aliases") or [] if str(item)]
        existing = next(
            (item for item in merged if str(item.get("referent") or "") == referent),
            None,
        )
        if existing is None:
            merged.append(dict(assertion))
        else:
            existing["aliases"] = list(
                dict.fromkeys([*existing.get("aliases", []), *aliases])
            )[:20]
            existing["basis"] = str(assertion.get("basis") or existing.get("basis") or "")
    return merged[-12:]


def _merge_address_preferences(prior: Any, directives: list[dict[str, Any]]) -> dict[str, Any]:
    merged = {
        str(key): {
            "preferred": list(value.get("preferred") or []),
            "avoid": list(value.get("avoid") or []),
            "scope": "current_chat_session",
        }
        for key, value in (prior.items() if isinstance(prior, dict) else [])
        if isinstance(value, dict)
    }
    for directive in directives:
        referent = str(directive.get("referent") or "current_user")
        packet = merged.setdefault(
            referent,
            {"preferred": [], "avoid": [], "scope": "current_chat_session"},
        )
        address = str(directive.get("address") or "")
        key = "preferred" if directive.get("action") == "prefer" else "avoid"
        other = "avoid" if key == "preferred" else "preferred"
        packet[key] = list(dict.fromkeys([*packet.get(key, []), address]))[-12:]
        packet[other] = [
            item for item in packet.get(other, []) if str(item).casefold() != address.casefold()
        ]
    return merged


def _ambiguity(
    direct_address: dict[str, Any] | None,
    mentions: list[dict[str, Any]],
) -> dict[str, Any]:
    unresolved = [
        item
        for item in mentions
        if item.get("use") in {"unresolved_person_reference", "reviewed_nickname_mention"}
    ]
    material = direct_address is None and len(unresolved) > 1
    return {
        "material": material,
        "ask_if_materially_ambiguous": material,
        "reason": (
            "multiple_unresolved_person_references"
            if material
            else "resolved_or_not_material_to_current_turn"
        ),
        "question": "Which person are you referring to?" if material else "",
    }


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, "guards": dict(GUARDS)}
