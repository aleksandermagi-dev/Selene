from __future__ import annotations

import json

from selene.associative_intuition import (
    associative_intuition_status,
    build_associative_intuition_bridge,
)
from selene.conversational_contribution import (
    build_conversational_contribution_packet,
)
from selene.db import connect, init_db
from selene.dream_state import _collect_source_candidates
from selene.metacognition import evaluate_metacognition
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _approved_concept(
    conn,
    *,
    key="forces_motion",
    title="Pushes and pulls",
    domain="elementary science",
    claim="A push or pull can change an object's motion.",
    relationships=None,
):
    cursor = conn.execute(
        """
        INSERT INTO selene_comprehension_concepts
        (concept_key, title, domain, central_claim, principles_json,
         relationships_json, examples_json, counterexamples_json, limits_json,
         source_refs, provenance_boundary, confidence, retention_state,
         chat_use_permission, state, review_status, payload_json)
        VALUES (?, ?, ?, ?, '[]', ?, '[]', '[]', '[]', ?, ?, 'reviewed',
                'retained_approved_knowledge', 'available_as_knowledge_resource',
                'approved_knowledge_resource', 'approved_for_knowledge_use', '{}')
        """,
        (
            key,
            title,
            domain,
            claim,
            json.dumps(relationships or ["Forces influence whether motion changes."]),
            json.dumps([f"teaching_item:{key}"]),
            "test_source_bound_approved_knowledge",
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _assert_bounded(result):
    assert result["is_organ"] is False
    assert result["connective_tissue_only"] is True
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["automatic_memory_write"] is False
    assert result["automatic_study_write"] is False
    assert result["automatic_dream_routing"] is False
    assert result["truth_decision_authority"] is False
    assert result["expression_authority"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["autonomous_action_allowed"] is False


def test_status_declares_connective_tissue_not_a_new_organ(tmp_path):
    conn = _conn(tmp_path)
    _approved_concept(conn)

    status = associative_intuition_status(conn)

    assert status["status"] == "associative_intuition_bridge_ready"
    assert status["eligible_source_counts"]["approved_knowledge"] == 1
    assert status["writes_records"] is False
    _assert_bounded(status)


def test_structural_cues_can_form_a_felt_connection_without_forcing_words(tmp_path):
    conn = _conn(tmp_path)
    _approved_concept(conn)

    result = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "A shove makes the resting cart move."},
    )

    assert result["status"] == "associative_intuition_candidate_ready"
    assert result["selected_state"] == "felt_connection"
    assert result["selected_candidate"]["activation_basis"]["shared_semantic_cues"] == [
        "change_motion",
        "force_influence",
    ]
    assert result["contribution_ready"] is False
    assert result["contribution_candidates"] == []
    assert result["study_handoff"]["available"] is True
    assert result["study_handoff"]["automatic_write"] is False
    _assert_bounded(result)


def test_supported_terms_and_relations_can_supply_one_provisional_connection(tmp_path):
    conn = _conn(tmp_path)
    _approved_concept(conn)

    bridge = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "Could a push change the cart's motion?"},
    )
    contribution = build_conversational_contribution_packet(
        {
            "content_seed": "We can compare the cart before and after the push.",
            "upstream_candidates": bridge["contribution_candidates"],
        }
    )

    assert bridge["selected_state"] == "articulated_connection"
    assert bridge["contribution_ready"] is True
    assert len(bridge["contribution_candidates"]) == 1
    assert contribution["selected_kind"] == "connection"
    assert contribution["selection_count"] == 1
    assert bridge["selected_candidate"]["association_is_proof"] is False
    _assert_bounded(bridge)


def test_one_broad_resemblance_does_not_create_a_connection(tmp_path):
    conn = _conn(tmp_path)
    _approved_concept(conn)

    result = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "The purple sunset looked beautiful."},
    )

    assert result["status"] == "associative_intuition_no_connection_noticed"
    assert result["selected_state"] == "no_connection_noticed"
    assert result["candidate_count"] == 0
    assert result["study_handoff"]["available"] is False


def test_already_active_dual_horizon_material_is_not_reactivated(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _approved_concept(conn)

    result = build_associative_intuition_bridge(
        conn,
        {
            "trigger_text": "Could a push change the cart's motion?",
            "dual_horizon_context": {
                "approved_long_range_horizon": {
                    "selected_context_ids": [f"approved-knowledge-{concept_id}"]
                }
            },
        },
    )

    assert result["candidate_count"] == 0
    assert any(
        item["reason"] == "source_is_already_active_in_dual_horizon"
        for item in result["held_back_sources"]
    )


def test_only_reviewed_expression_eligible_dream_material_can_reactivate(tmp_path):
    conn = _conn(tmp_path)
    cycle_id = int(
        conn.execute(
            """
            INSERT INTO selene_dream_cycles
            (cycle_key, cycle_label, phase, source_snapshot_json, source_refs,
             provenance_boundary, review_status, payload_json)
            VALUES ('cycle-association-test', 'Association test', 'awake_with_pending_review', '[]',
                    '[]', 'test_dream_boundary', 'pending_review', '{}')
            """
        ).lastrowid
    )
    for key, state, review, eligible in (
        ("pending", "pending_review", "pending_review", 0),
        ("approved", "approved_for_expression", "reviewed", 1),
    ):
        conn.execute(
            """
            INSERT INTO selene_dream_reflections
            (cycle_id, reflection_key, reflection_kind, title, reflection,
             why_it_may_matter, uncertainty, source_refs, state, review_status,
             expression_eligible, provenance_boundary, payload_json)
            VALUES (?, ?, 'cross_source_pattern', ?, ?, ?, ?, '[]', ?, ?, ?,
                    'test_dream_boundary', '{}')
            """,
            (
                cycle_id,
                f"dream-{key}",
                f"{key.title()} motion reflection",
                "A push may change motion in a related system.",
                "The relationship may be worth comparing.",
                "Similarity is not proof.",
                state,
                review,
                eligible,
            ),
        )
    conn.commit()

    result = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "Could a push change motion here?"},
    )

    dream_sources = [
        item
        for item in result["candidates"]
        if item["source_class"] == "approved_dream_reflection"
    ]
    assert len(dream_sources) == 1
    assert dream_sources[0]["source_title"] == "Approved motion reflection"


def test_metacognition_observes_the_bridge_without_upgrading_it(tmp_path):
    conn = _conn(tmp_path)
    _approved_concept(conn)
    bridge = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "A shove makes the resting cart move."},
    )

    result = evaluate_metacognition(
        {
            "prompt": "What might connect here?",
            "candidate_text": "There may be a connection worth inspecting.",
            "associative_intuition": bridge,
        }
    )

    assessment = result["associative_intuition_assessment"]
    assert assessment["observed"] is True
    assert assessment["selected_state"] == "felt_connection"
    assert assessment["association_used_as_evidence"] is False
    assert assessment["association_used_as_proof"] is False
    assert assessment["automatic_retention"] is False


def test_visible_study_connections_are_available_to_dream_without_becoming_memory(tmp_path):
    conn = _conn(tmp_path)
    session_id = int(
        conn.execute(
            """
            INSERT INTO selene_study_sessions
            (session_key, title, focus, source_refs, provenance_boundary)
            VALUES ('study-association-test', 'Motion study', 'motion', '[]',
                    'test_study_boundary')
            """
        ).lastrowid
    )
    conn.execute(
        """
        INSERT INTO selene_study_notes
        (session_id, note_kind, meaning_summary, note_text, source_refs,
         provenance_boundary)
        VALUES (?, 'connection', ?, ?, '[]', 'test_study_boundary')
        """,
        (
            session_id,
            "Push and motion may connect through force.",
            "This is still a working connection.",
        ),
    )
    conn.commit()
    changes_before = conn.total_changes

    candidates = _collect_source_candidates(conn)

    study = [item for item in candidates if item["reflection_kind"] == "study_pondering"]
    assert len(study) == 1
    assert "working Study note" in study[0]["uncertainty"]
    assert conn.total_changes == changes_before


def test_status_and_preview_routes_are_read_only(tmp_path):
    conn = _conn(tmp_path)
    _approved_concept(conn)
    changes_before = conn.total_changes

    status = route_request(conn, "associative_intuition.status", {})
    preview = route_request(
        conn,
        "associative_intuition.preview",
        {"trigger_text": "Could a push change the cart's motion?"},
    )

    assert status["result"]["status"] == "associative_intuition_bridge_ready"
    assert preview["result"]["selected_state"] == "articulated_connection"
    assert status["authority_event"]["persisted"] is False
    assert preview["authority_event"]["persisted"] is False
    assert conn.total_changes == changes_before
