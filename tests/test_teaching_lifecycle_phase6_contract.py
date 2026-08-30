from __future__ import annotations

import json

import pytest

from selene.comprehension_integration import retrieve_approved_knowledge
from selene.comprehension_integration import (
    build_instructional_source_role_receipt,
    build_instructional_why_receipt,
)
from selene.curriculum_authorization import (
    _GROUP_DEFINITIONS,
    _curriculum_instructional_why,
    _curriculum_source_roles,
)
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _why(*, missing: str = ""):
    receipt = {
        "why_kind": "mechanism",
        "explanatory_relationship": "Increasing external pressure raises the temperature at which liquid water and vapor balance.",
        "why_it_matters": "The relationship explains why the same liquid can boil at different temperatures in different pressure conditions.",
        "scope": "Use for bounded comparisons of liquid-water boiling under stated pressure conditions.",
        "failure_or_exception_condition": "Composition, dissolved material, and an unstated pressure change can alter the comparison.",
        "unresolved_uncertainty": "The exact boiling temperature still requires a measured pressure and an appropriate reference.",
    }
    receipt.pop(missing, None)
    return receipt


def _roles(*, current: bool = False):
    roles = [
        {
            "role": "current_fact" if current else "source_statement",
            "content_fields": ["material", "principles"],
            "source_refs": ["synthetic:phase6b:water-pressure"],
        },
        {
            "role": "inference",
            "content_fields": ["relationships"],
            "source_refs": ["synthetic:phase6b:water-pressure"],
        },
        {
            "role": "example",
            "content_fields": ["examples", "counterexamples"],
            "source_refs": ["synthetic:phase6b:water-pressure"],
        },
        {
            "role": "practice",
            "content_fields": ["distinct_application", "questions"],
            "source_refs": ["synthetic:phase6b:water-pressure"],
        },
        {
            "role": "verification",
            "content_fields": ["limits", "correction_response"],
            "source_refs": ["synthetic:phase6b:water-pressure"],
        },
    ]
    return roles


def _propose(conn, *, key: str, current: bool = False, why=None, roles=None):
    return route_request(
        conn,
        "comprehension.concepts.propose",
        {
            "concept_key": key,
            "title": "Water boiling and pressure",
            "domain": "synthetic.phase6b.science",
            "material": "The boiling temperature of water depends on the surrounding pressure as well as the liquid's composition.",
            "principles": ["A boiling-temperature claim needs a stated pressure condition."],
            "relationships": ["Pressure changes the liquid-vapor balance used to identify boiling."],
            "examples": ["A pressure cooker can keep liquid water above its ordinary sea-level boiling temperature."],
            "counterexamples": ["A higher thermometer reading alone does not establish that pressure caused the change."],
            "limits": ["This bounded lesson does not calculate a boiling point from pressure."],
            "source_refs": ["synthetic:phase6b:water-pressure"],
            "teaching_source_type": "bounded_public_academic_curriculum",
            "knowledge_class": "time_sensitive_current_claim" if current else "public_academic_foundation",
            "freshness_class": "time_sensitive_current" if current else "durable_foundation_with_source_specific_limits",
            "source_roles": roles if roles is not None else _roles(current=current),
            "instructional_why": why if why is not None else _why(),
        },
    )["result"]["item"]


def _acquire(conn, concept_id: int, *, learning_state: str = "developing"):
    return route_request(
        conn,
        "teaching.lifecycle.acquire",
        {
            "concept_id": concept_id,
            "vocabulary": ["pressure: force distributed across an area"],
            "uncertainties": ["The exact value needs an attributed pressure condition."],
            "near_concept_distinctions": ["Boiling and evaporation are related but not identical processes."],
            "learning_state": learning_state,
        },
    )["result"]


def _integrate(conn, concept_id: int, *, learning_state: str = "developing"):
    return route_request(
        conn,
        "teaching.lifecycle.integrate",
        {
            "concept_id": concept_id,
            "scope_of_application": "Use only for bounded pressure-and-boiling comparisons with the relevant conditions stated.",
            "contradiction_classification": "none_identified",
            "unresolved_questions": ["What pressure and composition apply in the present case?"],
            "integration_confidence": "bounded",
            "learning_state": learning_state,
        },
    )["result"]


def _express(conn, concept_id: int):
    return route_request(
        conn,
        "teaching.lifecycle.express",
        {
            "concept_id": concept_id,
            "explanation": "Water does not have one context-free boiling temperature: the surrounding pressure changes when liquid and vapor can balance.",
            "distinct_examples": ["Inside a pressure cooker, elevated pressure lets the water become hotter before sustained boiling occurs."],
            "analogies": ["It is like changing the opposing load before a transition can happen, while keeping the material itself identified."],
            "questions": ["What pressure and liquid composition apply to this comparison?"],
            "comparisons": ["Evaporation can occur below boiling, while boiling involves vapor formation throughout the liquid."],
            "conversational_participation": "I would state the pressure condition before comparing temperatures and leave the exact value open until it is sourced.",
            "limits": ["This does not provide an exact value for an unstated pressure or mixture."],
            "counterexamples": ["A warm open cup can evaporate without the entire liquid boiling."],
            "correction_response": "If the pressure condition changes, I would revise the temperature claim instead of preserving the old number.",
            "source_alignment": True,
        },
    )["result"]


def test_phase6_contract_flows_from_proposal_through_lifecycle_and_retrieval(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn, key="synthetic_phase6b_durable_water_pressure")

    proposal = concept["payload"]
    assert proposal["source_role_receipt"]["status"] == "typed_source_roles_recorded"
    assert {item["role"] for item in proposal["source_role_receipt"]["roles"]} == {
        "source_statement",
        "inference",
        "example",
        "practice",
        "verification",
    }
    assert proposal["knowledge_class"] == "public_academic_foundation"
    assert proposal["freshness_class"] == "durable_foundation_with_source_specific_limits"

    acquired = _acquire(conn, concept["id"])
    integrated = _integrate(conn, concept["id"])
    expressed = _express(conn, concept["id"])
    approved = route_request(
        conn,
        "teaching.lifecycle.approve",
        {"concept_id": concept["id"], "aleks_approved": True, "approval_actor": "Aleks"},
    )["result"]

    assert acquired["snapshot"]["source_role_receipt"] == proposal["source_role_receipt"]
    assert acquired["snapshot"]["learning_state"] == "developing"
    assert acquired["snapshot"]["completion_forced"] is False
    assert integrated["snapshot"]["instructional_why_receipt"]["status"] == "complete"
    assert integrated["snapshot"]["instructional_why_receipt"]["why_kind"] == "mechanism"
    assert expressed["stage_complete"] is True
    assert approved["snapshot"]["knowledge_class"] == "public_academic_foundation"
    assert approved["snapshot"]["freshness_class"] == "durable_foundation_with_source_specific_limits"

    retrieved = retrieve_approved_knowledge(conn, "How does pressure change water boiling?", limit=3)
    assert retrieved["items"][0]["id"] == concept["id"]
    assert retrieved["items"][0]["source_role_receipt"]["status"] == "typed_source_roles_recorded"
    assert retrieved["items"][0]["instructional_why_receipt"]["why_it_matters"]
    assert retrieved["items"][0]["freshness_class"] == "durable_foundation_with_source_specific_limits"


def test_incomplete_instructional_why_remains_visible_without_forced_completion(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(
        conn,
        key="synthetic_phase6b_incomplete_why",
        why=_why(missing="why_it_matters"),
    )
    held_acquire = _acquire(conn, concept["id"], learning_state="needs_representation")
    assert held_acquire["stage_complete"] is False
    assert "learning_state.needs_representation" in held_acquire["snapshot"]["missing_fields"]
    _acquire(conn, concept["id"], learning_state="developing")
    integrated = _integrate(conn, concept["id"], learning_state="unclear")
    status = route_request(conn, "teaching.lifecycle.status")["result"]

    assert integrated["stage_complete"] is False
    assert integrated["snapshot"]["instructional_why_receipt"]["status"] == "needs_review"
    assert "instructional_why.why_it_matters" in integrated["snapshot"]["missing_fields"]
    assert integrated["snapshot"]["learning_state"] == "unclear"
    assert integrated["snapshot"]["completion_forced"] is False
    assert status["non_forced_learning_states"] == [
        "developing",
        "needs_representation",
        "needs_prerequisite",
        "revisit",
        "unclear",
    ]


def test_invalid_source_role_is_rejected_before_candidate_creation(tmp_path):
    conn = _conn(tmp_path)
    bad_roles = _roles()
    bad_roles[0] = {**bad_roles[0], "role": "automatic_truth"}

    with pytest.raises(ValueError, match="unsupported instructional source role"):
        _propose(conn, key="synthetic_phase6b_invalid_role", roles=bad_roles)

    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 0


def test_public_academic_retention_cannot_bypass_teaching_lifecycle(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn, key="synthetic_phase6b_no_lifecycle_bypass")
    route_request(
        conn,
        "comprehension.understanding.evaluate",
        {
            "concept_id": concept["id"],
            "teach_back": "Water's boiling condition depends on surrounding pressure, so a temperature claim needs that condition stated.",
            "application": "A sealed pressure cooker can sustain liquid water above the ordinary open-pot boiling temperature.",
            "limits": ["An exact value still needs an attributed pressure and composition."],
            "counterexample": "Surface evaporation below boiling is not the same whole-liquid transition.",
            "correction_response": "I would revise the value when the pressure condition changes.",
            "source_alignment": True,
        },
    )

    with pytest.raises(ValueError, match="requires complete Acquire, Integrate, and Express"):
        route_request(
            conn,
            "comprehension.concepts.decide",
            {"concept_id": concept["id"], "action": "approve_knowledge"},
        )


def test_current_fact_is_retained_as_reviewed_current_claim_but_not_seeded_as_durable_knowledge(tmp_path):
    conn = _conn(tmp_path)
    concept = _propose(conn, key="synthetic_phase6b_current_water_pressure", current=True)
    _acquire(conn, concept["id"])
    _integrate(conn, concept["id"])
    _express(conn, concept["id"])
    approved = route_request(
        conn,
        "teaching.lifecycle.approve",
        {"concept_id": concept["id"], "aleks_approved": True, "approval_actor": "Aleks"},
    )["result"]

    assert approved["snapshot"]["current_fact_present"] is True
    assert approved["snapshot"]["knowledge_resource_active"] is False
    assert approved["item"]["retention_state"] == "retained_reviewed_current_claim"
    assert approved["item"]["chat_use_permission"] == "requires_fresh_current_source"
    assert retrieve_approved_knowledge(conn, "water pressure boiling")["items"] == []


def test_curriculum_preparation_records_full_lesson_contract(tmp_path):
    conn = _conn(tmp_path)
    route_request(
        conn,
        "curriculum.authorization.activate_f1",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Synthetic Phase 6B curriculum-contract verification only.",
        },
    )
    prepared = route_request(conn, "curriculum.foundation.prepare_f1", {})["result"]
    concept = route_request(
        conn,
        "comprehension.concepts.list",
        {"limit": 20},
    )["result"]["items"][-1]

    assert prepared["created_count"] > 0
    assert concept["payload"]["source_role_receipt"]["status"] == "typed_source_roles_recorded"
    assert concept["payload"]["instructional_why_receipt"]["status"] == "complete"
    assert concept["payload"]["source_metadata"]["instructional_contract_version"] == "phase6b_typed_source_and_why_v1"


def test_reproposal_upgrades_only_the_open_candidate_contract_idempotently(tmp_path):
    conn = _conn(tmp_path)
    first = route_request(
        conn,
        "comprehension.concepts.propose",
        {
            "concept_key": "synthetic_phase6b_open_candidate_upgrade",
            "title": "Open candidate",
            "material": "An earlier open candidate has source provenance but predates the typed instructional contract.",
            "source_refs": ["synthetic:phase6b:open-candidate"],
        },
    )["result"]["item"]
    assert first["payload"]["instructional_why_receipt"]["status"] == "needs_review"

    second = _propose(conn, key="synthetic_phase6b_open_candidate_upgrade")

    assert second["id"] == first["id"]
    assert second["payload"]["source_role_receipt"]["status"] == "typed_source_roles_recorded"
    assert second["payload"]["instructional_why_receipt"]["status"] == "complete"
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 1


def test_current_fact_cannot_inherit_standing_curriculum_coverage(tmp_path):
    conn = _conn(tmp_path)
    route_request(
        conn,
        "curriculum.authorization.activate_f1",
        {
            "aleks_authorized": True,
            "authorization_actor": "Aleks",
            "authorization_basis": "Synthetic current-fact exception verification only.",
        },
    )
    prepared = route_request(conn, "curriculum.foundation.prepare_f1", {})["result"]
    concept_id = prepared["created"][0]["concept_id"]
    row = conn.execute(
        "SELECT payload_json FROM selene_comprehension_concepts WHERE id = ?",
        (concept_id,),
    ).fetchone()
    payload = json.loads(row["payload_json"])
    payload["knowledge_class"] = "time_sensitive_current_claim"
    payload["freshness_class"] = "time_sensitive_current"
    payload["source_role_receipt"]["current_fact_present"] = True
    payload["source_role_receipt"]["roles"][0]["role"] = "current_fact"
    conn.execute(
        "UPDATE selene_comprehension_concepts SET payload_json = ? WHERE id = ?",
        (json.dumps(payload, sort_keys=True), concept_id),
    )
    conn.commit()

    coverage = route_request(
        conn,
        "curriculum.authorization.evaluate",
        {"concept_id": concept_id},
    )["result"]

    assert coverage["decision"] == "exception_review_required"
    assert "outdated_or_time_sensitive_claim" in coverage["exceptions"]


def test_all_implemented_curriculum_lessons_have_complete_phase6b_contracts():
    lesson_count = 0
    for group in _GROUP_DEFINITIONS:
        for lesson in group["lessons"]:
            lesson_count += 1
            source_refs = list(lesson.get("source_refs") or group.get("source_refs") or [])
            source_receipt = build_instructional_source_role_receipt(
                _curriculum_source_roles(lesson, source_refs),
                source_refs=source_refs,
                knowledge_class="public_academic_foundation",
                freshness_class="durable_foundation_with_source_specific_limits",
            )
            why_receipt = build_instructional_why_receipt(
                _curriculum_instructional_why(lesson)
            )

            assert source_receipt["role_types"] == [
                "source_statement",
                "inference",
                "example",
                "practice",
                "verification",
            ]
            assert source_receipt["current_fact_present"] is False
            assert why_receipt["status"] == "complete"

    assert len(_GROUP_DEFINITIONS) == 26
    assert lesson_count == 152
