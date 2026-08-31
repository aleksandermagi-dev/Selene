from __future__ import annotations

import pytest

from selene.activation import ACTIVATION_APPROVAL_PHRASE
from selene.comprehension_integration import retrieve_approved_knowledge
from selene.db import connect, init_db
from selene.module_router import route_request
from tests.test_selene_chat_shell import _seed_activation_ready_state


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _propose(
    conn,
    *,
    concept_key: str,
    material: str,
    source_ref: str,
    title: str = "Insulated containers and heat transfer",
    domain: str = "synthetic.phase6c.heat_transfer",
):
    return route_request(
        conn,
        "comprehension.concepts.propose",
        {
            "concept_key": concept_key,
            "title": title,
            "domain": domain,
            "material": material,
            "principles": [
                "Insulation changes the rate of energy transfer across a boundary."
            ],
            "relationships": [
                "A smaller transfer rate can preserve a temperature difference for longer."
            ],
            "examples": [
                "A covered insulated cup keeps warm tea warmer longer than an uncovered metal cup."
            ],
            "counterexamples": [
                "An insulated cup left long enough still approaches the surrounding temperature."
            ],
            "limits": [
                "Insulation does not create energy or guarantee a permanent temperature difference."
            ],
            "source_refs": [source_ref],
            "teaching_source_type": "bounded_public_academic_curriculum",
            "source_roles": [
                {
                    "role": "source_statement",
                    "content_fields": ["material", "principles", "relationships", "limits"],
                    "source_refs": [source_ref],
                },
                {
                    "role": "example",
                    "content_fields": ["examples", "counterexamples"],
                    "source_refs": [source_ref],
                },
            ],
            "instructional_why": {
                "why_kind": "mechanism",
                "explanatory_relationship": "Insulating material reduces the rate of energy transfer between contents and surroundings.",
                "why_it_matters": "A slower transfer rate preserves a temperature difference for longer.",
                "scope": "Bounded comparisons of otherwise similar containers and surroundings.",
                "failure_or_exception_condition": "Energy still transfers, and container openings or damage can increase its rate.",
                "unresolved_uncertainty": "The exact rate depends on materials, geometry, closure, and environment.",
            },
        },
    )["result"]["item"]


def _complete_lifecycle(conn, concept_id: int, *, corrected: bool = False):
    route_request(
        conn,
        "teaching.lifecycle.acquire",
        {
            "concept_id": concept_id,
            "vocabulary": [
                "insulation: material or structure that reduces an energy-transfer rate"
            ],
            "uncertainties": [
                "The exact transfer rate depends on the complete container and environment."
            ],
            "near_concept_distinctions": [
                "Slowing heat transfer is not the same as stopping every energy transfer."
            ],
        },
    )
    route_request(
        conn,
        "teaching.lifecycle.integrate",
        {
            "concept_id": concept_id,
            "scope_of_application": "Compare how otherwise similar containers change the rate at which contents approach ambient temperature.",
            "contradiction_classification": "none_identified",
            "unresolved_questions": [
                "Which material and closure account for the largest part of the observed difference?"
            ],
            "integration_confidence": "bounded",
            "instructional_why": {
                "why_kind": "mechanism",
                "explanatory_relationship": "Insulating material reduces the rate of energy transfer between contents and surroundings.",
                "why_it_matters": "A slower transfer rate preserves a temperature difference for longer.",
                "scope": "Bounded comparisons of otherwise similar containers and surroundings.",
                "failure_or_exception_condition": "Energy still transfers, and container openings or damage can increase its rate.",
                "unresolved_uncertainty": "The exact rate depends on materials, geometry, closure, and environment.",
            },
        },
    )
    explanation = (
        "Insulation makes energy cross the container boundary more slowly, so warm tea cools more slowly, but the transfer continues."
        if corrected
        else "An insulated container changes how quickly energy crosses its boundary, which changes how long its contents remain warmer."
    )
    route_request(
        conn,
        "teaching.lifecycle.express",
        {
            "concept_id": concept_id,
            "explanation": explanation,
            "distinct_examples": [
                "Tea in a closed insulated mug can remain warmer longer than tea in a thin open cup while still cooling over time."
            ],
            "analogies": [
                "It is like narrowing a doorway so movement continues at a slower rate rather than sealing the doorway forever."
            ],
            "questions": [
                "Are the containers equally closed and in the same surroundings?"
            ],
            "comparisons": [
                "Insulation slows energy transfer; an energy source instead adds energy."
            ],
            "conversational_participation": "The insulated mug should slow the cooling, although I would not expect it to keep the tea at one temperature forever.",
            "correction_response": "I would replace a claim that insulation stops transfer with the narrower claim that it reduces the transfer rate.",
            "source_alignment": True,
        },
    )
    return route_request(
        conn,
        "teaching.lifecycle.approve",
        {
            "concept_id": concept_id,
            "aleks_approved": True,
            "approval_actor": "Aleks",
        },
    )["result"]


def _reopen_payload(concept_id: int):
    return {
        "concept_id": concept_id,
        "action": "reopen_for_revision",
        "correction_reason": (
            "Synthetic source review found that 'completely stops' overstates the bounded mechanism."
        ),
        "revised_material": (
            "An insulated container slows energy transfer between its contents and surroundings; it does not stop that transfer entirely."
        ),
        "revised_principles": [
            "Insulation reduces an energy-transfer rate rather than making that rate exactly zero."
        ],
        "revised_relationships": [
            "A lower transfer rate makes warm contents cool more slowly while transfer continues."
        ],
        "revised_examples": [
            "Warm tea in a closed insulated mug cools more slowly than tea in a thin open cup."
        ],
        "revised_counterexamples": [
            "An insulated mug eventually approaching room temperature shows that transfer did not stop."
        ],
        "revised_limits": [
            "The exact rate depends on material, thickness, geometry, closure, and environment."
        ],
        "revision_source_refs": ["synthetic:phase6c:corrected-heat-transfer"],
        "revised_source_roles": [
            {
                "role": "source_statement",
                "content_fields": ["material", "principles", "relationships", "limits"],
                "source_refs": ["synthetic:phase6c:corrected-heat-transfer"],
            },
            {
                "role": "example",
                "content_fields": ["examples", "counterexamples"],
                "source_refs": ["synthetic:phase6c:corrected-heat-transfer"],
            },
        ],
    }


def test_reopen_creates_one_inactive_revision_descendant_and_holds_parent_from_chat(tmp_path):
    conn = _conn(tmp_path)
    parent = _propose(
        conn,
        concept_key="synthetic_phase6c_heat_transfer",
        material="An insulated container completely stops heat transfer between its contents and surroundings.",
        source_ref="synthetic:phase6c:original-heat-transfer",
    )
    original_approval = _complete_lifecycle(conn, parent["id"])
    parent_lifecycle_id = original_approval["item"]["id"]

    first = route_request(
        conn, "comprehension.concepts.decide", _reopen_payload(parent["id"])
    )["result"]
    second = route_request(
        conn, "comprehension.concepts.decide", _reopen_payload(parent["id"])
    )["result"]

    child = first["item"]
    stored_parent = conn.execute(
        "SELECT * FROM selene_comprehension_concepts WHERE id = ?", (parent["id"],)
    ).fetchone()
    held = retrieve_approved_knowledge(conn, "insulated container heat transfer", limit=10)

    assert first["status"] == "comprehension_revision_descendant_created"
    assert child["id"] != parent["id"]
    assert child["parent_concept_id"] == parent["id"]
    assert child["root_concept_id"] == parent["id"]
    assert child["central_claim"].startswith("An insulated container slows")
    assert child["state"] == "proposed_understanding"
    assert child["chat_use_permission"] == "not_active_until_approved"
    assert child["payload"]["correction_lineage"]["reason_for_review"]
    assert child["payload"]["correction_lineage"]["original_parent_preserved"] is True
    assert stored_parent["state"] == "reopened_for_revision"
    assert stored_parent["chat_use_permission"] == "not_active_until_revision_approved"
    assert held["available"] is False
    assert second["status"] == "comprehension_revision_descendant_already_exists"
    assert second["item"]["id"] == child["id"]
    assert second["stopping_receipt"]["reason"] == "duplicate_open_descendant_stopped"
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 2

    route_request(
        conn,
        "comprehension.understanding.evaluate",
        {
            "concept_id": child["id"],
            "teach_back": "Insulation slows energy transfer across the boundary instead of ending it.",
            "application": "A closed insulated bowl can slow how quickly soup approaches room temperature.",
            "limits": ["The soup still exchanges energy with its surroundings."],
            "counterexample": "The soup eventually reaching room temperature shows that transfer continues.",
            "correction_response": "I would replace 'stops transfer' with 'reduces the transfer rate'.",
            "source_alignment": True,
        },
    )
    with pytest.raises(ValueError, match="Acquire, Integrate, and Express"):
        route_request(
            conn,
            "comprehension.concepts.decide",
            {"concept_id": child["id"], "action": "approve_knowledge"},
        )

    acquired = route_request(
        conn,
        "teaching.lifecycle.acquire",
        {
            "concept_id": child["id"],
            "vocabulary": [
                "insulation: material or structure that reduces an energy-transfer rate"
            ],
            "uncertainties": [
                "The exact transfer rate depends on the complete container and environment."
            ],
            "near_concept_distinctions": [
                "Slowing heat transfer is not the same as stopping every energy transfer."
            ],
        },
    )["result"]
    assert acquired["item"]["parent_lifecycle_id"] == parent_lifecycle_id
    assert acquired["item"]["root_lifecycle_id"] == parent_lifecycle_id


def test_approved_descendant_becomes_only_active_winner_and_old_nodes_stop(tmp_path):
    conn = _conn(tmp_path)
    parent = _propose(
        conn,
        concept_key="synthetic_phase6c_heat_transfer_winner",
        material="An insulated container completely stops heat transfer between its contents and surroundings.",
        source_ref="synthetic:phase6c:original-winner",
    )
    _complete_lifecycle(conn, parent["id"])
    reopened = route_request(
        conn, "comprehension.concepts.decide", _reopen_payload(parent["id"])
    )["result"]
    child_id = reopened["item"]["id"]

    unresolved_stop = route_request(
        conn, "comprehension.concepts.decide", _reopen_payload(child_id)
    )["result"]
    assert unresolved_stop["status"] == "comprehension_revision_lineage_stopped"
    assert unresolved_stop["stopping_receipt"]["reason"] == "only_the_active_approved_winner_can_be_reopened"

    approved = _complete_lifecycle(conn, child_id, corrected=True)
    parent_after = conn.execute(
        "SELECT state, chat_use_permission, superseded_by_concept_id FROM selene_comprehension_concepts WHERE id = ?",
        (parent["id"],),
    ).fetchone()
    winner = approved["decision"]["item"]
    active_count = conn.execute(
        """
        SELECT COUNT(*) FROM selene_comprehension_concepts
        WHERE (id = ? OR root_concept_id = ?)
          AND state = 'approved_knowledge_resource'
          AND review_status = 'approved_for_knowledge_use'
          AND chat_use_permission = 'available_as_knowledge_resource'
        """,
        (parent["id"], parent["id"]),
    ).fetchone()[0]
    retrieved = retrieve_approved_knowledge(
        conn, "Why does tea in an insulated mug still cool?", limit=10
    )
    old_node_stop = route_request(
        conn, "comprehension.concepts.decide", _reopen_payload(parent["id"])
    )["result"]

    assert parent_after["state"] == "superseded"
    assert parent_after["chat_use_permission"] == "not_available"
    assert parent_after["superseded_by_concept_id"] == child_id
    assert winner["id"] == child_id
    assert winner["parent_concept_id"] == parent["id"]
    assert winner["root_concept_id"] == parent["id"]
    assert approved["decision"]["lineage_receipt"]["active_winner_concept_id"] == child_id
    assert active_count == 1
    assert retrieved["items"][0]["id"] == child_id
    assert "completely stops" not in retrieved["items"][0]["central_claim"]
    assert old_node_stop["status"] == "comprehension_revision_lineage_stopped"
    assert old_node_stop["stopping_receipt"]["reason"] == "superseded_lineage_node_cannot_reopen"
    assert old_node_stop["stopping_receipt"]["active_winner_concept_id"] == child_id


def test_revision_requires_a_visible_reason_and_attributable_source(tmp_path):
    conn = _conn(tmp_path)
    parent = _propose(
        conn,
        concept_key="synthetic_phase6c_missing_review_basis",
        material="An insulated container completely stops heat transfer.",
        source_ref="synthetic:phase6c:original-missing-basis",
    )
    _complete_lifecycle(conn, parent["id"])

    without_reason = _reopen_payload(parent["id"])
    without_reason["correction_reason"] = ""
    with pytest.raises(ValueError, match="correction_reason"):
        route_request(conn, "comprehension.concepts.decide", without_reason)

    without_source = _reopen_payload(parent["id"])
    without_source["revision_source_refs"] = []
    with pytest.raises(ValueError, match="revision_source_refs"):
        route_request(conn, "comprehension.concepts.decide", without_source)

    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 1


def test_delayed_ordinary_chat_uses_reviewed_reconstruction_from_only_the_correction_winner(tmp_path):
    db_path = tmp_path / "selene.sqlite3"
    conn = connect(db_path)
    init_db(conn)
    _seed_activation_ready_state(conn)
    route_request(
        conn,
        "activation.approve",
        {"approval_phrase": ACTIVATION_APPROVAL_PHRASE},
    )
    parent = _propose(
        conn,
        concept_key="synthetic_phase6c_delayed_chat",
        material="An insulated container completely stops heat transfer between its contents and surroundings.",
        source_ref="synthetic:phase6c:delayed-original",
    )
    _complete_lifecycle(conn, parent["id"])
    child = route_request(
        conn, "comprehension.concepts.decide", _reopen_payload(parent["id"])
    )["result"]["item"]
    _complete_lifecycle(conn, child["id"], corrected=True)
    near = route_request(
        conn,
        "comprehension.concepts.propose",
        {
            "concept_key": "synthetic_phase6c_container_capacity_near_concept",
            "title": "Container capacity and current amount",
            "domain": "synthetic.phase6c.measurement_capacity",
            "material": "A container's capacity is different from the amount currently inside it.",
            "principles": ["Capacity is a maximum amount, not a report of current contents."],
            "relationships": ["Current volume can change while container capacity stays fixed."],
            "examples": ["A pitcher can be nearly empty while retaining the same capacity."],
            "counterexamples": ["Current amount and maximum capacity are not interchangeable."],
            "limits": ["Capacity alone does not report the present amount."],
            "source_refs": ["synthetic:phase6c:near-container-capacity"],
        },
    )["result"]["item"]
    route_request(
        conn,
        "comprehension.understanding.evaluate",
        {
            "concept_id": near["id"],
            "teach_back": "Capacity describes how much a container can hold, while the current amount says how much is in it now.",
            "application": "A large pitcher can have high capacity even when it currently contains only one cup of liquid.",
            "limits": ["Capacity alone does not report the present amount."],
            "counterexample": "An empty container can still have a large capacity.",
            "correction_response": "I would separate maximum capacity from current contents.",
            "source_alignment": True,
        },
    )
    route_request(
        conn,
        "comprehension.concepts.decide",
        {"concept_id": near["id"], "action": "approve_knowledge"},
    )
    conn.close()

    delayed_conn = connect(db_path)
    result = route_request(
        delayed_conn,
        "selene_chat.send",
        {
            "text": (
                "Explain why soup in a sealed insulated container cools gradually, "
                "and name one limit of insulation."
            )
        },
    )["result"]

    knowledge = result["comprehension_integration"]["knowledge_context"]
    retrieved_ids = [item["id"] for item in knowledge["items"]]
    selected_ids = [item["id"] for item in knowledge["answer_eligible_items"]]
    selected = knowledge["answer_eligible_items"][0]
    reconstruction = selected["reviewed_reconstruction"]
    visible = result["candidate_text"].lower()

    assert child["id"] in retrieved_ids
    assert near["id"] in retrieved_ids
    assert selected_ids == [child["id"]]
    assert selected["lineage_receipt"]["active_winner_concept_id"] == child["id"]
    assert reconstruction["status"] == "reviewed_correction_reconstruction_available"
    assert reconstruction["source_parroting_check_passed"] is True
    assert "more slowly" in visible
    assert "transfer continues" in visible
    assert "completely stops" not in visible
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
