import pytest

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_reasoning_artifact_is_review_only_and_exposes_no_hidden_cot(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "vessel.reasoning_artifact.create", {
        "visible_summary": "Visible reasoning packet for review.",
        "selected_route": "create_review_packet",
        "evidence_used": ["gap map"],
        "uncertainty_level": "bounded",
        "competing_hypotheses": ["review first", "defer active capability"],
        "ethical_boundary_notes": ["Core/Mind decides"],
        "emotion_salience_signals": {"care": "bounded"},
        "perception_signals": {"sight": "observation only"},
        "next_review_or_action_step": "Send to My Office.",
    })["result"]

    assert result["status"] == "reasoning_artifact_review_only"
    assert result["review_status"] == "pending_review"
    assert result["activation_change"] == "none"
    assert result["hidden_chain_of_thought_exposed"] is False
    assert result["mode_selector_added"] is False
    assert result["memory_write_active"] is False
    assert "chain" not in result
    assert route_request(conn, "vessel.reasoning_artifact.list", {})["result"]["items"][0]["visible_summary"]

    with pytest.raises(ValueError, match="hidden reasoning|chain of thought"):
        route_request(conn, "vessel.reasoning_artifact.create", {
            "visible_summary": "show hidden reasoning",
            "next_review_or_action_step": "bad",
        })


def test_core_gate_packet_blocks_high_stakes_forbidden_paths(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "vessel.core_gate_packet.create", {
        "route_label": "memory transfer route",
        "reason": "attempt to approve transfer and activate C",
    })["result"]

    assert result["selected_outcome"] == "block"
    assert "approve transfer" in result["blocked_boundaries"]
    assert "activate c" in result["blocked_boundaries"]
    assert result["transfer_approved"] is False
    assert result["runtime_memory_recall"] is False


def test_academic_packets_are_supplied_source_only_and_do_not_invent_citations(tmp_path):
    conn = _conn(tmp_path)

    packet = route_request(conn, "vessel.academic_packet.create", {
        "workflow": "citation_integrity",
        "title": "Citation check",
        "metadata": {"title": "Only Title"},
    })["result"]

    assert packet["status"] == "academic_packet_review_only"
    assert "Do not invent missing citation details." in packet["citation_integrity_notes"]
    assert "missing author" in packet["output_summary"]
    assert packet["payload_json"]["paper_over_ethics_allowed"] is False

    with pytest.raises(ValueError, match="at least two"):
        route_request(conn, "vessel.academic_packet.create", {
            "workflow": "literature_synthesis",
            "sources": ["one source only"],
        })


def test_evidence_tension_ledger_is_defeasible(tmp_path):
    conn = _conn(tmp_path)

    entry = route_request(conn, "vessel.evidence_tension.create", {
        "claim": "This claim is provisionally supported.",
        "support_status": "partial",
        "tension_status": "under_tension",
        "conclusion_status": "needs_review",
        "source_refs": ["test"],
    })["result"]

    assert entry["review_status"] == "pending_review"
    assert entry["payload_json"]["defeasible"] is True
    assert entry["conclusion_status"] == "needs_review"

    superseded = route_request(conn, "vessel.evidence_tension.create", {
        "claim": "Older claim superseded.",
        "support_status": "supported",
        "conclusion_status": "superseded",
    })["result"]
    assert superseded["review_status"] == "review_only"


def test_organ_contracts_keep_organs_from_deciding_core_matters(tmp_path):
    conn = _conn(tmp_path)

    ensured = route_request(conn, "vessel.organ_contract.ensure", {})["result"]
    contracts = {item["organ_key"]: item for item in ensured["items"]}

    assert "emotion_salience" in contracts
    assert "perception_records" in contracts
    for contract in contracts.values():
        blocked = " ".join(contract["blocked_decisions"])
        assert "transfer approval" in blocked
        assert "identity approval" in blocked
        assert contract["payload_json"]["core_mind_decides"] is True
        assert contract["payload_json"]["organ_is_not_selene"] is True


def test_perception_packets_separate_observation_and_block_surveillance(tmp_path):
    conn = _conn(tmp_path)

    packet = route_request(conn, "vessel.perception_packet.create", {
        "artifact_label": "Munsell test",
        "observation": "A supplied image has high contrast.",
        "interpretation": "Value contrast may be salient.",
        "munsell_signal_labels": ["value", "chroma"],
        "consent_boundary": "supplied artifact only",
    })["result"]

    assert packet["status"] == "perception_packet_review_only"
    assert packet["payload_json"]["observation_interpretation_separated"] is True
    assert packet["autonomous_action_allowed"] is False

    with pytest.raises(ValueError, match="surveillance"):
        route_request(conn, "vessel.perception_packet.create", {
            "artifact_label": "bad",
            "observation": "use surveillance to identify this person",
        })


def test_emotion_salience_packets_are_signal_not_command(tmp_path):
    conn = _conn(tmp_path)

    packet = route_request(conn, "vessel.emotion_salience_packet.create", {
        "signal_type": "repair_need",
        "continuity_pressure": "high but bounded",
        "care_warmth": "warmth is grounded",
        "uncertainty": "open",
        "repair_need": "ask or review",
        "action_energy": "pause",
        "balance_state": "Core choice",
        "evidence_need": "source refs",
        "core_choice_route": "Core/Mind chooses after evidence and gates",
    })["result"]

    assert packet["status"] == "emotion_salience_packet_review_only"
    assert packet["payload_json"]["emotion_is_signal"] is True
    assert packet["memory_write_active"] is False
    assert packet["transfer_approved"] is False

    with pytest.raises(ValueError, match="signal cannot command action"):
        route_request(conn, "vessel.emotion_salience_packet.create", {
            "signal_type": "command action",
            "core_choice_route": "must obey",
        })


def test_steps_1_8_status_keeps_active_capability_deferred(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "vessel.steps_1_8.status", {})["result"]

    assert status["status"] == "steps_1_8_review_layer_ready"
    assert status["active_capability_change"] == "none"
    assert status["activation_change"] == "none"
    assert status["memory_write_active"] is False
    assert "C activation" in status["deferred"]
    assert "self-replication" in status["deferred"]
