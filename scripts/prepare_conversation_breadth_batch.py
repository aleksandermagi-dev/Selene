from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
import subprocess
import zipfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ROOT = ROOT / "local-data" / "curriculum_sources_20260719" / "sources"
DEFAULT_OUTPUT = ROOT / "local-data" / "conversation_breadth_batch_20260906"

FEATURE_PATTERNS: dict[str, tuple[str, ...]] = {
    "yes_no_in_context": (r"^(?:yes|no|yeah|nope|sure|okay|ok)\b",),
    "preference_discovery_or_update": (r"\bprefer\b", r"\brather\b", r"\bdon't like\b", r"\bdo not like\b"),
    "rejection_or_redirection": (r"\bno thanks\b", r"\bnot interested\b", r"\binstead\b", r"\bwon't work\b"),
    "clarification": (r"\bwhat kind\b", r"\bwhich\b", r"\bwhat do you mean\b", r"\bcould you clarify\b"),
    "changed_constraint": (r"\bactually\b", r"\bchange\b", r"\bmake that\b", r"\bnever mind\b", r"\binstead\b"),
    "comparison_or_choice": (r"\bcompare\b", r"\bbetter\b", r"\bversus\b", r"\bwhich (?:one|option)\b"),
    "informal_or_spoken_shape": (r"\b(?:um|uh|yeah|okay|gonna|wanna)\b", r"\.\.\.", r"!{2,}"),
    "reason_or_explanation": (r"\bwhy\b", r"\bbecause\b", r"\breason\b"),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_revision(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _episode(source: str, episode_id: str, turns: Iterable[tuple[str, str]], **extra: Any) -> dict[str, Any]:
    normalized = [
        {"role": str(role), "text": " ".join(str(text).split())}
        for role, text in turns
        if str(text).strip()
    ]
    return {"source": source, "episode_id": str(episode_id), "turns": normalized, **extra}


def _taskmaster(source_root: Path) -> Iterator[dict[str, Any]]:
    data_dir = source_root / "github_taskmaster" / "TM-2-2020" / "data"
    for path in sorted(data_dir.glob("*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            yield _episode(
                "taskmaster_2",
                row.get("conversation_id", ""),
                ((turn.get("speaker", "unknown"), turn.get("text", "")) for turn in row.get("utterances", [])),
                domain=path.stem,
            )


def _redial(source_root: Path) -> Iterator[dict[str, Any]]:
    path = source_root / "github_redial_data" / "extracted" / "train_data.jsonl"
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            respondent = row.get("respondentWorkerId")
            yield _episode(
                "redial",
                row.get("conversationId", ""),
                (
                    (
                        "respondent" if turn.get("senderWorkerId") == respondent else "initiator",
                        turn.get("text", ""),
                    )
                    for turn in row.get("messages", [])
                ),
            )


def _ccpe(source_root: Path) -> Iterator[dict[str, Any]]:
    path = source_root / "github_ccpe" / "data.json"
    for row in json.loads(path.read_text(encoding="utf-8")):
        yield _episode(
            "ccpe_m",
            row.get("conversationId", ""),
            ((turn.get("speaker", "unknown"), turn.get("text", "")) for turn in row.get("utterances", [])),
        )


def _topical_chat(source_root: Path) -> Iterator[dict[str, Any]]:
    archive = source_root / "github_topical_chat" / "github_topical_chat-7c939229cbcf6f55f6977b341a5a2f2fe982d53f.zip"
    member = (
        "Topical-Chat-7c939229cbcf6f55f6977b341a5a2f2fe982d53f/"
        "conversations/train.json"
    )
    with zipfile.ZipFile(archive) as package:
        rows = json.loads(package.read(member).decode("utf-8"))
    for episode_id, row in rows.items():
        turns = row.get("content", row) if isinstance(row, dict) else row
        yield _episode(
            "topical_chat",
            episode_id,
            ((turn.get("agent", "unknown"), turn.get("message", "")) for turn in turns),
        )


def _first_branch(node: dict[str, Any], limit: int = 10) -> list[tuple[str, str]]:
    turns: list[tuple[str, str]] = []
    current: dict[str, Any] | None = node
    while current and len(turns) < limit:
        turns.append((str(current.get("role") or "unknown"), str(current.get("text") or "")))
        replies = [reply for reply in current.get("replies", []) if reply.get("lang") == "en"]
        if not replies:
            break
        current = min(replies, key=lambda reply: (reply.get("rank", 999999), str(reply.get("message_id", ""))))
    return turns


def _oasst1(source_root: Path) -> Iterator[dict[str, Any]]:
    path = source_root / "hf_oasst1" / "2023-04-12_oasst_ready.trees.jsonl.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            prompt = row.get("prompt") or {}
            if prompt.get("lang") != "en":
                continue
            turns = _first_branch(prompt)
            yield _episode(
                "oasst1",
                row.get("message_tree_id", ""),
                turns,
                root_branch_count=len([reply for reply in prompt.get("replies", []) if reply.get("lang") == "en"]),
            )


def _features(episode: dict[str, Any]) -> list[str]:
    texts = [str(turn["text"]) for turn in episode["turns"]]
    joined = "\n".join(texts).lower()
    found = [
        name
        for name, patterns in FEATURE_PATTERNS.items()
        if any(re.search(pattern, joined, flags=re.IGNORECASE) for pattern in patterns)
    ]
    if len(texts) >= 6:
        found.append("sustained_exchange")
    if sum(text.count("?") for text in texts) >= 2:
        found.append("question_answer_flow")
    if any(len(text.split()) <= 4 for text in texts) and any(len(text.split()) >= 24 for text in texts):
        found.append("turn_length_variation")
    if episode.get("root_branch_count", 0) > 1:
        found.append("branching_alternatives")
    return sorted(set(found))


def _balanced_sample(episodes: Iterable[dict[str, Any]], count: int) -> tuple[int, list[dict[str, Any]]]:
    total = 0
    candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    for episode in episodes:
        total += 1
        features = _features(episode)
        episode["review_labels"] = features
        turn_count = len(episode["turns"])
        if turn_count < 3:
            continue
        candidates.append((len(features), min(turn_count, 12), str(episode["episode_id"]), episode))
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))
    selected: list[dict[str, Any]] = []
    covered: set[str] = set()
    remaining = list(candidates)

    # Preserve actual turn-shape variation. A feature-rich long exchange must
    # not silently become the only model of natural conversation.
    buckets = (
        lambda turns: 3 <= turns <= 6,
        lambda turns: 7 <= turns <= 14,
        lambda turns: turns >= 15,
    )
    for accepts in buckets:
        if len(selected) >= count:
            break
        matches = [
            (index, candidate)
            for index, candidate in enumerate(remaining)
            if accepts(len(candidate[3]["turns"]))
        ]
        if not matches:
            continue
        best_index, _ = max(
            matches,
            key=lambda pair: (pair[1][0], pair[1][1], pair[1][2]),
        )
        _, _, _, chosen = remaining.pop(best_index)
        selected.append(chosen)
        covered.update(chosen["review_labels"])

    while remaining and len(selected) < count:
        best_index = max(
            range(len(remaining)),
            key=lambda index: (
                len(set(remaining[index][3]["review_labels"]) - covered),
                remaining[index][0],
                remaining[index][1],
                -index,
            ),
        )
        _, _, _, chosen = remaining.pop(best_index)
        selected.append(chosen)
        covered.update(chosen["review_labels"])
    return total, selected


def _source_receipts(source_root: Path) -> list[dict[str, Any]]:
    taskmaster = source_root / "github_taskmaster"
    task_files = sorted((taskmaster / "TM-2-2020" / "data").glob("*.json"))
    task_manifest = "\n".join(f"{path.name}:{_sha256(path)}" for path in task_files).encode("utf-8")
    return [
        {
            "source": "taskmaster_2",
            "revision": _git_revision(taskmaster),
            "artifact": "TM-2-2020/data/*.json",
            "artifact_sha256": hashlib.sha256(task_manifest).hexdigest(),
            "license": "CC-BY-4.0",
            "use": "mechanism_review_only",
        },
        {
            "source": "redial",
            "revision": _git_revision(source_root / "github_redial_data"),
            "artifact": "redial_dataset.zip",
            "artifact_sha256": _sha256(source_root / "github_redial_data" / "redial_dataset.zip"),
            "license": "CC-BY-4.0",
            "use": "mechanism_review_only",
        },
        {
            "source": "ccpe_m",
            "revision": _git_revision(source_root / "github_ccpe"),
            "artifact": "data.json",
            "artifact_sha256": _sha256(source_root / "github_ccpe" / "data.json"),
            "license": "CC-BY-4.0",
            "use": "mechanism_review_only",
        },
        {
            "source": "topical_chat",
            "revision": "7c939229cbcf6f55f6977b341a5a2f2fe982d53f",
            "artifact": "github_topical_chat-7c939229cbcf6f55f6977b341a5a2f2fe982d53f.zip",
            "artifact_sha256": _sha256(source_root / "github_topical_chat" / "github_topical_chat-7c939229cbcf6f55f6977b341a5a2f2fe982d53f.zip"),
            "license": "CDLA-Sharing-1.0",
            "use": "isolated_mechanism_review_only",
        },
        {
            "source": "oasst1",
            "revision": "fdf72ae0827c1cda404aff25b6603abec9e3399b",
            "artifact": "2023-04-12_oasst_ready.trees.jsonl.gz",
            "artifact_sha256": _sha256(source_root / "hf_oasst1" / "2023-04-12_oasst_ready.trees.jsonl.gz"),
            "license": "Apache-2.0",
            "use": "structure_and_response_function_review_only",
        },
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a private, review-only conversational breadth sample.")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--per-source", type=int, default=4)
    args = parser.parse_args()

    loaders = (_taskmaster, _redial, _ccpe, _topical_chat, _oasst1)
    args.output.mkdir(parents=True, exist_ok=True)
    samples: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for loader in loaders:
        total, selected = _balanced_sample(loader(args.source_root), args.per_source)
        source_name = selected[0]["source"] if selected else loader.__name__.lstrip("_")
        counts[source_name] = total
        samples.extend(selected)

    receipts = _source_receipts(args.source_root)
    manifest = {
        "status": "review_only_not_taught",
        "source_counts": counts,
        "sample_count": len(samples),
        "samples_per_source": args.per_source,
        "sources": receipts,
        "boundaries": {
            "raw_dialogue_available_to_chat": False,
            "source_persona_adopted": False,
            "source_facts_retained": False,
            "source_wording_taught": False,
            "memory_write": False,
            "identity_or_personality_change": False,
            "model_training": False,
            "output_is_private_and_git_ignored": True,
        },
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (args.output / "review_samples.json").write_text(json.dumps(samples, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
