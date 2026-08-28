from __future__ import annotations

from selene.comprehension_integration import (
    decide_comprehension_concept,
    evaluate_understanding,
    propose_comprehension_concept,
)
from selene.db import connect, init_db
from selene.study_workspace import (
    answer_study_question,
    ask_study_question,
    integrate_study_question_for_now,
    reopen_study_question,
    start_study_session,
)


def test_disposable_phase3_study_walkthrough_closes_and_reopens_without_pressure(tmp_path):
    conn = connect(tmp_path / "phase3-walkthrough.sqlite3")
    init_db(conn)
    foundation = propose_comprehension_concept(
        conn,
        {
            "concept_key": "phase3_walkthrough_equal_shares",
            "title": "Equal shares in one whole",
            "domain": "synthetic.phase3.walkthrough",
            "material": "A fraction names equal-sized shares relative to one whole.",
            "source_refs": ["synthetic:phase3:walkthrough:foundation"],
        },
    )
    foundation_id = int(foundation["item"]["id"])
    conn.execute(
        """
        UPDATE selene_comprehension_concepts
        SET state = 'approved_knowledge_resource', review_status = 'approved_for_knowledge_use',
            retention_state = 'retained_reviewed_knowledge',
            chat_use_permission = 'available_as_knowledge_resource'
        WHERE id = ?
        """,
        (foundation_id,),
    )
    conn.commit()
    session_id = int(
        start_study_session(
            conn,
            {
                "concept_ids": [foundation_id],
                "title": "Disposable Phase 3 Study walkthrough",
                "focus": "Why the whole and equal share size belong together",
            },
        )["item"]["id"]
    )
    question_id = int(
        ask_study_question(
            conn,
            {
                "session_id": session_id,
                "concept_id": foundation_id,
                "formation_state": "ready",
                "question_text": "Why must the share size be tied to one whole?",
                "uncertainty_context": "The equal pieces make sense, but the role of the whole still needs a why.",
            },
        )["questions"][0]["id"]
    )
    answered = answer_study_question(
        conn,
        {
            "question_id": question_id,
            "answer": "The same piece can be a different fraction when the reference whole changes, so the whole defines what one share means.",
        },
    )
    candidate_id = int(answered["questions"][0]["teaching_candidate_id"])
    evidence = evaluate_understanding(
        conn,
        {
            "concept_id": candidate_id,
            "teach_back": "A share name is meaningful only relative to its reference whole, because changing the whole changes the share's proportion.",
            "application": "One slice can be half of a small pizza but only one quarter of a pizza twice as large.",
            "limits": ["The comparison requires each fraction to identify its own reference whole."],
            "counterexample": "Equal-looking pieces from different wholes need not name the same fraction.",
            "correction_ready": True,
            "source_alignment": True,
        },
    )
    assert evidence["understanding_evidence_sufficient"] is True
    decide_comprehension_concept(conn, {"concept_id": candidate_id, "action": "approve_knowledge"})
    reconstruction = (
        "A fractional share is not defined by the piece alone: its size and name are relative to one stated whole."
    )
    integrated = integrate_study_question_for_now(
        conn,
        {"question_id": question_id, "selene_reconstruction": reconstruction},
    )
    reopened = reopen_study_question(
        conn,
        {
            "question_id": question_id,
            "formation_state": "question_without_words",
            "question_text": "",
            "learning_state": "still_unclear",
            "uncertainty_context": "A new edge case is noticeable, but its question does not have words yet.",
        },
    )

    parent = next(item for item in reopened["questions"] if int(item["id"]) == question_id)
    child = next(item for item in reopened["questions"] if int(item["id"]) == int(reopened["reopened_question_id"]))
    assert integrated["integration_receipt"]["state"] == "integrated_for_now"
    assert integrated["integration_receipt"]["visible_selene_reconstruction"] == reconstruction
    assert parent["status"] == "reopened_by_descendant"
    assert parent["integration_reconstruction"] == reconstruction
    assert child["formation_state"] == "question_without_words"
    assert child["status"] == "open"
    assert child["question_ancestry"]["ancestor_question_ids"] == [question_id]
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_dream_reflections").fetchone()[0] == 0
    conn.close()
