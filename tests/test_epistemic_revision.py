from __future__ import annotations

import pytest

from selene.db import connect, init_db
from selene.epistemic_revision import (
    UPDATE_KINDS,
    build_epistemic_revision_plan,
    epistemic_revision_response_seed,
)
from selene.module_router import route_request


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["automatic_cocoon_routing"] is False
    assert result["direct_truth_authority"] is False


def test_status_and_plan_routes_are_inspectable_and_bounded(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    status = route_request(conn, "epistemic_revision.status")["result"]
    plan = route_request(
        conn,
        "epistemic_revision.plan",
        {
            "requested_kind": "refinement",
            "prior_claim": "The method works.",
            "revised_claim": "The method works for stable inputs.",
        },
    )["result"]

    assert set(status["supported_update_kinds"]) == UPDATE_KINDS
    assert plan["update_kind"] == "refinement"
    assert plan["validity"] == "earlier_claim_retained_with_precision"
    _assert_bounded(status)
    _assert_bounded(plan)


@pytest.mark.parametrize(
    ("kind", "disposition"),
    [
        ("correction", "apply_affected_update_and_continue"),
        ("refinement", "apply_narrow_refinement"),
        ("scope_restriction", "retain_with_narrower_scope"),
        ("extension", "add_without_erasing_supported_base"),
        ("competing_explanation", "compare_without_premature_replacement"),
        ("unresolved_contradiction", "hold_contradiction_visible"),
        ("replacement", "replace_affected_claim_preserve_ancestry"),
        ("reopening", "reopen_affected_model_once"),
    ],
)
def test_all_supported_update_kinds_preserve_selective_revision(kind, disposition):
    result = build_epistemic_revision_plan(
        {
            "requested_kind": kind,
            "prior_claim": "The earlier model explains the observation.",
            "revised_claim": "The revised model explains the observation under narrower conditions.",
            "scope": "the stated conditions",
            "dependent_claims": ["the downstream prediction"],
            "source_refs": ["test:visible-evidence"],
        }
    )

    assert result["detected"] is True
    assert result["disposition"] == disposition
    assert result["preserved_structure"]["full_context_reset_required"] is False
    assert result["preserved_structure"]["useful_superseded_structure_deleted"] is False
    assert result["dependent_recheck"]["maximum_recheck_passes_without_new_material"] == 1
    assert result["model_ancestry"]["preserved"] is True
    assert result["retained_state_handoff"]["automatic_knowledge_rewrite"] is False
    _assert_bounded(result)


def test_newtonian_scope_is_narrowed_without_erasing_valid_ancestry():
    result = build_epistemic_revision_plan(
        {
            "prompt": "Newtonian mechanics applies only at low speeds and weak gravity.",
            "previous_claims": ["Newtonian mechanics explains motion."],
        }
    )
    response = epistemic_revision_response_seed(result)

    assert result["update_kind"] == "scope_restriction"
    assert result["validity"] == "earlier_claim_valid_only_in_stated_scope"
    assert result["model_ancestry"]["prior_model"] == "Newtonian mechanics explains motion."
    assert result["model_ancestry"]["preserved"] is True
    assert "low speeds and weak gravity" in response
    assert "should not carry it beyond" in response


def test_evidence_can_update_either_aleks_or_selene_without_changing_the_contract():
    shared = {
        "requested_kind": "correction",
        "prior_claim": "The first count was 12.",
        "revised_claim": "The checked count is 11.",
    }
    aleks_update = build_epistemic_revision_plan({**shared, "update_subject": "aleks"})
    selene_update = build_epistemic_revision_plan({**shared, "update_subject": "selene"})

    assert aleks_update["update_subject"] == "aleks"
    assert selene_update["update_subject"] == "selene"
    assert aleks_update["disposition"] == selene_update["disposition"]
    assert aleks_update["evidence_may_update_either_participant"] is True
    assert selene_update["social_posture"]["wrongness_is_failure"] is False


def test_competing_explanation_and_unresolved_contradiction_are_not_forced_closed():
    competing = build_epistemic_revision_plan(
        {
            "prompt": "Another explanation could instead be measurement bias.",
            "previous_claims": ["The signal reflects a physical change."],
        }
    )
    contradiction = build_epistemic_revision_plan(
        {
            "prompt": "This conflicts with the earlier result and cannot both be true.",
            "previous_claims": ["The earlier result remains valid."],
        }
    )

    assert competing["validity"] == "multiple_live_candidates"
    assert competing["metacognitive_handoff"]["compare_competing_explanations"] is True
    assert "not a settled replacement" in epistemic_revision_response_seed(competing)
    assert contradiction["validity"] == "conflict_unresolved"
    assert contradiction["metacognitive_handoff"]["hold_for_evidence"] is True
    assert "would not force them into agreement" in epistemic_revision_response_seed(contradiction)


@pytest.mark.parametrize("target_class", ["identity", "personality", "governance", "law", "authority"])
def test_conversation_revision_cannot_mutate_core_mind_owned_targets(target_class):
    result = build_epistemic_revision_plan(
        {
            "requested_kind": "replacement",
            "target_class": target_class,
            "prior_claim": "prior",
            "revised_claim": "replacement",
        }
    )

    assert result["detected"] is False
    assert result["status"] == "epistemic_revision_held_by_owner"
    assert result["owner_lock"]["owner"] == "Core/Mind"
    assert result["disposition"] == "defer_to_core_mind"
    _assert_bounded(result)


def test_narrative_use_of_wrongness_does_not_become_a_correction_without_a_prior_claim():
    result = build_epistemic_revision_plan(
        {"prompt": "Being wrong can be useful evidence when learning."}
    )

    assert result["detected"] is False
    assert result["update_kind"] == "none"
