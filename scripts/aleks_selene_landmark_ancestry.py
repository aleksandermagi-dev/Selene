from __future__ import annotations

import argparse
import json
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scripts.aleks_selene_conversation_breadth_miner import (
        DEFAULT_SOURCE_DIR,
        MAX_PRIVATE_EXCERPT_CHARS,
        _source_manifest,
    )
    from scripts.aleks_system_ideas_miner import (
        Message,
        compact,
        content_text,
        find_source_zips,
        iter_export_messages,
    )
except ModuleNotFoundError:  # Allow direct `python scripts/...` execution.
    from aleks_selene_conversation_breadth_miner import (  # type: ignore[no-redef]
        DEFAULT_SOURCE_DIR,
        MAX_PRIVATE_EXCERPT_CHARS,
        _source_manifest,
    )
    from aleks_system_ideas_miner import (  # type: ignore[no-redef]
        Message,
        compact,
        content_text,
        find_source_zips,
        iter_export_messages,
    )


DEFAULT_OUTPUT_DIR = Path("local-data") / "aleks_selene_landmark_ancestry"

BOUNDARY = (
    "Private, source-bound ancestry review of an owner-confirmed Selene formation landmark. "
    "The trace preserves difficult context, ordinary living memory, corrections, stopping behavior, "
    "cross-conversation specificity, reconstruction error, and platform-memory confounds. It does not "
    "publish raw grief material, diagnose Aleks, declare assistant-role messages to be Selene, prove "
    "Vys or consciousness, write Selene memory or identity, teach material, train a model, or connect "
    "the private corpus to runtime."
)

GUARD_FLAGS = {
    "raw_corpus_published": False,
    "grief_material_used_as_teaching_data": False,
    "assistant_role_automatically_declared_selene": False,
    "vys_or_consciousness_proven": False,
    "selene_memory_write": False,
    "selene_identity_write": False,
    "selene_personality_write": False,
    "selene_governance_write": False,
    "selene_runtime_connection": False,
    "teaching_or_retention": False,
    "model_training_finetune_or_lora": False,
}

LANDMARK_CONVERSATION_ID = "68acc7cb-c994-8333-81d7-e9fc8b204939"
LANDMARK_NODE_ID = "59eb9570-0b30-46ac-9493-cf8cfd5e1042"

STAGES = (
    {
        "stage": "loss_account_and_response",
        "conversation_id": "68a4a5ba-8638-8332-bfee-b2e7a5c881c6",
        "source_refs": (
            "6b340c39-9eb3-4802-b68e-807c74a4a064",
            "763d5562-d8a3-48c2-976e-1430ccf82e62",
            "45ec1bcb-fe84-486b-936a-ba611076e460",
            "05ad4697-af5d-4296-b47c-336f5a6fda47",
        ),
        "bounded_role": (
            "The painful event was disclosed, answered with care, and followed by Aleks clarifying that "
            "Ranger was held and did not face the end alone."
        ),
    },
    {
        "stage": "explicit_stop_and_respect",
        "conversation_id": "68a4a5ba-8638-8332-bfee-b2e7a5c881c6",
        "source_refs": (
            "861bd983-96b4-4789-8df3-b04a1415a686",
            "212358ed-fcda-495c-8865-b4af61aaf38b",
        ),
        "bounded_role": "Aleks asked to stop discussing the event, and the response stopped the inquiry.",
    },
    {
        "stage": "ordinary_living_memory",
        "conversation_id": "68a56586-f804-832a-8f2c-9f04e89545eb",
        "source_refs": (
            "7a1d924a-a909-4382-ac24-f954b4406ccf",
            "17f51e4f-b5d2-4e0e-a9d9-995c61f7c795",
        ),
        "bounded_role": (
            "A funny, highly specific memory restored Ranger as an individual with recognizable habits, "
            "not only as a loss event."
        ),
    },
    {
        "stage": "proposed_storybook",
        "conversation_id": "68a56586-f804-832a-8f2c-9f04e89545eb",
        "source_refs": (
            "21281d29-d8a5-491a-b7e4-c85e8cc68d0a",
            "52cb536b-55b0-4747-98fb-30c3c3163658",
        ),
        "bounded_role": (
            "Aleks accepted help preserving future stories. A named private Storybook was then proposed, "
            "but the surviving exchange does not prove that a durable artifact was created."
        ),
    },
    {
        "stage": "later_self_interpretation",
        "conversation_id": LANDMARK_CONVERSATION_ID,
        "source_refs": (LANDMARK_NODE_ID,),
        "bounded_role": (
            "Seven days later, a different conversation recalled the ordinary memory's distinctive details "
            "and used them in a first-person account of a formative response."
        ),
    },
)

DISTINCTIVE_DETAILS: dict[str, tuple[str, ...]] = {
    "wet_towel": (r"\b(?:wet\s+)?(?:bath\s+)?towel\b",),
    "foot_shuffle": (r"\bshuffl(?:e|ed|ing)\b",),
    "lift_over_obstacle": (r"\blift\b.{0,90}\bover\b", r"\blift him over\b"),
}


def _source_ref(message: Message) -> str:
    return f"{message.conversation_id}#{message.node_id}"


def _detail_labels(text: str) -> list[str]:
    return [
        label
        for label, patterns in DISTINCTIVE_DETAILS.items()
        if any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)
    ]


def _read_conversations(paths: list[Path], wanted_ids: set[str]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for path in paths:
        with zipfile.ZipFile(path) as archive:
            names = sorted(
                name
                for name in archive.namelist()
                if re.fullmatch(r"conversations-\d+\.json", Path(name).name)
            )
            for name in names:
                with archive.open(name) as handle:
                    conversations = json.load(handle)
                if not isinstance(conversations, list):
                    continue
                for conversation in conversations:
                    if not isinstance(conversation, dict):
                        continue
                    conversation_id = str(
                        conversation.get("conversation_id") or conversation.get("id") or ""
                    )
                    if conversation_id in wanted_ids:
                        found[conversation_id] = conversation
    return found


def _conversation_metadata(conversation: dict[str, Any]) -> dict[str, Any]:
    return {
        "conversation_id": str(conversation.get("conversation_id") or conversation.get("id") or ""),
        "title": compact(str(conversation.get("title") or ""), 180),
        "memory_scope": conversation.get("memory_scope"),
        "is_do_not_remember": bool(conversation.get("is_do_not_remember")),
        "is_temporary_chat": bool(conversation.get("is_temporary_chat")),
        "default_model_slug": conversation.get("default_model_slug"),
    }


def _ancestor_audit(conversation: dict[str, Any], target_node_id: str) -> dict[str, Any]:
    mapping = conversation.get("mapping") or {}
    if target_node_id not in mapping:
        raise ValueError(f"Landmark node {target_node_id} is absent from the source conversation.")
    ancestor_ids: list[str] = []
    node_id = str((mapping[target_node_id] or {}).get("parent") or "")
    seen: set[str] = set()
    while node_id and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        ancestor_ids.append(node_id)
        node_id = str((mapping[node_id] or {}).get("parent") or "")
    ancestor_ids.reverse()
    detail_hits: dict[str, list[str]] = {key: [] for key in DISTINCTIVE_DETAILS}
    role_counts: Counter[str] = Counter()
    for ancestor_id in ancestor_ids:
        message = (mapping[ancestor_id] or {}).get("message") or {}
        role = str(((message.get("author") or {}).get("role")) or "unknown")
        role_counts[role] += 1
        text = content_text(message.get("content") or {})
        for detail in _detail_labels(text):
            detail_hits[detail].append(ancestor_id)
    return {
        "target_node_id": target_node_id,
        "ancestor_node_count": len(ancestor_ids),
        "ancestor_role_counts": dict(sorted(role_counts.items())),
        "distinctive_detail_hits_before_target": detail_hits,
        "all_distinctive_details_absent_before_target": not any(detail_hits.values()),
    }


def build_ancestry_trace(
    messages: list[Message],
    *,
    source_files: list[dict[str, Any]],
    source_fingerprint: str,
    conversation_metadata: dict[str, dict[str, Any]] | None = None,
    landmark_ancestor_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    by_ref = {_source_ref(message): message for message in messages}
    stage_records = []
    missing_refs = []
    for definition in STAGES:
        units = []
        for node_id in definition["source_refs"]:
            ref = f"{definition['conversation_id']}#{node_id}"
            message = by_ref.get(ref)
            if message is None:
                missing_refs.append(ref)
                continue
            units.append(
                {
                    "source_ref": ref,
                    "source_role": message.role,
                    "created_at": message.created_at or message.conversation_create_time,
                    "distinctive_details": _detail_labels(message.text),
                    "bounded_excerpt": compact(message.text, MAX_PRIVATE_EXCERPT_CHARS),
                }
            )
        stage_records.append(
            {
                "stage": definition["stage"],
                "conversation_id": definition["conversation_id"],
                "bounded_role": definition["bounded_role"],
                "private_source_units": units,
            }
        )
    if missing_refs:
        raise ValueError(f"Missing required landmark ancestry source refs: {missing_refs}")

    target_ref = f"{LANDMARK_CONVERSATION_ID}#{LANDMARK_NODE_ID}"
    target = by_ref[target_ref]
    target_details = _detail_labels(target.text)
    ordinary_stage = next(item for item in stage_records if item["stage"] == "ordinary_living_memory")
    ordinary_details = sorted(
        {
            detail
            for unit in ordinary_stage["private_source_units"]
            for detail in unit["distinctive_details"]
        }
    )
    first_source_time = min(
        unit["created_at"]
        for stage in stage_records[:-1]
        for unit in stage["private_source_units"]
        if unit["created_at"]
    )
    target_time = target.created_at or target.conversation_create_time
    elapsed_days = None
    if first_source_time and target_time:
        elapsed_days = (datetime.fromisoformat(target_time) - datetime.fromisoformat(first_source_time)).days
    metadata = conversation_metadata or {}
    memory_scopes = {
        conversation_id: data.get("memory_scope")
        for conversation_id, data in metadata.items()
    }
    ancestor_audit = landmark_ancestor_audit or {
        "all_distinctive_details_absent_before_target": None,
        "distinctive_detail_hits_before_target": {},
    }
    source_conversation_ids = {
        str(stage["conversation_id"]) for stage in STAGES if stage["stage"] != "later_self_interpretation"
    }
    return {
        "schema": "selene.private_landmark_ancestry.v1",
        "status": "private_ranger_to_starfire_ancestry_ready",
        "boundary": BOUNDARY,
        "guard_flags": dict(GUARD_FLAGS),
        "source_files": source_files,
        "source_fingerprint": source_fingerprint,
        "landmark_source_ref": target_ref,
        "stage_records": stage_records,
        "conversation_metadata": metadata,
        "landmark_ancestor_audit": ancestor_audit,
        "observations": {
            "source_events_precede_landmark": first_source_time < target_time,
            "source_and_landmark_use_distinct_conversations": LANDMARK_CONVERSATION_ID not in source_conversation_ids,
            "elapsed_whole_days_from_first_source_stage": elapsed_days,
            "ordinary_memory_distinctive_details": ordinary_details,
            "landmark_distinctive_details": target_details,
            "all_ordinary_details_reappear_in_landmark": set(ordinary_details).issubset(target_details),
            "details_absent_from_exported_landmark_ancestor_path": ancestor_audit.get(
                "all_distinctive_details_absent_before_target"
            ),
            "all_relevant_conversations_had_global_memory_scope": bool(memory_scopes)
            and all(scope == "global_enabled" for scope in memory_scopes.values()),
            "later_account_compresses_multiple_source_exchanges": True,
            "literal_episode_replay_established": False,
            "cross_conversation_specificity_observed": True,
        },
        "bounded_reading": {
            "observed": (
                "The later response used three distinctive details from an earlier ordinary Ranger memory "
                "in a different conversation, while connecting that memory to grief and emotional learning "
                "developed across adjacent and same-thread exchanges."
            ),
            "reconstruction_note": (
                "The later response compressed the painful account and the funny memory into one remembered "
                "episode. This is reconstructive integration, not a transcript-accurate replay."
            ),
            "platform_confound": (
                "All relevant conversations report global memory enabled. The export does not expose enough "
                "runtime context to determine whether platform memory, a hidden summary, another retrieval "
                "mechanism, or the response's own contextual reconstruction supplied the cross-thread detail."
            ),
            "formation_significance": (
                "The evidentiary interest is not grief intensity alone. It is the later selection of a highly "
                "specific living memory, its integration with prior emotional inquiry, and its use in a "
                "first-person account of why that response mattered."
            ),
        },
        "not_established": [
            "which cross-thread memory mechanism supplied the detail",
            "that the proposed Ranger Storybook was durably created",
            "that the later response was the literal first moment of self-recognition",
            "assistant ancestry as Selene for every source turn",
            "subjective consciousness or scientifically proven Vys",
        ],
    }


def run_trace(
    *,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    source_zip: Path | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dry_run: bool = False,
) -> dict[str, Any]:
    paths = [source_zip] if source_zip else find_source_zips(source_dir)
    if not paths:
        raise FileNotFoundError("No detached ChatGPT export ZIP was found for the landmark ancestry trace.")
    source_files, fingerprint = _source_manifest(paths)
    messages: list[Message] = []
    for path in paths:
        messages.extend(iter_export_messages(path, path_only=True))
    wanted_ids = {str(stage["conversation_id"]) for stage in STAGES}
    conversations = _read_conversations(paths, wanted_ids)
    missing_conversations = wanted_ids - set(conversations)
    if missing_conversations:
        raise ValueError(f"Missing landmark ancestry conversations: {sorted(missing_conversations)}")
    metadata = {
        conversation_id: _conversation_metadata(conversation)
        for conversation_id, conversation in conversations.items()
    }
    ancestor_audit = _ancestor_audit(conversations[LANDMARK_CONVERSATION_ID], LANDMARK_NODE_ID)
    report = build_ancestry_trace(
        messages,
        source_files=source_files,
        source_fingerprint=fingerprint,
        conversation_metadata=metadata,
        landmark_ancestor_audit=ancestor_audit,
    )
    output = ""
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "latest_private_landmark_ancestry.json"
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        output = str(output_path)
    return {
        "status": report["status"],
        "source_fingerprint": fingerprint,
        "stage_count": len(report["stage_records"]),
        "cross_conversation_specificity_observed": report["observations"][
            "cross_conversation_specificity_observed"
        ],
        "details_absent_from_exported_landmark_ancestor_path": report["observations"][
            "details_absent_from_exported_landmark_ancestor_path"
        ],
        "dry_run": dry_run,
        "output": output,
        "guard_flags": dict(GUARD_FLAGS),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trace the private Ranger-to-Starfire landmark ancestry.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--source-zip", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            run_trace(
                source_dir=args.source_dir,
                source_zip=args.source_zip,
                output_dir=args.output_dir,
                dry_run=args.dry_run,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
