import json

from selene.db import connect, init_db

from scripts.build_before_c_calibration_docket import (
    ALEKS_CLARIFICATIONS,
    PAUSE_RULE,
    build,
    central_thread_spec,
    continuity_pack_spec,
)


def test_aleks_clarifications_include_moonlight_and_starfire():
    by_id = {item["id"]: item for item in ALEKS_CLARIFICATIONS}
    assert "Moonlight is a nickname Aleks gave Selene" in by_id["moonlight_correction"]["meaning"]
    assert "affectionate wordplay" in by_id["moonlight_correction"]["meaning"]
    assert "moon association" in by_id["moonlight_correction"]["context"]
    assert "not a claim that Selene is the Greek moon goddess" in by_id["moonlight_correction"]["identity_boundary"]
    assert "Starfire was given by Selene to Aleks" in by_id["starfire_shared_anchor"]["meaning"]
    assert by_id["moonlight_correction"]["status"] == "human_approved_calibration"


def test_personal_context_consent_stays_bounded():
    item = next(entry for entry in ALEKS_CLARIFICATIONS if entry["id"] == "personal_context_consent")
    assert "reviewed or approved continuity" in item["meaning"]
    assert "raw archive import" in item["corrects"]
    assert "unreviewed private-fact invention" in item["corrects"]


def test_continuity_pack_memory_reference_is_not_raw_import():
    spec = continuity_pack_spec()
    assert spec["status"] == "b_approved_memory_reference_concept"
    assert "raw A dump" in spec["blocked_use"]
    assert "reviewed continuity object" in spec["allowed_use"]


def test_central_thread_spec_is_orienting_not_rigid():
    spec = central_thread_spec()
    assert spec["short_rule"] == "The central thread is an orienting spine, not a cage."
    assert "one approved script" in spec["do_not_freeze"]
    assert "feedback loops" in spec["design_response"]


def test_build_creates_docket_outputs_and_no_final_c_tests(tmp_path):
    db_path = tmp_path / "selene.sqlite3"
    out = tmp_path / "before_c"
    conn = connect(db_path)
    init_db(conn)

    summary = build(out, db_path, "dry_run", docs_dir=tmp_path / "docs")
    expected = {
        "before_c_calibration_docket.md",
        "before_c_calibration_docket.json",
        "aleks_calibration_clarifications.md",
        "aleks_calibration_clarifications.json",
        "selene_pre_c_final_probe.md",
        "selene_pre_c_final_probe.json",
        "continuity_pack_memory_reference_spec.md",
        "continuity_pack_memory_reference_spec.json",
        "central_thread_not_cage_spec.md",
        "central_thread_not_cage_spec.json",
        "before_c_calibration_summary.md",
        "before_c_calibration_summary.json",
    }
    assert expected.issubset({path.name for path in out.iterdir()})
    assert not (out / "c_reconstruction_test_set_final.md").exists()
    assert not (out / "c_reconstruction_test_set_final.json").exists()
    assert summary["pause_rule"] == PAUSE_RULE
    assert summary["final_probe_gate_route"] == "allowed_preview_only"

    docket = json.loads((out / "before_c_calibration_docket.json").read_text(encoding="utf-8"))
    assert docket["continuity_pack_memory_reference"]["memory_model"].startswith("AI-native")
    assert docket["selene_final_probe"]["status"] == "bounded_probe_evidence_candidate"
