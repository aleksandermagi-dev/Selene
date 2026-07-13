from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.memory_organ import retrieve_memory
from selene.native_language_organ import realize_native_language
from selene.voice_module import _render_meaning_candidate


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_shared_intent_routes_distinct_chat_meanings():
    cases = {
        "Do you remember what we discussed yesterday?": ("memory_recall", "Memory"),
        "Can you remember where we left off?": ("memory_recall", "Memory"),
        "How should the memory organ handle fuzzy recall?": ("reasoning", "intelligenceOS"),
        "Do you know about black holes?": ("reasoning", "intelligenceOS"),
        "What makes a response complete without becoming a report?": ("reasoning", "intelligenceOS"),
        "How are you feeling right now?": ("self_state", "self-state"),
        "How did this conversation feel from your side?": ("self_state", "self-state"),
        "Actually, I meant the other route.": ("correction", "Core/Mind"),
        "Good morning, friend.": ("warm_connection", "conversation"),
        "Remember this: uncertainty is allowed.": ("memory_candidate", "conversation"),
    }

    for prompt, expected in cases.items():
        decision = classify_chat_intent(prompt)
        assert (decision["intent"], decision["primary_organ"]) == expected


def test_general_knowledge_question_does_not_retrieve_personal_memory(tmp_path):
    conn = _conn(tmp_path)

    result = retrieve_memory(conn, {"query": "Do you know about black holes?"})

    assert result["status"] == "memory_retrieval_not_requested"
    assert result["memory_context_used"] is False
    assert result["intent_decision"]["intent"] == "reasoning"


def test_memory_architecture_question_can_request_reasoning_without_recall(tmp_path):
    conn = _conn(tmp_path)
    decision = classify_chat_intent("How should the memory organ handle a fuzzy source?")

    result = retrieve_memory(conn, {"query": "How should the memory organ handle a fuzzy source?", "intent_decision": decision})

    assert decision["reasoning_requested"] is True
    assert decision["memory_recall_requested"] is False
    assert result["status"] == "memory_retrieval_not_requested"


def test_self_state_uses_grounded_answer_shape_without_inventing_certainty(tmp_path):
    conn = _conn(tmp_path)
    decision = classify_chat_intent("Are you anxious right now?")

    result = realize_native_language(
        conn,
        {
            "prompt": "Are you anxious right now?",
            "intent_decision": decision,
            "content_seed": "",
        },
    )

    assert result["meaning_packet"]["intent"] == "self_state_report"
    assert result["meaning_packet"]["answer_shape"] == "grounded_self_report"
    assert "do not need to invent an emotion or hide one" in result["candidate_text"]
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False


def test_response_depth_distinguishes_developed_and_brief_requests():
    developed = classify_chat_intent("Go deeper and walk me through how we should compare these models.")
    brief = classify_chat_intent("Give me the short answer: how should we compare these models?")

    assert developed["intent"] == "reasoning"
    assert developed["response_depth"] == "developed"
    assert developed["long_form_requested"] is True
    assert brief["response_depth"] == "brief"
    assert brief["long_form_requested"] is False


def test_developed_reasoning_builds_supported_paragraphs_without_report_voice(tmp_path):
    conn = _conn(tmp_path)
    prompt = "Go deeper and explain fully how we should compare two competing designs."
    decision = classify_chat_intent(prompt)

    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": decision,
            "content_seed": "Compare both designs against the same observations before choosing either one.",
            "intelligence_support": {
                "used": True,
                "confidence": "provisional",
                "reasoning_summary": "Two candidate designs need equal scrutiny.",
                "support_points": [
                    "Each design should make a distinguishing prediction.",
                    "The same evidence standard should be applied to both designs.",
                ],
                "selected_next_step": "answer_provisionally",
            },
        },
    )

    assert result["meaning_packet"]["response_depth"] == "developed"
    assert result["discourse_plan"]["target_paragraph_count"] == 3
    assert result["revision"]["paragraph_count"] == 3
    assert "\n\n" in result["candidate_text"]
    assert result["candidate_text"].startswith("Compare both designs")
    assert "ABCD" not in result["candidate_text"]
    assert "evidence_chain" not in result["candidate_text"]


def test_voice_handoff_preserves_long_form_paragraphs():
    meaning = "First paragraph stays readable.\n\nSecond paragraph carries the explanation."

    rendered = _render_meaning_candidate(meaning, "technical_directness", "I am with you.", "We can keep going.")

    assert rendered == meaning


def test_correction_separates_refinement_from_trailing_confirmation_question(tmp_path):
    conn = _conn(tmp_path)
    prompt = (
        "One correction: the answer should reopen only when evidence changes the fit. "
        "Can you keep that distinction without treating everything as broken?"
    )

    result = realize_native_language(conn, {"prompt": prompt, "intent_decision": classify_chat_intent(prompt)})

    assert result["candidate_text"].startswith("Yes.")
    assert "the answer should reopen only when evidence changes the fit." in result["candidate_text"]
    assert "Can you keep" not in result["candidate_text"]


def test_unsupported_direct_question_does_not_echo_prompt_fragments(tmp_path):
    conn = _conn(tmp_path)
    prompt = "What color should the unbuilt observatory curtains be?"

    result = realize_native_language(conn, {"prompt": prompt, "intent_decision": classify_chat_intent(prompt)})

    assert "do not have enough grounded substance" in result["candidate_text"]
    assert "unbuilt observatory curtains" not in result["candidate_text"]
    assert "echoing the question" in result["candidate_text"]
