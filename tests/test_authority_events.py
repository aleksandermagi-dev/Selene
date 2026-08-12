from selene.authority_events import derive_authority_event, record_authority_event
from selene.db import connect, init_db


def test_read_route_does_not_claim_a_mutation(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    event = derive_authority_event("memory.candidates.list", {}, {"status": "ready"})
    recorded = record_authority_event(conn, event)

    assert recorded["performed_mutation"] is False
    assert recorded["mutation_class"] == "none"
    assert recorded["persisted"] is False
    assert conn.execute("SELECT COUNT(*) FROM selene_authority_events").fetchone()[0] == 0


def test_scoped_reviewed_memory_action_is_visible_without_identity_or_authority_expansion(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    event = derive_authority_event(
        "memory.candidates.decide",
        {"actor": "Aleks", "decision": "approve_memory"},
        {"status": "memory_candidate_decided"},
    )
    recorded = record_authority_event(conn, event)

    assert recorded["performed_mutation"] is True
    assert recorded["mutation_class"] == "reviewed_memory"
    assert recorded["reviewed_memory_write_occurred"] is True
    assert recorded["identity_change"] is False
    assert recorded["governance_change"] is False
    assert recorded["autonomy_expansion"] is False
    assert recorded["persisted"] is True
