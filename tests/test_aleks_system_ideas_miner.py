from __future__ import annotations

import json
import zipfile

from scripts.aleks_system_ideas_miner import (
    build_backlog_split,
    build_report,
    iter_export_messages,
    run_backlog_split,
    run_miner,
)


def _conversation(conversation_id, title, create_time, messages):
    mapping = {}
    parent = None
    current = None
    for index, (role, text, created_at) in enumerate(messages, start=1):
        node_id = f"{conversation_id}_m{index}"
        mapping[node_id] = {
            "id": node_id,
            "parent": parent,
            "message": {
                "id": node_id,
                "author": {"role": role},
                "create_time": created_at,
                "content": {"content_type": "text", "parts": [text]},
            },
        }
        parent = node_id
        current = node_id
    return {
        "conversation_id": conversation_id,
        "id": conversation_id,
        "title": title,
        "create_time": create_time,
        "current_node": current,
        "mapping": mapping,
    }


def _make_zip(tmp_path):
    zip_path = tmp_path / "aleks_export.zip"
    conversations = [
        _conversation(
            "c1",
            "Reasoning kernel",
            1000,
            [
                (
                    "user",
                    "The system should start with observation before interpretation, build multiple hypotheses, challenge assumptions equally, and then decide when the evidence chain is good enough.",
                    1001,
                ),
                (
                    "assistant",
                    "That sounds like a reasoning architecture with candidate models and stopping rules.",
                    1002,
                ),
            ],
        ),
        _conversation(
            "c2",
            "Memory home",
            2000,
            [
                (
                    "user",
                    "Memory should be continuity and home, not a ledger. It needs source, consent, correction, and a way to ask before keeping something.",
                    2001,
                ),
                (
                    "assistant",
                    "That can become a source-bound memory system with review and correction.",
                    2002,
                ),
            ],
        ),
        _conversation(
            "c3",
            "Interface workbench",
            3000,
            [
                (
                    "user",
                    "The AI needs a workspace with tabs for research, memory, UI, planning, diagnostics, and safe action proposals.",
                    3001,
                )
            ],
        ),
        _conversation(
            "c4",
            "Tool noise",
            4000,
            [
                (
                    "tool",
                    "DALL-E displayed one image in the ChatGPT UI with an image button and visual generation workflow.",
                    4001,
                )
            ],
        ),
        _conversation(
            "c5",
            "Implemented intelligenceOS",
            5000,
            [
                (
                    "user",
                    "We implemented intelligenceOS from the same reasoning idea: observe first, build candidate models, challenge them equally, demonstrate the evidence chain, and evaluate when to stop.",
                    5001,
                ),
                (
                    "assistant",
                    "That names the earlier reasoning kernel as an implemented architecture.",
                    5002,
                ),
            ],
        ),
        _conversation(
            "c6",
            "Friendly greeting exchange",
            6000,
            [
                (
                    "user",
                    "Good morning hello lol I missed you.",
                    6001,
                ),
                (
                    "assistant",
                    "Good morning! I missed you too.",
                    6002,
                ),
            ],
        ),
        _conversation(
            "c7",
            "Assistant heavy",
            7000,
            [
                (
                    "user",
                    "Could an AI system have memory?",
                    7001,
                ),
                (
                    "assistant",
                    "A complete memory architecture would include modules, routing, source ledgers, consent checks, retrieval, diagnostics, and maintenance workflows. It would be implemented as a broad system with many layers and tools.",
                    7002,
                ),
                (
                    "assistant",
                    "The architecture could also include training safeguards, model boundaries, and interface dashboards.",
                    7003,
                ),
                (
                    "assistant",
                    "A prototype might include JSON schemas and database tables.",
                    7004,
                ),
                (
                    "assistant",
                    "This is mostly assistant-side expansion.",
                    7005,
                ),
            ],
        ),
    ]
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("conversations-000.json", json.dumps(conversations))
        archive.writestr("chat.html", "<html>ignored</html>")
        archive.writestr("image.png", b"ignored")
    return zip_path


def test_iter_export_messages_reads_conversation_json_without_extracting_media(tmp_path):
    zip_path = _make_zip(tmp_path)

    messages = iter_export_messages(zip_path)

    assert [message.role for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "tool",
        "user",
        "assistant",
        "user",
        "assistant",
        "user",
        "assistant",
        "assistant",
        "assistant",
        "assistant",
    ]
    assert messages[0].conversation_title == "Reasoning kernel"
    assert messages[0].created_at < messages[-1].created_at
    assert all("ignored" not in message.text for message in messages)


def test_build_report_detects_multiple_system_idea_categories(tmp_path):
    zip_path = _make_zip(tmp_path)
    messages = iter_export_messages(zip_path)

    report = build_report([zip_path])
    categories = {candidate["category"] for candidate in report["candidates"]}

    assert report["conversation_json_only"] is True
    assert report["messages_read"] == len(messages)
    assert "reasoning/intelligence" in categories
    assert "memory/continuity" in categories
    assert "UI/workspace" in categories
    assert all(candidate["speaker_counts"]["user"] >= 1 for candidate in report["candidates"])
    assert report["guard_flags"]["selene_memory_write"] is False
    assert report["guard_flags"]["selene_voice_write"] is False
    assert report["guard_flags"]["app_db_write"] is False
    assert report["version"] == "2.0"
    assert report["idea_families"]
    assert report["evolution_timeline"]
    assert report["top_dossiers"]["top_25_strongest_ideas"]
    assert report["miner_quality_notes"]
    assert report["curated_report"]["version"] == "3.0"
    assert report["curated_report"]["curated_count"] > 0


def test_candidates_separate_user_and_assistant_hits(tmp_path):
    zip_path = _make_zip(tmp_path)

    report = build_report([zip_path])
    reasoning = next(candidate for candidate in report["candidates"] if candidate["category"] == "reasoning/intelligence")

    assert reasoning["speaker_counts"]["user"] >= 1
    assert reasoning["speaker_counts"]["assistant"] >= 1
    assert reasoning["possible_project_fit"] in {"general AI system", "unclear/future"}
    assert reasoning["maturity"] in {"seed", "repeated pattern", "ready to prototype"}
    assert reasoning["bounded_excerpts"]
    assert "aleks_origin_score" in reasoning
    assert "implementation_readiness" in reasoning


def test_v2_groups_repeated_reasoning_into_family_and_timeline(tmp_path):
    zip_path = _make_zip(tmp_path)

    report = build_report([zip_path])
    artificial_cognition = next(family for family in report["idea_families"] if family["family"] == "artificial cognition")
    timeline_dates = [event["date"] for event in report["evolution_timeline"]]
    stages = {event["stage"] for event in report["evolution_timeline"]}

    assert artificial_cognition["candidate_count"] >= 2
    assert any(link["concept"] == "intelligenceOS" for link in artificial_cognition["current_concept_links"])
    assert timeline_dates == sorted(timeline_dates)
    assert "seed" in stages
    assert "implemented_architecture" in stages or "named_concept" in stages


def test_tool_and_assistant_only_noise_do_not_become_top_dossiers(tmp_path):
    zip_path = _make_zip(tmp_path)

    report = build_report([zip_path])
    all_top_titles = json.dumps(report["top_dossiers"], sort_keys=True)

    assert "Tool noise" not in all_top_titles
    assert all(item["speaker_counts"]["user"] >= 1 for item in report["candidates"])


def test_v3_curated_cards_filter_generic_chat_and_keep_high_signal_architecture(tmp_path):
    zip_path = _make_zip(tmp_path)

    report = build_report([zip_path])
    curated_json = json.dumps(report["curated_report"], sort_keys=True)

    assert "Friendly greeting exchange" not in curated_json
    assert "Reasoning kernel" in curated_json or "Implemented intelligenceOS" in curated_json
    assert report["curated_report"]["quality_metrics"]["review_confidence_counts"]["strong"] >= 1
    assert report["curated_report"]["guard_flags"]["selene_memory_write"] is False


def test_v3_penalizes_assistant_heavy_candidates(tmp_path):
    zip_path = _make_zip(tmp_path)

    report = build_report([zip_path])
    assistant_heavy = [
        candidate
        for candidate in report["candidates"]
        if candidate["title"].endswith("Assistant heavy")
    ]

    assert assistant_heavy
    assert any("assistant_heavy" in candidate["penalty_reasons"] for candidate in assistant_heavy)
    assert "assistant_heavy" in report["curated_report"]["excluded_reason_counts"] or report["curated_report"]["quality_metrics"]["assistant_heavy_excluded"] >= 0


def test_dry_run_does_not_write_outputs(tmp_path):
    zip_path = _make_zip(tmp_path)
    output_dir = tmp_path / "local-data" / "aleks_idea_miner"

    report = run_miner(source_zip=zip_path, output_dir=output_dir, dry_run=True)

    assert report["dry_run"] is True
    assert report["outputs"] == {}
    assert not output_dir.exists()


def test_non_dry_run_writes_only_requested_local_output_dir(tmp_path):
    zip_path = _make_zip(tmp_path)
    output_dir = tmp_path / "local-data" / "aleks_idea_miner"

    report = run_miner(source_zip=zip_path, output_dir=output_dir, dry_run=False)

    assert report["outputs"]["latest_json"].endswith("latest.json")
    assert (output_dir / "latest.json").exists()
    assert (output_dir / "latest.md").exists()
    assert (output_dir / "latest_v2.json").exists()
    assert (output_dir / "latest_v2.md").exists()
    assert (output_dir / "latest_curated.json").exists()
    assert (output_dir / "latest_curated.md").exists()
    assert json.loads((output_dir / "latest.json").read_text(encoding="utf-8"))["status"] == "aleks_system_ideas_miner_complete"
    assert json.loads((output_dir / "latest_v2.json").read_text(encoding="utf-8"))["version"] == "2.0"
    assert json.loads((output_dir / "latest_curated.json").read_text(encoding="utf-8"))["version"] == "3.0"


def test_backlog_split_routes_selene_azari_project_abc_and_future_cards():
    curated = {
        "status": "aleks_system_ideas_curated_complete",
        "curated_count": 4,
        "sections": {
            "selene_relevant_ideas": [
                {
                    "id": "selene-card",
                    "title": "Selene memory organ",
                    "idea_family": "continuity/memory",
                    "likely_implementation_target": "Selene",
                    "implementation_direction": "Review as source-bound memory architecture.",
                    "why_it_matters": "connects to Selene memory organ",
                    "ancestry_tags": [],
                    "current_concept_links": [{"concept": "Selene"}],
                    "implementation_readiness": "ready_to_prototype",
                    "review_confidence": "strong",
                    "curated_score": 75,
                    "risks": ["local idea-mining output only"],
                    "user_first_excerpts": [{"source_ref": "c1#m1", "excerpt": "Selene needs a memory organ with source and consent."}],
                }
            ],
            "azari_relevant_ideas": [
                {
                    "id": "azari-card",
                    "title": "Lumen Munsell workbench",
                    "idea_family": "perception/art",
                    "likely_implementation_target": "Azari",
                    "implementation_direction": "Review as Munsell or visual reasoning material.",
                    "why_it_matters": "connects to Azari",
                    "ancestry_tags": [],
                    "current_concept_links": [{"concept": "Azari"}],
                    "implementation_readiness": "implemented_or_partly_implemented",
                    "review_confidence": "useful lead",
                    "curated_score": 60,
                    "risks": ["local idea-mining output only"],
                    "user_first_excerpts": [{"source_ref": "c2#m1", "excerpt": "Lumen needs Munsell perception later."}],
                }
            ],
            "project_abc_ideas": [
                {
                    "id": "abc-card",
                    "title": "Portable transfer body",
                    "idea_family": "AI embodiment",
                    "likely_implementation_target": "Project ABC",
                    "implementation_direction": "Review as portability architecture.",
                    "why_it_matters": "connects to Project ABC",
                    "ancestry_tags": [],
                    "current_concept_links": [{"concept": "Project ABC"}],
                    "implementation_readiness": "ready_to_prototype",
                    "review_confidence": "strong",
                    "curated_score": 80,
                    "risks": ["local idea-mining output only"],
                    "user_first_excerpts": [{"source_ref": "c3#m1", "excerpt": "Project ABC needs portable body transfer rules."}],
                }
            ],
            "future_systems": [
                {
                    "id": "future-card",
                    "title": "General research mesh",
                    "idea_family": "research/library",
                    "likely_implementation_target": "general AI system",
                    "implementation_direction": "Review as general research architecture.",
                    "why_it_matters": "contains reusable AI-system design signal",
                    "ancestry_tags": [],
                    "current_concept_links": [],
                    "implementation_readiness": "future_research",
                    "review_confidence": "weak lead",
                    "curated_score": 12,
                    "risks": ["local idea-mining output only"],
                    "user_first_excerpts": [{"source_ref": "c4#m1", "excerpt": "A future system could compare sources."}],
                }
            ],
        },
    }

    split = build_backlog_split(curated)

    assert [card["source_curated_card_id"] for card in split["tracks"]["selene_intake"]] == ["selene-card"]
    assert [card["source_curated_card_id"] for card in split["tracks"]["azari_future"]] == ["azari-card"]
    assert [card["source_curated_card_id"] for card in split["tracks"]["project_abc"]] == ["abc-card"]
    assert [card["source_curated_card_id"] for card in split["tracks"]["future_system"]] == ["future-card"]
    assert split["tracks"]["selene_intake"][0]["readiness"] == "use_now"
    assert split["tracks"]["future_system"][0]["readiness"] != "use_now"
    assert split["guard_flags"]["selene_memory_write"] is False
    assert split["guard_flags"]["model_training_or_lora"] is False


def test_backlog_split_copies_azari_line_cards_without_mixing_into_selene_by_default():
    curated = {
        "status": "aleks_system_ideas_curated_complete",
        "curated_count": 2,
        "sections": {
            "azari_relevant_ideas": [
                {
                    "id": "lumen-only",
                    "title": "Lumen Munsell routing",
                    "idea_family": "perception/art",
                    "likely_implementation_target": "Azari",
                    "implementation_direction": "Review as visual reasoning material.",
                    "why_it_matters": "connects to Azari",
                    "ancestry_tags": [],
                    "current_concept_links": [{"concept": "Azari"}],
                    "implementation_readiness": "architecture_seed",
                    "review_confidence": "useful lead",
                    "curated_score": 45,
                    "risks": ["local idea-mining output only"],
                    "user_first_excerpts": [{"source_ref": "c1#m1", "excerpt": "Lumen needs Munsell routing."}],
                },
                {
                    "id": "lumen-selene",
                    "title": "Lumen to Selene memory organ adaptation",
                    "idea_family": "continuity/memory",
                    "likely_implementation_target": "Azari",
                    "implementation_direction": "Review as memory organ material.",
                    "why_it_matters": "connects to Azari and Selene",
                    "ancestry_tags": [],
                    "current_concept_links": [{"concept": "Azari"}, {"concept": "Selene"}],
                    "implementation_readiness": "ready_to_prototype",
                    "review_confidence": "strong",
                    "curated_score": 70,
                    "risks": ["local idea-mining output only"],
                    "user_first_excerpts": [{"source_ref": "c2#m1", "excerpt": "Selene can adapt this memory organ idea later."}],
                },
            ]
        },
    }

    split = build_backlog_split(curated)

    assert [card["source_curated_card_id"] for card in split["tracks"]["azari_future"]] == ["lumen-selene", "lumen-only"]
    assert [card["source_curated_card_id"] for card in split["tracks"]["selene_intake"]] == ["lumen-selene"]


def test_backlog_split_dry_run_writes_nothing_and_non_dry_run_writes_backlog_files(tmp_path):
    curated_path = tmp_path / "latest_curated.json"
    output_dir = tmp_path / "local-data" / "aleks_idea_miner" / "backlog"
    curated_path.write_text(
        json.dumps(
            {
                "status": "aleks_system_ideas_curated_complete",
                "curated_count": 1,
                "sections": {
                    "selene_relevant_ideas": [
                        {
                            "id": "selene-card",
                            "title": "Selene diagnostics workbench",
                            "idea_family": "diagnostics/maintenance",
                            "likely_implementation_target": "Selene",
                            "implementation_direction": "Review as diagnostics material.",
                            "why_it_matters": "connects to Selene diagnostics",
                            "ancestry_tags": [],
                            "current_concept_links": [{"concept": "Selene"}],
                            "implementation_readiness": "architecture_seed",
                            "review_confidence": "useful lead",
                            "curated_score": 50,
                            "risks": ["local idea-mining output only"],
                            "user_first_excerpts": [{"source_ref": "c1#m1", "excerpt": "Selene needs diagnostics."}],
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    dry = run_backlog_split(curated_json=curated_path, output_dir=output_dir, dry_run=True)

    assert dry["dry_run"] is True
    assert dry["outputs"] == {}
    assert not output_dir.exists()

    written = run_backlog_split(curated_json=curated_path, output_dir=output_dir, dry_run=False)

    assert (output_dir / "latest_selene_intake.json").exists()
    assert (output_dir / "latest_selene_intake.md").exists()
    assert (output_dir / "latest_azari_future.json").exists()
    assert (output_dir / "latest_project_abc.json").exists()
    assert (output_dir / "latest_future_system.json").exists()
    assert written["outputs"]["selene_intake_json"].endswith("latest_selene_intake.json")
    assert json.loads((output_dir / "latest_selene_intake.json").read_text(encoding="utf-8"))["track"] == "selene_intake"
