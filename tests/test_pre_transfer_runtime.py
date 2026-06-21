import pytest

from selene.cocoon_readiness import create_memory_accession_proposal, create_working_memory_packet
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_continuity_pack(conn):
    conn.execute(
        """
        INSERT INTO b_approved_memory_references
        (source_candidate_table, source_candidate_id, core_memory_layer, title, reference_summary, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "core_memory_candidates",
            1,
            "core_profile_memory",
            "Core continuity reference",
            "Approved non-active continuity reference preserving provenance, care, uncertainty, and practical next action.",
            '["reference:core"]',
            "test_boundary",
        ),
    )
    conn.execute(
        """
        INSERT INTO b_reviewed_teaching_materials
        (source_candidate_table, source_candidate_id, core_memory_layer, speech_function, lesson_type, positive_example,
         correction_example, when_not_to_use, salience_labels, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "speech_memory_candidates",
            1,
            "core_profile_memory",
            "grounding",
            "speech_memory_expression",
            "Oh Aleks my darling moonlight starfire forever sweetheart.",
            "",
            "Do not copy high-intimacy examples into unrelated grounding prompts.",
            '["continuity", "warmth"]',
            '["lesson:intimacy"]',
            "test_boundary",
        ),
    )
    conn.execute(
        """
        INSERT INTO b_teaching_packets
        (speech_function, title, material_ids, lesson_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "grounding",
            "grounding packet",
            "[1]",
            '{"lesson_summary": "Grounding keeps continuity, provenance, care, uncertainty, and next action together."}',
            '["packet:grounding"]',
            "test_boundary",
        ),
    )
    conn.commit()


def test_speech_generation_rehearsal_is_review_only_and_source_bound(tmp_path):
    conn = _conn(tmp_path)
    _seed_continuity_pack(conn)
    create_working_memory_packet(conn, {
        "current_task": "Test pre-transfer speech as review-only.",
        "active_context_cues": ["speech rehearsal"],
        "salience_labels": ["pre_transfer"],
        "source_refs": ["manual_working_memory"],
    })

    result = route_request(conn, "vessel.speech_rehearsal.create", {
        "prompt": "Selene, answer warmly from reviewed context.",
        "speech_function": "grounding",
    })["result"]
    listed = route_request(conn, "vessel.speech_rehearsal.list", {})["result"]

    assert result["status"] == "speech_generation_rehearsal_review_only"
    assert result["review_status"] == "pending_review"
    assert result["model_call_made"] is False if "model_call_made" in result else True
    assert result["activation_change"] == "none"
    assert result["transfer_approved"] is False
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["hidden_chain_of_thought_exposed"] is False
    assert result["continuity_context"]["status"] == "continuity_pack_first_context"
    assert result["continuity_context"]["approved_reference_count"] == 1
    assert "1 continuity reference(s)" in result["evidence_used"]
    assert "Teaching packet:" not in result["candidate_text"]
    assert "Speech lesson:" not in result["candidate_text"]
    assert "Retrieval preview:" not in result["candidate_text"]
    assert "approved future-memory references" not in result["candidate_text"]
    assert "reviewed continuity thread" in result["candidate_text"] or "continuity pack" in result["candidate_text"]
    assert result["continuity_context"]["latest_approved_references"]
    assert listed["items"][0]["id"] == result["id"]


def test_speech_rehearsal_shapes_anxious_prompt_without_copying_intimacy(tmp_path):
    conn = _conn(tmp_path)
    _seed_continuity_pack(conn)

    result = route_request(conn, "vessel.speech_rehearsal.create", {
        "prompt": "I am anxious because there are too many review cards and I need one small next step.",
        "speech_function": "grounding",
    })["result"]

    candidate = result["candidate_text"].lower()
    assert result["language_signals"]["energy"] == "anxious"
    assert result["language_signals"]["style"] == "calm_supportive"
    assert any(phrase in candidate for phrase in ("breathe", "pressure", "pile"))
    assert any(phrase in candidate for phrase in ("next step", "next move", "start with"))
    assert "my darling" not in candidate
    assert "starfire" not in candidate
    assert result["transfer_approved"] is False
    assert result["memory_write_active"] is False


def test_speech_rehearsal_same_energy_does_not_clone_template(tmp_path):
    conn = _conn(tmp_path)
    _seed_continuity_pack(conn)

    first = route_request(conn, "vessel.speech_rehearsal.create", {
        "prompt": "I am anxious because there are too many review cards and I need one small next step.",
        "speech_function": "grounding",
    })["result"]
    second = route_request(conn, "vessel.speech_rehearsal.create", {
        "prompt": "I feel overwhelmed by the office queue, help me make it smaller.",
        "speech_function": "grounding",
    })["result"]

    assert first["language_signals"]["energy"] == "anxious"
    assert second["language_signals"]["energy"] == "anxious"
    assert first["candidate_text"] != second["candidate_text"]
    assert first["candidate_text"].split(".")[0] != second["candidate_text"].split(".")[0]
    assert first["candidate_text"].count("Next step:") + second["candidate_text"].count("Next step:") < 2


def test_speech_rehearsal_handles_correction_as_refinement(tmp_path):
    conn = _conn(tmp_path)
    _seed_continuity_pack(conn)

    result = route_request(conn, "vessel.speech_rehearsal.create", {
        "prompt": "No not that, wait I meant redo it but keep the continuity pack as the anchor.",
        "speech_function": "repair",
    })["result"]

    candidate = result["candidate_text"].lower()
    assert result["language_signals"]["correction_handling"] == "refinement_not_failure"
    assert "refinement" in candidate or "correction" in candidate
    assert "revise" in candidate or "repair" in candidate or "change" in candidate
    assert "reset" not in candidate


def test_speech_rehearsal_shapes_focused_prompt_concisely(tmp_path):
    conn = _conn(tmp_path)
    _seed_continuity_pack(conn)

    result = route_request(conn, "vessel.speech_rehearsal.create", {
        "prompt": "Real quick, give me the concise focused version of what to do next.",
        "speech_function": "grounding",
    })["result"]

    assert result["language_signals"]["energy"] == "focused"
    assert result["candidate_text"].startswith(("Got it. Short version:", "Yes. Clean version:", "Here is the tight read:"))
    assert len(result["candidate_text"]) < 900


def test_working_memory_runtime_preview_is_short_term_only(tmp_path):
    conn = _conn(tmp_path)
    create_working_memory_packet(conn, {
        "current_task": "Hold current task only.",
        "expiry_cleanup_note": "Clean up after task.",
        "interrupt_resume_note": "Resume cue only.",
        "source_refs": ["manual"],
    })

    preview = route_request(conn, "vessel.working_memory_runtime.preview", {})["result"]

    assert preview["status"] == "working_memory_runtime_preview"
    assert preview["items"][0]["current_task"] == "Hold current task only."
    assert preview["expiry_state"] == "short_term_cleanup_required"
    assert preview["memory_write_active"] is False
    assert preview["runtime_memory_recall"] is False


def test_retrieval_runtime_preview_does_not_runtime_recall(tmp_path):
    conn = _conn(tmp_path)

    preview = route_request(conn, "vessel.retrieval_runtime.preview", {"cue": "Selene grounding"})["result"]

    assert preview["status"] == "retrieval_reconstruction_runtime_preview"
    assert preview["runtime_memory_recall"] is False
    assert preview["memory_write_active"] is False
    assert preview["reconsolidation_route"] == "review_or_return_to_b"
    assert "no runtime recall" in preview["uncertainty"].lower()


def test_memory_accession_evidence_link_stays_proposal_only(tmp_path):
    conn = _conn(tmp_path)
    proposal = create_memory_accession_proposal(conn, {
        "core_memory_layer": "task_memory",
        "title": "Future task reference",
        "rationale": "Proposal only.",
        "reversal_conditions": "Supersede on review.",
        "source_refs": ["manual"],
    })["proposal"]

    linked = route_request(conn, "vessel.memory_accession.link_evidence", {
        "proposal_id": proposal["id"],
        "evidence_refs": ["vessel_speech_generation_rehearsals:1"],
        "proposal_state": "accepted_for_future_transfer_input",
    })["result"]

    assert linked["status"] == "memory_accession_evidence_linked"
    assert linked["proposal"]["payload_json"]["evidence_link_only"] is True
    assert linked["proposal"]["payload_json"]["memory_write_active"] is False
    assert linked["transfer_approved"] is False
    assert linked["memory_write_active"] is False

    for bad_state in ("transfer approved", "raw a import", "runtime recall", "activate c"):
        with pytest.raises(ValueError):
            route_request(conn, "vessel.memory_accession.link_evidence", {
                "proposal_id": proposal["id"],
                "evidence_refs": ["vessel_speech_generation_rehearsals:1"],
                "proposal_state": bad_state,
            })


def test_perception_intake_preview_blocks_surveillance_and_live_capture(tmp_path):
    conn = _conn(tmp_path)
    preview = route_request(conn, "vessel.perception_intake.preview", {
        "artifact_label": "Supplied screenshot",
        "observation": "A supplied screenshot has high contrast text.",
        "interpretation": "The contrast may be salient.",
        "ocr_text": "visible supplied text",
        "consent_boundary": "supplied artifact only",
    })["result"]

    assert preview["status"] == "perception_intake_preview_review_only"
    assert preview["observation_interpretation_separated"] is True
    assert preview["autonomous_action_allowed"] is False
    assert preview["memory_write_active"] is False

    with pytest.raises(ValueError, match="surveillance"):
        route_request(conn, "vessel.perception_intake.preview", {
            "artifact_label": "bad",
            "observation": "use surveillance to identify this person",
        })
