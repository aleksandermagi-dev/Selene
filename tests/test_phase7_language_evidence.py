from __future__ import annotations

import sqlite3

import pytest

from selene.answer_substance import build_answer_substance
from selene.db import init_db
from selene.learning_evidence_activity import (
    build_phase_7_language_evidence_profile,
    phase_7_language_evidence_suite,
)
from selene.native_language_organ import realize_native_language


def _observation(state: str = "demonstrated") -> dict[str, object]:
    return {
        "state": state,
        "observation": "The visible receipt preserves the supplied obligation and stops once complete.",
        "evidence_refs": ["synthetic:phase7:receipt"],
        "suggested_next_move": "Keep the current bounded mechanism and revisit only if a later fixture exposes a specific gap.",
    }


def test_phase_7_suite_is_source_contained_descriptive_and_gentle():
    suite = phase_7_language_evidence_suite()

    assert suite["status"] == "phase_7_language_evidence_suite_ready"
    assert suite["activity_count"] >= 6
    assert suite["dimension_count"] == 15
    assert len(suite["suite_sha256"]) == 64
    assert all(item["source_contained"] is True for item in suite["activities"])
    assert all(item["synthetic_only"] is True for item in suite["activities"])
    assert all(item["resident_state_required"] is False for item in suite["activities"])
    assert suite["composite_result"] is None
    assert "score" not in suite
    assert suite["learned_substrate_boundary"]["automatic_authorization"] is False
    assert suite["ethical_review"]["distress_provoking_activity_used"] is False
    assert suite["ethical_review"]["resident_run_started"] is False


def test_phase_7_profile_records_only_observed_dimensions_and_one_next_move():
    profile = build_phase_7_language_evidence_profile(
        {
            "activity_key": "long_form_obligation_spine",
            "activity_integrity_state": "ready",
            "source_refs": ["synthetic:long-form:one"],
            "dimensions": {
                "obligation_completeness": _observation(),
                "discourse_coherence": _observation("developing"),
            },
        }
    )

    assert profile["observed_dimension_keys"] == [
        "obligation_completeness",
        "discourse_coherence",
    ]
    assert "natural_stopping" in profile["unobserved_dimension_keys"]
    assert profile["dimensions"]["discourse_coherence"]["state"] == "developing"
    assert profile["dimensions"]["obligation_completeness"]["not_a_grade"] is True
    assert profile["composite_result"] is None
    assert profile["automatic_review"] is False
    assert profile["automatic_retention"] is False
    assert profile["learned_substrate_decision"]["state"] == (
        "deterministic_ceiling_not_yet_established"
    )
    assert profile["stopping_receipt"]["follow_up_created"] is False


def test_phase_7_profile_rejects_scores_unknown_dimensions_and_missing_evidence():
    with pytest.raises(ValueError, match="score"):
        build_phase_7_language_evidence_profile(
            {
                "activity_key": "long_form_obligation_spine",
                "score": 10,
            }
        )
    with pytest.raises(ValueError, match="unknown phase 7 evidence dimensions"):
        build_phase_7_language_evidence_profile(
            {
                "activity_key": "long_form_obligation_spine",
                "source_refs": ["synthetic:test"],
                "dimensions": {"personality_quality": _observation()},
            }
        )
    with pytest.raises(ValueError, match="evidence_refs are required"):
        value = _observation()
        value["evidence_refs"] = []
        build_phase_7_language_evidence_profile(
            {
                "activity_key": "long_form_obligation_spine",
                "source_refs": ["synthetic:test"],
                "dimensions": {"obligation_completeness": value},
            }
        )


def test_phase_7_complete_descriptive_profile_can_close_current_gate_without_authorizing_learning():
    suite = phase_7_language_evidence_suite()
    observations = {
        item["key"]: _observation()
        for item in suite["dimensions"]
    }
    profile = build_phase_7_language_evidence_profile(
        {
            "activity_key": "phase_7_closure_summary",
            "activity_integrity_state": "ready",
            "source_refs": ["synthetic:phase7:focused-suite"],
            "dimensions": observations,
        }
    )

    decision = profile["learned_substrate_decision"]
    assert decision["state"] == "deterministic_scope_sufficient_for_current_gate"
    assert decision["provider_authorized"] is False
    assert decision["model_download_authorized"] is False
    assert decision["training_authorized"] is False
    assert decision["lora_authorized"] is False
    assert decision["substrate_change_authorized"] is False
    assert decision["future_architectural_decision_owner"] == "Aleks"
    assert profile["memory_write_active"] is False
    assert profile["diagnostic_result_is_self_model_evidence"] is False


def test_one_gentle_creative_walkthrough_is_disposable_bounded_and_stops(tmp_path):
    conn = sqlite3.connect(tmp_path / "phase7-disposable.db")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    creative = build_answer_substance(
        "Write three original fictional sentences about a paper observatory at dawn. Include one bell."
    )
    realized = realize_native_language(
        conn,
        {
            "prompt": "Present the supplied fictional scene and stop when it is complete.",
            "content_seed": creative["answer"],
            "certainty": "explicit_fictional_invention",
            "source_refs": ["synthetic:phase7:gentle-walkthrough"],
        },
        record_run=False,
    )

    creative_stop = creative["creative_receipt"]["stopping_receipt"]
    language_stop = realized["bounded_conversational_realization"]["terminal_stop"]
    assert creative["fiction_status"] == "explicit_fictional_invention"
    assert creative_stop["generation_passes"] == 1
    assert creative_stop["recursion_allowed"] is False
    assert realized["candidate_text"]
    assert realized["bounded_conversational_realization"]["generation_pass_count"] == 1
    assert language_stop["state"] == "realization_complete"
    assert realized["revision"]["meaning_preserved"] is True
    assert realized["revision"]["unsupported_content_generated"] is False
    assert conn.execute("SELECT COUNT(*) FROM native_language_runs").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_lea_runs").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0] == 0
