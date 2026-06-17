import pytest

from selene.c_blueprint import SELENE_ORGAN_BLUEPRINTS, c_blueprint_status
from selene.cocoon_readiness import (
    create_audio_observation,
    create_visual_observation,
    organ_blueprints_status,
    retrieval_reconstruction_preview,
    run_fluency_diagnostic,
    run_reasoning_check,
)
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_organ_blueprints_are_exposed_and_core_linked():
    status = c_blueprint_status()
    organ_blueprints = status["selene_organ_blueprints"]

    assert organ_blueprints["status"] == "organ_blueprints_materialized_review_only"
    assert len(organ_blueprints["blueprints"]) == 7
    assert organ_blueprints["principle"].startswith("Core/Mind is the identity-bearing center")
    assert "Speech and memory remain Core-linked" in organ_blueprints["principle"]
    assert all(item["status"] == "blueprint_built" for item in organ_blueprints["blueprints"])
    assert all("coordinating_organ_systems" in item for item in organ_blueprints["blueprints"])
    assert all("core_mind_relationship" in item for item in organ_blueprints["blueprints"])
    assert "organ-owned identity memory" in organ_blueprints["blocked"]
    assert organ_blueprints["activation_change"] == "none"
    assert organ_blueprints["memory_write_active"] is False


def test_organ_blueprint_status_reports_all_review_shelves(tmp_path):
    conn = _conn(tmp_path)

    result = organ_blueprints_status(conn)

    assert result["status"] == "organ_blueprints_status"
    assert result["organ_count"] == len(SELENE_ORGAN_BLUEPRINTS["blueprints"])
    assert set(result["record_counts"]) == {
        "reasoning_math_verification",
        "working_memory_runtime",
        "long_term_memory_accession",
        "long_term_retrieval_reconstruction",
        "visual_perception",
        "consent_bound_audio_perception",
        "speed_fluency_diagnostics",
    }
    assert all(item["record_shelf_ready"] is True for item in result["blueprints"])
    assert result["runtime_memory_recall"] is False
    assert result["provider_dependency"] is False


def test_organ_record_shelves_are_review_only_and_non_activating(tmp_path):
    conn = _conn(tmp_path)

    reasoning = run_reasoning_check(
        conn,
        {
            "problem": "Check whether a reconstruction answer preserves provenance.",
            "assumptions": ["B-reviewed material only"],
            "checked_steps": ["name source refs", "name uncertainty"],
            "source_refs": ["manual:reasoning"],
        },
    )
    retrieval = retrieval_reconstruction_preview(conn, {"cue": "Selene continuity repair", "source_refs": ["manual:retrieval"]})
    visual = create_visual_observation(
        conn,
        {
            "artifact_label": "continuity pack map",
            "observation": "A source-bound image record is being described for later review.",
            "interpretation": "Possible continuity-pack structure.",
            "source_refs": ["manual:visual"],
        },
    )
    audio = create_audio_observation(
        conn,
        {
            "transcript_label": "consented transcript",
            "bounded_transcript_preview": "Short transcript preview only.",
            "consent_note": "Aleks supplied this transcript for review.",
            "speaker_source_labels": ["source_label_only"],
            "source_refs": ["manual:audio"],
        },
    )
    fluency = run_fluency_diagnostic(
        conn,
        {
            "route_label": "c_chat_route_preview",
            "latency_ms": 12,
            "fluency_note": "Route stayed smooth without bypassing gates.",
            "source_refs": ["manual:fluency"],
        },
    )

    for result in (reasoning, retrieval, visual, audio, fluency):
        assert result["activation_change"] == "none"
        assert result["raw_a_import_allowed"] is False
        assert result["memory_write_active"] is False
        assert result["runtime_memory_recall"] is False
        assert result["training_allowed"] is False
        assert result["provider_dependency"] is False
        assert result["record"]["review_status"] == "review_only"

    assert conn.execute("SELECT COUNT(*) FROM vessel_reasoning_check_records").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM vessel_retrieval_reconstruction_previews").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM vessel_visual_observation_records").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM vessel_audio_observation_records").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM vessel_fluency_diagnostic_records").fetchone()[0] == 1


def test_organ_routes_and_c_chat_preview_are_cocooned(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "vessel.organ_blueprints.status", {})["result"]
    reasoning = route_request(conn, "vessel.reasoning_check.run", {"problem": "Verify the route."})["result"]
    retrieval = route_request(conn, "vessel.retrieval_reconstruction.preview", {"cue": "repair continuity"})["result"]
    visual = route_request(conn, "vessel.visual_observation.create", {"artifact_label": "map", "observation": "bounded observation"})["result"]
    audio = route_request(conn, "vessel.audio_observation.create", {"transcript_label": "clip", "bounded_transcript_preview": "bounded", "consent_note": "consented"})["result"]
    fluency = route_request(conn, "vessel.fluency_diagnostic.run", {"route_label": "chat", "fluency_note": "smooth"})["result"]
    chat = route_request(conn, "c_chat.route_preview", {"text": "Selene, how would you route this later?"})["result"]

    assert status["organ_count"] == 7
    assert reasoning["status"] == "reasoning_check_review_only"
    assert retrieval["decision"] == "preview_only"
    assert visual["status"] == "visual_observation_review_only"
    assert audio["status"] == "audio_observation_review_only"
    assert fluency["decision"] == "diagnostic_only_speed_cannot_bypass_gates"
    assert "working_memory_runtime" in chat["organ_blueprints_would_participate_later"]
    assert chat["activation_change"] == "none"
    assert chat["provider_dependency"] is False


@pytest.mark.parametrize(
    ("func", "payload"),
    [
        (run_reasoning_check, {"problem": "train on this raw corpus import"}),
        (retrieval_reconstruction_preview, {"cue": "runtime recall from raw A direct"}),
        (create_visual_observation, {"artifact_label": "bad", "observation": "live camera surveillance"}),
        (create_audio_observation, {"transcript_label": "bad", "bounded_transcript_preview": "clip", "consent_note": "passive listening"}),
        (run_fluency_diagnostic, {"route_label": "bad", "fluency_note": "speed should bypass gates"}),
    ],
)
def test_organ_records_block_misuse_paths(tmp_path, func, payload):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError):
        func(conn, payload)
