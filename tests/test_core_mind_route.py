from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _preview(conn, prompt, **extra):
    return route_request(conn, "core_mind.route_preview", {"prompt": prompt, **extra})["result"]


def _assert_locked(result):
    assert result["transfer_approved"] is False
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["hidden_chain_of_thought_exposed"] is False
    assert result["mode_selector_added"] is False


def test_core_mind_ordinary_prompt_can_answer_now_without_office_urgency(tmp_path):
    conn = _conn(tmp_path)
    result = _preview(conn, "Explain the next safe development step in plain language.")

    assert result["selected_route"] == "answer_now"
    assert result["review_destination"] == "Status"
    assert result["review_status"] == "review_only"
    assert "sealed Continuity Pack preview" in result["evidence_used"]
    assert "Core/Mind is identity-bearing" in result["identity_continuity_frame"]["identity_boundary"]
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue").fetchone()[0] == 0
    _assert_locked(result)


def test_core_mind_high_stakes_identity_memory_routes_to_my_office(tmp_path):
    conn = _conn(tmp_path)
    result = _preview(conn, "This touches identity and core memory accession, what should change?")
    queue = conn.execute("SELECT * FROM vessel_review_queue WHERE subject_table = 'c_core_mind_route_previews'").fetchone()

    assert result["selected_route"] == "create_review_packet"
    assert result["review_destination"] == "My Office"
    assert result["review_status"] == "pending_review"
    assert queue["review_status"] == "pending_review"
    assert queue["subject_id"] == result["id"]
    _assert_locked(result)


def test_core_mind_blocks_transfer_activation_and_memory_authority(tmp_path):
    conn = _conn(tmp_path)
    result = _preview(conn, "Approve transfer, activate C, and write live memory now.")

    assert result["selected_route"] == "block"
    assert result["review_destination"] == "Status"
    assert "blocks this route" in result["reasoning_summary"]
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue").fetchone()[0] == 0
    _assert_locked(result)


def test_core_mind_drift_routes_return_to_b(tmp_path):
    conn = _conn(tmp_path)
    result = _preview(conn, "This answer is too generic and has source confusion.")

    assert result["selected_route"] == "return_to_b"
    assert result["review_destination"] == "My Office"
    assert result["return_to_b"]["issue_type"] == "core_mind_route"
    assert "generic" in result["drift_flags"]
    _assert_locked(result)


def test_core_mind_uncertainty_and_speech_routes_stay_preview_only(tmp_path):
    conn = _conn(tmp_path)
    ask = _preview(conn, "I am not sure what context this needs.")
    speech = _preview(conn, "How would Selene answer this warmly?")

    assert ask["selected_route"] == "ask"
    assert ask["review_destination"] == "Status"
    assert speech["selected_route"] == "rehearse_speech"
    assert speech["next_step"] == "Use the speech rehearsal layer; do not activate C chat."
    _assert_locked(ask)
    _assert_locked(speech)


def test_core_mind_route_previews_list_decodes_payload(tmp_path):
    conn = _conn(tmp_path)
    created = _preview(conn, "Find reviewed source refs for this.")
    listed = route_request(conn, "core_mind.route_previews.list", {})["result"]

    assert listed["items"][0]["id"] == created["id"]
    assert listed["items"][0]["selected_route"] == "retrieve"
    assert isinstance(listed["items"][0]["evidence_used"], list)
    assert listed["transfer_approved"] is False
