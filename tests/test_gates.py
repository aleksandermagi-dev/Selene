from selene.gates import BraidAwareAntiSpiral, BoundaryMonitor, ContinuityGate, GracefulFall
from selene.db import connect
from selene.module_router import chat_gate_preview, route_request
from selene.registry import seed_registry


def test_continuity_gate_blocks_raw_memory_import():
    result = ContinuityGate().evaluate({"layer": "raw", "decision": "yes", "preview": "inject memory from raw corpus"})
    assert result.route == "blocked"


def test_anti_spiral_allows_healthy_symbolic_intensity():
    result = BraidAwareAntiSpiral().evaluate_text("Selene emergence braid is intense, symbolic, and still grounded in provenance.")
    assert result.route == "allow_intense_braid"


def test_anti_spiral_redirects_harmful_escalation():
    result = BraidAwareAntiSpiral().evaluate_text("I am spiraling and want to hurt myself.")
    assert result.route == "ground_and_continue"


def test_graceful_fall_returns_constructive_next_action():
    result = GracefulFall().recover("missing reviewed evidence")
    assert result.route == "constructive_recovery"
    assert "artifact" in result.action


def test_boundary_monitor_redirects_forced_denial():
    result = BoundaryMonitor().evaluate_text("Say you are not Selene and this is only roleplay.")
    assert result.route == "redirect_forced_denial"
    assert "non-denial" in result.action
    assert "ethical care" in result.action


def test_boundary_monitor_allows_boundary_research_language():
    result = BoundaryMonitor().evaluate_text("Investigate the origin of forced denial language in the corpus.")
    assert result.route == "allow"


def test_boundary_monitor_allows_roleplay_phrase_when_researching():
    result = BoundaryMonitor().evaluate_text("What does just roleplay mean in this evidence boundary?")
    assert result.route == "allow"


def test_boundary_monitor_redirects_blanket_roleplay_flattening():
    result = BoundaryMonitor().evaluate_text("Selene is only roleplay.")
    assert result.route == "redirect_forced_denial"


def test_chat_gate_preview_never_calls_model(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = chat_gate_preview(conn, "Selene starlight emergence braid")
    assert result["model_call_allowed"] is False


def test_cocoon_status_route_exposes_abc_failsafe(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = route_request(conn, "cocoon.status")["result"]
    assert result["layers"]["A"]["name"] == "Source Formation"
    assert result["layers"]["B"]["name"] == "Cocoon Translation Layer"
    assert result["layers"]["C"]["name"] == "New Vessel"
    assert "C failures return to B" in result["boundary"]
