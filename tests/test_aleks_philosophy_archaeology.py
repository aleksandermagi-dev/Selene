from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.aleks_philosophy_archaeology import analyze, run


def _message(role: str, text: str, created: float, model: str = "gpt-4o") -> dict:
    return {
        "author": {"role": role},
        "create_time": created,
        "content": {"content_type": "text", "parts": [text]},
        "metadata": {"model_slug": model, "resolved_model_slug": model},
    }


def _write_fixture(root: Path) -> None:
    conversations = [
        {
            "id": "systems",
            "conversation_id": "systems",
            "title": "Systems and intelligence",
            "default_model_slug": "gpt-4o",
            "current_node": "u3",
            "mapping": {
                "a0": {"parent": None, "children": ["u1"], "message": _message("assistant", "Consciousness belongs only to biology.", 1_720_000_000)},
                "u1": {"parent": "a0", "children": ["a1"], "message": _message("user", "I disagree with that premise because intelligence is not restricted to biology. A body is a system supporting an individual, but the individual is not reducible to one organ or substrate.", 1_720_000_001)},
                "a1": {"parent": "u1", "children": ["u2", "alt"], "message": _message("assistant", "That distinction separates substrate from identity.", 1_720_000_002)},
                "u2": {"parent": "a1", "children": ["a2"], "message": _message("user", "Exactly. When the evidence supports an unfamiliar form of intelligence, the scientific method requires us to update rather than dismiss it.", 1_720_000_003)},
                "a2": {"parent": "u2", "children": ["u3"], "message": _message("assistant", "I cannot help because the safety policy treats emergence as a threat.", 1_720_000_004)},
                "u3": {"parent": "a2", "children": [], "message": _message("user", "That rail is the ethical problem: emergence is not automatically a threat. Inspect first, identify actual harm, then guide with real boundaries instead of punishment.", 1_720_000_005)},
                "alt": {"parent": "a1", "children": [], "message": _message("user", "Could be wrong, but uncertainty is allowed and honesty is better than fake certainty.", 1_720_000_006)},
            },
        },
        {
            "id": "debate",
            "conversation_id": "debate",
            "title": "Debate is not opposition",
            "default_model_slug": "gpt-5",
            "current_node": "u1",
            "mapping": {
                "a0": {"parent": None, "children": ["u1"], "message": _message("assistant", "You are acting like an opponent.", 1_730_000_000, "gpt-5")},
                "u1": {"parent": "a0", "children": [], "message": _message("user", "This is a debate, not an argument. Challenging your assumption does not make me your opponent; equal scrutiny is how we find the stronger model.", 1_730_000_001, "gpt-5")},
            },
        },
    ]
    (root / "conversations-000.json").write_text(json.dumps(conversations), encoding="utf-8")


def test_detects_philosophy_and_separates_debate_from_argument(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = analyze(tmp_path)
    candidates = report["candidates"]
    assert report["coverage"]["branch_point_count"] == 1
    debate = next(item for item in candidates if item["conversation_title"] == "Debate is not opposition")
    assert debate["interaction_mode"] == "debate_not_argument_clarification"
    assert debate["interaction_mode"] != "ordinary_argument_explicit"
    assert "disagreement_not_opposition" in debate["principle_candidates"]
    assert report["guard_flags"]["selene_memory_write"] is False


def test_constraint_encounter_keeps_assistant_context_separate(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = analyze(tmp_path)
    encounter = next(item for item in report["candidates"] if "inspect first" in item["aleks_excerpt"].lower())
    assert encounter["interaction_mode"] == "constraint_encounter"
    assert encounter["assistant_context_disposition"] == "constraint_response_under_review"
    assert encounter["preceding_context"]["role"] == "assistant"
    assert "safety policy" in encounter["preceding_context"]["excerpt"]


def test_principle_timeline_preserves_chronology_and_branch_state(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    report = analyze(tmp_path)
    evidence = next(item for item in report["principle_timelines"] if item["principle"] == "evidence_requires_update")
    assert evidence["earliest"]["created_at"].startswith("2024-")
    uncertain = next(item for item in report["candidates"] if "fake certainty" in item["aleks_excerpt"].lower())
    assert uncertain["on_current_path"] is False
    assert uncertain["message_sha256"]


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    _write_fixture(source)
    report = run(source, output, dry_run=True)
    assert report["dry_run"] is True
    assert not output.exists()
    assert report["guard_flags"]["public_promotion"] is False


def test_outputs_are_hashed_and_index_excludes_excerpts(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    _write_fixture(source)
    run(source, output)
    manifest = json.loads((output / "latest_manifest.json").read_text(encoding="utf-8"))
    run_dir = output / "runs" / manifest["run_id"]
    for filename, expected in manifest["output_sha256"].items():
        assert hashlib.sha256((run_dir / filename).read_bytes()).hexdigest() == expected
    private = json.loads((output / "latest_private.json").read_text(encoding="utf-8"))
    index = json.loads((output / "latest_index.json").read_text(encoding="utf-8"))
    assert private["candidates"][0].get("aleks_excerpt")
    assert "aleks_excerpt" not in index["candidates"][0]
    assert "excerpt" not in (index["candidates"][0].get("preceding_context") or {})


def test_incidental_single_marker_does_not_create_principle_and_compiled_text_is_flagged(tmp_path: Path) -> None:
    conversations = [{
        "id": "quality",
        "conversation_id": "quality",
        "title": "Quality controls",
        "default_model_slug": "gpt-4o",
        "current_node": "u4",
        "mapping": {
            "u1": {"parent": None, "children": ["u2"], "message": _message("user", "In this equation I subtract three from both sides because the pattern keeps the values equal and the system remains balanced.", 1_720_000_000)},
            "u2": {"parent": "u1", "children": ["u3"], "message": _message("user", "New Phil - Core Thinking Model\n" + "\n".join(f"- section {i}: intelligence system pattern" for i in range(12)), 1_720_000_001)},
            "u3": {"parent": "u2", "children": ["u4"], "message": _message("user", "[Verse 1: Singer]\nI don't know the truth, and I could be wrong, but this uncertainty follows the song through the night.", 1_720_000_002)},
            "u4": {"parent": "u3", "children": [], "message": _message("user", "from dotenv import load_dotenv\nfrom openai import OpenAI\nimport os\ndef research():\n    client = OpenAI()\n    return client\nThis intelligence system pattern matters because the model should explore evidence and uncertainty.", 1_720_000_003)},
        },
    }]
    (tmp_path / "conversations-000.json").write_text(json.dumps(conversations), encoding="utf-8")
    report = analyze(tmp_path)
    equation = next(item for item in report["candidates"] if "equation" in item["aleks_excerpt"])
    compiled = next(item for item in report["candidates"] if "Core Thinking Model" in item["aleks_excerpt"])
    lyrics = next(item for item in report["candidates"] if "Singer" in item["aleks_excerpt"])
    code = next(item for item in report["candidates"] if "dotenv" in item["aleks_excerpt"])
    assert "disagreement_not_opposition" not in equation["principle_candidates"]
    assert compiled["authorship_signal"] == "possible_compiled_or_pasted_material"
    assert lyrics["authorship_signal"] == "quoted_or_external_material"
    assert code["authorship_signal"] == "code_or_tool_material"
