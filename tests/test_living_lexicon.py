from __future__ import annotations

import http.client
import json
import threading

from selene.db import connect, init_db
from selene.language_teaching_shelf import prepare_language_teaching_shelf
from selene.living_lexicon import (
    enrich_semantic_units_from_living_lexicon,
    list_living_lexicon,
    living_lexicon_status,
    query_living_lexicon,
)
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.sidecar import SeleneHandler, SeleneServer


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False


def test_living_lexicon_derives_reviewed_entries_without_a_new_retention_store(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    tables_before = {
        str(row[0])
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    changes_before = conn.total_changes

    status = living_lexicon_status(conn)
    items = list_living_lexicon(conn)

    tables_after = {
        str(row[0])
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    assert status["status"] == "living_lexicon_ready"
    assert status["reviewed_language_lesson_count"] == 61
    assert status["reviewed_vocabulary_term_count"] >= 250
    assert status["reviewed_vocabulary_catalog_entry_count"] >= 250
    assert status["available_surface_entry_count"] == 4
    assert status["available_surface_form_count"] == 9
    assert status["reviewed_terms_are_automatic_synonyms"] is False
    assert status["derived_at_query_time"] is True
    assert status["database_write_performed"] is False
    assert items["item_count"] == 4
    held = list_living_lexicon(
        conn,
        {"source_kind": "reviewed_language_term_catalog", "include_held": True, "limit": 5},
    )
    assert held["item_count"] == 5
    assert all(item["available_to_nlo"] is False for item in held["items"])
    assert all("no_reviewed_surface_equivalence_set" in item["held_reasons"] for item in held["items"])
    assert conn.total_changes == changes_before
    assert tables_after == tables_before
    assert not any("lexicon" in name for name in tables_after)
    _assert_locked(status)
    _assert_locked(items)


def test_living_lexicon_matches_only_the_reviewed_field_form_and_register(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    match = query_living_lexicon(
        conn,
        {"field": "predicate", "form": "begin with", "register": "planning"},
    )
    mismatch = query_living_lexicon(
        conn,
        {"field": "predicate", "form": "begin with", "register": "tender"},
    )

    assert match["status"] == "living_lexicon_match_ready"
    assert match["forms"] == ["start with", "begin with", "lead with"]
    assert match["entries"][0]["source_id"] == "answer_then_expand"
    assert match["entries"][0]["understanding_state"] == "reviewed_language_guidance"
    assert "approved" not in " ".join(match["forms"]).lower()
    assert mismatch["status"] == "living_lexicon_no_supported_match"
    assert mismatch["forms"] == []
    _assert_locked(match)


def test_prompt_grounded_entries_are_available_for_one_query_and_never_persisted(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    entry = {
        "id": "current_turn_inspect",
        "field": "predicate",
        "lemma": "inspect",
        "forms": ["inspect", "examine"],
        "sense": "look carefully at the supplied object in the current task",
        "part_of_speech": "transitive_verb",
        "grammatical_behavior": ["takes the supplied object as its object"],
        "registers": ["ordinary", "technical"],
        "understanding_state": "prompt_grounded",
        "source_refs": ["current_turn:test"],
    }

    current = query_living_lexicon(
        conn,
        {
            "field": "predicate",
            "form": "inspect",
            "prompt_grounded_entries": [entry],
        },
    )
    later = query_living_lexicon(conn, {"field": "predicate", "form": "inspect"})
    held = query_living_lexicon(
        conn,
        {
            "field": "predicate",
            "form": "invented alternate",
            "prompt_grounded_entries": [
                {
                    **entry,
                    "id": "missing_provenance",
                    "lemma": "invented alternate",
                    "forms": ["invented alternate"],
                    "source_refs": [],
                }
            ],
        },
    )

    assert current["forms"] == ["inspect", "examine"]
    assert current["entries"][0]["durable"] is False
    assert current["prompt_grounded_entries_persisted"] is False
    assert later["status"] == "living_lexicon_no_supported_match"
    assert held["status"] == "living_lexicon_no_supported_match"
    assert conn.total_changes == changes_before


def test_only_approved_knowledge_with_explicit_lexical_metadata_contributes_entries(tmp_path):
    conn = _conn(tmp_path)
    lexical_entry = {
        "id": "supported_observation",
        "field": "object",
        "lemma": "supported observation",
        "forms": ["supported observation", "evidence-backed observation"],
        "sense": "an observation whose stated support is available",
        "part_of_speech": "noun_phrase",
        "grammatical_behavior": ["can fill an object role"],
        "registers": ["technical"],
        "source_refs": ["source:test:observation"],
        "exactness_lock": True,
    }
    common = (
        "title", "general", "central claim", "[]", "[]", "[]", "[]", "[]",
        json.dumps(["source:test:concept"]), "test:living_lexicon", "clear",
        "retained_reviewed_knowledge", "available_as_knowledge_resource",
        "test correction", json.dumps({"lexical_entries": [lexical_entry]}),
    )
    conn.execute(
        """
        INSERT INTO selene_comprehension_concepts
        (concept_key, title, domain, central_claim, principles_json, relationships_json,
         examples_json, counterexamples_json, limits_json, source_refs,
         provenance_boundary, confidence, retention_state, chat_use_permission,
         correction_path, payload_json, state, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                'approved_knowledge_resource', 'approved_for_knowledge_use')
        """,
        ("approved_lexical_concept", *common),
    )
    conn.execute(
        """
        INSERT INTO selene_comprehension_concepts
        (concept_key, title, domain, central_claim, principles_json, relationships_json,
         examples_json, counterexamples_json, limits_json, source_refs,
         provenance_boundary, confidence, retention_state, chat_use_permission,
         correction_path, payload_json, state, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                'proposed_understanding', 'pending_cocoon_teaching_review')
        """,
        ("unapproved_lexical_concept", *common),
    )
    conn.commit()

    result = query_living_lexicon(
        conn,
        {"field": "object", "form": "supported observation", "register": "technical"},
    )

    assert result["entry_count"] == 1
    assert result["entries"][0]["source_kind"] == "approved_knowledge"
    assert result["entries"][0]["source_id"] == "approved_lexical_concept"
    assert result["forms"] == ["supported observation", "evidence-backed observation"]
    assert result["entries"][0]["exactness_lock"] is True
    enriched = enrich_semantic_units_from_living_lexicon(
        conn,
        [
            {
                "id": "exact_observation",
                "subject": "the record",
                "predicate": "contain",
                "object": "supported observation",
            }
        ],
    )
    assert enriched["units"][0]["lexical_choices"]["object"] == ["supported observation"]


def test_living_lexicon_enriches_structured_units_but_respects_exactness_locks(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    ordinary = {
        "id": "preserve_structure",
        "subject": "the revision",
        "predicate": "preserve",
        "object": "the supported structure",
        "required": True,
        "source_refs": ["test:current_turn"],
    }
    locked = {**ordinary, "id": "locked_preserve", "exactness_lock": True}

    enriched = enrich_semantic_units_from_living_lexicon(conn, [ordinary, locked])

    assert enriched["selected_entry_keys"] == [
        "language:lexical_variation:living_preserve_supported_meaning"
    ]
    assert enriched["units"][0]["lexical_choices"]["predicate"] == ["preserve", "keep"]
    assert "lexical_choices" not in enriched["units"][1]
    assert enriched["exactness_locks_respected"] is True
    assert enriched["meaning_change_allowed"] is False


def test_nlo_uses_living_lexicon_on_structured_meaning_without_adding_content(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    changes_before = conn.total_changes
    result = realize_native_language(
        conn,
        {
            "prompt": "What should the revision do?",
            "content_seed": "The revision preserves the supported structure.",
            "semantic_propositions": [
                {
                    "id": "preserve_structure",
                    "subject": "the revision",
                    "predicate": "preserve",
                    "object": "the supported structure",
                    "required": True,
                    "meaning_keys": ["revision retains supported structure"],
                    "source_refs": ["test:current_turn"],
                }
            ],
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
            "conversation_context": {"turn_count": 3},
        },
        record_run=False,
    )

    assert result["version"] == "v32_human_conversational_realization"
    assert result["meaning_packet"]["living_lexicon"]["selected_entry_count"] == 1
    assert result["semantic_frame"]["propositions"][0]["lexical_choices"]["predicate"] == [
        "preserve",
        "keep",
    ]
    assert result["formation"]["lexical_choice_unit_count"] == 1
    assert result["candidate_text"].endswith(
        ("The revision preserves the supported structure.", "The revision keeps the supported structure.")
    )
    assert result["revision"]["unsupported_content_generated"] is False
    assert conn.total_changes == changes_before


def test_living_lexicon_routes_are_inspectable_and_read_only(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    changes_before = conn.total_changes

    status = route_request(conn, "native_language.lexicon.status")["result"]
    items = route_request(
        conn,
        "native_language.lexicon.items",
        {"field": "predicate", "limit": 2},
    )["result"]
    query = route_request(
        conn,
        "native_language.lexicon.query",
        {"field": "predicate", "form": "select"},
    )["result"]

    assert status["status"] == "living_lexicon_ready"
    assert items["item_count"] == 2
    assert query["forms"] == ["choose", "select"]
    assert conn.total_changes == changes_before
    _assert_locked(status)


def test_living_lexicon_http_status_and_query_routes_are_available(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    prepare_language_teaching_shelf(server.conn)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request("GET", "/api/native-language/lexicon/status")
        status_response = client.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request(
            "POST",
            "/api/native-language/lexicon/query",
            body=json.dumps({"field": "predicate", "form": "keep"}),
            headers={"Content-Type": "application/json"},
        )
        query_response = client.getresponse()
        query_payload = json.loads(query_response.read().decode("utf-8"))
        client.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert status_response.status == 200
    assert status_payload["status"] == "living_lexicon_ready"
    assert query_response.status == 200
    assert query_payload["forms"] == ["preserve", "keep"]
