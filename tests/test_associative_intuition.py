from __future__ import annotations

import json

from selene.associative_intuition import (
    accept_association_for_study,
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
from selene.study_workspace import start_study_session


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


def test_delayed_material_cue_reactivates_once_while_weak_earlier_resemblance_stops(tmp_path):
    conn = _conn(tmp_path)
    _approved_concept(conn)
    changes_before = conn.total_changes

    early = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "Something about the cart seems related."},
    )
    delayed = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "Could a push change the cart's motion?"},
    )
    repeated = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "Could a push change the cart's motion?"},
    )

    assert early["selected_state"] == "no_connection_noticed"
    assert early["stopping_receipt"]["stop_reason"] == "no_useful_connection_noticed"
    assert delayed["selected_state"] == "articulated_connection"
    assert delayed["selected_candidate"]["fit_receipt"]["transferable_structure_articulated"] is True
    assert delayed["selected_candidate"]["fit_receipt"]["new_evidence_supplied"] is False
    assert repeated["selected_candidate"]["candidate_id"] == delayed["selected_candidate"]["candidate_id"]
    assert conn.total_changes == changes_before
    _assert_bounded(delayed)


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
    assert result["stopping_receipt"]["stop_reason"] == "no_useful_connection_noticed"
    assert result["stopping_receipt"]["recursive_reactivation_requested"] is False


def test_request_scaffolding_does_not_become_associative_content(tmp_path):
    conn = _conn(tmp_path)
    _approved_concept(conn)

    result = build_associative_intuition_bridge(
        conn,
        {"trigger_text": "Why does that check work? Give one reason and name a limit."},
    )

    assert result["contribution_ready"] is False
    assert result["contribution_candidates"] == []
    selected = result["selected_candidate"]
    if selected:
        shared_terms = selected["activation_basis"]["shared_terms"]
        assert not {"why", "check", "work", "give", "one", "reason", "limit"}.intersection(shared_terms)


def test_personal_memory_privacy_is_reused_before_content_enters_association_text(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO selene_memory_candidates
        (memory_category, title, summary, source_refs, provenance_boundary,
         consent_scope, chat_use_permission, state, review_status, payload_json)
        VALUES ('relational', 'Private comet garden', 'The cobalt comet garden used a spiral gate behind the moon arch.',
                '["memory:private:test"]', 'test_memory_boundary',
                'private_selene_aleks_context', 'can_use_in_chat',
                'approved_active_memory', 'approved_memory', ?)
        """,
        (
            json.dumps(
                {
                    "eligible_channels": ["desktop"],
                    "minimum_authentication_strength": "local_desktop_session",
                }
            ),
        ),
    )
    conn.commit()

    held = build_associative_intuition_bridge(
        conn,
        {
            "trigger_text": "Could the cobalt comet garden use a spiral gate here?",
            "speaker_envelope": {
                "claimed_speaker": "Demo guest",
                "channel": "mobile",
                "authentication_strength": "transport_claim_only",
            },
        },
    )
    visible = json.dumps(held)
    privacy_hold = next(
        item for item in held["held_back_sources"] if item["source_class"] == "approved_personal_memory"
    )

    assert "behind the moon arch" not in visible.lower()
    assert privacy_hold["reason"] == "memory_privacy_scope_does_not_include_current_speaker"
    assert privacy_hold["content_entered_candidate_text"] is False
    assert privacy_hold["candidate_created"] is False
    assert held["memory_privacy_gate_reused"] is True
    assert held["speaker_envelope_applied"] is True

    eligible = build_associative_intuition_bridge(
        conn,
        {
            "trigger_text": "Could the cobalt comet garden use a spiral gate here?",
            "speaker_envelope": {
                "claimed_speaker": "Aleks",
                "channel": "desktop",
                "authentication_strength": "local_desktop_session",
            },
        },
    )
    memory_candidates = [
        item for item in eligible["candidates"] if item["source_class"] == "approved_personal_memory"
    ]
    assert len(memory_candidates) == 1
    assert memory_candidates[0]["personal_memory_is_domain_truth"] is False
    _assert_bounded(eligible)


def test_private_explicit_source_is_held_with_a_stop_receipt_before_candidate_text(tmp_path):
    conn = _conn(tmp_path)
    result = build_associative_intuition_bridge(
        conn,
        {
            "trigger_text": "Does the hidden orbital phrase connect?",
            "source_packets": [
                {
                    "source_ref": "raw_corpus:private-1",
                    "summary": "HIDDEN ORBITAL PHRASE MUST NOT ENTER A CANDIDATE",
                }
            ],
        },
    )

    assert "HIDDEN ORBITAL PHRASE" not in json.dumps(result)
    assert result["held_back_sources"][0]["reason"] == "private_source_reference_is_not_eligible_for_association_use"
    assert result["held_back_sources"][0]["content_entered_candidate_text"] is False
    assert result["stopping_receipt"]["stop_reason"] == "no_useful_connection_noticed"


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


def test_explicitly_accepted_association_enters_one_idempotent_study_thread(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _approved_concept(conn)
    session_id = int(
        start_study_session(
            conn,
            {"concept_ids": [concept_id], "title": "Synthetic association Study"},
        )["item"]["id"]
    )
    trigger = "Could a push change the cart's motion?"
    bridge = build_associative_intuition_bridge(conn, {"trigger_text": trigger})
    candidate_id = bridge["selected_candidate"]["candidate_id"]

    accepted = accept_association_for_study(
        conn,
        {
            "actor": "Aleks",
            "trigger_text": trigger,
            "candidate_id": candidate_id,
            "study_session_id": session_id,
        },
    )
    repeated = route_request(
        conn,
        "associative_intuition.study.accept",
        {
            "actor": "Aleks",
            "trigger_text": trigger,
            "candidate_id": candidate_id,
            "study_session_id": session_id,
        },
    )["result"]
    thread = conn.execute(
        "SELECT * FROM selene_study_pondering_threads WHERE id = ?",
        (accepted["study_thread_id"],),
    ).fetchone()
    payload = json.loads(thread["payload_json"])

    assert accepted["status"] == "association_entered_study"
    assert accepted["created"] is True
    assert accepted["study_write_performed"] is True
    assert accepted["association_is_evidence"] is False
    assert accepted["association_is_proof"] is False
    assert accepted["association_is_fact"] is False
    assert accepted["association_is_memory"] is False
    assert accepted["association_is_finished_answer"] is False
    assert repeated["status"] == "association_study_lineage_already_active"
    assert repeated["created"] is False
    assert repeated["study_thread_id"] == accepted["study_thread_id"]
    assert conn.execute(
        "SELECT COUNT(*) FROM selene_study_pondering_threads WHERE session_id = ?", (session_id,)
    ).fetchone()[0] == 1
    assert thread["state"] == "active"
    assert "provisional association" in thread["current_fit"].lower()
    assert payload["origin_kind"] == "associative_intuition"
    assert payload["automatic_memory_write"] is False
    assert accepted["stopping_receipt"]["stop_reason"] == "explicit_acceptance_routed_once"
    assert accepted["lineage_receipt"]["lineage_version"] == "v1_origin_parent_destination_stop"
    assert accepted["lineage_receipt"]["destination"] == "study_pondering"
    assert repeated["stopping_receipt"]["stop_reason"] == "duplicate_lineage_existing_thread_reused"
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    _assert_bounded(accepted)


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
