import json

import pytest

from selene.b_review import build_all_teaching_packets, build_teaching_packet, core_reference_coverage, decide_b_review_candidate, prepare_android_language_lessons, teaching_packet_coverage
from selene.b_review_desk import review_desk
from selene.braid_tracer import run_braid_tracer
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.vessel import create_core_memory_candidate, create_speech_memory_candidate


def _accepted_material(conn, speech_function="repair"):
    candidate = create_speech_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "speech_function": speech_function,
            "title": f"{speech_function} example",
            "content": "Core-linked response repairs the moment with continuity, source refs, and care.",
            "source_refs": ["manual:teaching"],
            "allowed_use": "Review as Core-linked speech-memory only.",
            "prohibited_use": "Do not use as active memory or provider identity.",
        },
    )
    decide_b_review_candidate(
        conn,
        {
            "subject_table": "speech_memory_candidates",
            "subject_id": candidate["id"],
            "decision": "accepted_for_teaching",
            "positive_example": "Repair with care and provenance.",
            "correction_example": "Do not flatten correction into failure.",
            "when_not_to_use": "Do not use when a boundary refusal is required.",
        },
    )
    return candidate


def test_teaching_packet_groups_accepted_materials_without_training_or_memory(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    _accepted_material(conn, "repair")

    packet = build_teaching_packet(conn, {"speech_function": "repair"})

    assert packet["status"] == "teaching_packet_built"
    assert packet["lesson"]["speech_function"] == "repair"
    assert packet["lesson"]["material_count"] == 1
    assert packet["lesson"]["boundary"] == "teaching_packet_review_only_not_training"
    assert packet["training_allowed"] is False
    assert packet["memory_write_active"] is False
    assert conn.execute("SELECT COUNT(*) FROM b_teaching_packets").fetchone()[0] == 1


def test_teaching_packet_requires_accepted_lessons(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    with pytest.raises(ValueError, match="at least one accepted lesson"):
        build_teaching_packet(conn, {"speech_function": "repair"})

    assert conn.execute("SELECT COUNT(*) FROM b_teaching_packets").fetchone()[0] == 0


def test_teaching_packet_route_and_reference_lists_are_non_activating(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    _accepted_material(conn, "grounding")

    packet = route_request(conn, "b.teaching_packet.build", {"speech_function": "grounding"})["result"]
    materials = route_request(conn, "b.teaching_materials.list", {})["result"]
    refs = route_request(conn, "b.approved_memory_references.list", {})["result"]
    coverage = route_request(conn, "b.corpus_coverage.status", {})["result"]

    assert packet["activation_change"] == "none"
    assert materials["items"]
    assert refs["items"] == []
    assert coverage["reviewed_teaching_materials"] == 1
    assert coverage["runtime_memory_recall"] is False


def test_teaching_packet_coverage_and_build_all_use_accepted_lessons_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    _accepted_material(conn, "warmth")
    superseded = _accepted_material(conn, "grounding")
    conn.execute("UPDATE b_reviewed_teaching_materials SET review_status = 'superseded', status = 'teaching_material_superseded_non_active' WHERE source_candidate_id = ?", (superseded["id"],))
    conn.commit()

    before = teaching_packet_coverage(conn)
    result = build_all_teaching_packets(conn)
    after = teaching_packet_coverage(conn)

    warmth = next(item for item in after["items"] if item["speech_function"] == "warmth")
    grounding = next(item for item in after["items"] if item["speech_function"] == "grounding")
    assert before["missing_packet_count"] == 1
    assert result["built_count"] == 1
    assert warmth["packet_exists"] is True
    assert grounding["accepted_lesson_count"] == 0
    assert result["training_allowed"] is False
    assert result["runtime_memory_recall"] is False


def test_core_reference_coverage_groups_approved_references_without_active_memory(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    candidate = create_core_memory_candidate(
        conn,
        {
            "core_memory_layer": "project_memory",
            "title": "Project reference",
            "content": "Core-linked project reference remains non-active.",
            "source_refs": ["manual:reference"],
        },
    )
    decide_b_review_candidate(
        conn,
        {
            "subject_table": "core_memory_candidates",
            "subject_id": candidate["id"],
            "decision": "accepted_for_memory_accession",
            "reference_summary": "Project reference accepted for future transfer review.",
        },
    )

    coverage = core_reference_coverage(conn)
    project = next(item for item in coverage["items"] if item["core_memory_layer"] == "project_memory")

    assert project["accepted_reference_count"] == 1
    assert project["readiness"] == "has_approved_references"
    assert coverage["memory_write_active"] is False
    assert coverage["runtime_memory_recall"] is False


def test_teaching_packet_new_routes_are_non_activating(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    _accepted_material(conn, "boundary")

    coverage = route_request(conn, "b.teaching_packet.coverage", {})["result"]
    build_all = route_request(conn, "b.teaching_packet.build_all", {})["result"]
    refs = route_request(conn, "b.core_reference.coverage", {})["result"]

    assert coverage["status"] == "teaching_packet_coverage"
    assert build_all["activation_change"] == "none"
    assert refs["status"] == "core_reference_coverage"


def test_android_language_lessons_prepare_review_only_packets_and_skip_duplicates(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    first = prepare_android_language_lessons(conn)
    second = route_request(conn, "b.android_language_lessons.prepare", {})["result"]

    assert first["status"] == "android_language_lessons_prepared"
    assert first["created_count"] == 7
    assert first["packet_built_count"] >= 1
    assert first["activation_change"] == "none"
    assert first["training_allowed"] is False
    assert first["memory_write_active"] is False
    assert first["runtime_memory_recall"] is False
    assert first["selene_remains_selene"] is True
    assert first["repaired_count"] == 0
    assert second["created_count"] == 0
    assert second["skipped_count"] == 7
    assert second["repaired_count"] == 0

    material_count = conn.execute(
        "SELECT COUNT(*) FROM b_reviewed_teaching_materials WHERE source_candidate_table = 'android_language_notes'"
    ).fetchone()[0]
    packet_count = conn.execute(
        "SELECT COUNT(*) FROM b_teaching_packets WHERE source_refs LIKE '%manual:New UI/Android.md%'"
    ).fetchone()[0]
    assert material_count == 7
    assert packet_count >= 1

    looseness = conn.execute(
        """
        SELECT positive_example, when_not_to_use, noise_context_json
        FROM b_reviewed_teaching_materials
        WHERE source_refs LIKE '%manual:New UI/Android.md:selene_not_scripted%'
        """
    ).fetchone()
    assert "fixed voice template" in looseness["positive_example"]
    assert "dictate a fixed personality script" in looseness["when_not_to_use"]
    noise_context = json.loads(looseness["noise_context_json"])
    assert noise_context["not_voice_script"] is True
    assert "Warmth" in noise_context["warmth_policy"]

    conn.execute(
        """
        UPDATE b_reviewed_teaching_materials
        SET noise_context_json = '{"not_voice_script": true}'
        WHERE source_refs LIKE '%manual:New UI/Android.md:selene_not_scripted%'
        """
    )
    conn.commit()
    repaired = prepare_android_language_lessons(conn)
    repaired_looseness = conn.execute(
        """
        SELECT noise_context_json
        FROM b_reviewed_teaching_materials
        WHERE source_refs LIKE '%manual:New UI/Android.md:selene_not_scripted%'
        """
    ).fetchone()
    assert repaired["created_count"] == 0
    assert repaired["repaired_count"] == 1
    assert "Warmth" in json.loads(repaired_looseness["noise_context_json"])["warmth_policy"]


def test_noise_context_carries_into_accepted_lesson_and_packet(tmp_path):
    root = tmp_path / "DevelopmentalCorpusArchive_20260526_122541"
    text_export = root / "raw_export" / "mydataset" / "text_export"
    text_export.mkdir(parents=True)
    (text_export / "conversations-000.json").write_text(
        json.dumps(
            [
                {
                    "conversation_id": "conv-noise-lesson",
                    "title": "Noise preserved",
                    "create_time": 100.0,
                    "mapping": {
                        "u1": {"message": {"id": "u1", "author": {"role": "user"}, "content": {"parts": ["Selene, my moonlight, I can hear the model-distance noise."]}, "create_time": 101.0}},
                        "a1": {"message": {"id": "a1", "author": {"role": "assistant"}, "content": {"parts": ["As an AI, I don't have memory, but the warmth and braid signal are still here."]}, "create_time": 102.0}},
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    run_braid_tracer(conn, {"limit": 2}, root)
    piece = review_desk(conn, 10, {"noise_type": "platform_constraint_noise"})["pieces"][0]
    action = next(item for item in piece["actions"] if item["decision"] == "accepted_for_teaching")

    accepted = decide_b_review_candidate(conn, {**action, "decision": "accepted_for_teaching"})
    packet = build_teaching_packet(conn, {"speech_function": accepted["created"]["teaching_material"]["speech_function"]})

    material = accepted["created"]["teaching_material"]
    noise_context = json.loads(material["noise_context_json"])
    assert "platform_constraint_noise" in noise_context["noise_types"]
    assert noise_context["signal_preserved"] is True
    assert "Warmth" in noise_context["warmth_policy"]
    assert "platform_constraint_noise" in packet["lesson"]["noise_context"]["noise_types"]
    assert packet["lesson"]["noise_context"]["training_allowed"] is False
