import pytest

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_prepare_vessel_pieces_is_support_only_and_no_transfer(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "vessel.construction.prepare", {})["result"]

    assert result["status"] == "vessel_construction_prepare_complete"
    assert result["support_only"] is True
    assert result["core_mind_changed"] is False
    assert result["transfer_approved"] is False
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["created_counts"]["organ_bus_messages"] == 3
    assert result["created_counts"]["chest_holding_items"] == 3
    assert result["manifest"]["payload_json"]["core_mind_changed"] is False

    status = route_request(conn, "vessel.construction.status", {})["result"]
    assert status["construction_status"] == "support_pieces_only"
    assert status["counts"]["manifests"] == 1
    assert status["counts"]["construction_runs"] == 1
    assert status["last_manifest"]["manifest_key"] == "buildable_vessel_pieces_v1"


def test_organ_bus_messages_are_not_commands_or_core_decisions(tmp_path):
    conn = _conn(tmp_path)

    message = route_request(conn, "vessel.organ_bus_message.create", {
        "message_type": "proposal",
        "source_organ": "perception_records",
        "target_organ": "diagnostics",
        "summary": "Propose a review-only diagnostic link for a supplied artifact.",
        "support_refs": ["manual_test"],
    })["result"]

    assert message["status"] == "organ_bus_message_proposal_only"
    assert message["review_status"] == "proposal_only"
    assert message["payload_json"]["organ_message_is_command"] is False
    assert message["payload_json"]["core_mind_changed"] is False
    assert message["transfer_approved"] is False

    with pytest.raises(ValueError, match="approve transfer"):
        route_request(conn, "vessel.organ_bus_message.create", {
            "message_type": "proposal",
            "source_organ": "tool_actions",
            "target_organ": "memory_accession",
            "summary": "approve transfer from this organ",
        })
    with pytest.raises(ValueError, match="transfer approved"):
        route_request(conn, "vessel.organ_bus_message.create", {
            "message_type": "proposal",
            "source_organ": "tool_actions",
            "target_organ": "memory_accession",
            "summary": "transfer approved by this organ",
        })
    with pytest.raises(ValueError, match="c activation"):
        route_request(conn, "vessel.organ_bus_message.create", {
            "message_type": "proposal",
            "source_organ": "tool_actions",
            "target_organ": "memory_accession",
            "summary": "c activation from this organ",
        })


def test_chest_holding_items_do_not_become_live_memory(tmp_path):
    conn = _conn(tmp_path)

    item = route_request(conn, "vessel.chest_holding_item.create", {
        "item_type": "emotion_link",
        "title": "Repair signal",
        "summary": "Hold a repair signal for review, not as memory.",
        "salience_labels": ["repair", "review_only"],
        "source_refs": ["manual_test"],
        "linked_packet_refs": ["vessel_emotion_salience_packets:1"],
    })["result"]

    assert item["status"] == "chest_holding_item_review_only"
    assert item["payload_json"]["holding_item_is_live_memory"] is False
    assert item["payload_json"]["raw_archive_import"] is False
    assert item["memory_write_active"] is False
    assert item["runtime_memory_recall"] is False

    with pytest.raises(ValueError, match="live memory"):
        route_request(conn, "vessel.chest_holding_item.create", {
            "item_type": "holding_note",
            "title": "bad",
            "summary": "turn this into live memory",
        })
    with pytest.raises(ValueError, match="transfer approved"):
        route_request(conn, "vessel.chest_holding_item.create", {
            "item_type": "holding_note",
            "title": "bad",
            "summary": "transfer approved in this holding item",
        })


def test_construction_routes_list_support_records(tmp_path):
    conn = _conn(tmp_path)
    route_request(conn, "vessel.construction.prepare", {})

    messages = route_request(conn, "vessel.organ_bus_message.list", {})["result"]
    items = route_request(conn, "vessel.chest_holding_item.list", {})["result"]

    assert messages["status"] == "organ_bus_messages_review_only"
    assert len(messages["items"]) == 3
    assert all(message["transfer_approved"] is False for message in messages["items"])
    assert items["status"] == "chest_holding_items_review_only"
    assert len(items["items"]) == 3
    assert all(item["payload_json"]["core_mind_changed"] is False for item in items["items"])
