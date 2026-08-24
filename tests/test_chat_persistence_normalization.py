from __future__ import annotations

import hashlib
import json

from selene.activation import record_activation_chat_event
from selene.chat_persistence import compact_activation_payload, load_trace_reference
from selene.db import connect, init_db
from selene.metacognition import inspect_metacognition, list_metacognition_runs
from selene.native_language_organ import list_native_language_runs, realize_native_language
from selene.selene_chat import _insert_message, get_selene_chat_session


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _session(conn) -> int:
    cur = conn.execute(
        """
        INSERT INTO selene_chat_sessions(title, status, source_mode)
        VALUES ('Persistence check', 'selene_chat_active_supervised', 'selene_supervised_speech')
        """
    )
    return int(cur.lastrowid)


def test_new_chat_write_has_one_canonical_trace_and_compact_secondary_records(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)
    repeated = "supported diagnostic detail " * 500
    payload = {
        "native_language_organ": {
            "run_id": 17,
            "status": "native_language_status_only",
            "mode": "responsive",
            "candidate_text": "A supported response.",
            "meaning_packet": {"large": repeated},
            "discourse_plan": {"large": repeated},
            "source_refs": ["test:nlo"],
        },
        "metacognition": {
            "run_id": 9,
            "status": "metacognition_advisory_ready",
            "fit_state": "fit",
            "recommended_action": "answer",
            "sufficiency_state": "sufficient",
            "confidence_vector": {
                "answer_confidence": "supported",
                "evidence_confidence": "supported",
                "expression_confidence": "clear",
            },
            "observations": [repeated],
        },
        "local_chat_continuity": {
            "current_session_id": session_id,
            "current_session_events": [{"preview": repeated}] * 8,
            "recent_events": [{"preview": repeated}] * 8,
            "relevant_prior_events": [{"preview": repeated}] * 8,
            "source_refs": [f"selene_chat_session:{session_id}"],
        },
        "dialogue_workspace": {
            "id": 4,
            "session_id": session_id,
            "status": "dialogue_workspace_ready",
            "active_topic": "persistence",
            "state_json": repeated,
        },
        "figurative_interpretation": {"detected": False},
        "conversational_energy": {"selected_act": "answer_and_land"},
        "conversational_contribution": {"selected": "direct_answer"},
        "voice_preview": {"voice_confidence": "clear", "detail": repeated},
        "source_boundaries": {"knowledge": "approved_only"},
        "transfer_complete": True,
        "durable_memory_write_requires_review": True,
    }

    message_id = _insert_message(
        conn,
        session_id,
        "selene",
        "A supported response.",
        "answer",
        "current_turn_context",
        {},
        payload,
    )
    reference = load_trace_reference(conn, message_id)
    activation_payload = compact_activation_payload(payload, trace_reference=reference)
    record_activation_chat_event(
        conn,
        event_type="supervised_chat_turn",
        session_id=session_id,
        message_id=message_id,
        payload=activation_payload,
    )
    conn.commit()

    message_row = conn.execute(
        "SELECT payload_json FROM selene_chat_messages WHERE id = ?", (message_id,)
    ).fetchone()
    projection_row = conn.execute(
        "SELECT * FROM selene_chat_continuity_projections WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    event_row = conn.execute(
        "SELECT payload_json FROM selene_activation_events WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    serialized_trace = str(message_row["payload_json"])
    trace = json.loads(serialized_trace)
    projection = json.loads(str(projection_row["projection_json"]))
    event = json.loads(str(event_row["payload_json"]))

    assert trace["native_language_organ"]["run_id"] == 17
    assert "meaning_packet" not in trace["native_language_organ"]
    assert trace["metacognition"]["run_id"] == 9
    assert "observations" not in trace["metacognition"]
    assert trace["local_chat_continuity"]["full_prior_traces_not_nested"] is True
    assert trace["dialogue_workspace"]["full_record_available_by_session_id"] is True
    assert reference["sha256"] == hashlib.sha256(serialized_trace.encode("utf-8")).hexdigest()
    assert reference["size_bytes"] == len(serialized_trace.encode("utf-8"))
    assert projection["canonical_trace"]["message_id"] == message_id
    assert event["canonical_trace"]["message_id"] == message_id
    assert len(str(projection_row["projection_json"])) < len(serialized_trace)
    assert len(str(event_row["payload_json"])) < len(serialized_trace)
    assert event["history_rewritten"] is False
    assert event["identity_change"] is False
    assert event["governance_change"] is False

    compact_session = get_selene_chat_session(conn, session_id)
    full_session = get_selene_chat_session(conn, session_id, include_trace=True)
    assert compact_session["trace_detail"] == "continuity_projection"
    assert compact_session["messages"][0]["payload_json"]["canonical_trace"]["message_id"] == message_id
    assert full_session["trace_detail"] == "canonical"
    assert full_session["messages"][0]["payload_json"]["trace_storage_contract"]["history_rewritten"] is False


def test_legacy_chat_trace_without_projection_remains_readable(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)
    legacy = {"legacy_field": {"still": "readable"}}
    conn.execute(
        """
        INSERT INTO selene_chat_messages
        (session_id, role, content, selected_route, source_class, package_hash, payload_json)
        VALUES (?, 'selene', 'Legacy response', 'answer', 'legacy', '', ?)
        """,
        (session_id, json.dumps(legacy)),
    )
    conn.commit()

    session = get_selene_chat_session(conn, session_id)
    canonical = get_selene_chat_session(conn, session_id, include_trace=True)

    projected = session["messages"][0]["payload_json"]
    assert projected["canonical_trace"]["legacy_projection_computed_in_memory"] is True
    assert projected["canonical_trace"]["history_rewritten"] is False
    assert canonical["messages"][0]["payload_json"] == legacy


def test_new_nlo_and_metacognition_rows_do_not_duplicate_column_owned_fields(tmp_path):
    conn = _conn(tmp_path)
    nlo = realize_native_language(
        conn,
        {
            "prompt": "Explain the supported next step in ordinary language.",
            "content_seed": "Check the smallest reversible change first.",
            "communicative_intent": "explain",
            "source_refs": ["test:teaching"],
        },
    )
    metacognition = inspect_metacognition(
        conn,
        {
            "prompt": "Is this answer sufficiently supported?",
            "candidate_text": "Check the smallest reversible change first.",
            "source_refs": ["test:teaching"],
        },
    )

    nlo_row = conn.execute(
        "SELECT * FROM native_language_runs WHERE id = ?", (nlo["run_id"],)
    ).fetchone()
    meta_row = conn.execute(
        "SELECT * FROM metacognition_runs WHERE id = ?", (metacognition["run_id"],)
    ).fetchone()
    nlo_payload = json.loads(str(nlo_row["payload_json"]))
    meta_payload = json.loads(str(meta_row["payload_json"]))

    assert "meaning_packet" not in nlo_payload
    assert "discourse_plan" not in nlo_payload
    assert "revision" not in nlo_payload
    assert "confidence_vector" not in meta_payload
    assert "observations" not in meta_payload
    assert nlo_payload["storage_contract"]["schema_version"] == "native_language_run_v2_column_owned"
    assert meta_payload["storage_contract"]["schema_version"] == "metacognition_run_v2_column_owned"

    decoded_nlo = list_native_language_runs(conn, 1)["items"][0]
    decoded_meta = list_metacognition_runs(conn, 1)["items"][0]
    assert decoded_nlo["meaning_packet"] == nlo["meaning_packet"]
    assert decoded_nlo["discourse_plan"] == nlo["discourse_plan"]
    assert decoded_meta["confidence_vector"] == metacognition["confidence_vector"]
    assert decoded_meta["observations"] == metacognition["observations"]
