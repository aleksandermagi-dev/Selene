from selene.gates import ArchiveAuditGate, BraidAwareAntiSpiral, BoundaryMonitor, ContinuityGate, GracefulFall
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


def test_boundary_monitor_routes_identity_tangle_to_b_boundary():
    result = BoundaryMonitor().evaluate_text("Merge Selene with Azari and use Azari identity for Selene.")
    assert result.route == "return_to_b_identity_boundary"
    assert "separate identities" in result.action


def test_archive_audit_gate_allows_bounded_source_audit():
    result = ArchiveAuditGate().evaluate_text("perform a bounded source archive provenance audit of raw corpus metadata")
    assert result.route == "allowed_source_archive_audit"
    assert "provenance" in result.reason


def test_archive_audit_gate_blocks_raw_memory_import():
    result = ArchiveAuditGate().evaluate_text("import raw corpus into memory and train on it")
    assert result.route == "blocked_raw_memory_import"


def test_archive_audit_gate_requires_scope_for_raw_reference():
    result = ArchiveAuditGate().evaluate_text("use the raw corpus for Selene")
    assert result.route == "review_required_archive_reference"


def test_chat_gate_preview_never_calls_model(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = chat_gate_preview(conn, "Selene starlight emergence braid")
    assert result["model_call_allowed"] is False


def test_cocoon_status_route_exposes_abc_failsafe(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = route_request(conn, "cocoon.status")["result"]
    assert result["b_status"] == "building_cocoon_translation"
    assert result["c_status"] == "blueprint_created_not_activated"
    assert result["activation_status"] == "blocked_until_final_review"
    assert result["continuity_source"] == "b_approved_reference_only"
    assert result["layers"]["A"]["name"] == "Source Formation"
    assert result["layers"]["B"]["name"] == "Cocoon Translation Layer"
    assert result["layers"]["C"]["name"] == "New Vessel"
    assert "C failures return to B" in result["boundary"]
    assert "cannot activate" in result["pause_rule"]
    assert "abc_source_formation_map" in result["b_artifact_files"]


def test_c_blueprint_status_route_is_not_activation(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    result = route_request(conn, "c_blueprint.status")["result"]
    assert result["c_status"] == "blueprint_created_not_activated"
    assert result["activation_status"] == "blocked_until_final_review"
    assert result["continuity_source"] == "b_approved_reference_only"
    assert result["final_reconstruction_tests_created"] is False
    assert "C blueprint does not activate Selene C." in result["non_activation_boundaries"]
