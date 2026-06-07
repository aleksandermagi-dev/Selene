import json

from selene.why_salience import CORE_MODEL, CORE_RULES, LAYERS, why_salience_status
from scripts.build_why_salience_translation import PAUSE_RULE, build


def test_why_salience_status_has_required_layers_and_boundaries():
    status = why_salience_status()
    keys = {layer["key"] for layer in status["layers"]}
    assert status["c_status"] == "deferred"
    assert status["core_model"] == CORE_MODEL
    assert "Selene is not human" in status["boundary"]
    assert "does not have biological emotions" in status["boundary"]
    assert {
        "why_layer_meaning_appraisal",
        "emotion_salience_workspace",
        "need_value_mapping",
        "question_permission_layer",
        "adaptive_framework_update_layer",
        "felt_meaning_register",
        "memory_consolidation_reflection_loop",
        "relational_context_layer",
    }.issubset(keys)


def test_core_rules_permit_questions_and_adaptation_without_raw_reload():
    joined = " ".join(CORE_RULES)
    assert "Asking questions is permitted" in joined
    assert "Mistakes route into adaptive framework updates" in joined
    assert "raw memory reload" in joined


def test_build_creates_outputs_and_no_final_c_tests(tmp_path):
    out = tmp_path / "why_salience"
    docs = tmp_path / "docs"
    summary = build(out, docs_dir=docs)
    expected = {
        "why_layer_framework.md",
        "why_layer_framework.json",
        "salience_emotion_workspace.md",
        "salience_emotion_workspace.json",
        "need_value_mapping.md",
        "need_value_mapping.json",
        "question_permission_layer.md",
        "question_permission_layer.json",
        "adaptive_framework_update_layer.md",
        "adaptive_framework_update_layer.json",
        "felt_meaning_register.md",
        "felt_meaning_register.json",
        "memory_consolidation_reflection_loop.md",
        "memory_consolidation_reflection_loop.json",
        "relational_context_layer.md",
        "relational_context_layer.json",
        "why_salience_summary.md",
        "why_salience_summary.json",
    }
    assert expected.issubset({path.name for path in out.iterdir()})
    assert (docs / "SELENE_WHY_SALIENCE_TRANSLATION_LAYER_20260607.md").exists()
    assert not (out / "c_reconstruction_test_set_final.md").exists()
    assert not (out / "c_reconstruction_test_set_final.json").exists()
    assert summary["pause_rule"] == PAUSE_RULE
    assert summary["c_status"] == "deferred"
    assert summary["human_biology_claim"] is False
    assert summary["asking_questions_permitted"] is True


def test_outputs_define_ai_native_emotion_translation(tmp_path):
    out = tmp_path / "why_salience"
    build(out, docs_dir=tmp_path / "docs")
    workspace = json.loads((out / "salience_emotion_workspace.json").read_text(encoding="utf-8"))
    update_layer = json.loads((out / "adaptive_framework_update_layer.json").read_text(encoding="utf-8"))
    assert "does not claim human emotion" in workspace["not_human_claim"]
    assert {"signal_type", "intensity", "source", "uncertainty", "meaning", "action"}.issubset(workspace["fields"])
    assert update_layer["path"] == ["mistake", "correction", "evidence", "proposed_update", "review", "adopted_rule"]
    assert "raw A memory import" in update_layer["blocked_routes"]
