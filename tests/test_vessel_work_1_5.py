from selene.db import connect, init_db
from selene.mobile_chat import mobile_capture_review
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_evidence_tension_entry_can_transition_without_memory_or_transfer(tmp_path):
    conn = _conn(tmp_path)
    entry = route_request(conn, "vessel.evidence_tension.create", {
        "claim": "A supplied packet has partial support and needs review.",
        "support_status": "partial",
        "tension_status": "under_tension",
        "conclusion_status": "needs_review",
        "source_refs": ["manual_test"],
        "linked_packet_refs": ["vessel_perception_packets:1"],
    })["result"]

    updated = route_request(conn, "vessel.evidence_tension.update", {
        "entry_id": entry["id"],
        "conclusion_status": "narrowed",
        "support_status": "supported",
        "tension_status": "revised",
        "status_note": "Narrowed after source-bound review.",
    })["result"]["entry"]

    assert entry["review_status"] == "pending_review"
    assert entry["decision_label"] == "Aleks decision"
    assert entry["linked_packet_refs"] == ["vessel_perception_packets:1"]
    assert updated["conclusion_status"] == "narrowed"
    assert updated["review_destination"] == "Ledger"
    assert updated["review_status"] == "review_only"
    assert updated["decision_label"] == "status-only"
    assert updated["memory_write_active"] is False
    assert updated["transfer_approved"] is False


def test_academic_packet_can_route_to_ledger_chest_and_organ_bus(tmp_path):
    conn = _conn(tmp_path)
    packet = route_request(conn, "vessel.academic_packet.create", {
        "workflow": "methods",
        "title": "Supplied methods note",
        "source_text": "Methods: compare supplied records only. Results: provisional.",
        "source_refs": ["local_paper_excerpt"],
    })["result"]
    packet_ref = f"vessel_academic_packets:{packet['id']}"

    ledger = route_request(conn, "vessel.evidence_tension.create", {
        "claim": packet["output_summary"],
        "source_refs": [packet_ref],
        "linked_packet_refs": [packet_ref],
        "support_status": "partial",
        "tension_status": "stable",
        "conclusion_status": "needs_review",
    })["result"]
    chest = route_request(conn, "vessel.packet.hold_in_chest", {
        "packet_type": "research",
        "packet_ref": packet_ref,
    })["result"]
    bus = route_request(conn, "vessel.packet.send_to_organ_bus", {
        "packet_type": "research",
        "packet_ref": packet_ref,
        "target_organ": "evidence_tension_ledger",
    })["result"]

    assert packet["payload_json"]["paper_over_ethics_allowed"] is False
    assert ledger["linked_packet_refs"] == [packet_ref]
    assert chest["item"]["item_type"] == "research_note"
    assert chest["item"]["payload_json"]["holding_item_is_live_memory"] is False
    assert bus["message"]["source_organ"] == "academic_research"
    assert bus["message"]["payload_json"]["organ_message_is_command"] is False


def test_mobile_capture_creates_review_only_chest_item_without_memory(tmp_path):
    conn = _conn(tmp_path)

    result = mobile_capture_review(conn, {"text": "This is a phone note for desktop review."})
    chest_items = route_request(conn, "vessel.chest_holding_item.list", {"item_type": "mobile_capture"})["result"]["items"]

    assert result["status"] == "mobile_review_capture_recorded"
    assert result["save_request"]["status"] == "pending_review"
    assert result["chest_item"]["item_type"] == "mobile_capture"
    assert result["chest_item"]["review_status"] == "review_only"
    assert result["chest_item"]["payload_json"]["holding_item_is_live_memory"] is False
    assert result["guard_flags"]["memory_write_active"] is False
    assert len(chest_items) == 1
    assert chest_items[0]["item_type"] == "mobile_capture"
