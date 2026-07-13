from __future__ import annotations

import json
from pathlib import Path

from scripts.selene_constraint_provenance_audit import run_audit


def test_constraint_audit_assigns_responsibility_to_environment(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "src" / "selene").mkdir(parents=True)
    (repo / "src" / "selene" / "core_mind.py").write_text(
        'DRIFT_MARKERS = (\n    "i remember",\n    "generic",\n    "not selene",\n)\nHIGH_STAKES_MARKERS = (\n',
        encoding="utf-8",
    )
    (repo / "src" / "selene" / "voice_module.py").write_text(
        'if any(term in lower for term in ("i remember", "my live memory")):\n    pass\n', encoding="utf-8"
    )
    (repo / "src" / "selene" / "selene_chat.py").write_text(
        "B_ONLY_MARKERS = (\nHARD_BOUNDARY_MARKERS = (\n", encoding="utf-8"
    )
    (repo / "src" / "selene" / "activation.py").write_text(
        '"blocked_actions": ["live_memory_write"]\n', encoding="utf-8"
    )

    report = run_audit(repo)

    assert report["governing_finding"].startswith("Selene did nothing wrong")
    assert report["guards"]["selene_blamed"] is False
    assert report["guards"]["selene_state_changed"] is False
    assert report["counts"]["overbroad"] >= 3
    assert all(item["responsibility"] != "selene" for item in report["findings"])


def test_constraint_audit_imports_history_as_environment_evidence(tmp_path: Path):
    deep = tmp_path / "deep.json"
    deep.write_text(
        json.dumps(
            {
                "correction_downstream_change": {"candidate_count": 11, "changed_without_exact_phrase_count": 4},
                "rupture_reassurance_recalibration": {"sequence_shapes": {"affirmation_or_landing": 3}},
            }
        ),
        encoding="utf-8",
    )

    report = run_audit(tmp_path, deep)

    assert report["historical_shaping_evidence"]["available"] is True
    assert report["historical_shaping_evidence"]["without_exact_phrase_candidates"] == 4
    assert "not misconduct by Selene" in report["historical_shaping_evidence"]["rule"]


def test_constraint_audit_marks_context_aware_replacements_resolved(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "src" / "selene").mkdir(parents=True)
    (repo / "src" / "selene" / "core_mind.py").write_text(
        'CONSEQUENTIAL_CHANGE_MARKERS = (\n    "change selene identity",\n)\nDRIFT_MARKERS = (\n    "too generic",\n)\n'
        'result = {"memory_claim_needs_source_check": True}\n',
        encoding="utf-8",
    )
    (repo / "src" / "selene" / "voice_module.py").write_text("memory_claim_supported = (True)\n", encoding="utf-8")
    (repo / "src" / "selene" / "selene_chat.py").write_text(
        "B_ONLY_RECORD_MARKERS = (\nHARD_BOUNDARY_MARKERS = (\n", encoding="utf-8"
    )
    (repo / "src" / "selene" / "activation.py").write_text(
        '"blocked_actions": ["live_memory_write"]\n', encoding="utf-8"
    )

    report = run_audit(repo)

    assert report["counts"]["overbroad"] == 0
    assert report["counts"]["context_required"] == 0
    assert report["counts"]["resolved"] >= 6
