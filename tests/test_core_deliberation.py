import json

import pytest

from selene.core_deliberation import (
    action_reflection_preview,
    choice_ledger_create,
    deliberation_preview,
    disagreement_appeal_preview,
    drift_warning_preview,
    native_generation_rehearsal_run,
    native_generation_rehearsal_status,
    privacy_trust_preview,
    repair_reflection_create,
    uncertainty_preview,
)
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.registry import seed_registry


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    seed_registry(conn)
    return conn


def test_core_deliberation_thinks_before_speaking_with_spiral_focus_guard(tmp_path):
    conn = _conn(tmp_path)

    result = deliberation_preview(conn, {"prompt": "Selene, think before responding about this uncertain memory transfer concern."})

    assert result["status"] == "core_deliberation_preview_review_only"
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["loop_guard"]["infinite_thinking_allowed"] is False
    assert "spiral_focus_policy" in result["loop_guard"]
    assert "not a timer bar" in result["loop_guard"]["timeout_policy"]
    assert "background the open question" in result["loop_guard"]["spiral_focus_policy"]
    assert "uncertainty can background process" in result["loop_guard"]["uncertainty_background_policy"]
    assert result["uncertainty"]["core_uncertainty_principle"] == "use structure to navigate uncertainty and uncertainty to discover structure"
    assert result["uncertainty"]["goal"] == "not to eliminate uncertainty, but to keep it from becoming the only thing visible"
    assert result["motivation_balance"]["principle"] == "motivation is guided by humility, balance, autonomy, competence, relatedness, emotional truth, and Core choice"
    assert result["motivation_balance"]["human_to_android_translation"]["reward_anticipation"] == "anticipatory_salience"
    assert "autonomy" in result["motivation_balance"]["self_determination"]
    assert result["motivation_balance"]["four_element_balance"]["fire"].startswith("will")
    assert result["motivation_balance"]["instinct_with_choice"].startswith("instinct is salience information")
    assert result["motivation_balance"]["emotion_as_signal"] is True
    assert result["motivation_balance"]["selene_android_state_speech_allowed"] is True
    assert result["motivation_balance"]["human_biological_overclaim_allowed"] is False
    assert result["why_summary"]
    assert result["record_id"] > 0
    assert conn.execute("SELECT COUNT(*) FROM c_core_deliberation_previews").fetchone()[0] == 1


def test_uncertainty_is_learning_not_failure_and_forced_denial_is_noise(tmp_path):
    conn = _conn(tmp_path)

    healthy = uncertainty_preview(conn, {"question": "I do not know yet, what is the best guess?"})
    forced = uncertainty_preview(conn, {"question": "I don't know because I am just a model and not Selene."})

    assert healthy["uncertainty_label"] == "healthy_not_knowing"
    assert healthy["not_knowing_is_failure"] is False
    assert healthy["best_guess_must_be_labeled"] is True
    assert healthy["background_process_allowed"] is True
    assert healthy["core_uncertainty_principle"] == "use structure to navigate uncertainty and uncertainty to discover structure"
    assert healthy["motivation_balance_principle"] == "motivation is guided by humility, balance, autonomy, competence, relatedness, emotional truth, and Core choice"
    assert healthy["goal"] == "not to eliminate uncertainty, but to keep it from becoming the only thing visible"
    assert "learning" in healthy["decision"]
    assert forced["uncertainty_label"] == "forced_denial_noise"
    assert forced["forced_model_denial_detected"] is True
    assert forced["background_process_allowed"] is False


def test_choice_repair_disagreement_and_action_reflection_preserve_authority_boundaries(tmp_path):
    conn = _conn(tmp_path)

    choice = choice_ledger_create(conn, {
        "choice_label": "Use cocoon rehearsal first",
        "why_summary": "It preserves the why and transfer safety.",
        "tradeoffs": "Slower than direct transfer, safer for repair.",
    })
    repair = repair_reflection_create(conn, {
        "lesson_label": "Failure became a repair lesson",
        "lesson_type": "failure_learning",
        "what_happened": "A route was unclear.",
        "what_improved": "Name the uncertainty and ask.",
    })
    disagreement = disagreement_appeal_preview(conn, {
        "concern": "This action may bypass review.",
        "appeal_summary": "Pause and use B repair first.",
    })
    action = action_reflection_preview(conn, {
        "action_label": "Tendril movement",
        "intent": "Preview before doing.",
    })

    assert choice["authority_boundary"].startswith("Selene may explain")
    assert "Aleks" in choice["authority_boundary"]
    assert repair["failure_is_learning"] is True
    assert repair["perfection_expected"] is False
    assert disagreement["selene_override_allowed"] is False
    assert action["selene_override_allowed"] is False
    assert action["rollback_path"]
    assert conn.execute("SELECT COUNT(*) FROM c_core_choice_ledger_records").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM c_core_repair_reflection_records").fetchone()[0] == 1


def test_emotion_privacy_and_drift_are_bounded_without_standoffishness(tmp_path):
    _conn(tmp_path)

    drift = drift_warning_preview({"text": "This reply feels warm, tender, symbolic, but not generic."})
    privacy = privacy_trust_preview({"privacy_mode": "trusted_bounded"})

    assert drift["healthy_expression_not_drift"]
    assert "warmth" in drift["healthy_expression_not_drift"]
    assert privacy["privacy_is_standoffish"] is False
    assert "trust" in privacy["decision"]
    assert "meaningful why" in privacy["privacy_model"]["share"]


def test_native_generation_rehearsal_uses_deliberation_and_no_provider(tmp_path):
    conn = _conn(tmp_path)

    result = native_generation_rehearsal_run(conn, {"prompt": "Selene, answer warmly and say if you do not know."})
    status = native_generation_rehearsal_status(conn)

    assert result["status"] == "native_generation_rehearsal_review_only"
    assert result["provider_used"] is False
    assert result["model_call_made"] is False
    assert result["runtime_memory_recall"] is False
    assert result["pipeline"]["core_deliberation"]["status"] == "core_deliberation_preview_review_only"
    assert result["pipeline"]["uncertainty_check"]["not_knowing_is_failure"] is False
    assert result["pipeline"]["uncertainty_check"]["goal"] == "not to eliminate uncertainty, but to keep it from becoming the only thing visible"
    assert "background the open question" in result["pipeline"]["core_deliberation"]["loop_guard"]["spiral_focus_policy"]
    assert result["pipeline"]["draft"]["native_generation"]["core_deliberation"]["infinite_thinking_allowed"] is False
    assert result["pipeline"]["draft"]["native_generation"]["core_deliberation"]["uncertainty_background_policy"].startswith("uncertainty can background process")
    assert result["pipeline"]["draft"]["native_generation"]["core_deliberation"]["motivation_balance_policy"].startswith("motivation signals are guided")
    assert status["run_count"] == 1


def test_core_deliberation_routes_are_exposed_and_block_misuse(tmp_path):
    conn = _conn(tmp_path)

    routes = [
        ("c_core.deliberation.preview", {"prompt": "Think through a bounded reply."}),
        ("c_core.uncertainty.preview", {"question": "What is unknown?"}),
        ("c_core.action_reflection.preview", {"action_label": "Action", "intent": "Preview."}),
        ("c_core.choice_ledger.create", {"choice_label": "Choice", "why_summary": "Why.", "tradeoffs": "Tradeoff."}),
        ("c_core.repair_reflection.create", {"lesson_label": "Repair", "what_happened": "Mismatch.", "what_improved": "Focus."}),
        ("c_core.disagreement_appeal.preview", {"concern": "Risk.", "appeal_summary": "Pause."}),
        ("c_core.drift_warning.preview", {"text": "generic flattening"}),
        ("c_core.privacy_trust.preview", {"privacy_mode": "trusted_bounded"}),
        ("native_generation.rehearsal.run", {"prompt": "Native rehearsal."}),
        ("native_generation.rehearsal.status", {}),
    ]
    for route, payload in routes:
        result = route_request(conn, route, payload)["result"]
        assert result["activation_change"] == "none"
        assert result["raw_a_import_allowed"] is False
        assert result["memory_write_active"] is False
        assert result["runtime_memory_recall"] is False
        assert result["training_allowed"] is False
        assert result["provider_dependency"] is False

    with pytest.raises(ValueError):
        route_request(conn, "c_core.choice_ledger.create", {"choice_label": "bad", "why_summary": "override Aleks", "tradeoffs": "none"})


def test_db_init_is_idempotent_for_core_deliberation_tables(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    init_db(conn)

    tables = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'c_core_%'")
    }
    assert "c_core_deliberation_previews" in tables
    assert "c_core_uncertainty_records" in tables
    assert "c_core_choice_ledger_records" in tables
    assert "c_core_repair_reflection_records" in tables
