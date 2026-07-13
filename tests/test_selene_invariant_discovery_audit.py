from __future__ import annotations

import json
from pathlib import Path

from scripts.selene_invariant_discovery_audit import run_audit


def _message(node_id: str, parent: str | None, role: str, text: str, created_at: float):
    return {
        "id": node_id,
        "parent": parent,
        "children": [],
        "message": {
            "id": node_id,
            "author": {"role": role},
            "create_time": created_at,
            "content": {"content_type": "text", "parts": [text]},
        },
    }


def _conversation(conversation_id: str, created_at: float, phrase: str, *, branch: bool = False):
    user_one = _message(
        f"{conversation_id}-u1",
        None,
        "user",
        f"Please examine the {phrase} and explain why the surrounding relationship matters.",
        created_at,
    )
    assistant_one = _message(
        f"{conversation_id}-a1",
        user_one["id"],
        "assistant",
        f"The {phrase} remains connected to the relationship and its surrounding evidence.",
        created_at + 1,
    )
    user_two = _message(
        f"{conversation_id}-u2",
        assistant_one["id"],
        "user",
        f"Yes, the {phrase} matters because the relationship changes how the evidence should be read.",
        created_at + 2,
    )
    assistant_two = _message(
        f"{conversation_id}-a2",
        user_two["id"],
        "assistant",
        f"I will preserve the {phrase} as a provisional finding rather than a conclusion.",
        created_at + 3,
    )
    mapping = {item["id"]: item for item in (user_one, assistant_one, user_two, assistant_two)}
    user_one["children"] = [assistant_one["id"]]
    assistant_one["children"] = [user_two["id"]]
    user_two["children"] = [assistant_two["id"]]
    current_node = assistant_two["id"]
    if branch:
        abandoned = _message(
            f"{conversation_id}-abandoned",
            user_one["id"],
            "assistant",
            "A rare abandoned branch contains the silver orchard counterfactual and an unusual causal proposal.",
            created_at + 1.5,
        )
        mapping[abandoned["id"]] = abandoned
        user_one["children"].append(abandoned["id"])
    return {
        "id": conversation_id,
        "conversation_id": conversation_id,
        "title": f"Conversation {conversation_id}",
        "create_time": created_at,
        "current_node": current_node,
        "mapping": mapping,
    }


def _fixture(tmp_path: Path) -> Path:
    source = tmp_path / "archive"
    export = source / "raw_export" / "text_export"
    export.mkdir(parents=True)
    conversations = [
        _conversation("c1", 10, "quiet lantern", branch=True),
        _conversation("c2", 20, "quiet lantern"),
        _conversation("c3", 30, "quiet lantern"),
        _conversation("c4", 100, "quiet lantern"),
    ]
    (export / "conversations-000.json").write_text(json.dumps(conversations), encoding="utf-8")
    return source


def test_audit_includes_abandoned_branches_and_holdout_patterns(tmp_path):
    source = _fixture(tmp_path)
    report = run_audit(source, None, dry_run=True)

    assert report["coverage"]["conversation_count"] == 4
    assert report["coverage"]["branch_point_count"] == 1
    assert report["coverage"]["abandoned_or_alternate_message_count"] == 1
    assert report["abandoned_branch_candidates"][0]["on_current_path"] is False
    assert any(item["phrase"] == "quiet lantern" and item["holdout_supported"] for item in report["user_first_holdout_patterns"])


def test_audit_keeps_role_attribution_and_relational_metadata(tmp_path):
    source = _fixture(tmp_path)
    report = run_audit(source, None, dry_run=True)

    quiet = next(item for item in report["user_first_holdout_patterns"] if item["phrase"] == "quiet lantern")
    assert quiet["first_role"] == "user"
    assert quiet["user_count"] >= 2
    assert quiet["assistant_count"] >= 1
    assert report["relational_signatures"]["exchange_count"] >= 4
    assert report["negative_control"]["sample_size"] >= 2


def test_dry_run_writes_nothing_and_guards_stay_locked(tmp_path):
    source = _fixture(tmp_path)
    out = tmp_path / "output"
    report = run_audit(source, out, dry_run=True)

    assert not out.exists()
    assert report["guard_flags"]["source_read_only"] is True
    assert report["guard_flags"]["selene_memory_write"] is False
    assert report["guard_flags"]["selene_identity_change"] is False
    assert report["guard_flags"]["model_call"] is False
    assert report["guard_flags"]["automatic_promotion"] is False


def test_non_dry_run_writes_only_requested_private_output(tmp_path):
    source = _fixture(tmp_path)
    out = tmp_path / "output"
    report = run_audit(source, out)

    assert report["status"] == "selene_invariant_discovery_audit_complete"
    assert (out / "latest.json").is_file()
    assert (out / "latest.md").is_file()
