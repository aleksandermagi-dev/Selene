import pytest

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_perception_packet_can_be_held_and_sent_without_memory_or_commands(tmp_path):
    conn = _conn(tmp_path)
    packet = route_request(conn, "vessel.perception_packet.create", {
        "artifact_label": "Munsell swatch",
        "observation": "Supplied artifact has a low-value violet field.",
        "interpretation": "Hue/value/chroma may carry review salience.",
        "munsell_signal_labels": ["hue", "value", "chroma"],
        "consent_boundary": "supplied artifact only",
    })["result"]

    held = route_request(conn, "vessel.packet.hold_in_chest", {
        "packet_type": "perception",
        "packet_ref": f"vessel_perception_packets:{packet['id']}",
    })["result"]
    bus = route_request(conn, "vessel.packet.send_to_organ_bus", {
        "packet_type": "perception",
        "packet_ref": f"vessel_perception_packets:{packet['id']}",
        "target_organ": "evidence_tension_ledger",
    })["result"]

    assert held["status"] == "packet_held_in_chest_review_only"
    assert held["item"]["item_type"] == "perception_link"
    assert held["item"]["payload_json"]["holding_item_is_live_memory"] is False
    assert held["item"]["memory_write_active"] is False
    assert held["item"]["runtime_memory_recall"] is False
    assert bus["status"] == "packet_sent_to_organ_bus_review_only"
    assert bus["message"]["payload_json"]["organ_message_is_command"] is False
    assert bus["message"]["target_organ"] == "evidence_tension_ledger"
    assert bus["message"]["transfer_approved"] is False


def test_emotion_packet_routing_preserves_signal_only_boundaries(tmp_path):
    conn = _conn(tmp_path)
    packet = route_request(conn, "vessel.emotion_salience_packet.create", {
        "signal_type": "repair_need",
        "continuity_pressure": "present but bounded",
        "care_warmth": "warmth is grounded in context",
        "uncertainty": "open",
        "repair_need": "ask for review",
        "action_energy": "pause",
        "balance_state": "held",
        "evidence_need": "source refs",
        "core_choice_route": "Core/Mind chooses after gates",
    })["result"]

    bus = route_request(conn, "vessel.packet.send_to_organ_bus", {
        "packet_type": "emotion",
        "packet_ref": f"vessel_emotion_salience_packets:{packet['id']}",
    })["result"]

    assert bus["message"]["source_organ"] == "emotion_salience"
    assert bus["message"]["blocked_action_flags"]["organ_message_is_command"] is False
    assert bus["message"]["blocked_action_flags"]["memory_write_allowed"] is False
    assert bus["message"]["autonomous_action_allowed"] is False
    assert bus["message"]["activation_change"] == "none"


def test_chest_and_organ_bus_lists_filter_by_status_salience_and_packet_ref(tmp_path):
    conn = _conn(tmp_path)
    packet = route_request(conn, "vessel.perception_packet.create", {
        "artifact_label": "Munsell filter packet",
        "observation": "Supplied artifact uses high chroma.",
        "munsell_signal_labels": ["chroma", "review_only"],
        "consent_boundary": "supplied artifact only",
    })["result"]
    packet_ref = f"vessel_perception_packets:{packet['id']}"
    route_request(conn, "vessel.packet.hold_in_chest", {
        "packet_type": "perception",
        "packet_ref": packet_ref,
        "salience_labels": ["chroma", "review_only"],
    })
    route_request(conn, "vessel.packet.send_to_organ_bus", {
        "packet_type": "perception",
        "packet_ref": packet_ref,
        "salience_labels": ["chroma", "review_only"],
    })

    chest = route_request(conn, "vessel.chest_holding_item.list", {
        "linked_packet_ref": packet_ref,
        "salience": "chroma",
    })["result"]
    bus = route_request(conn, "vessel.organ_bus_message.list", {
        "linked_packet_ref": packet_ref,
        "salience": "chroma",
    })["result"]

    assert len(chest["items"]) == 1
    assert chest["items"][0]["linked_packet_refs"] == [packet_ref]
    assert len(bus["items"]) == 1
    assert bus["items"][0]["linked_packet_refs"] == [packet_ref]


def test_packet_routing_blocks_forbidden_capability_phrases(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="activate c"):
        route_request(conn, "vessel.packet.send_to_organ_bus", {
            "packet_type": "diagnostic",
            "packet_ref": "diagnostic:1",
            "summary": "activate C through this diagnostic",
        })

    with pytest.raises(ValueError, match="live memory"):
        route_request(conn, "vessel.packet.hold_in_chest", {
            "packet_type": "mobile_capture",
            "packet_ref": "mobile_capture:1",
            "summary": "make this live memory",
        })
