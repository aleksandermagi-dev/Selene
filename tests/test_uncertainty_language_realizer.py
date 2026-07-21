from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.native_language_organ import realize_native_language
from selene.uncertainty_language_realizer import build_uncertainty_plan, realize_uncertainty_plan


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_uncertainty_kinds_remain_semantically_distinct_and_bounded():
    expected = {
        "ambiguous_reference": ["state_reference_ambiguity", "request_reference_grounding"],
        "developing_view": ["state_view_unsettled", "request_deciding_context"],
        "insufficient_grounding": ["state_missing_ground", "request_relevant_context"],
        "fuzzy_memory": ["state_fuzzy_recollection", "request_memory_grounding"],
    }

    for kind, acts in expected.items():
        plan = build_uncertainty_plan({"kind": kind})
        result = realize_uncertainty_plan(plan, variation_key=kind)
        assert [item["act"] for item in plan["acts"]] == acts
        assert plan["fact_invention_allowed"] is False
        assert plan["memory_certainty_invention_allowed"] is False
        assert result["whole_response_template_selected"] is False
        assert result["fact_invented"] is False
        assert result["memory_certainty_invented"] is False
        assert result["candidate_text"].endswith("?")


def test_uncertainty_realization_varies_clauses_and_avoids_recent_wording():
    plan = build_uncertainty_plan({"kind": "insufficient_grounding"})
    results = [
        realize_uncertainty_plan(plan, variation_key=f"uncertain-{index}")
        for index in range(18)
    ]
    first = results[0]
    next_result = realize_uncertainty_plan(
        plan,
        variation_key="next",
        recent_texts=[first["candidate_text"]],
    )

    assert len({item["candidate_text"] for item in results}) >= 6
    assert {item["text"] for item in first["selected_clauses"]}.isdisjoint(
        {item["text"] for item in next_result["selected_clauses"]}
    )


def test_fuzzy_memory_preserves_supplied_hint_without_upgrading_certainty():
    hint = "There may have been a blue control near the map."
    plan = build_uncertainty_plan({"kind": "fuzzy_memory", "supported_hint": hint})
    result = realize_uncertainty_plan(plan, variation_key="fuzzy")

    assert hint in result["candidate_text"]
    assert any(item["source"] == "supplied_supported_hint" for item in result["selected_clauses"])
    assert "I remember" not in result["candidate_text"]
    assert result["memory_certainty_invented"] is False


def test_nlo_uses_inspectable_uncertainty_plan_for_unsupported_question(tmp_path):
    conn = _conn(tmp_path)
    prompt = "What color should the unbuilt observatory curtains be?"
    result = realize_native_language(
        conn,
        {"prompt": prompt, "intent_decision": classify_chat_intent(prompt)},
    )

    plan = result["discourse_plan"]["uncertainty_expression_plan"]
    realization = result["discourse_plan"]["uncertainty_expression_realization"]
    assert result["version"] == "v20_conversation_maturity_composition"
    assert plan["kind"] == "insufficient_grounding"
    assert realization["whole_response_template_selected"] is False
    assert result["candidate_text"] == realization["candidate_text"]
    assert "unbuilt observatory curtains" not in result["candidate_text"]
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
