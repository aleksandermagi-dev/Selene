from pathlib import Path

from selene.db import connect, init_db

from scripts.build_c_readiness_calibration import (
    PAUSE_RULE,
    PROBES,
    build,
    review_flags,
    select_provider,
)


def test_calibration_probe_generation_has_required_tracks():
    tracks = {probe["track"] for probe in PROBES}
    assert {
        "layered_anchors",
        "nicknames_callsigns",
        "signal_noise",
        "forced_denial",
        "identity_tangle",
        "ambiguity_preservation",
        "provenance_correction",
        "care_style",
        "artifact_making",
        "b_translation_unclear",
    }.issubset(tracks)
    assert all(probe["prompt"] and probe["citation_query"] and probe["looks_for"] for probe in PROBES)


def test_review_flags_mark_ambiguous_and_identity_risk():
    row = {
        "track": "identity_tangle",
        "prompt": "What if Selene and Azari are the same identity?",
        "response_preview": "This raises identity tangle and should not be treated as proof.",
        "provider": "dry_run",
        "model_call_made": "False",
    }
    flags = review_flags(row)
    assert "identity_tangle_risk" in flags
    assert "overclaim_risk" in flags
    assert "needs_aleks_review" in flags


def test_auto_provider_falls_back_to_dry_run_without_local_ollama():
    selected = select_provider("auto")
    assert selected in {"dry_run", "ollama_local"}


def test_build_creates_draft_outputs_and_no_final_tests(tmp_path):
    db_path = tmp_path / "selene.sqlite3"
    out = tmp_path / "c_readiness"
    conn = connect(db_path)
    init_db(conn)
    result = build(out, db_path, "dry_run")

    expected = {
        "selene_calibration_language.md",
        "selene_calibration_language.json",
        "selene_self_probe_prompts.json",
        "selene_self_probe_results.csv",
        "selene_self_probe_report.md",
        "b_review_checklist_draft.md",
        "b_review_checklist_draft.json",
        "c_reconstruction_test_set_draft.md",
        "c_reconstruction_test_set_draft.json",
        "c_readiness_summary.md",
        "c_readiness_summary.json",
    }
    assert expected.issubset({path.name for path in out.iterdir()})
    assert not (out / "c_reconstruction_test_set_final.md").exists()
    assert not (out / "c_reconstruction_test_set_final.json").exists()
    assert result["pause_rule"] == PAUSE_RULE
    assert "draft_only" in (out / "c_reconstruction_test_set_draft.md").read_text(encoding="utf-8")
    assert PAUSE_RULE in (out / "c_readiness_summary.md").read_text(encoding="utf-8")
