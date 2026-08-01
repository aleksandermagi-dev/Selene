from __future__ import annotations

import sqlite3

import pytest

from selene.comprehension_integration import propose_comprehension_concept
from selene.db import init_db
from selene.module_router import route_request
from selene.study_workspace import (
    PRIOR_F1_LEA_GOALS,
    answer_study_question,
    ask_study_question,
    form_study_note,
    list_learning_compass,
    list_study_sessions,
    list_study_materials,
    list_open_study_attention,
    seed_prior_f1_lea_learning_compass,
    start_learning_compass_goal,
    start_study_session,
    study_workspace_status,
    update_learning_compass_goal,
    update_study_note_clarification,
    update_study_session,
)


def _conn(tmp_path):
    conn = sqlite3.connect(tmp_path / "selene.db")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def _concept(conn, *, approved: bool = True) -> int:
    result = propose_comprehension_concept(
        conn,
        {
            "concept_key": f"study-test-equal-shares-{'approved' if approved else 'candidate'}",
            "title": "Equal shares",
            "domain": "mathematics.fractions",
            "material": "Equal fractional shares must have the same size.",
            "source_refs": ["curriculum:test:equal-shares"],
        },
    )
    concept_id = int(result["item"]["id"])
    if approved:
        conn.execute(
            """
            UPDATE selene_comprehension_concepts
            SET state = 'approved_knowledge_resource',
                review_status = 'approved_for_knowledge_use',
                retention_state = 'retained_reviewed_knowledge',
                chat_use_permission = 'available_as_knowledge_resource'
            WHERE id = ?
            """,
            (concept_id,),
        )
        conn.commit()
    return concept_id


def _approved_concept_with_key(conn, concept_key: str) -> int:
    result = propose_comprehension_concept(
        conn,
        {
            "concept_key": concept_key,
            "title": concept_key.replace("_", " "),
            "domain": "curriculum.f1.synthetic_lea_support",
            "material": f"Source-supported foundation for {concept_key}.",
            "source_refs": [f"curriculum:test:{concept_key}"],
        },
    )
    concept_id = int(result["item"]["id"])
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
    return concept_id


def _prior_f1_lea_fixture(conn) -> None:
    for concept_key in dict.fromkeys(
        key for goal in PRIOR_F1_LEA_GOALS for key in goal["concept_keys"]
    ):
        _approved_concept_with_key(conn, concept_key)
    for index, goal in enumerate(PRIOR_F1_LEA_GOALS, start=1):
        cursor = conn.execute(
            "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, 'active', 'selene_local')",
            (f"Gentle LEA {index}",),
        )
        session_id = int(cursor.lastrowid)
        conn.execute(
            """
            INSERT INTO selene_chat_messages
            (session_id, role, content, selected_route, source_class, payload_json)
            VALUES (?, 'user', ?, 'answer_now', 'aleks_direct', '{}')
            """,
            (session_id, f"{goal['prompt_fragment']} Continue the gentle activity."),
        )
        conn.execute(
            """
            INSERT INTO selene_chat_messages
            (session_id, role, content, selected_route, source_class, payload_json)
            VALUES (?, 'selene', ?, 'answer_now', 'selene_local', '{}')
            """,
            (session_id, goal["lea_observation"]),
        )
    conn.commit()


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["hidden_retention_allowed"] is False


def test_study_workspace_uses_only_approved_knowledge_and_keeps_visible_evidence(tmp_path):
    conn = _conn(tmp_path)
    approved_id = _concept(conn)
    session = start_study_session(
        conn,
        {"title": "Fractions study", "focus": "Why equal size matters", "concept_ids": [approved_id]},
    )
    session_id = int(session["item"]["id"])
    reflected = update_study_session(
        conn,
        {
            "session_id": session_id,
            "current_understanding": "Fourth means one of four equal shares.",
            "connections": ["Equal shares connect division and fractions."],
            "uncertainties": ["How should an uneven drawing be described?"],
        },
    )

    assert reflected["item"]["current_understanding"].startswith("Fourth means")
    assert len(reflected["learning_evidence"]) == 2
    assert all(item["review_status"] == "descriptive_learning_evidence" for item in reflected["learning_evidence"])
    _assert_locked(reflected)

    unapproved_id = _concept(conn, approved=False)
    with pytest.raises(ValueError, match="approved"):
        start_study_session(conn, {"concept_ids": [unapproved_id]})


def test_study_material_catalog_surfaces_only_approved_chat_eligible_knowledge(tmp_path):
    conn = _conn(tmp_path)
    approved_id = _concept(conn)
    unapproved_id = _concept(conn, approved=False)

    status = study_workspace_status(conn)
    materials = list_study_materials(conn)

    assert status["eligible_material_count"] == 1
    assert [item["id"] for item in materials["items"]] == [approved_id]
    assert materials["items"][0]["study_eligible"] is True
    assert unapproved_id not in [item["id"] for item in materials["items"]]
    _assert_locked(materials)


def test_aleks_answer_resolves_question_in_session_and_proposes_attributed_update(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    started = start_study_session(conn, {"concept_ids": [concept_id]})
    session_id = int(started["item"]["id"])
    asked = ask_study_question(
        conn,
        {
            "session_id": session_id,
            "concept_id": concept_id,
            "question_text": "Why must fourths be equal in size?",
            "formation_state": "ready",
        },
    )
    question_id = int(asked["questions"][0]["id"])
    answered = answer_study_question(
        conn,
        {
            "question_id": question_id,
            "answer": "Because the whole is divided into four shares of the same size; unequal pieces are not four equal shares.",
        },
    )

    question = answered["questions"][0]
    candidate = answered["teaching_update_candidate"]
    assert question["status"] == "answered_in_session"
    assert question["answered_by"] == "Aleks"
    assert answered["answer_use"]["usable_in_current_study_session"] is True
    assert answered["answer_use"]["durable_chat_use"] is False
    assert candidate["state"] == "proposed_understanding"
    assert candidate["chat_use_permission"] == "not_active_until_approved"
    assert "speaker:Aleks" in candidate["source_refs"]
    assert question["teaching_candidate_id"] == candidate["id"]
    _assert_locked(answered)


def test_question_without_words_is_supported_without_inventing_content(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    session_id = int(start_study_session(conn, {"concept_ids": [concept_id]})["item"]["id"])
    result = ask_study_question(
        conn,
        {
            "session_id": session_id,
            "formation_state": "question_without_words",
            "uncertainty_context": "Something about equal size and the whole does not connect yet.",
        },
    )

    assert result["questions"][0]["question_text"] == ""
    assert result["questions"][0]["formation_state"] == "question_without_words"
    _assert_locked(result)


def test_study_session_list_surfaces_open_questions_for_learning_queue(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    session_id = int(start_study_session(conn, {"concept_ids": [concept_id]})["item"]["id"])
    ask_study_question(
        conn,
        {
            "session_id": session_id,
            "question_text": "How does equal size affect the name of a fraction?",
            "formation_state": "ready",
        },
    )

    items = list_study_sessions(conn)["items"]

    assert items[0]["id"] == session_id
    assert items[0]["open_question_count"] == 1
    _assert_locked(list_study_sessions(conn))


def test_selene_notepad_forms_source_linked_note_without_inventing_clarification(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    session_id = int(start_study_session(conn, {"concept_ids": [concept_id]})["item"]["id"])

    no_gap = form_study_note(conn, {"session_id": session_id, "attention_mode": "clarification"})
    formed = form_study_note(conn, {"session_id": session_id})
    repeated = form_study_note(conn, {"session_id": session_id})

    assert no_gap["status"] == "study_clarification_signal_not_present"
    assert no_gap["created"] is False
    assert formed["created"] is True
    assert formed["item"]["note_kind"] == "notice"
    assert formed["item"]["clarification_state"] == "not_needed"
    assert "This is the center of it" in formed["item"]["meaning_summary"]
    assert formed["item"]["note_text"]
    assert formed["item"]["metacognition"]["hidden_chain_of_thought_exposed"] is False
    assert f"selene_study_session:{session_id}" in formed["item"]["source_refs"]
    assert repeated["status"] == "no_new_study_note_signal"
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    _assert_locked(formed)


def test_clarification_lane_moves_uncertainty_into_question_and_tracks_answer(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    session_id = int(start_study_session(conn, {"concept_ids": [concept_id]})["item"]["id"])
    update_study_session(
        conn,
        {
            "session_id": session_id,
            "uncertainties": ["I can name equal shares, but I am not sure how an uneven drawing changes the fraction name."],
        },
    )
    formed = form_study_note(conn, {"session_id": session_id, "attention_mode": "clarification"})
    note_id = int(formed["item"]["id"])
    initially_pinned = list_open_study_attention(conn)

    developing = update_study_note_clarification(
        conn,
        {"note_id": note_id, "action": "develop_question"},
    )
    ready = update_study_note_clarification(
        conn,
        {
            "note_id": note_id,
            "action": "form_question",
            "formation_state": "ready",
            "question_text": "How should an uneven drawing change the name of the shares?",
        },
    )
    question_id = int(ready["item"]["linked_question_id"])
    question_pinned = list_open_study_attention(conn)
    answered = answer_study_question(
        conn,
        {
            "question_id": question_id,
            "answer": "A fraction name describes equal shares of one whole; uneven pieces do not form equal fractional shares.",
        },
    )
    reopened = update_study_note_clarification(conn, {"note_id": note_id, "action": "reopen"})

    assert formed["item"]["note_kind"] == "uncertainty"
    assert formed["item"]["clarification_state"] == "unclear"
    assert initially_pinned["items"][0]["id"] == note_id
    assert initially_pinned["items"][0]["attention_type"] == "clarification_note"
    assert developing["item"]["clarification_state"] == "question_forming"
    assert ready["item"]["clarification_state"] == "question_ready"
    assert question_pinned["open_count"] == 1
    assert question_pinned["items"][0]["linked_question_id"] == question_id
    assert any(int(item["id"]) == question_id for item in ready["session"]["questions"])
    answered_note = next(item for item in answered["notes"] if int(item["id"]) == note_id)
    assert answered_note["clarification_state"] == "answered"
    assert reopened["item"]["clarification_state"] == "reopened"
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    _assert_locked(reopened)


def test_direct_question_stays_in_open_attention_until_answered(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    session_id = int(start_study_session(conn, {"concept_ids": [concept_id]})["item"]["id"])
    asked = ask_study_question(
        conn,
        {
            "session_id": session_id,
            "concept_id": concept_id,
            "question_text": "Why must equal shares have the same size?",
            "formation_state": "ready",
        },
    )
    question_id = int(asked["questions"][0]["id"])

    pinned = list_open_study_attention(conn)
    answer_study_question(conn, {"question_id": question_id, "answer": "Equal names require equal portions of the whole."})
    after_answer = list_open_study_attention(conn)

    assert pinned["open_count"] == 1
    assert pinned["items"][0]["attention_type"] == "direct_question"
    assert pinned["items"][0]["session_id"] == session_id
    assert after_answer["open_count"] == 0
    assert after_answer["answered_items_remain_in_session_history"] is True
    _assert_locked(after_answer)


def test_prior_lea_seeds_four_descriptive_compass_goals_idempotently(tmp_path):
    conn = _conn(tmp_path)
    _prior_f1_lea_fixture(conn)

    first = seed_prior_f1_lea_learning_compass(conn)
    second = seed_prior_f1_lea_learning_compass(conn)

    assert len(first["created"]) == 4
    assert first["goal_count"] == 4
    assert first["open_count"] == 4
    assert first["grading_used"] is False
    assert first["performance_required"] is False
    assert all(item["state"] == "ready_to_explore" for item in first["items"])
    assert all(item["already_connected"] for item in first["items"])
    assert all(item["next_connection"] for item in first["items"])
    assert all(item["noticed_connections"] == [] for item in first["items"])
    assert len(second["created"]) == 0
    assert len(second["already_present"]) == 4
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    _assert_locked(second)


def test_compass_answer_updates_goal_without_claiming_understanding(tmp_path):
    conn = _conn(tmp_path)
    _prior_f1_lea_fixture(conn)
    seeded = seed_prior_f1_lea_learning_compass(conn)
    goal = seeded["items"][0]

    started = start_learning_compass_goal(conn, {"goal_id": goal["id"]})
    session_id = int(started["session"]["item"]["id"])
    concept_id = int(started["session"]["item"]["concept_ids"][0])
    asked = ask_study_question(
        conn,
        {
            "session_id": session_id,
            "concept_id": concept_id,
            "question_text": "Why does the larger tens digit decide this comparison?",
            "uncertainty_context": "I can name the tens, but the comparison still needs a why.",
            "formation_state": "ready",
        },
    )
    question_id = int(asked["questions"][0]["id"])
    question_goal = next(item for item in list_learning_compass(conn)["items"] if int(item["id"]) == int(goal["id"]))

    answer_study_question(
        conn,
        {
            "question_id": question_id,
            "answer": "Three tens already exceed two tens, so the ones do not reverse this comparison.",
        },
    )
    answered_goal = next(item for item in list_learning_compass(conn)["items"] if int(item["id"]) == int(goal["id"]))

    assert question_goal["state"] == "question_ready"
    assert answered_goal["state"] == "answer_received"
    assert answered_goal["latest_question_id"] == question_id
    assert answered_goal["state"] != "connected_for_now"
    assert "understanding is not assumed" in answered_goal["evidence"]["updates"][-1]["detail"].lower()
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    _assert_locked(list_learning_compass(conn))


def test_compass_supports_honest_uncertainty_integration_connection_and_reopening(tmp_path):
    conn = _conn(tmp_path)
    _prior_f1_lea_fixture(conn)
    goal = seed_prior_f1_lea_learning_compass(conn)["items"][1]
    started = start_learning_compass_goal(conn, {"goal_id": goal["id"]})
    session_id = int(started["session"]["item"]["id"])

    unclear = update_learning_compass_goal(
        conn,
        {
            "goal_id": goal["id"],
            "action": "still_unclear",
            "remaining_unclear": "I understand equal pieces, but I cannot yet give reproducible cutting steps.",
        },
    )
    unclear_goal = next(item for item in unclear["items"] if int(item["id"]) == int(goal["id"]))
    update_study_session(
        conn,
        {
            "session_id": session_id,
            "current_understanding": "Two centered cuts can make four regions, but equality still needs checking.",
            "connections": ["Ordered cutting steps connect fraction structure to algorithms."],
            "uncertainties": [],
        },
    )
    integrating_goal = next(item for item in list_learning_compass(conn)["items"] if int(item["id"]) == int(goal["id"]))
    connected = update_learning_compass_goal(
        conn,
        {
            "goal_id": goal["id"],
            "action": "connected_for_now",
            "reflection": "I can describe the cuts in order and check that the four shares have equal area.",
        },
    )
    connected_goal = next(item for item in connected["items"] if int(item["id"]) == int(goal["id"]))
    reopened = update_learning_compass_goal(conn, {"goal_id": goal["id"], "action": "reopen"})
    reopened_goal = next(item for item in reopened["items"] if int(item["id"]) == int(goal["id"]))

    assert unclear_goal["state"] == "still_unclear"
    assert "reproducible" in unclear_goal["remaining_unclear"]
    assert integrating_goal["state"] == "integrating"
    assert integrating_goal["noticed_connections"] == ["Ordered cutting steps connect fraction structure to algorithms."]
    assert connected_goal["state"] == "connected_for_now"
    assert connected_goal["remaining_unclear"] == ""
    assert reopened_goal["state"] == "reopened"
    _assert_locked(reopened)


def test_compass_does_not_allow_performed_connection_without_visible_reflection(tmp_path):
    conn = _conn(tmp_path)
    _prior_f1_lea_fixture(conn)
    goal = seed_prior_f1_lea_learning_compass(conn)["items"][0]

    with pytest.raises(ValueError, match="visible reflection"):
        update_learning_compass_goal(conn, {"goal_id": goal["id"], "action": "connected_for_now"})

    no_words = update_learning_compass_goal(
        conn,
        {"goal_id": goal["id"], "action": "still_unclear", "question_without_words": True},
    )
    item = next(entry for entry in no_words["items"] if int(entry["id"]) == int(goal["id"]))
    assert item["state"] == "still_unclear"
    assert "does not have words" in item["remaining_unclear"]
    _assert_locked(no_words)


def test_study_routes_are_registered_and_status_is_selene_owned(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    direct = study_workspace_status(conn)
    routed = route_request(conn, "study.status")["result"]
    routed_materials = route_request(conn, "study.materials.list")["result"]
    routed_compass = route_request(conn, "study.compass.list")["result"]

    assert direct["owner"] == "Selene"
    assert routed["status"] == "selene_study_workspace_ready"
    assert routed["eligible_material_count"] == 1
    assert routed_materials["items"][0]["id"] == concept_id
    assert routed_compass["status"] == "selene_learning_compass_ready"
    assert routed["study_is_cocoon"] is False
    _assert_locked(routed)
