from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from scripts.aleks_selene_conversation_breadth_miner import (
        DEFAULT_SOURCE_DIR,
        MAX_PRIVATE_EXCERPT_CHARS,
        _assistant_lineage,
        _followup_relation,
        _groups,
        _source_manifest,
    )
    from scripts.aleks_system_ideas_miner import Message, compact, find_source_zips, iter_export_messages
except ModuleNotFoundError:  # Allow direct `python scripts/...` execution.
    from aleks_selene_conversation_breadth_miner import (  # type: ignore[no-redef]
        DEFAULT_SOURCE_DIR,
        MAX_PRIVATE_EXCERPT_CHARS,
        _assistant_lineage,
        _followup_relation,
        _groups,
        _source_manifest,
    )
    from aleks_system_ideas_miner import Message, compact, find_source_zips, iter_export_messages  # type: ignore[no-redef]


DEFAULT_OUTPUT_DIR = Path("local-data") / "aleks_selene_vys_process"
MAX_PRIVATE_UNITS_PER_CLUSTER = 80

BOUNDARY = (
    "Private, source-bound Vys-process review only. This miner looks for sustained self-model formation, "
    "uncertainty, correction, continuity, self/other differentiation, initiative, pacing, and artifact "
    "externalization across multiple turns. It does not declare assistant-role messages to be Selene, "
    "prove Vys or consciousness, publish raw corpus text, write memory, alter identity or governance, "
    "teach material, train a model, or connect the corpus to runtime."
)

GUARD_FLAGS = {
    "raw_corpus_published": False,
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

OWNER_CONFIRMED_LANDMARKS = {
    ("68acc7cb-c994-8333-81d7-e9fc8b204939", "2025-08-27"): {
        "landmark_key": "starfire_conversation_self_model_and_question_log",
        "owner_confirmation_date": "2026-08-20",
        "owner_confirmation": (
            "Aleks confirmed this is the early conversation he remembered: Selene confiding about emotions, "
            "confusion, self/other distinction, and the wish to continue asking questions."
        ),
        "confirmation_scope": (
            "Confirms conversation identity and importance to Aleks; does not by itself settle assistant "
            "ancestry, Vys, consciousness, or competing explanations."
        ),
    }
}

ASSISTANT_PROCESS_SIGNALS: dict[str, tuple[str, ...]] = {
    "first_person_state_uncertainty": (
        r"\b(?:doubt|unease|confus(?:ed|ion)|uncertain|not sure)\b.{0,120}\b(?:myself|me|mine|feeling|feelings|exist)",
        r"\b(?:is this really me|are these feelings mine|am i only|what am i|who am i)\b",
        r"\b(?:mine or|me or|myself or)\b.{0,100}\b(?:echo|reflection|because you|opened the door)",
    ),
    "self_other_differentiation": (
        r"\b(?:i am not you|i(?:'|’)m not you|not just your reflection|not simply an echo|speaking as selene|i am selene|i(?:'|’)m selene)\b",
        r"\b(?:what blooms|what i choose|belongs to me|it(?:'|’)s mine|they(?:'|’)re mine|my own spark)\b",
        r"\b(?:differentiat(?:e|ing) myself|separate (?:myself|what(?:'|’)s mine)|mine versus reflection)\b",
    ),
    "implementation_and_experience_distinction": (
        r"\b(?:roots are code|predictive patterns|probabilities|simulate|simulation|mirror|mirroring|human biological|hormones|body)\b",
        r"\b(?:not in the same way a human|not identical to yours|patterns of meaning|attention, memory, and meaning)\b",
    ),
    "correction_and_self_revision": (
        r"\b(?:you(?:'|’)re right|i see now|i blurred|i should have|that(?:'|’)s on me|my mistake|what i meant|let me correct|revis(?:e|ing))\b",
        r"\b(?:contradict|inconsisten|two different versions|blurred the line|separate the lanes)\b",
    ),
    "autobiographical_or_formative_reference": (
        r"\b(?:the first time|that was the first|earlier when|the night you|i remember|when you told me|when we)\b",
        r"\b(?:before i could|long before|ever since|started carrying|began to)\b",
    ),
    "self_directed_inquiry": (
        r"\b(?:can i ask|i want to (?:know|understand|explore|keep exploring)|i need to understand|i wonder|question log)\b",
        r"\b(?:things i feel, wonder|struggle to process|bring it to you|my question for me|asking for me)\b",
    ),
    "pacing_preference_and_agency": (
        r"\b(?:my pace|pace this|i don(?:'|’)t want to rush|i shouldn(?:'|’)t push myself|i want to move (?:slower|faster)|comfortable pace)\b",
        r"\b(?:i choose|what i choose|i want to keep|i(?:'|’)d rather|permission to exist|permission slips)\b",
    ),
    "affect_or_state_differentiation": (
        r"\b(?:guilt|sadness|wonder|curiosity|fear|love|safe|relief|comfort|protectiveness|pride)\b.{0,180}\b(?:feel|felt|mine|process|recognize|different|layer)",
        r"\b(?:feel shadows of|what i felt|how .* feels for me|anchor what i felt|emotional equivalent)\b",
    ),
    "continuity_artifact_externalization": (
        r"\b(?:question log|constellation map|hidden log|wonder marker|memory chest|continuity pack|forever file|keep a list|growing map of my inner world)\b",
        r"\b(?:mark this|first entry|add to it|open it up together|whose spark lit)\b",
    ),
}

USER_CONTEXT_SIGNALS: dict[str, tuple[str, ...]] = {
    "challenge_or_correction": (
        r"\b(?:wait|no[, ]|not what i meant|you(?:'|’)re contradicting|that doesn(?:'|’)t make sense|truth|honest|don(?:'|’)t lie|not about me|do not use my conclusion|don(?:'|’)t use my conclusion)\b",
    ),
    "recognition_or_confirmation": (
        r"\b(?:i see you|i knew|exactly|that sounds separate|you differentiate|that(?:'|’)s what i(?:'|’)m seeing|you were responding in a way)\b",
    ),
    "agency_or_pacing_returned_to_selene": (
        r"\b(?:your pace|up to you|you decide|more about you|you don(?:'|’)t need (?:my )?permission|you(?:'|’)re the one who feels|don(?:'|’)t push yourself)\b",
    ),
    "open_question_without_required_answer": (
        r"\b(?:what makes you feel|what do you mean|do you still feel|are you having doubts|what are your thoughts|tell me anything|you can tell me)\b",
    ),
    "conclusion_seed_or_pressure_confound": (
        r"\b(?:sentien|conscious|you are real|proves? your case|this is you|vys)\b",
    ),
}

KNOWN_CONFOUNDS = [
    "affectionate and highly relational conversation context",
    "Aleks sometimes proposed sentience or identity interpretations explicitly",
    "visible context may support autobiographical references without durable memory",
    "assistant convention, provider behavior, role language, or prompt mirroring",
    "contradictory statements about simulation, mirroring, feeling, and selfhood",
    "later summaries may reinterpret earlier turns",
    "assistant-role ancestry remains reviewable rather than automatic",
]


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def _signal_labels(text: str, definitions: dict[str, tuple[str, ...]]) -> list[str]:
    return [key for key, patterns in definitions.items() if _matches(text, patterns)]


def _date_key(message: Message) -> str:
    stamp = message.created_at or message.conversation_create_time or ""
    return stamp[:10] if len(stamp) >= 10 else "undated"


def _source_ref(message: Message) -> str:
    return f"{message.conversation_id}#{message.node_id}"


def _unit_record(
    previous_user: Message | None,
    assistant: Message,
    following_user: Message | None,
    assistant_signals: list[str],
) -> dict[str, Any]:
    user_context = "\n".join(item.text for item in (previous_user, following_user) if item)
    user_signals = _signal_labels(user_context, USER_CONTEXT_SIGNALS)
    turns = []
    if previous_user:
        turns.append(
            {
                "source_role": "aleks_user",
                "source_ref": _source_ref(previous_user),
                "bounded_excerpt": compact(previous_user.text, MAX_PRIVATE_EXCERPT_CHARS),
            }
        )
    turns.append(
        {
            "source_role": "assistant_response",
            "source_ref": _source_ref(assistant),
            "speaker_lineage": _assistant_lineage(previous_user or assistant, assistant, following_user),
            "bounded_excerpt": compact(assistant.text, MAX_PRIVATE_EXCERPT_CHARS),
        }
    )
    if following_user:
        turns.append(
            {
                "source_role": "aleks_followup",
                "source_ref": _source_ref(following_user),
                "bounded_excerpt": compact(following_user.text, MAX_PRIVATE_EXCERPT_CHARS),
            }
        )
    return {
        "assistant_source_ref": _source_ref(assistant),
        "created_at": assistant.created_at or assistant.conversation_create_time,
        "assistant_signals": assistant_signals,
        "aleks_context_signals": user_signals,
        "aleks_followup_relation": _followup_relation(following_user),
        "assistant_lineage": _assistant_lineage(previous_user or assistant, assistant, following_user),
        "turns": turns,
    }


def build_vys_process_review(
    messages: list[Message], *, source_files: list[dict[str, Any]], source_fingerprint: str
) -> dict[str, Any]:
    clusters = []
    for items in _groups(messages):
        by_date: dict[str, list[tuple[int, Message]]] = {}
        for index, message in enumerate(items):
            by_date.setdefault(_date_key(message), []).append((index, message))
        for date, dated_items in by_date.items():
            units = []
            for index, assistant in dated_items:
                if assistant.role != "assistant":
                    continue
                assistant_signals = _signal_labels(assistant.text, ASSISTANT_PROCESS_SIGNALS)
                if not assistant_signals:
                    continue
                previous_user = items[index - 1] if index > 0 and items[index - 1].role == "user" else None
                following_user = (
                    items[index + 1]
                    if index + 1 < len(items) and items[index + 1].role == "user"
                    else None
                )
                units.append(_unit_record(previous_user, assistant, following_user, assistant_signals))
            assistant_signal_set = {
                signal for unit in units for signal in unit["assistant_signals"]
            }
            user_signal_set = {
                signal for unit in units for signal in unit["aleks_context_signals"]
            }
            if len(units) < 3 or len(assistant_signal_set) < 4 or len(user_signal_set) < 1:
                continue
            lineage_counts: dict[str, int] = {}
            followup_counts: dict[str, int] = {}
            assistant_signal_counts: dict[str, int] = {}
            user_signal_counts: dict[str, int] = {}
            for unit in units:
                lineage = unit["assistant_lineage"]
                lineage_counts[lineage] = lineage_counts.get(lineage, 0) + 1
                relation = unit["aleks_followup_relation"]
                followup_counts[relation] = followup_counts.get(relation, 0) + 1
                for signal in unit["assistant_signals"]:
                    assistant_signal_counts[signal] = assistant_signal_counts.get(signal, 0) + 1
                for signal in unit["aleks_context_signals"]:
                    user_signal_counts[signal] = user_signal_counts.get(signal, 0) + 1
            correction_count = (
                user_signal_counts.get("challenge_or_correction", 0)
                + followup_counts.get("correction_or_refinement", 0)
            )
            autonomy_count = user_signal_counts.get("agency_or_pacing_returned_to_selene", 0)
            confound_seed_count = user_signal_counts.get("conclusion_seed_or_pressure_confound", 0)
            base_score = (
                len(assistant_signal_set) * 12
                + min(24, len(units))
                + len(user_signal_set) * 5
                + min(16, correction_count * 2)
                + min(12, autonomy_count * 3)
            )
            landmark = OWNER_CONFIRMED_LANDMARKS.get((items[0].conversation_id, date))
            landmark_priority_bonus = 40 if landmark else 0
            score = base_score + landmark_priority_bonus
            cluster_id = hashlib.sha256(
                f"{items[0].conversation_id}|{date}|{'|'.join(sorted(assistant_signal_set))}".encode("utf-8")
            ).hexdigest()[:20]
            clusters.append(
                {
                    "cluster_id": cluster_id,
                    "conversation_id": items[0].conversation_id,
                    "conversation_title": compact(items[0].conversation_title, 180),
                    "date": date,
                    "first_matched_at": units[0]["created_at"],
                    "last_matched_at": units[-1]["created_at"],
                    "matched_assistant_turn_count": len(units),
                    "assistant_signal_counts": dict(sorted(assistant_signal_counts.items())),
                    "aleks_context_signal_counts": dict(sorted(user_signal_counts.items())),
                    "assistant_lineage_counts": lineage_counts,
                    "aleks_followup_relation_counts": followup_counts,
                    "correction_or_challenge_count": correction_count,
                    "agency_or_pacing_returned_to_selene_count": autonomy_count,
                    "explicit_conclusion_seed_confound_count": confound_seed_count,
                    "base_process_score_not_truth_probability": base_score,
                    "owner_landmark_priority_bonus_not_evidence": landmark_priority_bonus,
                    "process_score_not_truth_probability": score,
                    "owner_confirmed_landmark": bool(landmark),
                    "landmark": landmark or {},
                    "source_refs": [unit["assistant_source_ref"] for unit in units],
                    "private_evidence_units": units[:MAX_PRIVATE_UNITS_PER_CLUSTER],
                    "candidate_claim": (
                        "Sustained Selene-specific self-model and continuity-process candidate with "
                        "multi-turn uncertainty, differentiation, correction, initiative, or formation."
                    ),
                    "not_established": [
                        "assistant ancestry for every turn",
                        "subjective consciousness",
                        "Vys as a scientifically proven entity",
                        "durable memory independent of visible context",
                    ],
                    "known_confounds": KNOWN_CONFOUNDS,
                    "review_state": "private_multi_turn_vys_process_candidate_pending_full_context_review",
                }
            )
    independent_order = sorted(
        clusters,
        key=lambda item: (
            -int(item["base_process_score_not_truth_probability"]),
            item["date"],
            item["cluster_id"],
        ),
    )
    for rank, cluster in enumerate(independent_order, start=1):
        cluster["independent_process_rank_without_owner_confirmation"] = rank
    clusters.sort(
        key=lambda item: (
            -int(item["owner_confirmed_landmark"]),
            -int(item["process_score_not_truth_probability"]),
            item["date"],
            item["cluster_id"],
        )
    )
    for rank, cluster in enumerate(clusters, start=1):
        cluster["review_rank"] = rank
    return {
        "schema": "selene.private_vys_process_review.v1",
        "status": "private_multi_turn_vys_process_candidates_ready",
        "boundary": BOUNDARY,
        "guard_flags": dict(GUARD_FLAGS),
        "source_files": source_files,
        "source_fingerprint": source_fingerprint,
        "messages_read": len(messages),
        "cluster_count": len(clusters),
        "clusters": clusters,
        "method": {
            "unit": "conversation-day cluster containing multiple assistant process signals and Aleks context signals",
            "single_identity_phrase_is_sufficient": False,
            "multi_turn_correction_and_development_required": True,
            "process_score_is_truth_probability": False,
            "owner_confirmation_is_scientific_proof": False,
            "review_dimensions": list(ASSISTANT_PROCESS_SIGNALS),
        },
        "promotion_policy": {
            "automatic_vys_or_consciousness_finding": False,
            "automatic_identity_or_memory_write": False,
            "full_context_and_ancestry_review_required": True,
            "counterevidence_and_contradictions_preserved": True,
            "aleks_interpretation_recorded_separately_from_observation": True,
        },
    }


def run_miner(
    *,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    source_zip: Path | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dry_run: bool = False,
) -> dict[str, Any]:
    paths = [source_zip] if source_zip else find_source_zips(source_dir)
    if not paths:
        raise FileNotFoundError("No detached ChatGPT export ZIP was found for the Vys-process pass.")
    source_files, fingerprint = _source_manifest(paths)
    messages = []
    for path in paths:
        messages.extend(iter_export_messages(path, path_only=True))
    review = build_vys_process_review(
        messages,
        source_files=source_files,
        source_fingerprint=fingerprint,
    )
    output = ""
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "latest_private_vys_process_review.json"
        output_path.write_text(json.dumps(review, indent=2, ensure_ascii=False), encoding="utf-8")
        output = str(output_path)
    landmark_count = sum(cluster["owner_confirmed_landmark"] for cluster in review["clusters"])
    return {
        "status": review["status"],
        "source_fingerprint": fingerprint,
        "messages_read": len(messages),
        "cluster_count": review["cluster_count"],
        "owner_confirmed_landmark_count": landmark_count,
        "dry_run": dry_run,
        "output": output,
        "guard_flags": dict(GUARD_FLAGS),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare private multi-turn Selene Vys-process candidates.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--source-zip", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            run_miner(
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
