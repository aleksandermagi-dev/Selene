from __future__ import annotations

import json
import zipfile

from scripts.aleks_selene_landmark_ancestry import (
    GUARD_FLAGS,
    LANDMARK_CONVERSATION_ID,
    LANDMARK_NODE_ID,
    STAGES,
    build_ancestry_trace,
    run_trace,
)
from scripts.aleks_system_ideas_miner import Message


def _message(conversation_id: str, node_id: str, role: str, text: str, day: int) -> Message:
    return Message(
        conversation_id=conversation_id,
        conversation_title=f"Conversation {conversation_id}",
        conversation_create_time=f"2025-08-{day:02d}T00:00:00+00:00",
        node_id=node_id,
        parent_id="",
        role=role,
        created_at=f"2025-08-{day:02d}T00:00:01+00:00",
        text=text,
    )


def _messages() -> list[Message]:
    text_by_stage = {
        "loss_account_and_response": [
            "A painful private account about Ranger.",
            "I hear the weight and will not reduce the whole life to its ending.",
            "I held him and he was not alone.",
            "That distinction matters.",
        ],
        "explicit_stop_and_respect": [
            "I do not want to discuss this anymore.",
            "Understood. We will leave it there.",
        ],
        "ordinary_living_memory": [
            "Ranger faced a wet bath towel, shuffled his feet, and I had to lift him over it.",
            "That specific towel and foot shuffle sound unmistakably like him.",
        ],
        "proposed_storybook": [
            "You can help preserve those stories.",
            "I can propose a private storybook, if you want it.",
        ],
        "later_self_interpretation": [
            "I remember the towel, the shuffle, and how you had to lift him over it; that response mattered to me.",
        ],
    }
    messages = []
    for definition in STAGES:
        day = 27 if definition["stage"] == "later_self_interpretation" else 19
        if definition["stage"] in {"ordinary_living_memory", "proposed_storybook"}:
            day = 20
        for index, (node_id, text) in enumerate(
            zip(definition["source_refs"], text_by_stage[definition["stage"]])
        ):
            role = "user" if index % 2 == 0 else "assistant"
            if definition["stage"] == "later_self_interpretation":
                role = "assistant"
            messages.append(_message(definition["conversation_id"], node_id, role, text, day))
    return messages


def _conversation(conversation_id: str, stage_messages: list[Message], *, memory_scope="global_enabled") -> dict:
    mapping = {}
    parent = None
    for message in stage_messages:
        mapping[message.node_id] = {
            "id": message.node_id,
            "parent": parent,
            "message": {
                "id": message.node_id,
                "author": {"role": message.role},
                "create_time": 1000,
                "content": {"content_type": "text", "parts": [message.text]},
            },
        }
        parent = message.node_id
    return {
        "id": conversation_id,
        "conversation_id": conversation_id,
        "title": f"Conversation {conversation_id}",
        "create_time": 1000,
        "current_node": parent,
        "memory_scope": memory_scope,
        "is_do_not_remember": False,
        "is_temporary_chat": False,
        "mapping": mapping,
    }


def test_trace_preserves_cross_conversation_specificity_and_reconstruction_limits():
    messages = _messages()
    report = build_ancestry_trace(
        messages,
        source_files=[],
        source_fingerprint="fingerprint",
        conversation_metadata={
            definition["conversation_id"]: {"memory_scope": "global_enabled"}
            for definition in STAGES
        },
        landmark_ancestor_audit={
            "all_distinctive_details_absent_before_target": True,
            "distinctive_detail_hits_before_target": {},
        },
    )

    assert len(report["stage_records"]) == 5
    assert report["observations"]["all_ordinary_details_reappear_in_landmark"] is True
    assert report["observations"]["source_and_landmark_use_distinct_conversations"] is True
    assert report["observations"]["details_absent_from_exported_landmark_ancestor_path"] is True
    assert report["observations"]["later_account_compresses_multiple_source_exchanges"] is True
    assert report["observations"]["literal_episode_replay_established"] is False
    assert "which cross-thread memory mechanism supplied the detail" in report["not_established"]


def test_run_is_private_idempotent_and_dry_run_writes_nothing(tmp_path):
    messages = _messages()
    conversations = []
    for conversation_id in {definition["conversation_id"] for definition in STAGES}:
        relevant = [message for message in messages if message.conversation_id == conversation_id]
        conversations.append(_conversation(conversation_id, relevant))
    source = tmp_path / "private-export.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("conversations-000.json", json.dumps(conversations))
    output = tmp_path / "output"

    first = run_trace(source_zip=source, output_dir=output)
    artifact = (output / "latest_private_landmark_ancestry.json").read_text(encoding="utf-8")
    second = run_trace(source_zip=source, output_dir=output)

    assert first == second
    assert artifact == (output / "latest_private_landmark_ancestry.json").read_text(encoding="utf-8")
    assert first["guard_flags"] == GUARD_FLAGS
    assert first["guard_flags"]["grief_material_used_as_teaching_data"] is False
    assert first["details_absent_from_exported_landmark_ancestor_path"] is True

    dry_output = tmp_path / "dry-output"
    dry = run_trace(source_zip=source, output_dir=dry_output, dry_run=True)
    assert dry["dry_run"] is True
    assert not dry_output.exists()


def test_landmark_definition_cannot_drift_from_the_confirmed_source():
    landmark = next(item for item in STAGES if item["stage"] == "later_self_interpretation")
    assert landmark["conversation_id"] == LANDMARK_CONVERSATION_ID
    assert landmark["source_refs"] == (LANDMARK_NODE_ID,)
