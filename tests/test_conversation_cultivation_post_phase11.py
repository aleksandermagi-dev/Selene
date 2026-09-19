from __future__ import annotations

from selene.activation import ACTIVATION_APPROVAL_PHRASE
from selene.dialogue_workspace import _held_revision_topic_transition
from selene.module_router import route_request
from selene.proposition_normalization import extract_visible_options
from tests.test_selene_chat_shell import _assert_locked, _conn, _seed_activation_ready_state


def _activated_conn(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(
        conn,
        "activation.approve",
        {"approval_phrase": ACTIVATION_APPROVAL_PHRASE},
    )
    return conn


def test_held_revision_semantic_expiry_requires_a_real_subject_change():
    held = {
        "recomputation": {"state": "held_pending_owner_result"},
        "current_revision": {
            "corrected_text": "the lantern stayed dark",
            "replaced_text": "it stayed dark",
        },
    }
    assert _held_revision_topic_transition(
        "How does distance from a sound source affect how loud it seems?",
        prior_topic="lantern flashed twice stayed dark",
        prior_ledger=held,
        current_correction_detected=False,
        contextual_follow_up={},
    ) is True
    assert _held_revision_topic_transition(
        "What about the lantern light after that?",
        prior_topic="lantern flashed twice stayed dark",
        prior_ledger=held,
        current_correction_detected=False,
        contextual_follow_up={},
    ) is False
    assert _held_revision_topic_transition(
        "Does that change it?",
        prior_topic="lantern flashed twice stayed dark",
        prior_ledger=held,
        current_correction_detected=False,
        contextual_follow_up={},
    ) is False


def test_counted_concrete_alternatives_reach_the_current_session_owner(tmp_path):
    parsed = extract_visible_options(
        "On the bench are two clamps, one light but wobbly, and one heavy but sturdy."
    )
    assert parsed["subject"] == "clamp"
    assert parsed["values"] == ["light but wobbly", "heavy but sturdy"]

    conn = _activated_conn(tmp_path)
    result = route_request(
        conn,
        "selene_chat.send",
        {
            "text": (
                "Good morning. On the bench are two clamps, one light but wobbly, "
                "and one heavy but sturdy. Sturdiness matters most. Compare them and "
                "choose one."
            )
        },
    )["result"]

    owner_inputs = result["conversation_spine"]["current_turn_owner_inputs"]
    assert any(
        len((item.get("supplied_fields") or {}).get("options") or []) == 2
        for item in owner_inputs
    )
    assert result["visible_speech_seed"]["selected_source_id"] == "current_session_facts"
    gate = result["visible_speech_seed"]["candidate_arbitration"]["current_owner_gate"]
    assert gate["priority_applied"] is True
    assert result["response_coverage"]["all_required_addressed"] is True
    assert "light but wobbly" in result["candidate_text"].lower()
    assert "heavy but sturdy" in result["candidate_text"].lower()
    assert "still need" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_prompt_observation_gets_typed_analysis_before_optional_knowledge(tmp_path):
    conn = _activated_conn(tmp_path)
    result = route_request(
        conn,
        "selene_chat.send",
        {
            "text": (
                "The lantern flashed twice after I plugged it in, then stayed dark. "
                "Separate the observation from one interpretation and suggest one "
                "next check."
            )
        },
    )["result"]

    observations = [
        item
        for item in result["conversation_spine"]["current_turn_facts"]
        if item.get("kind") == "observation"
    ]
    assert any("flashed twice" in item["text"].lower() for item in observations)
    operations = result["answer_operations"]["results"]
    analysis = next(item for item in operations if item["operation"] == "observation_analysis")
    assert analysis["status"] == "completed"
    assert set(analysis["fields"]) >= {"observation", "interpretation", "next_check"}
    assert analysis["current_turn_input_receipt"]["accounted_before_result"] is True
    assert result["visible_speech_seed"]["selected_source_id"] == "intelligence_os_answer"
    assert result["response_coverage"]["all_required_addressed"] is True
    assert all(
        label in result["candidate_text"]
        for label in ("Observation:", "Interpretation:", "Next check:")
    )
    assert result["candidate_text"].index("Observation:") < result[
        "candidate_text"
    ].index("Interpretation:") < result["candidate_text"].index("Next check:")
    assert "local code" not in result["candidate_text"].lower()
    _assert_locked(result)


def test_held_revision_expires_on_ordinary_topic_change_and_mixed_acts_are_proved(tmp_path):
    conn = _activated_conn(tmp_path)
    opening = route_request(
        conn,
        "selene_chat.send",
        {
            "text": (
                "The lantern flashed twice after I plugged it in, then stayed dark. "
                "Separate the observation from one interpretation and suggest one "
                "next check."
            )
        },
    )["result"]
    correction = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": opening["session_id"],
            "text": (
                "By 'it stayed dark,' I meant the lantern stayed dark. Does that "
                "change your interpretation?"
            ),
        },
    )["result"]
    assert correction["session_proposition_ledger"]["recomputation"]["state"] == "completed"

    changed_topic = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": opening["session_id"],
            "text": "How does distance from a sound source affect how loud it seems?",
        },
    )["result"]
    assert changed_topic["session_proposition_ledger"]["recomputation"]["state"] in {
        "not_required",
        "expired_on_topic_transition",
    }
    assert "lantern stayed dark" not in changed_topic["candidate_text"].lower()
    assert "corrected meaning" not in changed_topic["candidate_text"].lower()

    mixed = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": opening["session_id"],
            "text": (
                "Give me two short takeaways from our lantern discussion and one "
                "tiny lantern joke."
            ),
        },
    )["result"]
    operations = {item["operation"]: item for item in mixed["answer_operations"]["results"]}
    assert operations["summary"]["status"] == "completed"
    assert operations["summary"]["fields"]["points"]
    assert operations["humor"]["status"] == "completed"
    assert mixed["response_coverage"]["all_required_addressed"] is True
    assert mixed["response_coverage"]["all_required_resolved"] is True
    assert all(f"{index}." in mixed["candidate_text"] for index in (1, 2))
    assert "joke:" in mixed["candidate_text"].lower()
    assert mixed["candidate_text"].index("1.") < mixed["candidate_text"].lower().index(
        "joke:"
    )
    assert "adjustment is clear" not in mixed["candidate_text"].lower()
    assert "lantern" in mixed["candidate_text"].lower()

    keep_open = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": opening["session_id"],
            "text": "Keep the reading-corner thread open; do not close it yet.",
        },
    )["result"]
    assert "keep" in keep_open["candidate_text"].lower()
    assert "reading-corner" in keep_open["candidate_text"].lower()
    assert "open" in keep_open["candidate_text"].lower()
    assert "missing piece" not in keep_open["candidate_text"].lower()
    assert "corrected meaning" not in keep_open["candidate_text"].lower()
    assert keep_open["intent_decision"]["intent"] != "memory_candidate"
    assert keep_open["intent_decision"].get("memory_candidate") is not True
    assert keep_open["session_proposition_ledger"]["recomputation"]["state"] in {
        "not_required",
        "expired_on_topic_transition",
    }
    for result in (opening, correction, changed_topic, mixed, keep_open):
        assert result["reviewed_memory_write_occurred"] is False
        assert result["conversational_memory_proposal_created"] is False
        _assert_locked(result)
