import pytest

from selene.cocoon_readiness import create_memory_accession_proposal, create_working_memory_packet
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_speech_generation_rehearsal_is_review_only_and_source_bound(tmp_path):
    conn = _conn(tmp_path)
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
    assert "Boundary: pre-transfer speech rehearsal only" in result["candidate_text"]
    assert listed["items"][0]["id"] == result["id"]


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
