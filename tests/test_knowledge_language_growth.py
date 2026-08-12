from __future__ import annotations

import http.client
import json
import threading

from selene.db import connect, init_db
from selene.knowledge_language_growth import (
    build_knowledge_language_growth,
    knowledge_language_growth_status,
    list_knowledge_language_resources,
)
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.sidecar import SeleneHandler, SeleneServer


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_approved_teaching(conn, *, approved=True, source_refs=True, parroting_passed=True):
    refs = ["source:test:plant-growth"] if source_refs else []
    payload = {
        "lexical_entries": [
            {
                "id": "plant_growth_need",
                "field": "predicate",
                "lemma": "need",
                "forms": ["need", "require"],
                "sense": "depend on a supplied condition or resource",
                "part_of_speech": "transitive_verb",
                "grammatical_behavior": ["takes the required resource as its object"],
                "registers": ["ordinary", "science"],
                "collocations": ["need light", "require water"],
                "near_concepts": ["prefer"],
                "distinctions": ["a need is not merely a preference"],
                "source_refs": refs,
            }
        ]
    }
    cursor = conn.execute(
        """
        INSERT INTO selene_comprehension_concepts
        (concept_key, title, domain, central_claim, principles_json,
         relationships_json, examples_json, counterexamples_json, limits_json,
         source_refs, provenance_boundary, confidence, retention_state,
         chat_use_permission, state, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test:plant_growth",
            "Plant growth",
            "elementary_science",
            "Plants need light to make food.",
            json.dumps(["Light supplies energy used in food-making processes."]),
            json.dumps(["Growth depends on several resources working together."]),
            json.dumps(["A seedling near a sunny window grows toward the light."]),
            json.dumps(["A plastic plant does not grow when placed in sunlight."]),
            json.dumps(["Light alone does not replace water or nutrients."]),
            json.dumps(refs),
            "test_approved_teaching_only",
            "reviewed",
            "retained_knowledge_resource" if approved else "candidate_not_retained",
            "available_as_knowledge_resource" if approved else "not_active_until_approved",
            "approved_knowledge_resource" if approved else "proposed_understanding",
            "approved_for_knowledge_use" if approved else "pending_cocoon_teaching_review",
            json.dumps(payload),
        ),
    )
    concept_id = int(cursor.lastrowid)
    acquire = {
        "vocabulary": ["plant", "light", "growth", "resource"],
    }
    express = {
        "explanation_in_original_language": "A plant uses light as one resource in making and supporting its food supply.",
        "distinct_examples": ["A seedling bends toward a bright window over several days."],
        "analogies": ["Light is one input in a larger living system."],
        "questions": ["Which resource is missing in this example?"],
        "comparisons": ["Light provides energy while water supplies material and transport."],
        "natural_conversational_participation": "We can explain the relationship and then check which condition is missing.",
        "limits": ["Light alone does not replace water or nutrients."],
        "counterexamples": ["A plastic plant does not grow in sunlight."],
        "correction_response": "I would revise the claim if it treated light as the only requirement.",
        "source_parroting_check": {"passed": parroting_passed},
        "understanding_evaluation": {"sufficient": True},
        "education_expression_personality_law": {"permitted": True},
    }
    conn.execute(
        """
        INSERT INTO selene_teaching_lifecycles
        (lifecycle_key, concept_id, current_stage, acquire_status, acquire_json,
         integrate_status, integrate_json, express_status, express_json,
         approval_status, source_refs, provenance_boundary, review_status,
         approval_mode)
        VALUES (?, ?, ?, 'complete', ?, 'complete', ?, 'complete', ?, ?, ?, ?, ?, ?)
        """,
        (
            f"lifecycle:test:{concept_id}",
            concept_id,
            "approved_knowledge_resource" if approved else "express_complete_awaiting_aleks_review",
            json.dumps(acquire),
            json.dumps({"status": "complete"}),
            json.dumps(express),
            "approved_by_aleks" if approved else "awaiting_aleks_review",
            json.dumps(refs),
            "test_teaching_lifecycle",
            "status_only",
            "item_exception_approval" if approved else "awaiting_decision",
        ),
    )
    conn.commit()
    return concept_id


def _knowledge_context(concept_id):
    item = {
        "id": concept_id,
        "concept_id": concept_id,
        "concept_key": "test:plant_growth",
        "title": "Plant growth",
        "domain": "elementary_science",
        "central_claim": "Plants need light to make food.",
        "principles": ["Light supplies energy used in food-making processes."],
        "relationships": ["Growth depends on several resources working together."],
        "examples": ["A seedling near a sunny window grows toward the light."],
        "counterexamples": ["A plastic plant does not grow when placed in sunlight."],
        "limits": ["Light alone does not replace water or nutrients."],
        "source_refs": ["source:test:plant-growth"],
    }
    return {
        "status": "comprehension_packet_ready",
        "knowledge_context": {
            "available": True,
            "answer_eligible": True,
            "answer_eligible_items": [item],
        },
    }


def _assert_locked(payload):
    assert payload["meaning_change_allowed"] is False
    assert payload["fact_generation_allowed"] is False
    assert payload["certainty_change_allowed"] is False
    assert payload["evidence_change_allowed"] is False
    assert payload["source_change_allowed"] is False
    assert payload["memory_write_active"] is False
    assert payload["identity_change_allowed"] is False
    assert payload["personality_change_allowed"] is False
    assert payload["governance_change_allowed"] is False
    assert payload["authority_change_allowed"] is False
    assert payload["training_allowed"] is False
    assert payload["lora_allowed"] is False


def test_approved_complete_teaching_compiles_vocabulary_and_affordances(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_approved_teaching(conn)
    status = knowledge_language_growth_status(conn)
    listed = list_knowledge_language_resources(conn)["items"]

    assert status["available_resource_count"] == 1
    assert status["reviewed_vocabulary_term_count"] == 4
    assert status["explicit_lexical_entry_count"] == 1
    assert listed[0]["concept_id"] == concept_id
    assert listed[0]["available_to_nlo"] is True
    assert "explanation" in listed[0]["construction_affordances"]
    assert "counterexample" in listed[0]["construction_affordances"]
    assert listed[0]["teaching_answers_exposed_as_templates"] is False
    _assert_locked(status)
    _assert_locked(listed[0])


def test_incomplete_or_provenance_free_teaching_remains_held(tmp_path):
    conn = _conn(tmp_path)
    _seed_approved_teaching(conn, approved=False, source_refs=False, parroting_passed=False)
    listed = list_knowledge_language_resources(conn, {"include_held": True})["items"]

    assert len(listed) == 1
    assert listed[0]["available_to_nlo"] is False
    assert "knowledge_not_approved" in listed[0]["held_reasons"]
    assert "missing_source_provenance" in listed[0]["held_reasons"]
    assert "source_parroting_check_incomplete" in listed[0]["held_reasons"]


def test_growth_labels_only_text_already_selected_for_the_answer(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_approved_teaching(conn)
    seed = (
        "Plants need light to make food. "
        "A seedling near a sunny window grows toward the light. "
        "Light alone does not replace water or nutrients."
    )
    result = build_knowledge_language_growth(
        conn,
        {
            "comprehension_context": _knowledge_context(concept_id),
            "content_seed": seed,
            "content_source_class": "approved_knowledge",
        },
    )

    assert result["active"] is True
    assert [item["role"] for item in result["content_units"]] == [
        "thesis",
        "example",
        "limitation",
    ]
    assert "A plastic plant" not in " ".join(item["text"] for item in result["content_units"])
    assert all(item["text_was_already_selected_for_answer"] for item in result["content_units"])
    assert all(item["text_generated_by_growth_bridge"] is False for item in result["content_units"])
    assert result["content_added"] is False
    assert result["teaching_answers_used_as_templates"] is False
    _assert_locked(result)


def test_nlo_and_loom_use_growth_roles_without_writes_or_source_parroting(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_approved_teaching(conn)
    changes_before = conn.total_changes
    seed = (
        "Plants need light to make food. "
        "A seedling near a sunny window grows toward the light. "
        "Light alone does not replace water or nutrients."
    )
    result = realize_native_language(
        conn,
        {
            "prompt": "Explain plant growth with an example and its limit.",
            "content_seed": seed,
            "visible_speech_seed": {
                "selected_source_id": "approved_comprehension",
                "selected_source_class": "approved_knowledge",
                "content_seed": seed,
                "release_allowed": True,
            },
            "comprehension_context": _knowledge_context(concept_id),
            "response_depth": "developed",
            "source_refs": ["source:test:plant-growth"],
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
        },
        record_run=False,
    )

    growth = result["knowledge_language_growth"]
    discourse = result["discourse_plan"]["supported_discourse"]
    assert result["version"] == "v32_human_conversational_realization"
    assert growth["active"] is True
    assert [item["role"] for item in discourse["content_units"]] == [
        "thesis",
        "example",
        "limitation",
    ]
    assert all(item["text_generated_by_growth_bridge"] is False for item in discourse["content_units"])
    assert result["revision"]["knowledge_language_growth_checked"] is True
    assert result["revision"]["knowledge_language_growth_content_added"] is False
    assert result["revision"]["teaching_answers_used_as_templates"] is False
    assert result["voice_handoff"]["knowledge_language_growth"] == growth
    assert conn.total_changes == changes_before


def test_growth_status_items_preview_and_http_routes_are_read_only(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _seed_approved_teaching(conn)
    changes_before = conn.total_changes
    payload = {
        "comprehension_context": _knowledge_context(concept_id),
        "content_seed": "Plants need light to make food.",
        "content_source_class": "approved_knowledge",
    }
    status = route_request(conn, "native_language.knowledge_growth.status")["result"]
    items = route_request(conn, "native_language.knowledge_growth.items")["result"]
    preview = route_request(conn, "native_language.knowledge_growth.preview", payload)["result"]

    assert status["status"] == "knowledge_language_growth_ready"
    assert items["item_count"] == 1
    assert preview["active"] is True
    assert conn.total_changes == changes_before

    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    _seed_approved_teaching(server.conn)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request("GET", "/api/native-language/knowledge-growth/status")
        status_response = client.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request("GET", "/api/native-language/knowledge-growth/items")
        items_response = client.getresponse()
        items_payload = json.loads(items_response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request(
            "POST",
            "/api/native-language/knowledge-growth/preview",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        preview_response = client.getresponse()
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        client.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert status_response.status == 200
    assert status_payload["status"] == "knowledge_language_growth_ready"
    assert items_response.status == 200
    assert items_payload["item_count"] == 1
    assert preview_response.status == 200
    assert preview_payload["active"] is True
