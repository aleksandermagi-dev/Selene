from __future__ import annotations

import sqlite3

from selene.current_turn_fact_ledger import (
    build_current_turn_fact_ledger,
    current_turn_fact_ledger_status,
)
from selene.pragmatic_planner import build_pragmatic_plan
from selene.module_router import route_request


def _ledger(prompt: str) -> dict:
    plan = build_pragmatic_plan({"prompt": prompt})
    return build_current_turn_fact_ledger(
        {
            "session_id": 17,
            "prompt": prompt,
            "obligations": plan["response_obligations"],
        }
    )


def _assert_locked(result: dict) -> None:
    assert result["writes_state"] is False
    assert result["durable_memory_write"] is False
    assert result["retained_knowledge_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_status_declares_one_turn_nonpersistent_coordination() -> None:
    result = current_turn_fact_ledger_status()

    assert result["scope"] == "one_visible_current_turn_only"
    assert result["owner_inputs_are_answers"] is False
    assert result["current_turn_facts_precede_optional_retrieval"] is True
    _assert_locked(result)


def test_router_exposes_the_fact_ledger_as_inspectable_nonwriting_machinery() -> None:
    conn = sqlite3.connect(":memory:")
    status = route_request(conn, "current_turn_facts.status")["result"]
    built = route_request(
        conn,
        "current_turn_facts.build",
        {"session_id": 2, "prompt": "Compare paper and card."},
    )["result"]

    assert status["status"] == "current_turn_fact_ledger_ready"
    assert built["status"] == "current_turn_fact_ledger_ready"
    assert built["facts_are_durable_memory"] is False
    _assert_locked(status)
    _assert_locked(built)


def test_comparison_paraphrases_preserve_options_and_criterion() -> None:
    first = _ledger("Compare paper and thin card. Durability matters more.")
    second = _ledger(
        "Contrast paper with thin card. The deciding factor is durability."
    )

    for ledger in (first, second):
        owner = ledger["owner_inputs"][0]
        assert [item.casefold() for item in owner["supplied_fields"]["options"]] == [
            "paper",
            "thin card",
        ]
        assert [item.casefold() for item in owner["supplied_fields"]["criteria"]] == [
            "durability"
        ]
        assert {"option", "criterion"}.issubset(ledger["facts_by_kind"])
        assert ledger["facts_are_durable_memory"] is False
        _assert_locked(ledger)


def test_comparison_request_clause_is_not_part_of_the_second_option() -> None:
    variants = (
        "Compare lanterns and mirrors and tell me which should come first.",
        "Contrast cedar with glass and explain which should come first.",
    )

    assert [
        _ledger(prompt)["owner_inputs"][0]["supplied_fields"]["options"]
        for prompt in variants
    ] == [["lanterns", "mirrors"], ["cedar", "glass"]]


def test_mixed_comparison_choice_and_reason_share_current_turn_support() -> None:
    ledger = _ledger(
        "Compare paper and thin card. Paper costs 2 dollars and thin card costs "
        "4 dollars. Durability matters more. Choose one and explain why."
    )
    by_function = {
        function: owner
        for owner in ledger["owner_inputs"]
        for function in owner["requested_response_functions"]
    }

    assert {"comparison", "choice", "reason"}.issubset(by_function)
    assert len(by_function["comparison"]["supplied_fields"]["options"]) == 2
    assert by_function["choice"]["supplied_fields"]["criteria"] == ["Durability"]
    quantity_ids = [
        item["id"] for item in ledger["facts"] if item["kind"] == "quantity"
    ]
    assert len(quantity_ids) == 2
    assert len(set(quantity_ids)) == 2


def test_direct_correction_preserves_new_and_replaced_values() -> None:
    ledger = _ledger("Actually, I meant 29, not 34. Recalculate the difference.")
    correction = next(item for item in ledger["facts"] if item["kind"] == "correction")

    assert correction["value"] == "29"
    assert correction["replaced_value"] == "34"
    assert any(
        "corrections" in owner["supplied_field_names"]
        for owner in ledger["owner_inputs"]
    )
    assert ledger["owner_inputs_are_answers"] is False
    _assert_locked(ledger)


def test_plain_observed_motion_is_available_to_the_hypothesis_owner() -> None:
    ledger = _ledger(
        "A plant bends toward one window each afternoon. Give one hypothesis, "
        "one alternative, and the smallest next observation."
    )
    owner = next(
        item
        for item in ledger["owner_inputs"]
        if "hypothesis" in item["requested_response_functions"]
    )

    assert owner["supplied_fields"]["observations"] == [
        "A plant bends toward one window each afternoon."
    ]
    assert owner["supplied_fields"]["relations"][0]["predicate"] == "bends"
    assert "observation" in ledger["facts_by_kind"]
    _assert_locked(ledger)


def test_natural_whether_choice_preserves_action_options_without_fixture_nouns() -> None:
    ledger = _ledger(
        "I'm deciding whether to sketch indoors or walk by the river. Which sounds better?"
    )

    options = [item["value"] for item in ledger["facts"] if item["kind"] == "option"]
    assert options == ["sketch indoors", "walk by the river"]
    assert all("porch" not in item.casefold() for item in options)
    _assert_locked(ledger)


def test_coordinated_attributes_are_separate_visible_relations() -> None:
    ledger = _ledger("A green cup is cracked and a silver cup is new.")
    relations = [item for item in ledger["facts"] if item["kind"] == "relation"]

    assert [
        (item["subject"], item["predicate"], item["object"])
        for item in relations
    ] == [
        ("green cup", "is", "cracked"),
        ("silver cup", "is", "new"),
    ]
    assert all(item["relation_type"] == "attribute" for item in relations)
    _assert_locked(ledger)


def test_requested_placement_is_an_operation_not_an_observed_state() -> None:
    ledger = _ledger("Move the green cup to the cabinet.")
    operation = next(item for item in ledger["facts"] if item["kind"] == "operation")

    assert operation["action"] == "move"
    assert operation["subject"] == "green cup"
    assert operation["object"] == "cabinet"
    assert operation["operation_status"] == "requested_not_executed"
    assert not any(
        item.get("state_update") is True for item in ledger["facts"]
    )
    _assert_locked(ledger)
