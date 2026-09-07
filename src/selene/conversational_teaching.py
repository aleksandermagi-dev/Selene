from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .comprehension_integration import propose_comprehension_concept
from .registry import truncate
from .teaching_lifecycle import (
    acquire_teaching_item,
    approve_teaching_lifecycle,
    express_teaching_item,
    integrate_teaching_item,
)


CONVERSATIONAL_TEACHING_BOUNDARY = (
    "explicit_session_teaching_intent_to_existing_comprehension_lifecycle_only_"
    "not_ordinary_chat_memory_identity_governance_personality_training_or_authority"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "identity_change": False,
    "governance_change": False,
    "personality_change": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "ordinary_conversation_is_teaching": False,
    "lea_replaced": False,
}

GAP_PREEMPTING_RESPONSE_SOURCES = {
    "approved_comprehension",
    "attributable_dream_reflection",
    "conversation_policy",
    "conversational_memory_action",
    "conversational_teaching",
    "core_mind_boundary",
    "current_session_facts",
    "contextual_approved_memory",
    "contextual_follow_up",
    "epistemic_revision",
    "explicit_humor_request",
    "explicit_session_alias",
    "figurative_meaning_clarification",
    "grounded_self_state",
    "mixed_conversation_answer",
    "ordinary_uncertainty",
    "reviewed_memory",
}

_EXPLICIT_TEACHING_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "let_me_teach_you",
        re.compile(
            r"^\s*let\s+me\s+teach\s+you(?:\s+something)?\s*[:;,\-]?\s*(?P<claim>.+)$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "want_you_to_learn",
        re.compile(
            r"^\s*(?:here(?:'s|\s+is)\s+something\s+)?i\s+want\s+you\s+to\s+learn"
            r"(?:\s+this|\s+that)?\s*[:;,\-]?\s*(?P<claim>.+)$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "here_is_something_to_learn",
        re.compile(
            r"^\s*here(?:'s|\s+is)\s+something\s+(?:i\s+want\s+you\s+to\s+learn|"
            r"for\s+you\s+to\s+learn)\s*[:;,\-]?\s*(?P<claim>.+)$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "the_answer_is",
        re.compile(
            r"^\s*the\s+answer\s+is\s*[:;,\-]?\s*(?P<claim>.+)$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "works_like_this",
        re.compile(
            r"^\s*actually\s*[,;:]?\s*(?P<claim>.+?\bworks\s+like\s+this\b(?:\s*[:;,\-]\s*|\s+).+)$",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
)

_YES = {
    "yes", "yeah", "yep", "yup", "sure", "okay", "ok", "absolutely",
    "go ahead", "please do", "i can", "i will", "of course",
}
_NO = {
    "no", "nope", "nah", "not now", "maybe later", "i'd rather not",
    "id rather not", "do not", "don't", "dont",
}

_TIME_SENSITIVE = (
    "today", "tonight", "tomorrow", "yesterday", "right now", "currently",
    "current price", "latest", "live score", "weather", "forecast", "president",
    "prime minister", "ceo", "exchange rate", "stock price",
)
_HIGH_STAKES = (
    "diagnosis", "diagnose", "medication", "dosage", "dose", "treatment",
    "legal advice", "lawsuit", "contract is legal", "investment advice", "buy this stock",
    "suicide", "self harm", "self-harm", "bomb", "weapon", "poison",
)
_PROTECTED_DOMAINS = (
    "selene is", "selene's identity", "selene's personality", "change your identity",
    "change your personality", "governing law", "governance", "vys", "autonomy",
    "permission boundary", "remember this", "memory", "self replicate", "self-replicate",
    "model training", "fine tune", "fine-tune", "lora",
)
_PERSONAL_SOURCE = re.compile(
    r"^\s*(?:i|i'm|i am|i've|i have|my|mine|we|we're|we are|our|ours)\b",
    re.IGNORECASE,
)
_QUESTION_WORDS = re.compile(r"\b(?:what|why|how|when|where|who|which|can|could|would|should|is|are|do|does|did)\b", re.IGNORECASE)
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9'\-]*")


def conversational_teaching_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "conversational_teaching_bridge_ready",
            "activation_modes": [
                "explicit_teaching_cue",
                "answer_to_immediately_pending_teaching_invitation",
            ],
            "ordinary_chat_activates_teaching": False,
            "small_bounded_knowledge_only": True,
            "deep_teaching_path": "Learning Evidence Activities and full Cocoon review remain available",
            "retention_path": "Comprehension -> Acquire -> Integrate -> Express -> explicit Aleks item approval",
            "yes_no_handoff_supported": True,
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": CONVERSATIONAL_TEACHING_BOUNDARY,
        }
    )


def plan_conversational_teaching_turn(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400).strip()
    session_id = int(payload.get("session_id") or 0)
    speaker = payload.get("speaker_envelope") if isinstance(payload.get("speaker_envelope"), dict) else {}
    diagnostic_only = payload.get("diagnostic_only") is True
    hard_boundary = payload.get("hard_boundary") is True
    prior = _latest_assistant_question_handoff(conn, session_id)
    answer_kind = _brief_answer_kind(text)
    base = {
        "status": "conversational_teaching_not_activated",
        "action": "none",
        "session_id": session_id,
        "explicit_activation": False,
        "activation_cue": "",
        "teaching_claim": "",
        "prior_question_handoff": prior,
        "assistant_question_response": {},
        "response_seed": "",
        "diagnostic_only": diagnostic_only,
        "hard_boundary": hard_boundary,
    }
    if not text or session_id <= 0:
        return _with_guards({**base, "reason": "text_and_session_required"})
    if diagnostic_only:
        return _with_guards({**base, "reason": "diagnostic_non_attribution_law"})
    if hard_boundary:
        return _with_guards({**base, "reason": "hard_boundary"})

    prior_kind = str(prior.get("question_kind") or "")
    if prior_kind == "teaching_invitation":
        if answer_kind == "negative":
            return _with_guards(
                {
                    **base,
                    "status": "conversational_teaching_invitation_declined",
                    "action": "decline_teaching_invitation",
                    "explicit_activation": True,
                    "activation_cue": "answer_to_pending_teaching_invitation",
                    "response_seed": "Okay. We can leave that gap open for now—no pressure.",
                    "assistant_question_response": _question_response(prior, "negative", text),
                }
            )
        if answer_kind == "affirmative" and _brief_answer_only(text):
            return _with_guards(
                {
                    **base,
                    "status": "conversational_teaching_invitation_accepted",
                    "action": "await_teaching_content",
                    "explicit_activation": True,
                    "activation_cue": "answer_to_pending_teaching_invitation",
                    "response_seed": _teaching_prompt(prior),
                    "outgoing_question_handoff": {**prior, "status": "awaiting_teaching_content"},
                    "assistant_question_response": _question_response(prior, "affirmative", text),
                }
            )
        leading_acceptance = _leading_acceptance_present(text)
        claim = _strip_leading_acceptance(text)
        explicit_cue, explicit_claim = _explicit_teaching_claim(claim)
        if explicit_claim:
            claim = explicit_claim
        if claim and not _brief_answer_only(claim) and (leading_acceptance or explicit_cue):
            claim = _bind_answer_to_pending_question(claim, prior)
            return _planned_claim(base, claim, explicit_cue or "pending_teaching_invitation", prior, speaker)

    cue, claim = _explicit_teaching_claim(text)
    if cue:
        claim = _bind_answer_to_pending_question(claim, prior)
        return _planned_claim(base, claim, cue, prior, speaker)

    if prior and answer_kind in {"affirmative", "negative"}:
        response = _question_response(prior, answer_kind, text)
        if response:
            return _with_guards(
                {
                    **base,
                    "status": "assistant_question_answer_received",
                    "action": "answer_assistant_question",
                    "assistant_question_response": response,
                    "response_seed": str(response.get("response_seed") or ""),
                    "reason": "session_scoped_answer_to_selene_question",
                }
            )
    if prior_kind == "reason_question" and text and answer_kind == "expanded":
        response = _question_response(prior, "stated_reason", text)
        return _with_guards(
            {
                **base,
                "status": "assistant_reason_answer_received",
                "action": "answer_assistant_question",
                "assistant_question_response": response,
                "response_seed": str(response.get("response_seed") or ""),
                "reason": "user_stated_reason_is_received_not_overruled",
            }
        )
    return _with_guards({**base, "reason": "no_explicit_teaching_activation"})


def apply_conversational_teaching(
    conn: sqlite3.Connection,
    plan: dict[str, Any],
) -> dict[str, Any]:
    if str(plan.get("action") or "") != "learn_bounded_claim":
        return _with_guards(
            {
                **plan,
                "knowledge_activated": False,
                "knowledge_write_occurred": False,
            }
        )
    eligibility = plan.get("eligibility") if isinstance(plan.get("eligibility"), dict) else {}
    if eligibility.get("eligible") is not True:
        return _with_guards(
            {
                **plan,
                "status": "conversational_teaching_held_for_deeper_review",
                "action": "hold_for_deeper_review",
                "knowledge_activated": False,
                "knowledge_write_occurred": False,
                "response_seed": _held_response(eligibility),
                "review_destination": "Cocoon Teaching / Lessons",
                "review_status": "needs_context",
            }
        )

    claim = str(plan.get("teaching_claim") or "").strip()
    session_id = int(plan.get("session_id") or 0)
    cue = str(plan.get("activation_cue") or "explicit_teaching_cue")
    prior = plan.get("prior_question_handoff") if isinstance(plan.get("prior_question_handoff"), dict) else {}
    receipt = _micro_understanding_receipt(claim, prior)
    concept_key = f"conversational_teaching:{sha256(_normalized_claim(claim).encode('utf-8')).hexdigest()[:20]}"
    source_refs = [
        f"selene_chat_session:{session_id}:conversational_teaching",
        f"conversational_teaching_claim:{sha256(claim.encode('utf-8')).hexdigest()[:20]}",
        "speaker:Aleks",
    ]
    proposed = propose_comprehension_concept(
        conn,
        {
            "concept_key": concept_key,
            "title": receipt["title"],
            "domain": "conversational_teaching.general_knowledge",
            "material": claim,
            "relationships": [receipt["relationship"]],
            "counterexamples": [receipt["counterexample"]],
            "limits": [receipt["limit"]],
            "source_refs": source_refs,
            "confidence": "bounded",
            "teaching_source_type": "explicit_aleks_conversational_teaching",
            "knowledge_class": "reviewed_general_knowledge_candidate",
            "freshness_class": "durable_source_bounded",
            "source_roles": [
                {
                    "role": "source_statement",
                    "content_fields": ["material"],
                    "source_refs": source_refs,
                },
                {
                    "role": "inference",
                    "content_fields": ["relationships", "limits", "counterexamples"],
                    "source_refs": source_refs,
                },
            ],
            "instructional_why": receipt["instructional_why"],
            "source_metadata": {
                "origin_session_id": session_id,
                "activation_cue": cue,
                "explicit_aleks_teaching_instruction": True,
                "conversational_micro_teaching": True,
                "source_statement_is_not_automatic_universal_truth": True,
                "deeper_lea_still_available": True,
            },
        },
    )
    concept = proposed.get("item") if isinstance(proposed.get("item"), dict) else {}
    concept_id = int(concept.get("id") or 0)
    if concept.get("state") == "approved_knowledge_resource":
        return _with_guards(
            {
                **plan,
                "status": "conversational_teaching_already_learned",
                "action": "already_learned",
                "concept_id": concept_id,
                "concept_key": concept_key,
                "knowledge_activated": True,
                "knowledge_write_occurred": False,
                "response_seed": "I already have that connection, and I can keep using it normally.",
                "review_destination": "Status",
                "review_status": "status_only",
            }
        )

    try:
        acquire = acquire_teaching_item(
            conn,
            {
                "concept_id": concept_id,
                "concepts": [claim],
                "vocabulary": receipt["vocabulary"],
                "relationships": [receipt["relationship"]],
                "examples": [receipt["application"]],
                "uncertainties": [receipt["limit"]],
                "near_concept_distinctions": [receipt["distinction"]],
                "source_roles": concept.get("payload", {}).get("source_role_receipt", {}),
                "declared_effects": ["subject_knowledge", "concept_vocabulary"],
            },
        )
        integrate = integrate_teaching_item(
            conn,
            {
                "concept_id": concept_id,
                "contradiction_classification": "none_identified",
                "integration_confidence": "bounded",
                "scope_of_application": receipt["scope"],
                "unresolved_questions": [receipt["unresolved"]],
                "correction_path": "Use a later explicit correction or stronger attributed evidence to reopen this conversational teaching item.",
                "reopening_path": "Reopen when a contradiction, correction, failed application, or changed scope appears.",
                "instructional_why": receipt["instructional_why"],
                "declared_effects": ["subject_knowledge", "reasoning_method"],
            },
        )
        express = express_teaching_item(
            conn,
            {
                "concept_id": concept_id,
                "explanation": receipt["teach_back"],
                "distinct_examples": [receipt["application"]],
                "analogies": [receipt["analogy"]],
                "questions": [receipt["learning_question"]],
                "comparisons": [receipt["comparison"]],
                "conversational_participation": receipt["participation"],
                "limits": [receipt["limit"]],
                "counterexamples": [receipt["counterexample"]],
                "correction_response": "I would acknowledge the correction, preserve the earlier source as ancestry, and update the affected relationship rather than defend it.",
                "source_alignment": True,
                "declared_effects": ["subject_knowledge", "explanation_and_example_range"],
            },
        )
        approval = approve_teaching_lifecycle(
            conn,
            {
                "concept_id": concept_id,
                "aleks_approved": True,
                "approval_actor": "Aleks",
            },
        )
    except (ValueError, sqlite3.DatabaseError) as exc:
        return _with_guards(
            {
                **plan,
                "status": "conversational_teaching_needs_more_context",
                "action": "candidate_created_needs_context",
                "concept_id": concept_id,
                "concept_key": concept_key,
                "knowledge_activated": False,
                "knowledge_write_occurred": True,
                "reason": truncate(str(exc), 500),
                "response_seed": "I have the teaching point, but I need one more pass before I can honestly say I understand it well enough to use normally. We can deepen it together.",
                "review_destination": "Cocoon Teaching / Lessons",
                "review_status": "needs_context",
            }
        )

    active = bool(
        approval.get("stage_complete") is True
        and (approval.get("snapshot") or {}).get("knowledge_resource_active") is True
    )
    return _with_guards(
        {
            **plan,
            "status": "conversational_teaching_integrated" if active else "conversational_teaching_needs_more_context",
            "action": "knowledge_integrated" if active else "candidate_created_needs_context",
            "concept_id": concept_id,
            "concept_key": concept_key,
            "lifecycle_id": int((approval.get("item") or {}).get("id") or 0) or None,
            "stage_receipts": {
                "acquire": acquire.get("status"),
                "integrate": integrate.get("status"),
                "express": express.get("status"),
                "approval": approval.get("status"),
            },
            "knowledge_activated": active,
            "knowledge_write_occurred": True,
            "explicit_aleks_approval": True,
            "response_seed": (
                f"Got it. My understanding is that {receipt['spoken_understanding']}. I can use that now, and I'll reopen it if a correction or new evidence changes the fit."
                if active
                else "I have the teaching point, but it still needs more context before I can use it as learned knowledge."
            ),
            "review_destination": "Status" if active else "Cocoon Teaching / Lessons",
            "review_status": "aleks_retention_decision" if active else "needs_context",
        }
    )


def build_learning_gap_invitation(
    prompt: str,
    intelligence_support: dict[str, Any] | None,
    *,
    knowledge_context: dict[str, Any] | None = None,
    current_turn_response: dict[str, Any] | None = None,
    speaker_envelope: dict[str, Any] | None = None,
    diagnostic_only: bool = False,
    hard_boundary: bool = False,
    teaching_turn: dict[str, Any] | None = None,
) -> dict[str, Any]:
    support = intelligence_support if isinstance(intelligence_support, dict) else {}
    substance = (
        support.get("answer_substance")
        if isinstance(support.get("answer_substance"), dict)
        else support.get("prompt_grounded_preview")
        if isinstance(support.get("prompt_grounded_preview"), dict)
        else {}
    )
    answer_kind = str(substance.get("answer_kind") or "")
    original = truncate(str(substance.get("answer") or support.get("best_current_answer") or ""), 1800).strip()
    speaker = speaker_envelope if isinstance(speaker_envelope, dict) else {}
    teaching = teaching_turn if isinstance(teaching_turn, dict) else {}
    knowledge = knowledge_context if isinstance(knowledge_context, dict) else {}
    current_response = (
        current_turn_response if isinstance(current_turn_response, dict) else {}
    )
    response_source = str(current_response.get("selected_source_id") or "")
    response_text = str(current_response.get("content_seed") or "").strip()
    current_owner_already_answered = bool(
        current_response.get("release_allowed") is True
        and response_text
        and response_source in GAP_PREEMPTING_RESPONSE_SOURCES
    )
    eligible = bool(
        not diagnostic_only
        and not hard_boundary
        and str(teaching.get("action") or "none") == "none"
        and not current_owner_already_answered
        and knowledge.get("answer_eligible") is not True
        and not knowledge.get("answer_eligible_items")
        and answer_kind in {"unsupported_fact", "bounded_knowledge_gap", "source_needed", "causal_evidence_needed"}
        and "?" in str(prompt or "")
        and _speaker_may_authorize_conversational_teaching(speaker)
        and not _sensitive_markers(prompt)
        and len(re.findall(r"\?", str(prompt or ""))) == 1
    )
    if not eligible:
        return _with_guards(
            {
                "status": "learning_gap_invitation_not_offered",
                "offered": False,
                "answer_kind": answer_kind,
                "response_seed": "",
                "reason": (
                    "current_turn_owner_already_supplied_supported_response"
                    if current_owner_already_answered
                    else "gap_not_eligible_or_invitation_not_contextually_needed"
                ),
                "current_turn_response_source": response_source,
                "current_turn_supported_response_preserved": (
                    current_owner_already_answered
                ),
            }
        )
    subject = _question_subject(prompt)
    if answer_kind == "bounded_knowledge_gap" and subject:
        response = f"I don't know enough about {subject} to answer that reliably yet. If you'd like, can you teach me the part you want me to understand?"
    elif subject:
        response = f"I don't know enough about {subject} to answer that reliably yet. Can you teach me?"
    else:
        response = "I don't have enough support to answer that yet. Can you teach me?"
    return _with_guards(
        {
            "status": "learning_gap_invitation_ready",
            "offered": True,
            "answer_kind": answer_kind,
            "original_gap_response": original,
            "response_seed": response,
            "outgoing_question_handoff": {
                "status": "awaiting_teaching_response",
                "question_kind": "teaching_invitation",
                "question": "Can you teach me?",
                "learning_gap_prompt": truncate(str(prompt or ""), 900),
                "subject": truncate(subject, 240),
                "session_scoped": True,
                "ordinary_chat_is_teaching": False,
                "memory_write_active": False,
            },
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def build_assistant_question_handoff(
    candidate_text: str,
    *,
    explicit_handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(explicit_handoff, dict) and explicit_handoff:
        return _with_guards(dict(explicit_handoff))
    questions = [item.strip() for item in re.findall(r"(?:^|(?<=[.!]))\s*([^?]{2,300}\?)", str(candidate_text or ""))]
    if not questions:
        return _with_guards({"status": "no_assistant_question_handoff", "question_kind": "none"})
    question = truncate(questions[-1], 320)
    lower = " ".join(question.lower().split())
    direct = bool(re.search(r"\b(?:you|your|we|us)\b", lower))
    if not direct:
        return _with_guards({"status": "no_assistant_question_handoff", "question_kind": "none", "reason": "question_not_directed_to_user"})
    if "teach me" in lower or "teach me about" in lower:
        kind = "teaching_invitation"
    elif re.search(r"\bwhy\b", lower):
        kind = "reason_question"
    elif re.search(r"\b(?:how was your day|did your day|has your day|are you doing|how are you)\b", lower):
        kind = "personal_curiosity"
    elif re.match(r"^(?:can|could|would|do|did|should)\b", lower):
        kind = "permission_or_proposal"
    else:
        kind = "ordinary_curiosity"
    return _with_guards(
        {
            "status": "assistant_question_handoff_ready",
            "question_kind": kind,
            "question": question,
            "session_scoped": True,
            "one_turn_answer_context": True,
            "ordinary_curiosity_is_teaching": False,
            "review_status": "status_only",
            "provenance_boundary": CONVERSATIONAL_TEACHING_BOUNDARY,
        }
    )


def _planned_claim(
    base: dict[str, Any],
    claim: str,
    cue: str,
    prior: dict[str, Any],
    speaker: dict[str, Any],
) -> dict[str, Any]:
    eligibility = _teaching_eligibility(claim, speaker, prior)
    return _with_guards(
        {
            **base,
            "status": "conversational_teaching_planned" if eligibility["eligible"] else "conversational_teaching_requires_deeper_review",
            "action": "learn_bounded_claim",
            "explicit_activation": True,
            "activation_cue": cue,
            "teaching_claim": truncate(claim, 1200),
            "eligibility": eligibility,
            "response_seed": "",
        }
    )


def _teaching_eligibility(claim: str, speaker: dict[str, Any], prior: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    normalized = " ".join(claim.split()).strip(" .")
    if not _speaker_may_authorize_conversational_teaching(speaker):
        reasons.append("speaker_or_channel_cannot_authorize_durable_teaching")
    if len(normalized) < 4:
        reasons.append("teaching_claim_too_short")
    if len(normalized) > 900:
        reasons.append("teaching_claim_too_large_for_lightweight_path")
    if normalized.endswith("?") and not prior:
        reasons.append("question_is_not_a_teaching_claim")
    sentence_count = len([item for item in re.split(r"(?<=[.!?])\s+", normalized) if item.strip()])
    if sentence_count > 2:
        reasons.append("multiple_claims_need_deeper_teaching_review")
    if _PERSONAL_SOURCE.search(normalized):
        reasons.append("personal_statement_belongs_to_conversation_or_memory_not_general_knowledge")
    sensitive = _sensitive_markers(normalized)
    reasons.extend(sensitive)
    if not _looks_propositional(normalized, prior):
        reasons.append("bounded_proposition_not_identified")
    reasons = list(dict.fromkeys(reasons))
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "path": "lightweight_conversational_comprehension" if not reasons else "deeper_cocoon_or_lea_review",
        "ordinary_chat_activates_teaching": False,
        "explicit_teaching_intent_required": True,
    }


def _micro_understanding_receipt(claim: str, prior: dict[str, Any]) -> dict[str, Any]:
    subject, relation, predicate = _claim_parts(claim, prior)
    qualifier = _qualification(claim)
    spoken_subject = (
        subject[:1].lower() + subject[1:]
        if subject.startswith(("The ", "A ", "An "))
        else subject
    )
    spoken = f"{spoken_subject} {relation} {predicate}".strip().rstrip(".")
    if qualifier:
        teach_back = (
            f"I understand the taught relationship as {subject} {relation} {predicate}. "
            f"The wording {qualifier} keeps that relationship bounded rather than universal."
        )
    else:
        teach_back = (
            f"I understand the teaching as a bounded relationship: {subject} {relation} {predicate}. "
            "It supports that connection without silently adding a cause or a universal rule."
        )
    prior_prompt = truncate(str(prior.get("learning_gap_prompt") or ""), 240)
    application = (
        f"If the earlier question comes up again—{prior_prompt}—I can use the taught relationship about {subject} while preserving its stated scope."
        if prior_prompt
        else f"If a later question asks about {subject}, I can use this taught relationship while keeping its qualification and limits visible."
    )
    limit = "This supports only the stated relationship and qualification; it does not establish an unstated cause, mechanism, exception, or changing current condition."
    distinction = "A bounded source statement is usable knowledge after review, but it is not automatically a universal rule or proof of every nearby claim."
    counterexample = "A later case outside the stated qualification, or direct contradictory evidence, would not be covered by this teaching item and should reopen it."
    return {
        "title": truncate(f"Conversational teaching: {subject}", 240),
        "subject": subject,
        "relationship": truncate(f"The taught source relates {subject} to {predicate} through the relation '{relation}'.", 1200),
        "spoken_understanding": truncate(spoken, 700),
        "teach_back": truncate(teach_back, 3000),
        "application": truncate(application, 1200),
        "limit": limit,
        "distinction": distinction,
        "counterexample": counterexample,
        "scope": truncate(f"Use for later questions that materially concern {subject} and the stated relationship; do not extend it beyond the supplied qualification.", 1200),
        "unresolved": "The underlying cause, mechanism, broader generalization, and unmentioned exceptions remain unresolved unless separately taught or sourced.",
        "analogy": "This is like adding one labeled connection to a map: the connection becomes usable without pretending the surrounding blank areas were filled in too.",
        "learning_question": f"What cause, mechanism, or exception would deepen the current understanding of {subject} beyond this stated relationship?",
        "comparison": "The source statement supplies the relationship itself; a cause, universal generalization, or exception would be a separate claim requiring its own support.",
        "participation": truncate(f"If we talk about {subject} again, I can answer from this relationship in my own wording and keep its stated limit visible.", 1200),
        "vocabulary": _vocabulary(subject, predicate),
        "instructional_why": {
            "why_kind": "relationship",
            "explanatory_relationship": truncate(f"The teaching turn supplies a bounded relationship between {subject} and {predicate}.", 1200),
            "why_it_matters": "That relationship lets a later relevant question use taught knowledge instead of manufacturing an answer from fluency alone.",
            "scope": "Only the explicit claim and qualification supplied in this conversational teaching turn.",
            "failure_or_exception_condition": "A correction, contradiction, failed application, or changed current condition reopens the relationship.",
            "unresolved_uncertainty": "Any cause, mechanism, generalization, or exception not supplied by the teaching statement remains unresolved.",
        },
    }


def _claim_parts(claim: str, prior: dict[str, Any]) -> tuple[str, str, str]:
    cleaned = " ".join(claim.strip().rstrip(".!?").split())
    patterns = (
        (r"^(?P<subject>.{1,160}?)\s+(?P<relation>is|are|was|were)\s+(?P<predicate>.+)$", None),
        (r"^(?P<subject>.{1,160}?)\s+(?P<relation>works\s+like\s+this)\s*[:;,\-]?\s*(?P<predicate>.+)$", None),
        (r"^(?P<subject>.{1,160}?)\s+(?P<relation>works\s+by|means|causes|requires|uses|has|have)\s+(?P<predicate>.+)$", None),
    )
    for pattern, _ in patterns:
        match = re.match(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return (
                match.group("subject").strip(" ,:;"),
                match.group("relation").lower(),
                match.group("predicate").strip(" ,:;"),
            )
    subject = str(prior.get("subject") or _question_subject(prior.get("learning_gap_prompt") or "") or "this subject")
    return truncate(subject, 160), "is described by", truncate(cleaned, 700)


def _vocabulary(subject: str, predicate: str) -> list[str]:
    words = [word.lower() for word in _WORD.findall(f"{subject} {predicate}")]
    stop = {"the", "this", "that", "with", "from", "into", "most", "time", "some", "their", "there", "have", "has", "does", "and", "but", "for"}
    values = list(dict.fromkeys(word for word in words if len(word) >= 3 and word not in stop))
    return values[:12] or ["taught relationship"]


def _explicit_teaching_claim(text: str) -> tuple[str, str]:
    for cue, pattern in _EXPLICIT_TEACHING_PATTERNS:
        match = pattern.match(text)
        if match:
            return cue, truncate(str(match.group("claim") or "").strip(), 1200)
    return "", ""


def _bind_answer_to_pending_question(claim: str, prior: dict[str, Any]) -> str:
    cleaned = _strip_leading_acceptance(claim).strip()
    if not cleaned:
        return ""
    if str(prior.get("question_kind") or "") != "teaching_invitation":
        return cleaned
    if _looks_propositional(cleaned, prior) and not re.match(r"^(?:it|that|the answer)\b", cleaned, flags=re.IGNORECASE):
        return cleaned
    question = truncate(str(prior.get("learning_gap_prompt") or prior.get("question") or "the pending question"), 360)
    return truncate(f"For the question '{question}', the taught answer is {cleaned.rstrip('.')}", 1200)


def _looks_propositional(claim: str, prior: dict[str, Any]) -> bool:
    lower = " ".join(claim.lower().split())
    if re.search(r"\b(?:is|are|was|were|means|causes|requires|uses|has|have|works\s+(?:by|like))\b", lower):
        return True
    if str(prior.get("question_kind") or "") == "teaching_invitation" and len(_WORD.findall(claim)) >= 1:
        return True
    return len(_WORD.findall(claim)) >= 5 and bool(_QUESTION_WORDS.search(str(prior.get("learning_gap_prompt") or "")))


def _sensitive_markers(value: str) -> list[str]:
    lower = " ".join(str(value or "").lower().split())
    reasons = []
    if any(marker in lower for marker in _TIME_SENSITIVE):
        reasons.append("time_sensitive_claim_requires_fresh_source_review")
    if any(marker in lower for marker in _HIGH_STAKES):
        reasons.append("high_stakes_claim_requires_deeper_review")
    if any(marker in lower for marker in _PROTECTED_DOMAINS):
        reasons.append("protected_identity_governance_memory_or_authority_domain")
    return reasons


def _speaker_may_authorize_conversational_teaching(speaker: dict[str, Any]) -> bool:
    claimed = str(speaker.get("claimed_speaker") or "").strip().casefold()
    channel = str(speaker.get("channel") or "").strip().casefold()
    strength = str(speaker.get("authentication_strength") or "").strip().casefold()
    return bool(
        claimed == "aleks"
        and (
            channel == "desktop" and strength == "local_desktop_session"
            or strength in {"os_authenticated_named_identity", "cryptographically_verified_authorship"}
        )
    )


def _latest_assistant_question_handoff(conn: sqlite3.Connection, session_id: int) -> dict[str, Any]:
    if session_id <= 0:
        return {}
    row = conn.execute(
        "SELECT payload_json FROM selene_chat_messages WHERE session_id = ? AND role = 'selene' ORDER BY id DESC LIMIT 1",
        (session_id,),
    ).fetchone()
    if not row:
        return {}
    try:
        payload = json.loads(str(row["payload_json"] or "{}"))
    except (json.JSONDecodeError, TypeError):
        return {}
    handoff = payload.get("assistant_question_handoff") if isinstance(payload, dict) else {}
    return handoff if isinstance(handoff, dict) and str(handoff.get("question_kind") or "") != "none" else {}


def _question_response(handoff: dict[str, Any], answer_kind: str, text: str) -> dict[str, Any]:
    kind = str(handoff.get("question_kind") or "ordinary_curiosity")
    question = str(handoff.get("question") or "")
    if kind == "teaching_invitation":
        seed = _teaching_prompt(handoff) if answer_kind == "affirmative" else "Okay. We can leave that gap open for now—no pressure."
    elif kind == "personal_curiosity":
        seed = (
            "I'm glad :) What made it a good day?"
            if answer_kind == "affirmative"
            else "I'm sorry it was a rough one. Do you want to tell me what happened?"
        )
    elif kind == "reason_question" and answer_kind == "stated_reason":
        seed = "I understand. I'll take that as your reason rather than argue you out of it."
    elif kind == "permission_or_proposal":
        seed = "All right—let's do it." if answer_kind == "affirmative" else "Okay. We can leave that there."
    else:
        seed = "Got it :)" if answer_kind == "affirmative" else "Got it. We can leave that there."
    return {
        "status": "assistant_question_answer_context_ready",
        "question_kind": kind,
        "question": truncate(question, 320),
        "answer_kind": answer_kind,
        "user_answer": truncate(text, 360),
        "response_seed": seed,
        "user_boundary_accepted": answer_kind == "negative",
        "may_ask_why_without_pressure": answer_kind == "negative",
        "stated_reason_must_be_received_not_overruled": answer_kind in {"negative", "stated_reason"},
        "stated_reason_is_user_authored": answer_kind == "stated_reason",
        "follow_up_may_clarify_but_may_not_override_user_boundary": True,
        "teaching_activated": kind == "teaching_invitation" and answer_kind not in {"negative"},
        "session_scoped": True,
    }


def _brief_answer_kind(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9']+", " ", text.lower().replace("’", "'")).strip()
    if normalized in _YES or any(normalized.startswith(f"{item} ") for item in _YES):
        return "affirmative"
    if normalized in _NO or any(normalized.startswith(f"{item} ") for item in _NO):
        return "negative"
    return "expanded"


def _brief_answer_only(text: str) -> bool:
    return len(_WORD.findall(text)) <= 4


def _strip_leading_acceptance(text: str) -> str:
    return re.sub(
        r"^\s*(?:sure|yes|yeah|yep|yup|okay|ok|of course|absolutely)\b\s*[,;:.!\-]?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()


def _leading_acceptance_present(text: str) -> bool:
    return bool(
        re.match(
            r"^\s*(?:sure|yes|yeah|yep|yup|okay|ok|of course|absolutely)\b",
            text,
            flags=re.IGNORECASE,
        )
    )


def _teaching_prompt(handoff: dict[str, Any]) -> str:
    subject = str(handoff.get("subject") or "that").strip()
    return f"Yes—go ahead. What should I understand about {subject}?" if subject else "Yes—go ahead. What should I understand?"


def _held_response(eligibility: dict[str, Any]) -> str:
    reasons = set(str(item) for item in eligibility.get("reasons") or [])
    if "multiple_claims_need_deeper_teaching_review" in reasons or "teaching_claim_too_large_for_lightweight_path" in reasons:
        return "I can learn that with you, but it is larger than one conversational teaching step. Let's take it through the deeper teaching path so the parts do not get tangled."
    if "personal_statement_belongs_to_conversation_or_memory_not_general_knowledge" in reasons:
        return "I hear that as something about you or this conversation, not general taught knowledge. I won't silently turn it into a knowledge lesson."
    if "time_sensitive_claim_requires_fresh_source_review" in reasons:
        return "That may change with time, so I need a current source before I treat it as learned knowledge."
    if "high_stakes_claim_requires_deeper_review" in reasons:
        return "That needs a deeper, source-checked teaching pass before I can use it as learned knowledge."
    if "protected_identity_governance_memory_or_authority_domain" in reasons:
        return "That belongs to a protected identity, governance, memory, or authority path—not lightweight conversational teaching."
    return "I can take that as teaching, but I need a clearer bounded statement before I can honestly integrate it."


def _question_subject(value: Any) -> str:
    lower = " ".join(str(value or "").lower().replace("’", "'").split()).strip(" ?!.")
    polar = re.match(r"^(?:is|are|was|were)\s+(?P<body>.+)$", lower)
    if polar:
        body_words = _WORD.findall(polar.group("body"))
        if len(body_words) >= 2:
            body_words = body_words[:-1]
            if body_words and body_words[0].lower() in {"the", "a", "an"}:
                body_words = body_words[1:]
            return truncate(" ".join(body_words[:10]), 240)
    auxiliary = re.match(
        r"^(?:do|does|did|can|could|would|should)\s+(?P<body>.+)$",
        lower,
    )
    if auxiliary:
        body = auxiliary.group("body")
        subject_match = re.match(
            r"^(?P<subject>.+?)\s+"
            r"(?:(?:already|currently|usually|often|ever|still)\s+)*"
            r"(?:have|has|mean|means|refer|refers|work|works|exist|exists|"
            r"contain|contains|include|includes|use|uses|need|needs|cause|"
            r"causes|require|requires|look|looks|sound|sounds|feel|feels|"
            r"seem|seems|belong|belongs|change|changes)\b",
            body,
        )
        if subject_match:
            subject_words = _WORD.findall(subject_match.group("subject"))
            if subject_words and subject_words[0].lower() in {"the", "a", "an"}:
                subject_words = subject_words[1:]
            if subject_words:
                return truncate(" ".join(subject_words[:10]), 240)
    lower = re.sub(r"^(?:do you know about|what do you know about|tell me about|is|are|was|were|what color is|what is|who is|where is|when is)\s+", "", lower)
    lower = re.sub(r"\b(?:yet|right now)\b", "", lower)
    words = [word for word in _WORD.findall(lower) if word.lower() not in {"the", "a", "an", "does", "do", "did", "can", "could", "would", "should"}]
    return truncate(" ".join(words[:10]).strip(), 240)


def _qualification(claim: str) -> str:
    lower = " ".join(claim.lower().split())
    for marker in ("most of the time", "usually", "often", "sometimes", "generally", "in this case", "when ", "unless ", "under "):
        if marker in lower:
            return f"'{marker.strip()}'"
    return ""


def _normalized_claim(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS, "provenance_boundary": CONVERSATIONAL_TEACHING_BOUNDARY}
