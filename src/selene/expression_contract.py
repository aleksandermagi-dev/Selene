from __future__ import annotations

import re
from hashlib import sha256
from typing import Any


EXPRESSION_CONTRACT_VERSION = "v1_coordinated_nlo_voice_release"


def coordinated_expression_contract() -> dict[str, Any]:
    """Describe the implemented expression pipeline without exclusive-owner shorthand."""
    return {
        "version": EXPRESSION_CONTRACT_VERSION,
        "selene_owns_visible_expression": True,
        "supported_content_owner": "selected_upstream_domain_or_conversation_owner",
        "meaning_and_epistemic_state_owner": "upstream_supported_content_and_epistemic_organs",
        "language_structure_owner": "Native Language Organ",
        "contextual_surface_realization": "NLO language and conversation realization modules",
        "final_expression_compatibility_layer": "Selene Voice Module",
        "visible_release_owner": "Conversation Spine and Selene Chat release gate",
        "voice_is_only_expression_author": False,
        "nlo_is_only_expression_author": False,
        "expression_is_coordinated": True,
        "voice_may_change_supported_meaning": False,
        "voice_may_change_claim_type": False,
        "voice_may_upgrade_evidence": False,
        "voice_may_upgrade_answer_confidence": False,
        "voice_may_change_memory_status": False,
        "voice_may_change_route": False,
        "expression_confidence_means": "surface_realization_and_compatibility_only",
        "expression_confidence_is_answer_correctness": False,
    }


def expression_meaning_invariant(source_text: str, candidate_text: str) -> dict[str, Any]:
    """Use exact lexical-content preservation as a conservative meaning invariant."""
    source = _canonical_expression_text(source_text)
    candidate = _canonical_expression_text(candidate_text)
    preserved = source == candidate
    return {
        "status": "expression_meaning_invariant_checked",
        "lexical_content_preserved": preserved,
        "meaning_invariant_preserved": preserved,
        "source_signature": _signature(source),
        "candidate_signature": _signature(candidate),
        "allowed_voice_transformations": [
            "whitespace_normalization",
            "paragraph_pacing",
        ],
        "claim_type_change_allowed": False,
        "evidence_status_change_allowed": False,
        "confidence_upgrade_allowed": False,
    }


def _canonical_expression_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _signature(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()
