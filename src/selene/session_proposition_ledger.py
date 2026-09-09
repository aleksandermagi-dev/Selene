from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


SESSION_PROPOSITION_BOUNDARY = (
    "visible_current_session_proposition_dependencies_and_revision_ancestry_only_no_"
    "hidden_reasoning_memory_identity_personality_governance_authority_training_or_action"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
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
    "hidden_chain_of_thought_exposed": False,
    "expression_authority": False,
}

_ACTIVE_STATES = {"active", "provisional_visible", "recomputed"}
_STALE_STATES = {"invalidated", "superseded"}


def session_proposition_ledger_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "session_proposition_ledger_ready",
            "version": "v2_active_structured_propositions",
            "is_organ": False,
            "owner": "Dialogue Workspace",
            "scope": "visible_current_session_only",
            "records": [
                "visible propositions",
                "typed visible current-turn facts and requested operations",
                "declared or typed dependencies",
                "selective invalidation",
                "recomputation receipts",
                "revision ancestry",
            ],
            "generates_answers": False,
            "automatic_retention": False,
            "ordinary_wrongness_is_failure": False,
            "review_status": "status_only",
            "provenance_boundary": SESSION_PROPOSITION_BOUNDARY,
        }
    )


def coordinate_session_revision_completion(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select one typed owner result for an active session revision.

    This coordinator does not generate a replacement answer. It proves that a
    current owner recomputed the changed result from the active revision before
    that result can be presented as correction completion.
    """

    payload = payload or {}
    ledger = _normalize_ledger(
        payload.get("session_proposition_ledger"),
        session_id=int(payload.get("session_id") or 0),
    )
    revision = _dict(ledger.get("current_revision"))
    recomputation = _dict(ledger.get("recomputation"))
    state = str(recomputation.get("state") or "not_required")
    pending = state in {"required", "held_pending_owner_result"}
    candidates = [
        item for item in payload.get("owner_candidates") or [] if isinstance(item, dict)
    ][:8]
    inspected: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    revision_id = str(recomputation.get("revision_id") or revision.get("revision_id") or "")
    corrected_text = str(revision.get("corrected_text") or "").strip()
    for candidate in candidates:
        source_id = str(candidate.get("source_id") or candidate.get("owner_id") or "")
        text = truncate(str(candidate.get("response_seed") or candidate.get("text") or ""), 5000).strip()
        operations = {
            str(item).strip().lower()
            for item in candidate.get("supported_operations") or []
            if str(item).strip()
        }
        candidate_revision_id = str(candidate.get("revision_id") or "")
        consumed_revision_text = truncate(
            str(candidate.get("consumed_revision_text") or ""), 1200
        ).strip()
        general_owner = candidate.get("legacy_fixture_compatibility") is not True
        typed_owner_result = candidate.get("typed_owner_result") is True
        responsible_owner = candidate.get("responsible_owner") is True
        current_turn_inputs_accounted_for = (
            candidate.get("current_turn_inputs_accounted_for") is True
        )
        matches_revision = bool(revision_id and candidate_revision_id == revision_id)
        revision_input_accounted_for = _revision_input_accounted_for(
            corrected_text,
            consumed_revision_text,
            text,
        )
        accepted = bool(
            pending
            and source_id
            and text
            and "correction" in operations
            and general_owner
            and typed_owner_result
            and responsible_owner
            and current_turn_inputs_accounted_for
            and matches_revision
            and revision_input_accounted_for
        )
        receipt = {
            "source_id": source_id,
            "has_visible_result": bool(text),
            "supported_operations": sorted(operations),
            "general_owner": general_owner,
            "typed_owner_result": typed_owner_result,
            "responsible_owner": responsible_owner,
            "current_turn_inputs_accounted_for": current_turn_inputs_accounted_for,
            "matches_active_revision": matches_revision,
            "consumed_revision_text": consumed_revision_text,
            "revision_input_accounted_for": revision_input_accounted_for,
            "accepted": accepted,
        }
        inspected.append(receipt)
        if accepted:
            eligible.append({**candidate, "_text": text, "_receipt": receipt})

    selected = eligible[0] if eligible else {}
    if not pending:
        status = "session_revision_completion_not_required"
        reason = "no dependent current-session result is awaiting recomputation"
    elif selected:
        status = "session_revision_owner_result_ready"
        reason = "one responsible owner recomputed the active revision"
    else:
        status = "session_revision_owner_result_held"
        reason = "no typed owner result recomputed the active revision"
    return _with_guards(
        {
            "status": status,
            "version": "v1_typed_revision_owner_completion",
            "pending": pending,
            "revision_id": revision_id,
            "recomputation_state": state,
            "selected_owner_id": str(
                selected.get("source_id") or selected.get("owner_id") or ""
            ),
            "response_seed": str(selected.get("_text") or ""),
            "owner_result_ready": bool(selected),
            "candidate_receipts": inspected,
            "reason": reason,
            "maximum_owner_recompute_passes": 1,
            "previous_answer_replay_is_recomputation": False,
            "legacy_fixture_is_general_completion_evidence": False,
            "ordinary_wrongness_is_failure": False,
            "generates_answers": False,
            "current_session_only": True,
            "review_status": "status_only",
            "provenance_boundary": SESSION_PROPOSITION_BOUNDARY,
        }
    )


def prepare_session_proposition_revision(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply one correction to a visible current-session dependency graph.

    The ledger coordinates revision; it does not decide truth or produce the
    corrected answer. A downstream owner must still recompute and visibly
    realize any affected result.
    """

    payload = payload or {}
    session_id = int(payload.get("session_id") or 0)
    prior = _normalize_ledger(payload.get("prior_ledger"), session_id=session_id)
    correction = _dict(payload.get("correction_refinement"))
    revision = _dict(payload.get("epistemic_revision_plan"))
    detected = correction.get("detected") is True or revision.get("detected") is True
    if not detected:
        prior_recomputation = _dict(prior.get("recomputation"))
        unresolved_state = str(prior_recomputation.get("state") or "")
        if payload.get("topic_transition") is True and unresolved_state in {
            "required",
            "held_pending_owner_result",
            "held_target_not_found",
            "held_missing_corrected_input",
        }:
            return _finalize(
                prior,
                status="session_proposition_revision_expired_to_ancestry",
                revision_event={},
                recomputation={
                    **prior_recomputation,
                    "state": "expired_on_topic_transition",
                    "reason": (
                        "a real topic transition ended the active correction posture; "
                        "revision ancestry remains inspectable"
                    ),
                    "preserved_across_turn": False,
                    "eligible_current_turn": False,
                },
            )
        if unresolved_state in {
            "required",
            "held_pending_owner_result",
            "held_target_not_found",
            "held_missing_corrected_input",
        }:
            return _finalize(
                prior,
                status="session_proposition_revision_held",
                revision_event=_dict(prior.get("current_revision")),
                recomputation={
                    **prior_recomputation,
                    "state": (
                        "held_pending_owner_result"
                        if unresolved_state == "required"
                        else unresolved_state
                    ),
                    "reason": str(
                        prior_recomputation.get("reason")
                        or "the current-session correction remains held for its responsible owner"
                    ),
                    "preserved_across_turn": True,
                },
            )
        return _finalize(
            prior,
            status="session_proposition_ledger_ready",
            revision_event={},
            recomputation={
                "state": "not_required",
                "reason": "no current-session correction is active",
                "affected_proposition_ids": [],
                "invalidated_result_ids": [],
                "preserved_proposition_ids": _active_ids(prior["propositions"]),
            },
        )

    corrected = truncate(
        str(correction.get("corrected_meaning") or revision.get("revised_claim") or ""),
        1200,
    ).strip()
    replaced = truncate(
        str(correction.get("replaced_meaning") or revision.get("prior_claim") or ""),
        1200,
    ).strip()
    target = truncate(str(revision.get("target") or replaced or ""), 800).strip()
    explicit_ids = {
        str(item)
        for item in payload.get("affected_proposition_ids") or []
        if str(item)
    }
    propositions = [dict(item) for item in prior["propositions"]]
    active = [item for item in propositions if str(item.get("status") or "") in _ACTIVE_STATES]
    matched = [item for item in active if str(item.get("id") or "") in explicit_ids]
    if not matched:
        matched = _match_targets(
            active,
            replaced=replaced,
            target=target,
            prefer_visible_basis=bool(
                correction.get("replacement_pair_extracted") is True
                or (corrected and replaced)
            ),
        )

    # Older sessions may predate the ledger. Preserve the visible prior claim
    # as ancestry so the first correction after an upgrade is still inspectable.
    if not matched and not active and (replaced or revision.get("prior_claim")):
        prior_text = replaced or str(revision.get("prior_claim") or "")
        synthetic = _proposition(
            text=prior_text,
            kind="premise",
            status="active",
            session_id=session_id,
            source="visible_prior_claim_from_revision",
            turn_id=str(payload.get("turn_id") or ""),
            thread_id=str(payload.get("thread_id") or ""),
            source_refs=_texts((revision.get("evidence") or {}).get("source_refs")),
        )
        propositions.append(synthetic)
        matched = [synthetic]

    event_id = _identifier(
        "session_revision",
        str(session_id),
        corrected,
        replaced,
        target,
        str(len(prior.get("revision_history") or [])),
    )
    matched_ids = {str(item.get("id") or "") for item in matched}
    descendant_ids = _descendants(propositions, matched_ids)
    affected_ids = matched_ids | descendant_ids
    invalidated_result_ids: list[str] = []
    superseded_ids: list[str] = []

    for item in propositions:
        proposition_id = str(item.get("id") or "")
        if proposition_id not in affected_ids:
            continue
        is_root = proposition_id in matched_ids
        kind = str(item.get("kind") or "result")
        if is_root and kind in {"premise", "observation", "source_statement"}:
            item["status"] = "superseded"
            item["superseded_by_revision_id"] = event_id
            superseded_ids.append(proposition_id)
        else:
            item["status"] = "invalidated"
            item["invalidated_by_revision_id"] = event_id
            invalidated_result_ids.append(proposition_id)

    revised_proposition: dict[str, Any] = {}
    if corrected and matched:
        revised_proposition = _proposition(
            text=corrected,
            kind="premise",
            status="active",
            session_id=session_id,
            source="current_session_correction",
            turn_id=str(payload.get("turn_id") or ""),
            thread_id=str(payload.get("thread_id") or _first_thread(matched)),
            source_refs=_texts((revision.get("evidence") or {}).get("source_refs")),
            replaces=sorted(matched_ids),
        )
        propositions.append(revised_proposition)
        for item in propositions:
            if str(item.get("id") or "") in matched_ids:
                item["replaced_by_proposition_id"] = revised_proposition["id"]

    if not matched:
        recomputation_state = "held_target_not_found"
        hold_reason = "the correction could not be bound to a visible current-session proposition"
    elif not corrected:
        recomputation_state = "held_missing_corrected_input"
        hold_reason = "the affected proposition is known but the corrected premise is not"
    elif invalidated_result_ids:
        recomputation_state = "required"
        hold_reason = "a responsible answer owner must recompute the invalidated dependent result"
    else:
        recomputation_state = "premise_revised_no_dependent_result"
        hold_reason = "the premise changed but no recorded dependent result requires recomputation"

    preserved_ids = [
        str(item.get("id") or "")
        for item in propositions
        if str(item.get("status") or "") in _ACTIVE_STATES
        and str(item.get("id") or "") != str(revised_proposition.get("id") or "")
    ]
    revision_event = {
        "revision_id": event_id,
        "kind": str(revision.get("update_kind") or "correction"),
        "corrected_text": corrected,
        "replaced_text": replaced,
        "target": target,
        "matched_proposition_ids": sorted(matched_ids),
        "invalidated_proposition_ids": sorted(affected_ids),
        "superseded_proposition_ids": sorted(superseded_ids),
        "revised_proposition_id": str(revised_proposition.get("id") or ""),
        "unaffected_context_preserved": True,
        "ordinary_wrongness_is_failure": False,
    }
    history = [
        item for item in prior.get("revision_history") or [] if isinstance(item, dict)
    ][-23:]
    history.append(revision_event)
    return _finalize(
        {**prior, "propositions": _bounded_propositions(propositions), "revision_history": history},
        status=(
            "session_proposition_revision_prepared"
            if recomputation_state in {"required", "premise_revised_no_dependent_result"}
            else "session_proposition_revision_held"
        ),
        revision_event=revision_event,
        recomputation={
            "state": recomputation_state,
            "reason": hold_reason,
            "revision_id": event_id,
            "affected_proposition_ids": sorted(affected_ids),
            "invalidated_result_ids": sorted(invalidated_result_ids),
            "revised_proposition_id": str(revised_proposition.get("id") or ""),
            "preserved_proposition_ids": preserved_ids,
            "maximum_owner_recompute_passes": 1,
            "owner_result_received": False,
            "visible_recomputation_received": False,
        },
    )


def record_visible_session_propositions(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record visible typed results and complete a pending recomputation once."""

    payload = payload or {}
    session_id = int(payload.get("session_id") or 0)
    ledger = _normalize_ledger(payload.get("ledger"), session_id=session_id)
    propositions = [dict(item) for item in ledger["propositions"]]
    turn_id = str(payload.get("turn_id") or "")
    thread_id = str(payload.get("thread_id") or "")
    candidate = truncate(str(payload.get("candidate_text") or ""), 5000).strip()
    operations = _dict(payload.get("answer_operations"))
    revision_completion = _dict(payload.get("session_revision_completion"))
    coverage = _dict(payload.get("coverage_evaluation"))
    completed = [
        item
        for item in operations.get("results") or []
        if isinstance(item, dict) and item.get("status") == "completed"
    ]
    current_fact_ids = _merge_current_turn_fact_propositions(
        propositions,
        _dict(payload.get("current_turn_fact_ledger")),
        session_id=session_id,
        turn_id=turn_id,
        thread_id=thread_id,
    )
    claim_ids = _merge_claim_propositions(
        propositions,
        _dict(payload.get("claim_evidence_packet")),
        session_id=session_id,
        turn_id=turn_id,
        thread_id=thread_id,
    )
    current_basis_ids = list(dict.fromkeys([*current_fact_ids, *claim_ids]))

    recomputation = dict(ledger.get("recomputation") or {})
    correction_result = next(
        (item for item in completed if str(item.get("operation") or "") == "correction"),
        {},
    )
    legacy_compatibility_result = bool(
        correction_result.get("legacy_fixture_compatibility") is True
    )
    visible_complete = bool(candidate and coverage.get("all_required_addressed") is True)
    typed_revision_owner_ready = bool(
        revision_completion.get("pending") is not True
        or revision_completion.get("owner_result_ready") is True
    )
    if recomputation.get("state") == "required":
        if correction_result and visible_complete and (
            typed_revision_owner_ready or legacy_compatibility_result
        ):
            revised_id = str(recomputation.get("revised_proposition_id") or "")
            recomputed = _proposition(
                text=candidate,
                kind="result",
                status="recomputed",
                session_id=session_id,
                source="visible_corrected_response",
                turn_id=turn_id,
                thread_id=thread_id,
                source_refs=_texts(correction_result.get("source_refs")),
                depends_on=[revised_id] if revised_id else current_basis_ids,
                recomputed_from=_texts(recomputation.get("invalidated_result_ids")),
            )
            propositions.append(recomputed)
            recomputation = {
                **recomputation,
                "state": "completed",
                "reason": (
                    "a historical compatibility result was visibly realized for this exact case without proving general revision capability"
                    if legacy_compatibility_result and not typed_revision_owner_ready
                    else "the responsible owner result was visibly realized once"
                ),
                "owner_result_received": True,
                "visible_recomputation_received": True,
                "recomputed_proposition_id": recomputed["id"],
                "general_capability_evidence_eligible": bool(
                    typed_revision_owner_ready and not legacy_compatibility_result
                ),
                "legacy_fixture_compatibility_used": legacy_compatibility_result,
            }
        else:
            recomputation = {
                **recomputation,
                "state": "held_pending_owner_result",
                "reason": (
                    "the visible correction result did not prove that its owner consumed the active revised premise"
                    if revision_completion.get("pending") is True
                    and revision_completion.get("owner_result_ready") is not True
                    else "the corrected result was not visibly completed by its responsible owner"
                ),
                "owner_result_received": bool(correction_result),
                "visible_recomputation_received": visible_complete,
                "typed_revision_owner_ready": typed_revision_owner_ready,
            }

    if candidate and not (correction_result and recomputation.get("state") == "completed"):
        landmarks = [
            item for item in payload.get("response_landmarks") or [] if isinstance(item, dict)
        ]
        if not landmarks:
            landmarks = [{"summary": candidate, "kind": "result", "id": ""}]
        for landmark in landmarks[:10]:
            text = truncate(str(landmark.get("summary") or ""), 1200).strip()
            if not text:
                continue
            propositions.append(
                _proposition(
                    text=text,
                    kind="result",
                    status=("active" if coverage.get("all_required_addressed") is True else "provisional_visible"),
                    session_id=session_id,
                    source="visible_selene_response",
                    turn_id=turn_id,
                    thread_id=str(landmark.get("thread_id") or thread_id),
                    source_refs=_operation_source_refs(completed),
                    depends_on=current_basis_ids,
                    landmark_id=str(landmark.get("id") or ""),
                )
            )

    return _finalize(
        {**ledger, "propositions": _bounded_propositions(propositions)},
        status="session_proposition_response_recorded",
        revision_event=_dict(ledger.get("current_revision")),
        recomputation=recomputation,
    )


def active_proposition_ids(ledger: dict[str, Any] | None) -> set[str]:
    return {
        str(item.get("id") or "")
        for item in _dict(ledger).get("propositions") or []
        if isinstance(item, dict) and str(item.get("status") or "") in _ACTIVE_STATES
    }


def stale_proposition_ids(ledger: dict[str, Any] | None) -> set[str]:
    return {
        str(item.get("id") or "")
        for item in _dict(ledger).get("propositions") or []
        if isinstance(item, dict) and str(item.get("status") or "") in _STALE_STATES
    }


def _normalize_ledger(value: Any, *, session_id: int) -> dict[str, Any]:
    supplied = _dict(value)
    return {
        "status": str(supplied.get("status") or "session_proposition_ledger_empty"),
        "version": "v2_active_structured_propositions",
        "session_id": int(supplied.get("session_id") or session_id),
        "propositions": [
            dict(item) for item in supplied.get("propositions") or [] if isinstance(item, dict)
        ][-96:],
        "revision_history": [
            dict(item) for item in supplied.get("revision_history") or [] if isinstance(item, dict)
        ][-24:],
        "current_revision": _dict(supplied.get("current_revision")),
        "recomputation": _dict(supplied.get("recomputation")),
    }


def _match_targets(
    propositions: list[dict[str, Any]],
    *,
    replaced: str,
    target: str,
    prefer_visible_basis: bool = False,
) -> list[dict[str, Any]]:
    needles = [value for value in (replaced, target) if value and value != "the affected claim"]
    if not needles:
        return []
    ranked: list[tuple[int, int, int, dict[str, Any]]] = []
    for index, item in enumerate(propositions):
        text = str(item.get("text") or "")
        score = max((_text_match_score(text, needle) for needle in needles), default=0)
        if score:
            basis_priority = int(
                prefer_visible_basis
                and str(item.get("kind") or "")
                in {
                    "premise", "observation", "source_statement", "claim",
                    "relation", "condition", "constraint", "correction",
                }
            )
            ranked.append((score, basis_priority, index, item))
    if not ranked:
        return []
    best = max((score, basis_priority) for score, basis_priority, _, _ in ranked)
    # Prefer the most recent equally strong visible target. A correction should
    # not silently rewrite every earlier mention of the same word.
    return [
        max(
            (entry for entry in ranked if entry[:2] == best),
            key=lambda entry: entry[2],
        )[3]
    ]


def _text_match_score(text: str, needle: str) -> int:
    haystack = _normalize(text)
    wanted = _normalize(needle)
    if not haystack or not wanted:
        return 0
    if wanted == haystack:
        return 100
    if wanted in haystack:
        return 80
    terms = set(wanted.split())
    overlap = len(terms & set(haystack.split()))
    return int(60 * overlap / max(1, len(terms))) if overlap else 0


def _revision_input_accounted_for(
    corrected_text: str,
    consumed_text: str,
    response_text: str,
) -> bool:
    """Require the owner result to consume content from the revised premise."""

    stop = {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "for",
        "from", "has", "have", "i", "in", "is", "it", "most", "not", "of",
        "on", "or", "still", "that", "the", "this", "to", "we", "what",
        "which", "with", "you", "your", "actually", "correction", "small",
    }

    def terms(value: str) -> set[str]:
        return {
            item
            for item in re.findall(r"[a-z0-9][a-z0-9'-]*", _normalize(value))
            if len(item) >= 3 and item not in stop
        }

    corrected_terms = terms(corrected_text)
    consumed_terms = terms(consumed_text)
    response_terms = terms(response_text)
    if not corrected_terms or not consumed_terms or not response_terms:
        return False
    shared = corrected_terms & consumed_terms
    required_shared = 1 if min(len(corrected_terms), len(consumed_terms)) == 1 else 2
    if len(shared) < required_shared:
        return False
    consumed_coverage = len(shared) / len(consumed_terms)
    visible_coverage = len(consumed_terms & response_terms) / len(consumed_terms)
    return consumed_coverage >= 0.5 and visible_coverage >= 0.5


def _descendants(propositions: list[dict[str, Any]], roots: set[str]) -> set[str]:
    found: set[str] = set()
    frontier = set(roots)
    while frontier:
        next_frontier: set[str] = set()
        for item in propositions:
            proposition_id = str(item.get("id") or "")
            dependencies = {str(value) for value in item.get("depends_on") or [] if str(value)}
            if proposition_id and proposition_id not in roots | found and dependencies & frontier:
                found.add(proposition_id)
                next_frontier.add(proposition_id)
        frontier = next_frontier
    return found


def _merge_claim_propositions(
    propositions: list[dict[str, Any]],
    packet: dict[str, Any],
    *,
    session_id: int,
    turn_id: str,
    thread_id: str,
) -> list[str]:
    claims = [item for item in packet.get("claims") or [] if isinstance(item, dict)]
    id_map: dict[str, str] = {}
    created: list[dict[str, Any]] = []
    for claim in claims[:30]:
        original_id = str(claim.get("claim_id") or "")
        proposition = _proposition(
            text=str(claim.get("text") or ""),
            kind=str(claim.get("claim_type") or "premise"),
            status="active",
            session_id=session_id,
            source="claim_evidence_packet",
            turn_id=turn_id,
            thread_id=thread_id,
            source_refs=_texts(claim.get("source_refs")),
        )
        id_map[original_id] = proposition["id"]
        proposition["claim_id"] = original_id
        proposition["validity"] = str(claim.get("validity") or "")
        created.append(proposition)
    for proposition, claim in zip(created, claims):
        proposition["depends_on"] = [
            id_map[value]
            for value in _texts(claim.get("basis_claim_ids"))
            if value in id_map
        ]
    propositions.extend(created)
    return [item["id"] for item in created]


def _merge_current_turn_fact_propositions(
    propositions: list[dict[str, Any]],
    ledger: dict[str, Any],
    *,
    session_id: int,
    turn_id: str,
    thread_id: str,
) -> list[str]:
    """Carry visible user-supplied structures into this session, never Memory."""

    facts = [item for item in ledger.get("facts") or [] if isinstance(item, dict)][:64]
    active_ids: list[str] = []
    for fact in facts:
        text = truncate(str(fact.get("text") or fact.get("value") or ""), 1600).strip()
        if not text:
            continue
        fact_key = _structured_fact_key(fact)
        existing = next(
            (
                item
                for item in reversed(propositions)
                if str(item.get("status") or "") in _ACTIVE_STATES
                and str(item.get("structured_fact_key") or "") == fact_key
            ),
            {},
        )
        if existing:
            active_ids.append(str(existing.get("id") or ""))
            continue

        replacement_key = str(fact.get("replacement_key") or "").strip()
        replaced = [
            item
            for item in propositions
            if replacement_key
            and str(item.get("status") or "") in _ACTIVE_STATES
            and str(item.get("replacement_key") or "") == replacement_key
        ]
        replaced_ids = {str(item.get("id") or "") for item in replaced if item.get("id")}
        proposition = _proposition(
            text=text,
            kind=str(fact.get("kind") or "observation"),
            status="active",
            session_id=session_id,
            source="current_visible_user_turn",
            turn_id=turn_id,
            thread_id=thread_id,
            source_refs=_texts(fact.get("source_ref")),
            replaces=sorted(replaced_ids),
            fact_id=str(fact.get("id") or ""),
            structured_fact_key=fact_key,
            replacement_key=replacement_key,
            subject=str(fact.get("subject") or ""),
            predicate=str(fact.get("predicate") or fact.get("action") or ""),
            object=str(fact.get("object") or ""),
            value=str(fact.get("value") or ""),
            relation_type=str(fact.get("relation_type") or ""),
            operation_status=str(fact.get("operation_status") or ""),
            reported_not_independently_verified=(
                fact.get("reported_not_independently_verified") is True
            ),
        )
        propositions.append(proposition)
        active_ids.append(proposition["id"])

        if replaced_ids:
            descendant_ids = _descendants(propositions, replaced_ids)
            for item in propositions:
                proposition_id = str(item.get("id") or "")
                if proposition_id in replaced_ids:
                    item["status"] = "superseded"
                    item["replaced_by_proposition_id"] = proposition["id"]
                elif proposition_id in descendant_ids:
                    item["status"] = "invalidated"
                    item["invalidated_by_proposition_id"] = proposition["id"]
    return [item for item in dict.fromkeys(active_ids) if item]


def _structured_fact_key(fact: dict[str, Any]) -> str:
    fields = [
        str(fact.get("kind") or "observation"),
        str(fact.get("subject") or ""),
        str(fact.get("predicate") or fact.get("action") or ""),
        str(fact.get("object") or ""),
        str(fact.get("value") or ""),
        str(fact.get("unit") or ""),
        str(fact.get("text") or ""),
    ]
    return "|".join(_normalize(item) for item in fields)


def _proposition(
    *,
    text: str,
    kind: str,
    status: str,
    session_id: int,
    source: str,
    turn_id: str,
    thread_id: str,
    source_refs: list[str] | None = None,
    depends_on: list[str] | None = None,
    replaces: list[str] | None = None,
    recomputed_from: list[str] | None = None,
    landmark_id: str = "",
    **metadata: Any,
) -> dict[str, Any]:
    clean = truncate(str(text or ""), 1600).strip()
    proposition_id = _identifier(
        "session_prop", str(session_id), kind, clean, turn_id, source, landmark_id
    )
    return {
        "id": proposition_id,
        "kind": kind or "result",
        "text": clean,
        "status": status,
        "depends_on": list(dict.fromkeys(depends_on or [])),
        "replaces": list(dict.fromkeys(replaces or [])),
        "recomputed_from": list(dict.fromkeys(recomputed_from or [])),
        "source": source,
        "source_refs": list(dict.fromkeys(source_refs or [])),
        "turn_id": turn_id,
        "thread_id": thread_id,
        "landmark_id": landmark_id,
        "scope": "current_session_only",
        "durable_memory_write": False,
        **metadata,
    }


def _bounded_propositions(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for item in values:
        proposition_id = str(item.get("id") or "")
        if not proposition_id:
            continue
        if proposition_id not in merged:
            order.append(proposition_id)
        merged[proposition_id] = item
    records = [merged[item] for item in order]
    active = [item for item in records if str(item.get("status") or "") in _ACTIVE_STATES]
    stale = [item for item in records if str(item.get("status") or "") in _STALE_STATES]
    # Keep current active state plus bounded revision ancestry.
    return [*stale[-32:], *active[-64:]][-96:]


def _finalize(
    ledger: dict[str, Any],
    *,
    status: str,
    revision_event: dict[str, Any],
    recomputation: dict[str, Any],
) -> dict[str, Any]:
    propositions = [item for item in ledger.get("propositions") or [] if isinstance(item, dict)]
    active = [item for item in propositions if str(item.get("status") or "") in _ACTIVE_STATES]
    stale = [item for item in propositions if str(item.get("status") or "") in _STALE_STATES]
    edges = [
        {"from": dependency, "to": str(item.get("id") or ""), "relation": "supports"}
        for item in propositions
        for dependency in item.get("depends_on") or []
        if dependency and item.get("id")
    ]
    return _with_guards(
        {
            **ledger,
            "status": status,
            "version": "v2_active_structured_propositions",
            "propositions": propositions,
            "dependency_edges": edges,
            "active_proposition_ids": [str(item.get("id") or "") for item in active],
            "stale_proposition_ids": [str(item.get("id") or "") for item in stale],
            "active_propositions": active,
            "current_revision": revision_event,
            "recomputation": recomputation,
            "unaffected_context_preserved": True,
            "stale_propositions_eligible_for_grounding": False,
            "ordinary_wrongness_is_failure": False,
            "generates_answers": False,
            "session_scoped_only": True,
            "review_status": "status_only",
            "provenance_boundary": SESSION_PROPOSITION_BOUNDARY,
        }
    )


def _active_ids(propositions: list[dict[str, Any]]) -> list[str]:
    return [
        str(item.get("id") or "")
        for item in propositions
        if str(item.get("status") or "") in _ACTIVE_STATES
    ]


def _operation_source_refs(results: list[dict[str, Any]]) -> list[str]:
    return list(
        dict.fromkeys(
            ref
            for item in results
            for ref in _texts(item.get("source_refs"))
        )
    )[:40]


def _first_thread(items: list[dict[str, Any]]) -> str:
    return next((str(item.get("thread_id") or "") for item in items if item.get("thread_id")), "")


def _identifier(prefix: str, *parts: str) -> str:
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _normalize(value: str) -> str:
    return " ".join(str(value or "").lower().replace("’", "'").split())


def _texts(value: Any) -> list[str]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = []
    return list(dict.fromkeys(truncate(str(item), 500) for item in values if str(item).strip()))


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
