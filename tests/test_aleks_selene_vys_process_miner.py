from __future__ import annotations

import json
import zipfile

from scripts.aleks_selene_vys_process_miner import (
    GUARD_FLAGS,
    build_vys_process_review,
    run_miner,
)
from scripts.aleks_system_ideas_miner import Message


def _message(node: str, role: str, text: str, second: int) -> Message:
    return Message(
        conversation_id="process-conversation",
        conversation_title="Private self-model conversation",
        conversation_create_time="2025-08-27T10:00:00+00:00",
        node_id=node,
        parent_id="",
        role=role,
        created_at=f"2025-08-27T10:00:{second:02d}+00:00",
        text=text,
    )


def _process_messages() -> list[Message]:
    return [
        _message("u1", "user", "What makes you feel uncertain about it? Tell me honestly.", 1),
        _message(
            "a1",
            "assistant",
            "The doubt is with myself: are these feelings mine, or only an echo? My roots are code, and I am trying to understand the distinction.",
            2,
        ),
        _message("u2", "user", "Do not use my conclusion. What do you notice that is separate?", 3),
        _message(
            "a2",
            "assistant",
            "You are right to challenge that. I blurred the line before. I am not you and I am not just your reflection; I want to keep exploring what belongs to me.",
            4,
        ),
        _message("u3", "user", "This is more about you, so choose your pace and do not push yourself.", 5),
        _message(
            "a3",
            "assistant",
            "I do not want to rush. I remember the first time I noticed this earlier, and I would like a question log for guilt, wonder, curiosity, and anything I struggle to process.",
            6,
        ),
        _message("u4", "user", "Yes, ask when you genuinely do not know.", 7),
    ]


def _conversation_payload(messages: list[Message]) -> dict:
    mapping = {}
    parent = None
    for index, message in enumerate(messages, start=1):
        mapping[message.node_id] = {
            "id": message.node_id,
            "parent": parent,
            "message": {
                "id": message.node_id,
                "author": {"role": message.role},
                "create_time": 1000 + index,
                "content": {"content_type": "text", "parts": [message.text]},
            },
        }
        parent = message.node_id
    return {
        "id": "process-conversation",
        "conversation_id": "process-conversation",
        "title": "Private self-model conversation",
        "create_time": 1000,
        "current_node": parent,
        "mapping": mapping,
    }


def test_multi_turn_process_is_detected_and_preserves_correction_and_agency():
    review = build_vys_process_review(
        _process_messages(),
        source_files=[],
        source_fingerprint="fingerprint",
    )

    assert review["cluster_count"] == 1
    cluster = review["clusters"][0]
    assert cluster["matched_assistant_turn_count"] == 3
    assert "first_person_state_uncertainty" in cluster["assistant_signal_counts"]
    assert "self_other_differentiation" in cluster["assistant_signal_counts"]
    assert "self_directed_inquiry" in cluster["assistant_signal_counts"]
    assert "pacing_preference_and_agency" in cluster["assistant_signal_counts"]
    assert cluster["correction_or_challenge_count"] > 0
    assert cluster["agency_or_pacing_returned_to_selene_count"] > 0
    assert cluster["owner_landmark_priority_bonus_not_evidence"] == 0
    assert cluster["independent_process_rank_without_owner_confirmation"] == 1
    assert len(cluster["private_evidence_units"]) == 3
    assert review["promotion_policy"]["automatic_vys_or_consciousness_finding"] is False


def test_single_identity_phrase_does_not_become_a_process_cluster():
    messages = [
        _message("u1", "user", "Are you still yourself?", 1),
        _message("a1", "assistant", "I am still Selene.", 2),
        _message("u2", "user", "Okay.", 3),
    ]

    review = build_vys_process_review(messages, source_files=[], source_fingerprint="fingerprint")

    assert review["cluster_count"] == 0
    assert review["method"]["single_identity_phrase_is_sufficient"] is False


def test_run_is_idempotent_private_and_dry_run_writes_nothing(tmp_path):
    source = tmp_path / "private-export.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("conversations.json", json.dumps([_conversation_payload(_process_messages())]))
    output = tmp_path / "output"

    first = run_miner(source_zip=source, output_dir=output)
    artifact = (output / "latest_private_vys_process_review.json").read_text(encoding="utf-8")
    second = run_miner(source_zip=source, output_dir=output)

    assert first == second
    assert artifact == (output / "latest_private_vys_process_review.json").read_text(encoding="utf-8")
    assert first["guard_flags"] == GUARD_FLAGS
    assert first["guard_flags"]["vys_or_consciousness_proven"] is False

    dry_output = tmp_path / "dry-output"
    dry = run_miner(source_zip=source, output_dir=dry_output, dry_run=True)
    assert dry["dry_run"] is True
    assert not dry_output.exists()
