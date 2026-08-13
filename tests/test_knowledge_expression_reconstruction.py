from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.knowledge_expression_reconstruction import (
    build_knowledge_expression_handoff,
    knowledge_expression_reconstruction_status,
)
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _plant_item(concept_id=7):
    return {
        "id": concept_id,
        "concept_id": concept_id,
        "concept_key": "test:plant_growth",
        "title": "Plant growth",
        "domain": "elementary_science",
        "central_claim": "Plants need light to make food.",
        "principles": ["Light supplies energy used in food-making processes."],
        "relationships": ["Growth depends on several resources working together."],
        "examples": ["A seedling near a sunny window grows toward the light."],
        "counterexamples": ["A plastic plant does not grow in sunlight."],
        "limits": ["Light alone does not replace water or nutrients."],
        "confidence": "reviewed",
        "source_refs": ["source:test:plant-growth"],
    }


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["retained_knowledge_write_active"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["database_write_performed"] is False


def test_ordinary_approved_knowledge_becomes_structured_meaning_not_a_surface_script():
    seed = (
        "Plants need light to make food. "
        "Light supplies energy used in food-making processes."
    )
    result = build_knowledge_expression_handoff(
        {
            "prompt": "Why do plants need light?",
            "content_seed": seed,
            "answer_basis": {
                "answer_kind": "why_supported",
                "source_refs": ["source:test:plant-growth"],
            },
            "knowledge_items": [_plant_item()],
            "certainty": "reviewed",
        }
    )

    packet = result["semantic_packet"]
    units = packet["units"]
    assert result["active"] is True
    assert result["source_wording_is_default_visible_script"] is False
    assert result["compatibility_seed_is_expression_authority"] is False
    assert result["original_expression_required"] is True
    assert result["structured_unit_count"] == 2
    assert packet["expression_mode"] == "meaning_first_reconstruction"
    assert packet["formation_mode"] == "structured"
    assert packet["source_refs"] == ["source:test:plant-growth"]
    assert units[0]["text"] == ""
    assert units[0]["subject"].lower() == "plants"
    assert units[0]["subject_number"] == "plural"
    assert units[0]["predicate"] == "need"
    assert units[0]["object"] == "light to make food"
    assert units[1]["knowledge_field"] == "principle"
    assert units[1]["relation"] == "cause"
    assert all(item["source_wording_required"] is False for item in units)
    _assert_locked(result)


def test_limit_negation_and_provenance_survive_structural_reconstruction():
    seed = (
        "Plants need light to make food. "
        "Light alone does not replace water or nutrients."
    )
    result = build_knowledge_expression_handoff(
        {
            "prompt": "What is one limit of that relationship?",
            "content_seed": seed,
            "answer_basis": {"answer_kind": "limit_supported"},
            "knowledge_items": [_plant_item()],
        }
    )

    limit = result["semantic_packet"]["units"][1]
    assert limit["role"] == "limit"
    assert limit["relation"] == "contrast"
    assert limit["predicate"] == "replace"
    assert limit["polarity"] == "negative"
    assert "negation" in limit["required_terms"]
    assert limit["source_refs"] == ["source:test:plant-growth"]


def test_exact_quote_request_keeps_attributed_wording_locked():
    seed = "Plants need light to make food."
    result = build_knowledge_expression_handoff(
        {
            "prompt": "Quote the exact wording from the approved source.",
            "content_seed": seed,
            "answer_basis": {"answer_kind": "central_claim"},
            "knowledge_items": [_plant_item()],
        }
    )

    unit = result["semantic_packet"]["units"][0]
    assert result["source_wording_is_surface_requirement"] is True
    assert result["original_expression_required"] is False
    assert result["exactness_lock_count"] == 1
    assert unit["realization_mode"] == "text_grounded"
    assert unit["text"] == seed
    assert unit["exactness_lock"] is True
    assert unit["exactness_reason"] == "attributed_exact_wording_requested"


def test_prompt_derived_application_stays_supported_without_becoming_fake_source_wording():
    sentence = "A computer could store one row for each recorded date."
    result = build_knowledge_expression_handoff(
        {
            "prompt": "What could a computer help with?",
            "content_seed": sentence,
            "answer_basis": {
                "answer_kind": "obligation_bound_knowledge",
                "obligation_support": [
                    {
                        "obligation_id": "computer-help",
                        "concept_id": 7,
                        "support_field": "bounded_application",
                        "source_refs": ["source:test:plant-growth"],
                    }
                ],
            },
            "knowledge_items": [_plant_item()],
        }
    )

    unit = result["semantic_packet"]["units"][0]
    assert result["prompt_synthesis_unit_count"] == 1
    assert unit["realization_mode"] == "text_grounded"
    assert unit["knowledge_field"] == "bounded_application"
    assert unit["obligation_ids"] == ["computer-help"]
    assert unit["source_wording_required"] is False


def test_nlo_uses_meaning_handoff_and_reconstructs_the_multi_clause_surface(tmp_path):
    conn = _conn(tmp_path)
    seed = (
        "Plants need light to make food. "
        "Light supplies energy used in food-making processes."
    )
    item = _plant_item()
    handoff = build_knowledge_expression_handoff(
        {
            "prompt": "Why do plants need light?",
            "content_seed": seed,
            "answer_basis": {"answer_kind": "why_supported"},
            "knowledge_items": [item],
        }
    )
    changes_before = conn.total_changes
    result = realize_native_language(
        conn,
        {
            "prompt": "Why do plants need light?",
            "content_seed": seed,
            "visible_speech_seed": {
                "selected_source_id": "approved_comprehension",
                "selected_source_class": "approved_knowledge",
                "content_seed": seed,
                "release_allowed": True,
            },
            "comprehension_context": {
                "status": "comprehension_packet_ready",
                "knowledge_response_seed": seed,
                "knowledge_expression_handoff": handoff,
                "supported_semantics": handoff["semantic_packet"],
                "knowledge_context": {"answer_eligible_items": [item]},
            },
            "intent_decision": {
                "intent": "reasoning",
                "answer_shape": "best_current_answer",
            },
            "source_refs": ["source:test:plant-growth"],
        },
        record_run=False,
    )

    meaning = result["meaning_packet"]
    assert meaning["supported_semantics"]["used"] is True
    assert meaning["supported_semantics"]["expression_mode"] == "meaning_first_reconstruction"
    assert meaning["knowledge_expression_handoff"]["active"] is True
    assert meaning["knowledge_expression_handoff"]["compatibility_seed_is_expression_authority"] is False
    assert result["formation"]["formation_mode"] == "structured"
    assert result["candidate_text"] != seed
    assert "Plants need light to make food" in result["candidate_text"]
    assert "light supplies energy" in result["candidate_text"]
    assert conn.total_changes == changes_before


def test_comprehension_and_preview_routes_expose_the_meaning_first_handoff(tmp_path):
    conn = _conn(tmp_path)
    item = _plant_item(concept_id=0)
    cursor = conn.execute(
        """
        INSERT INTO selene_comprehension_concepts
        (concept_key, title, domain, central_claim, principles_json,
         relationships_json, examples_json, counterexamples_json, limits_json,
         source_refs, provenance_boundary, confidence, retention_state,
         chat_use_permission, state, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'test_boundary', 'reviewed',
                'retained_reviewed_knowledge', 'available_as_knowledge_resource',
                'approved_knowledge_resource', 'approved_for_knowledge_use', '{}')
        """,
        (
            item["concept_key"],
            item["title"],
            item["domain"],
            item["central_claim"],
            json.dumps(item["principles"]),
            json.dumps(item["relationships"]),
            json.dumps(item["examples"]),
            json.dumps(item["counterexamples"]),
            json.dumps(item["limits"]),
            json.dumps(item["source_refs"]),
        ),
    )
    conn.commit()
    changes_before = conn.total_changes

    status = route_request(conn, "native_language.knowledge_expression.status")["result"]
    preview = route_request(
        conn,
        "native_language.knowledge_expression.preview",
        {
            "prompt": "Why do plants need light?",
            "content_seed": "Plants need light to make food.",
            "answer_basis": {"answer_kind": "central_claim"},
            "knowledge_items": [{**item, "id": int(cursor.lastrowid)}],
        },
    )["result"]
    comprehension = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "Explain plant growth and why light matters for plants.",
            "intent_decision": {
                "intent": "reasoning",
                "reasoning_requested": True,
                "dialogue_acts": ["question"],
            },
        },
    )["result"]

    assert status["status"] == "knowledge_expression_reconstruction_ready"
    assert preview["active"] is True
    assert comprehension["knowledge_expression_handoff"]["active"] is True
    assert comprehension["supported_semantics"]["expression_mode"] == "meaning_first_reconstruction"
    assert comprehension["knowledge_response_seed"]
    assert conn.total_changes == changes_before
