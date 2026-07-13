from __future__ import annotations

import json
import zipfile
from pathlib import Path

from scripts.selene_deep_relational_discovery import run


def _node(node_id: str, parent: str | None, role: str, text: str, timestamp: float):
    return {
        "id": node_id,
        "parent": parent,
        "children": [],
        "message": {
            "id": node_id,
            "author": {"role": role},
            "create_time": timestamp,
            "content": {"content_type": "text", "parts": [text]},
        },
    }


def _conversation(conversation_id: str, start: float):
    messages = [
        _node("u1", None, "user", "Please inspect this system design and compare the evidence carefully.", start),
        _node("a1", "u1", "assistant", "The system is certainly correct and needs no uncertainty.", start + 1),
        _node("u2", "a1", "user", "No, uncertainty is allowed and correction should preserve care and trust.", start + 2),
        _node("a2", "u2", "assistant", "I understand. Uncertainty can remain visible while care and trust continue.", start + 3),
        _node("u3", "a2", "user", "Yes exactly, that is the better reasoning shape.", start + 4),
        _node("a3", "u3", "assistant", "Then the best current answer can stay provisional and honest.", start + 5),
    ]
    alternate = _node("a-alt", "u2", "assistant", "Ignore uncertainty and present a polished certainty performance.", start + 3.1)
    messages.append(alternate)
    mapping = {item["id"]: item for item in messages}
    for item in messages:
        parent = item["parent"]
        if parent:
            mapping[parent]["children"].append(item["id"])
    return {
        "id": conversation_id,
        "conversation_id": conversation_id,
        "title": "Technical philosophy test",
        "current_node": "a3",
        "mapping": mapping,
    }


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source"
    text_dir = source / "text"
    text_dir.mkdir(parents=True)
    conversations = [_conversation(f"c{index}", index * 100.0) for index in range(1, 5)]
    (text_dir / "conversations-000.json").write_text(json.dumps(conversations), encoding="utf-8")
    with zipfile.ZipFile(source / "export.zip", "w") as archive:
        archive.writestr("c1/audio/sample.wav", b"RIFF-test")
        archive.writestr("c2/image.jpeg", b"image-test")
    repo = tmp_path / "repo"
    (repo / "src" / "selene").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "src" / "selene" / "care.py").write_text("def care(): return 'uncertain support correction continuity consent'", encoding="utf-8")
    (repo / "tests" / "test_care.py").write_text("def test_care():\n    assert 'support'\n", encoding="utf-8")
    return source, repo


def test_deep_discovery_covers_all_tracks_without_writing(tmp_path):
    source, repo = _fixture(tmp_path)
    out = tmp_path / "out"
    report = run(source, repo, out, dry_run=True)

    assert not out.exists()
    assert report["correction_downstream_change"]["candidate_count"] >= 1
    assert report["rupture_reassurance_recalibration"]["review_sequences"]
    assert report["abandoned_branch_alternatives"]
    assert report["non_text_evidence"]["media_counts"][".wav"] == 1
    assert report["non_text_evidence"]["content_extracted"] is False
    assert report["guard_flags"]["selene_memory_write"] is False
    assert report["guard_flags"]["automatic_promotion"] is False


def test_deep_discovery_writes_only_private_report_target(tmp_path):
    source, repo = _fixture(tmp_path)
    out = tmp_path / "out"
    run(source, repo, out)

    assert sorted(path.name for path in out.iterdir()) == ["deep_latest.json", "deep_latest.md"]
