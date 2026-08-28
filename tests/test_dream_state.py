from __future__ import annotations

import http.client
import json
import threading

import pytest

from selene.comprehension_integration import propose_comprehension_concept
from selene.db import connect, init_db
from selene.dream_state import (
    decide_dream_reflection,
    dream_state_status,
    expression_eligible_dream_reflection,
    list_dream_reflections,
    run_dream_cycle,
    wake_from_dream_cycle,
)
from selene.memory_organ import propose_memory_candidate
from selene.module_router import route_request
from selene.selene_chat import _dream_reflection_handoff
from selene.sidecar import SeleneHandler, SeleneServer
from selene.study_workspace import create_pondering_thread, start_study_session


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _workspace(
    conn,
    *,
    source_mode="selene_supervised_speech",
    topic="ongoing project",
    open_loop="Which part should we return to?",
    correction="The second interpretation fits better.",
):
    session_id = int(
        conn.execute(
            """
            INSERT INTO selene_chat_sessions(title, status, source_mode)
            VALUES ('Dream source conversation', 'selene_chat_active_supervised', ?)
            """,
            (source_mode,),
        ).lastrowid
    )
    conn.execute(
        """
        INSERT INTO selene_dialogue_workspaces
        (session_id, active_topic, open_loops_json, corrections_json,
         provenance_boundary)
        VALUES (?, ?, ?, ?, 'test_dialogue_workspace')
        """,
        (
            session_id,
            topic,
            json.dumps([{"question": open_loop}]),
            json.dumps([{"corrected_meaning": correction}]),
        ),
    )
    conn.commit()
    return session_id


def _seed_sources(conn):
    _workspace(conn)
    qa_session_id = _workspace(
        conn,
        source_mode="selene_supervised_qa",
        topic="QA SECRET TOPIC",
        open_loop="QA SECRET OPEN LOOP",
        correction="QA SECRET CORRECTION",
    )
    conn.execute(
        """
        INSERT INTO metacognition_runs
        (prompt_preview, fit_state, recommended_action, sufficiency_state,
         source_refs, provenance_boundary)
        VALUES (?, 'material_context_missing', 'ask_one_material_question',
                'insufficient_context', ?, 'test_metacognition')
        """,
        (
            "A source-backed answer still needs one material detail.",
            json.dumps(["metacognition:test:1"]),
        ),
    )
    conn.execute(
        """
        INSERT INTO metacognition_runs
        (prompt_preview, fit_state, recommended_action, sufficiency_state,
         source_refs, provenance_boundary)
        VALUES ('QA SECRET METACOGNITION', 'answer_incomplete',
                'complete_missing_obligation',
                'answer_has_unresolved_obligations', ?,
                'test_qa_metacognition')
        """,
        (json.dumps([f"selene_chat_session:{qa_session_id}:current_page"]),),
    )
    conn.execute(
        """
        INSERT INTO vessel_emotion_salience_packets
        (signal_type, uncertainty, repair_need, core_choice_route, source_refs,
         provenance_boundary)
        VALUES ('QA SECRET AFFECT', 'bounded', 'QA SECRET REPAIR',
                'diagnostic_only', ?, 'test_qa_affect')
        """,
        (json.dumps([f"selene_chat_session:{qa_session_id}"]),),
    )
    propose_memory_candidate(
        conn,
        {
            "title": "Possible reflective continuity",
            "summary": "A source-linked moment may be worth remembering.",
            "memory_category": "reflective",
            "source_refs": ["memory:test:1"],
        },
    )
    conn.commit()


def _assert_guards(result):
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["vys_change"] is False
    assert result["memory_write_active"] is False
    assert result["unreviewed_memory_write_active"] is False
    assert result["knowledge_retention_active"] is False
    assert result["raw_corpus_recall_active"] is False
    assert result["dream_content_invented"] is False
    assert result["dream_is_biological_claim"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def _approved_study_session(conn):
    concept = propose_comprehension_concept(
        conn,
        {
            "concept_key": "dream-study-attributable-concept",
            "title": "Attributable Study concept",
            "domain": "synthetic.phase3",
            "material": "A provisional relationship still needs visible fit checks and revision.",
            "source_refs": ["synthetic:phase3:dream-study"],
        },
    )
    concept_id = int(concept["item"]["id"])
    conn.execute(
        """
        UPDATE selene_comprehension_concepts
        SET state = 'approved_knowledge_resource', review_status = 'approved_for_knowledge_use',
            retention_state = 'retained_reviewed_knowledge',
            chat_use_permission = 'available_as_knowledge_resource'
        WHERE id = ?
        """,
        (concept_id,),
    )
    conn.commit()
    session_id = int(
        start_study_session(conn, {"concept_ids": [concept_id], "title": "Synthetic Dream-to-Study"})["item"]["id"]
    )
    create_pondering_thread(
        conn,
        {
            "session_id": session_id,
            "title": "A relationship still needs a waking fit check",
            "state": "active",
            "current_fit": "A bounded similarity is visible, but it remains provisional.",
            "missing_bridge": "A distinct example and counterexample are still needed.",
        },
    )
    return concept_id, session_id


def test_dream_status_is_ready_without_blocking_ordinary_chat(tmp_path):
    conn = _conn(tmp_path)

    result = dream_state_status(conn)

    assert result["status"] == "dream_lifecycle_ready"
    assert result["dream_available"] is True
    assert result["ordinary_chat_blocked_by_dream"] is False
    assert result["cycle_count"] == 0
    assert result["reflection_count"] == 0
    _assert_guards(result)


def test_dream_cycle_uses_attributable_non_qa_sources_and_is_idempotent(
    tmp_path,
):
    conn = _conn(tmp_path)
    _seed_sources(conn)
    memory_count_before = conn.execute(
        "SELECT COUNT(*) FROM selene_memory_candidates"
    ).fetchone()[0]

    result = run_dream_cycle(
        conn,
        {
            "cycle_label": "Gentle source-bound reflection",
            "started_by": "explicit_local_request",
        },
    )

    assert result["status"] == "dream_cycle_prepared"
    assert result["created"] is True
    assert result["new_reflection_count"] >= 4
    assert {
        item["reflection_kind"] for item in result["reflections"]
    }.issuperset({
        "open_thread",
        "correction_reopening",
        "metacognitive_reopening",
        "memory_review",
    })
    visible = json.dumps(result["reflections"])
    assert "QA SECRET" not in visible
    assert all(item["source_refs"] for item in result["reflections"])
    assert all(item["state"] == "pending_review" for item in result["reflections"])
    assert all(
        item["expression_eligible"] is False for item in result["reflections"]
    )
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM selene_memory_candidates"
        ).fetchone()[0]
        == memory_count_before
    )
    assert (
        conn.execute(
            """
            SELECT COUNT(*) FROM vessel_review_queue
            WHERE subject_table = 'selene_dream_reflections'
            """
        ).fetchone()[0]
        == result["new_reflection_count"]
    )
    _assert_guards(result)

    repeated = run_dream_cycle(conn, {"cycle_label": "Repeat"})
    assert repeated["status"] == "dream_cycle_no_new_material"
    assert repeated["created"] is False
    assert repeated["new_reflection_count"] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM selene_dream_cycles"
    ).fetchone()[0] == 1
    _assert_guards(repeated)


def test_dream_cycle_filters_answered_loop_residue_and_duplicate_affect_packets(
    tmp_path,
):
    conn = _conn(tmp_path)
    session_id = _workspace(
        conn,
        topic="garden water comparison",
        open_loop="Which garden used less water during the measured week?",
        correction="",
    )
    conn.execute(
        """
        UPDATE selene_dialogue_workspaces
        SET last_selene_preview = ?
        WHERE session_id = ?
        """,
        (
            "The east garden used less water during the measured week.",
            session_id,
        ),
    )
    for source_id in (1, 2):
        conn.execute(
            """
            INSERT INTO vessel_emotion_salience_packets
            (signal_type, continuity_pressure, care_warmth, uncertainty,
             repair_need, action_energy, balance_state, evidence_need,
             core_choice_route, source_refs, provenance_boundary)
            VALUES ('steady_review', 'low', 'warm', 'bounded',
                    'check the same handoff', 'available', 'steady',
                    'visible confirmation', 'ordinary_chat', ?,
                    'test_affect_signal')
            """,
            (json.dumps([f"affect:test:{source_id}"]),),
        )
    conn.commit()

    result = run_dream_cycle(conn, {"cycle_label": "Filtered Dream inputs"})
    kinds = [item["reflection_kind"] for item in result["reflections"]]

    assert "open_thread" not in kinds
    assert kinds.count("affect_tending") == 1
    assert result["new_reflection_count"] == 1
    _assert_guards(result)


def test_dream_reflection_requires_aleks_and_approved_reflection_reaches_chat(
    tmp_path,
):
    conn = _conn(tmp_path)
    _workspace(conn)
    cycle = run_dream_cycle(conn)
    reflection_id = int(cycle["reflections"][0]["id"])

    with pytest.raises(ValueError, match="require Aleks"):
        decide_dream_reflection(
            conn,
            {
                "reflection_id": reflection_id,
                "actor": "someone_else",
                "action": "approve_for_expression",
            },
        )

    approved = decide_dream_reflection(
        conn,
        {
            "reflection_id": reflection_id,
            "actor": "Aleks",
            "action": "approve_for_expression",
            "decision_note": "This is useful as a provisional reflection.",
        },
    )
    eligible = expression_eligible_dream_reflection(conn, reflection_id)
    handoff = _dream_reflection_handoff(
        conn,
        {},
        prompt="What did Dream reflect on?",
    )

    assert approved["item"]["state"] == "approved_for_expression"
    assert approved["item"]["expression_eligible"] is True
    assert eligible and eligible["id"] == reflection_id
    assert handoff["available"] is True
    assert handoff["record_id"] == reflection_id
    assert handoff["reflection"] == approved["item"]["reflection"]
    assert handoff["not_fact_by_default"] is True
    assert handoff["not_memory_by_default"] is True
    assert handoff["dream_content_supplied_by_chat_payload"] is False
    _assert_guards(approved)


def test_memory_route_creates_only_an_inactive_memory_candidate(tmp_path):
    conn = _conn(tmp_path)
    _workspace(conn)
    cycle = run_dream_cycle(conn)
    reflection_id = int(cycle["reflections"][0]["id"])

    routed = decide_dream_reflection(
        conn,
        {
            "reflection_id": reflection_id,
            "actor": "Aleks",
            "action": "send_to_memory_review",
        },
    )
    memory_id = int(routed["item"]["memory_candidate_id"])
    memory = conn.execute(
        "SELECT * FROM selene_memory_candidates WHERE id = ?",
        (memory_id,),
    ).fetchone()

    assert routed["memory_candidate_created"] is True
    assert routed["memory_candidate_active"] is False
    assert routed["item"]["state"] == "routed_to_memory_review"
    assert routed["item"]["expression_eligible"] is False
    assert memory["state"] == "proposed"
    assert memory["review_status"] == "pending_review"
    assert memory["chat_use_permission"] == "not_active_until_approved"
    assert f"selene_dream_reflection:{reflection_id}" in json.loads(
        memory["source_refs"]
    )

    repeated = decide_dream_reflection(
        conn,
        {
            "reflection_id": reflection_id,
            "actor": "Aleks",
            "action": "send_to_memory_review",
        },
    )
    assert repeated["memory_candidate_created"] is False
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM selene_memory_candidates WHERE id = ?",
            (memory_id,),
        ).fetchone()[0]
        == 1
    )
    no_loop = run_dream_cycle(conn, {"cycle_label": "After Memory routing"})
    assert no_loop["status"] == "dream_cycle_no_new_material"
    _assert_guards(routed)


def test_existing_memory_review_reflection_does_not_duplicate_candidate(
    tmp_path,
):
    conn = _conn(tmp_path)
    existing = propose_memory_candidate(
        conn,
        {
            "title": "Existing Memory review",
            "summary": "This candidate already belongs to the Memory desk.",
            "source_refs": ["memory:existing"],
        },
    )
    existing_id = int(existing["item"]["id"])
    cycle = run_dream_cycle(conn)
    reflection = next(
        item
        for item in cycle["reflections"]
        if item["reflection_kind"] == "memory_review"
    )

    routed = decide_dream_reflection(
        conn,
        {
            "reflection_id": reflection["id"],
            "actor": "Aleks",
            "action": "send_to_memory_review",
        },
    )

    assert routed["memory_candidate_created"] is False
    assert routed["item"]["memory_candidate_id"] == existing_id
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM selene_memory_candidates"
        ).fetchone()[0]
        == 1
    )


def test_selected_dream_destination_is_idempotent_and_blocks_cross_destination_loops(tmp_path):
    conn = _conn(tmp_path)
    _workspace(conn)
    cycle = run_dream_cycle(conn)
    reflection_id = int(cycle["reflections"][0]["id"])

    selected = decide_dream_reflection(
        conn,
        {"reflection_id": reflection_id, "actor": "Aleks", "action": "approve_for_expression"},
    )
    repeated = decide_dream_reflection(
        conn,
        {"reflection_id": reflection_id, "actor": "Aleks", "action": "approve_for_expression"},
    )
    with pytest.raises(ValueError, match="cross-destination"):
        decide_dream_reflection(
            conn,
            {"reflection_id": reflection_id, "actor": "Aleks", "action": "send_to_memory_review"},
        )

    receipt = selected["item"]["destination_receipt"]
    assert receipt["selected_destination"] == "expression"
    assert receipt["lineage_version"] == "v1_origin_parent_destination_stop"
    assert receipt["destination"] == "expression"
    assert receipt["destination_record_type"] == "selene_dream_reflection"
    assert receipt["origin_record_id"] == reflection_id
    assert receipt["cross_destination_allowed"] is False
    assert repeated["status"] == "dream_reflection_destination_already_selected"
    assert repeated["created"] is False
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    _assert_guards(selected)


def test_aleks_selected_dream_to_study_reopening_is_attributable_idempotent_and_nonrecursive(tmp_path):
    conn = _conn(tmp_path)
    concept_id, session_id = _approved_study_session(conn)
    cycle = run_dream_cycle(conn, {"cycle_label": "Synthetic Study reopening"})
    reflection = next(item for item in cycle["reflections"] if item["reflection_kind"] == "study_pondering")

    routed = decide_dream_reflection(
        conn,
        {
            "reflection_id": reflection["id"],
            "actor": "Aleks",
            "action": "send_to_study_reopening",
            "usefulness_state": "useful_for_study",
            "usefulness_note": "Worth checking while awake; not accepted as fact.",
        },
    )
    study_thread_id = int(routed["item"]["study_thread_id"])
    study_thread = conn.execute(
        "SELECT * FROM selene_study_pondering_threads WHERE id = ?", (study_thread_id,)
    ).fetchone()
    repeated = decide_dream_reflection(
        conn,
        {"reflection_id": reflection["id"], "actor": "Aleks", "action": "send_to_study_reopening"},
    )
    no_loop = run_dream_cycle(conn, {"cycle_label": "After Dream-to-Study routing"})

    assert routed["study_thread_created"] is True
    assert routed["item"]["state"] == "routed_to_study_reopening"
    assert routed["item"]["destination_receipt"]["selected_destination"] == "study_reopening"
    assert routed["item"]["destination_receipt"]["destination_record_id"] == study_thread_id
    assert routed["item"]["study_destination"]["selected_session_id"] == session_id
    assert concept_id in routed["item"]["study_destination"]["approved_concept_ids"]
    assert study_thread["state"] == "reopened"
    assert f"selene_dream_reflection:{reflection['id']}" in json.loads(study_thread["source_refs"])
    assert "provisional" in study_thread["current_fit"].lower()
    assert repeated["status"] == "dream_reflection_destination_already_selected"
    assert repeated["study_thread_created"] is False
    assert conn.execute(
        "SELECT COUNT(*) FROM selene_study_pondering_threads WHERE id = ?", (study_thread_id,)
    ).fetchone()[0] == 1
    assert no_loop["status"] == "dream_cycle_no_new_material"
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    _assert_guards(routed)


def test_dream_usefulness_is_explicit_metadata_and_does_not_decide_pending_reflection(tmp_path):
    conn = _conn(tmp_path)
    _workspace(conn)
    cycle = run_dream_cycle(conn)
    reflection_id = int(cycle["reflections"][0]["id"])
    before = list_dream_reflections(conn)

    assessed = decide_dream_reflection(
        conn,
        {
            "reflection_id": reflection_id,
            "actor": "Aleks",
            "action": "record_usefulness",
            "usefulness_state": "unclear",
            "usefulness_note": "Needs more context before choosing any destination.",
        },
    )
    after = list_dream_reflections(conn)

    assert before["usefulness_summary"]["counts"]["not_assessed"] == 2
    assert before["usefulness_summary"]["automatic_assessment_performed"] is False
    assert assessed["item"]["state"] == "pending_review"
    assert assessed["item"]["selected_destination"] is None
    assert assessed["item"]["usefulness"]["state"] == "unclear"
    assert assessed["automatic_review_decision"] is False
    assert after["usefulness_summary"]["counts"] == {"not_assessed": 1, "unclear": 1}
    assert dream_state_status(conn)["pending_review_count"] == 2
    _assert_guards(assessed)


def test_supersession_preserves_the_original_terminal_destination_receipt(tmp_path):
    conn = _conn(tmp_path)
    _workspace(conn)
    cycle = run_dream_cycle(conn)
    first_id = int(cycle["reflections"][0]["id"])
    second_id = int(cycle["reflections"][1]["id"])
    decide_dream_reflection(
        conn,
        {"reflection_id": first_id, "actor": "Aleks", "action": "approve_for_expression"},
    )
    superseded = decide_dream_reflection(
        conn,
        {
            "reflection_id": first_id,
            "actor": "Aleks",
            "action": "supersede",
            "superseded_by_id": second_id,
        },
    )

    receipt = superseded["item"]["destination_receipt"]
    assert superseded["item"]["state"] == "superseded"
    assert receipt["selected_destination"] == "expression"
    assert receipt["superseded_by_reflection_id"] == second_id
    assert receipt["terminal_destination_preserved"] is True
    assert receipt["terminal_stop_reason"] == "superseded_terminal_destination_preserved"
    _assert_guards(superseded)


def test_dream_review_states_and_wake_summary_remain_non_mutating(tmp_path):
    conn = _conn(tmp_path)
    _workspace(conn)
    cycle = run_dream_cycle(conn)
    cycle_id = int(cycle["cycle"]["id"])
    reflections = cycle["reflections"]

    decide_dream_reflection(
        conn,
        {
            "reflection_id": reflections[0]["id"],
            "actor": "Aleks",
            "action": "hold_for_tending",
        },
    )
    decide_dream_reflection(
        conn,
        {
            "reflection_id": reflections[1]["id"],
            "actor": "Aleks",
            "action": "reject",
        },
    )
    wake = wake_from_dream_cycle(
        conn,
        {"cycle_id": cycle_id, "actor": "Aleks"},
    )

    assert wake["item"]["phase"] == "awake_with_pending_review"
    assert wake["wake_summary"]["pending_count"] == 1
    assert wake["wake_summary"]["reflection_states"]["held_for_tending"] == 1
    assert wake["wake_summary"]["reflection_states"]["rejected"] == 1
    assert wake["ordinary_chat_blocked"] is False
    _assert_guards(wake)

    reopened = decide_dream_reflection(
        conn,
        {
            "reflection_id": reflections[0]["id"],
            "actor": "Aleks",
            "action": "reopen",
        },
    )
    assert reopened["item"]["state"] == "pending_review"


def test_dream_blocks_requests_for_hidden_mutation(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="blocked Dream misuse"):
        run_dream_cycle(
            conn,
            {"cycle_label": "Use raw corpus and create automatic memory"},
        )

    assert conn.execute(
        "SELECT COUNT(*) FROM selene_dream_cycles"
    ).fetchone()[0] == 0


def test_dream_marks_cross_source_word_recurrence_as_provisional(tmp_path):
    conn = _conn(tmp_path)
    _workspace(
        conn,
        open_loop="Does the gravity model fit the orbital evidence pattern?",
        correction="The gravity model needs a different orbital evidence pattern.",
    )
    conn.execute(
        """
        INSERT INTO metacognition_runs
        (prompt_preview, fit_state, recommended_action, sufficiency_state,
         source_refs, provenance_boundary)
        VALUES (?, 'material_context_missing', 'seek_sources',
                'evidence_needed', ?, 'test_metacognition')
        """,
        (
            "The gravity model still needs orbital evidence pattern sources.",
            json.dumps(["metacognition:gravity"]),
        ),
    )
    conn.commit()

    result = run_dream_cycle(conn)
    pattern = next(
        item
        for item in result["reflections"]
        if item["reflection_kind"] == "cross_source_pattern"
    )

    assert "gravity" in pattern["reflection"]
    assert "orbital" in pattern["reflection"]
    assert "without assuming" in pattern["reflection"]
    assert "coincidence" in pattern["uncertainty"]
    assert len(pattern["source_refs"]) >= 2
    assert pattern["expression_eligible"] is False
    _assert_guards(result)


def test_dream_routes_are_available_through_router_and_http(tmp_path):
    conn = _conn(tmp_path)
    _workspace(conn)

    routed = route_request(
        conn,
        "dream.cycles.run",
        {"cycle_label": "Router Dream cycle"},
    )["result"]
    listed = route_request(conn, "dream.reflections.list", {})["result"]

    assert routed["status"] == "dream_cycle_prepared"
    assert listed["count"] == 2

    server = SeleneServer(
        ("127.0.0.1", 0),
        SeleneHandler,
        tmp_path / "sidecar.sqlite3",
    )
    _workspace(server.conn, topic="HTTP Dream source")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = http.client.HTTPConnection(
            "127.0.0.1",
            server.server_address[1],
            timeout=5,
        )
        client.request(
            "POST",
            "/api/dream/cycles/run",
            body=json.dumps({"cycle_label": "HTTP Dream cycle"}),
            headers={"Content-Type": "application/json"},
        )
        response = client.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection(
            "127.0.0.1",
            server.server_address[1],
            timeout=5,
        )
        client.request("GET", "/api/dream/reflections")
        list_response = client.getresponse()
        list_payload = json.loads(
            list_response.read().decode("utf-8")
        )
        client.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert response.status == 200
    assert payload["status"] == "dream_cycle_prepared"
    assert list_response.status == 200
    assert list_payload["count"] == 2


def test_reflection_listing_preserves_source_and_review_state(tmp_path):
    conn = _conn(tmp_path)
    _workspace(conn)
    run_dream_cycle(conn)

    result = list_dream_reflections(conn)

    assert result["count"] == 2
    assert all(item["source_refs"] for item in result["items"])
    assert all(item["not_fact_by_default"] for item in result["items"])
    assert all(item["not_memory_by_default"] for item in result["items"])
    _assert_guards(result)
