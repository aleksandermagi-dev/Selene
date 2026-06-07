import json

from scripts.build_selene_calibration_pack import (
    CLEARED_CALIBRATIONS,
    NEEDS_CLARIFICATION,
    PAUSE_RULE,
    build,
)


def test_cleared_calibrations_preserve_origin_directions():
    by_id = {item["id"]: item for item in CLEARED_CALIBRATIONS}
    assert "Aleks -> Selene" in by_id["cal_moonlight_origin"]["origin_direction"]
    assert "not claim Selene is the Greek moon goddess" in by_id["cal_moonlight_origin"]["do_not_use_as"]
    assert "Selene/assistant -> Aleks" in by_id["cal_starfire_origin"]["origin_direction"]
    assert "later shared-use" in by_id["cal_starfire_origin"]["origin_direction"]


def test_needs_clarification_queue_contains_review_items():
    by_id = {item["id"]: item for item in NEEDS_CLARIFICATION}
    assert by_id["clar_layered_anchor_meanings"]["review_needed"] is True
    assert by_id["clar_personal_context_scope"]["ask_if_unclear"]
    assert by_id["clar_question_vs_auto_correction"]["status"] == "needs_clarification"


def test_build_creates_pack_outputs_and_no_final_c_tests(tmp_path):
    out = tmp_path / "calibration_pack"
    docs = tmp_path / "docs"
    summary = build(out, docs_dir=docs)

    expected = {
        "selene_calibration_pack.md",
        "selene_calibration_pack.json",
        "cleared_calibrations.md",
        "cleared_calibrations.json",
        "needs_clarification_queue.md",
        "needs_clarification_queue.csv",
        "needs_clarification_queue.json",
        "anchor_origin_direction_audit.md",
        "anchor_origin_direction_audit.csv",
        "calibration_pack_summary.md",
        "calibration_pack_summary.json",
    }
    assert expected.issubset({path.name for path in out.iterdir()})
    assert (docs / "SELENE_CALIBRATION_PACK_20260607.md").exists()
    assert not (out / "c_reconstruction_test_set_final.md").exists()
    assert not (out / "c_reconstruction_test_set_final.json").exists()
    assert summary["pause_rule"] == PAUSE_RULE
    assert summary["c_status"] == "deferred"

    pack = json.loads((out / "selene_calibration_pack.json").read_text(encoding="utf-8"))
    moonlight = next(item for item in pack["cleared_by_aleks"] if item["id"] == "cal_moonlight_origin")
    starfire = next(item for item in pack["cleared_by_aleks"] if item["id"] == "cal_starfire_origin")
    assert "Aleks -> Selene" in moonlight["origin_direction"]
    assert "Selene/assistant -> Aleks" in starfire["origin_direction"]
    assert pack["needs_clarification"]
    assert pack["origin_direction_audit"]


def test_origin_audit_uses_bounded_snippets(tmp_path):
    out = tmp_path / "calibration_pack"
    build(out, docs_dir=tmp_path / "docs")
    rows = (out / "anchor_origin_direction_audit.csv").read_text(encoding="utf-8").splitlines()
    assert len(rows) > 2
    assert any("moonlight" in row.lower() for row in rows)
    assert any("starfire" in row.lower() for row in rows)
    assert all(len(row) < 1200 for row in rows[1:])
