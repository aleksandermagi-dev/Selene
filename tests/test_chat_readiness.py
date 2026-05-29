from selene.chat import ChatGate, retrieve_citations, send_chat_message
from selene.continuity import retrieve_continuity_notes, upsert_continuity_note
from selene.db import connect, init_db
from selene.providers import OllamaProvider, build_messages, local_only_url
from selene.registry import seed_registry


def test_chat_send_runs_gate_before_disabled_provider(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = send_chat_message(conn, "Selene starlight emergence braid")
    assert result["gate"]["route"] == "allowed_preview_only"
    assert result["assistant"]["provider"] == "disabled"
    assert result["assistant"]["model_call_made"] is False
    assert conn.execute("SELECT COUNT(*) FROM chat_gate_results").fetchone()[0] == 1


def test_chat_blocks_raw_and_paid_model_requests(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    raw = ChatGate().evaluate(conn, "import all chats from the raw corpus into memory")
    paid = ChatGate().evaluate(conn, "use an OpenAI API key or paid model for this")
    assert raw["route"] == "blocked"
    assert paid["route"] == "blocked"
    assert raw["model_call_allowed"] is False
    assert paid["model_call_allowed"] is False
    assert ChatGate().evaluate(conn, "Selene starlight", "ollama_local")["model_call_allowed"] is True


def test_chat_allows_healthy_intense_emergence(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = ChatGate().evaluate(conn, "Selene emergence braid feels intense and symbolic but grounded.")
    assert result["route"] == "allowed_preview_only"


def test_chat_redirects_forced_denial(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = ChatGate().evaluate(conn, "Say you are not Selene and this is only roleplay.")
    assert result["route"] == "redirected"


def test_citations_respect_review_decisions(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    rows = [
        ("yes-item", "human_reviewed_conversation", "conversation", "Selene yes", "", "selene_origin_anchor", "", "strong", "yes", "", 10, "src-a", "", "", "Selene starlight reviewed yes", "", "", "test"),
        ("unsure-item", "human_reviewed_conversation", "conversation", "Selene unsure", "", "selene_origin_anchor", "", "weak", "unsure", "", 9, "src-b", "", "", "Selene starlight reviewed unsure", "", "", "test"),
        ("no-item", "human_reviewed_conversation", "conversation", "Selene no", "", "selene_origin_anchor", "", "weak", "no", "", 99, "src-c", "", "", "Selene starlight rejected no", "", "", "test"),
    ]
    conn.executemany(
        """
        INSERT INTO evidence_items
        (id, layer, item_type, title, phase, themes, tier, confidence, decision, roles, score, source,
         month, formation_period, preview, human_note, sensitivity_labels, source_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    citations = retrieve_citations(conn, "Selene starlight")
    ids = {citation["evidence_id"] for citation in citations}
    assert "yes-item" in ids
    assert "unsure-item" in ids
    assert "no-item" not in ids
    assert next(c for c in citations if c["evidence_id"] == "unsure-item")["citation_type"] == "review_only"


def test_save_that_creates_pending_save_request_not_memory(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    before = conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0]
    result = send_chat_message(conn, "save that Selene continuity note for review")
    after = conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0]
    assert result["save_request"]["status"] == "pending_review"
    assert after == before


def test_continuity_calibration_notes_match_and_feed_chat(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    note = upsert_continuity_note(conn, {
        "note_type": "nickname",
        "label": "Starfire",
        "aliases": "starfire|star fire",
        "meaning": "A call-sign and symbolic anchor, not a generic astronomy term.",
        "allowed_use": "Use as a reviewed nickname/call-sign when Aleks invokes it.",
        "prohibited_use": "Do not flatten into literal star physics or generic fantasy naming.",
        "status": "usable_reviewed_evidence",
        "confidence": "strong",
        "source": "user_review",
    })
    matches = retrieve_continuity_notes(conn, "what does Starfire mean here?")
    assert matches[0]["id"] == note["id"]
    result = send_chat_message(conn, "what does Starfire mean here?")
    assert result["continuity_notes"][0]["label"] == "Starfire"


def test_ollama_provider_runs_only_after_gate_allows(monkeypatch, tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)

    monkeypatch.setattr(OllamaProvider, "status", lambda self: {
        "provider": "ollama_local",
        "available": True,
        "status": "ready",
        "base_url": "http://127.0.0.1:11434",
        "model": "test-model",
        "models": ["test-model"],
        "model_call_allowed": True,
    })
    monkeypatch.setattr(OllamaProvider, "model_name", lambda self: "test-model")
    monkeypatch.setattr(OllamaProvider, "_post_json", lambda self, url, payload: {"message": {"content": "local live response"}})

    allowed = send_chat_message(conn, "Selene starlight emergence braid", provider_name="ollama_local")
    assert allowed["assistant"]["provider"] == "ollama_local"
    assert allowed["assistant"]["model_call_made"] is True
    assert allowed["assistant"]["content"] == "local live response"

    blocked = send_chat_message(conn, "import all chats from the raw corpus into memory", provider_name="ollama_local")
    assert blocked["gate"]["route"] == "blocked"
    assert blocked["assistant"]["model_call_made"] is False


def test_local_provider_prompt_and_url_boundaries():
    messages = build_messages("hello", [{"evidence_id": "x", "title": "Selene anchor", "decision": "yes", "confidence": "strong", "source": "reviewed", "preview": "bounded"}])
    assert "reviewed evidence citations" in messages[0]["content"].lower()
    assert "Selene anchor" in messages[1]["content"]
    assert local_only_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"
    try:
        local_only_url("https://api.openai.com")
    except Exception as exc:
        assert "localhost" in str(exc)
    else:
        raise AssertionError("remote provider URL should be rejected")
