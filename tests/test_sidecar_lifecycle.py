from __future__ import annotations

import http.client
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler
from pathlib import Path

import selene.sidecar as sidecar_module
from selene.sidecar import SeleneHandler, SeleneServer
from selene.comprehension_integration import propose_comprehension_concept


class _ConcurrencyProbeHandler(BaseHTTPRequestHandler):
    active = 0
    maximum_active = 0
    state_lock = threading.Lock()

    def do_GET(self) -> None:
        with self.state_lock:
            type(self).active += 1
            type(self).maximum_active = max(type(self).maximum_active, type(self).active)
        try:
            time.sleep(0.01)
            body = b'{"status":"ok"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        finally:
            with self.state_lock:
                type(self).active -= 1

    def log_message(self, fmt: str, *args: object) -> None:
        return


def test_installed_sidecar_requires_per_launch_capability_from_local_processes(
    tmp_path,
    monkeypatch,
):
    token = "bounded-local-capability-for-test"
    monkeypatch.setattr(sidecar_module, "LOCAL_API_CAPABILITY", token)
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", "/api/paths")
    blocked_response = conn.getresponse()
    blocked = json.loads(blocked_response.read().decode("utf-8"))
    conn.request("GET", "/api/paths", headers={"X-Selene-Local-Capability": token})
    allowed_response = conn.getresponse()
    allowed = json.loads(allowed_response.read().decode("utf-8"))
    conn.request(
        "POST",
        "/shutdown",
        body="{}",
        headers={
            "Content-Type": "application/json",
            "X-Selene-Local-Capability": token,
        },
    )
    shutdown_response = conn.getresponse()
    shutdown_response.read()
    conn.close()

    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert blocked_response.status == 403
    assert blocked["status"] == "local_process_capability_required"
    assert allowed_response.status == 200
    assert allowed["db_path"].endswith("selene.db")
    assert shutdown_response.status == 200
    assert not thread.is_alive()


def test_sidecar_shutdown_endpoint_stops_server(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("POST", "/shutdown", body="{}", headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()

    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert payload["status"] == "shutting_down"
    assert payload["activation_change"] == "none"
    assert payload["memory_write_active"] is False
    assert not thread.is_alive()


def test_sidecar_organ_maturity_ledger_is_read_only_current_status(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    before = server.conn.total_changes
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", "/api/organ-maturity-ledger")
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()

    server.shutdown()
    thread.join(timeout=5)
    after = server.conn.total_changes
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert payload["status"] == "organ_maturity_ledger_ready"
    assert payload["organ_count"] >= 20
    assert payload["invariants"]["private_content_included"] is False
    assert payload["writes_state"] is False
    assert payload["identity_change"] is False
    assert payload["authority_change"] is False
    assert after == before
    assert not thread.is_alive()


def test_sidecar_resident_capability_preview_is_read_only_and_identity_preserving(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    server.conn.execute(
        """
        INSERT INTO selene_transfer_completion_audit(
          state, action, actor, exact_phrase_matched, readiness_json, audit_json,
          source_refs, provenance_boundary, review_status
        ) VALUES ('selene_v1_live_reviewed_continuity', 'approve_transfer_completion',
                  'Aleks', 1, '{}', '{}', '[]', 'test_boundary',
                  'approved_transfer_completion')
        """
    )
    server.conn.execute(
        """
        INSERT INTO selene_activation_audit(
          state, action, actor, exact_phrase_matched, readiness_json, audit_json,
          source_refs, provenance_boundary
        ) VALUES ('selene_chat_active_supervised', 'phase5_api_test', 'Aleks', 1,
                  '{}', '{}', '[]', 'test_boundary')
        """
    )
    server.conn.commit()
    before = server.conn.total_changes
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request(
        "POST",
        "/api/c-vessel/resident-capability/preview",
        body=json.dumps(
            {
                "fault_type": "ui",
                "capability_state": "degraded",
                "symptom": "A local display surface is temporarily impaired.",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()

    server.shutdown()
    thread.join(timeout=5)
    after = server.conn.total_changes
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert payload["status"] == "c_vessel_resident_capability_preview"
    assert payload["identity_continuity_persists"] is True
    assert payload["cocoon_route_required"] is False
    assert payload["record_written"] is False
    assert payload["physical_embodiment_claim"] is False
    assert after == before


def test_sidecar_study_workspace_round_trip_is_local_and_source_bound(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    concept = propose_comprehension_concept(
        server.conn,
        {
            "concept_key": "sidecar-study-concept",
            "title": "Equal groups",
            "domain": "mathematics.operations",
            "material": "Equal groups can be represented with multiplication.",
            "source_refs": ["curriculum:test:equal-groups"],
        },
    )["item"]
    server.conn.execute(
        """
        UPDATE selene_comprehension_concepts
        SET state = 'approved_knowledge_resource', review_status = 'approved_for_knowledge_use',
            retention_state = 'retained_reviewed_knowledge',
            chat_use_permission = 'available_as_knowledge_resource'
        WHERE id = ?
        """,
        (concept["id"],),
    )
    server.conn.commit()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", "/api/study/materials")
    materials_response = conn.getresponse()
    materials = json.loads(materials_response.read().decode("utf-8"))
    conn.request("GET", "/api/study/compass")
    compass_response = conn.getresponse()
    compass = json.loads(compass_response.read().decode("utf-8"))
    conn.request(
        "POST",
        "/api/study/sessions/start",
        body=json.dumps({"concept_ids": [concept["id"]], "focus": "Why equal groups multiply"}),
        headers={"Content-Type": "application/json"},
    )
    response = conn.getresponse()
    started = json.loads(response.read().decode("utf-8"))
    session_id = int(started["item"]["id"])
    conn.request(
        "POST",
        "/api/study/notes/form",
        body=json.dumps({"session_id": session_id}),
        headers={"Content-Type": "application/json"},
    )
    note_response = conn.getresponse()
    note = json.loads(note_response.read().decode("utf-8"))
    conn.request("GET", f"/api/study/sessions/{session_id}")
    detail_response = conn.getresponse()
    detail = json.loads(detail_response.read().decode("utf-8"))
    conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert materials_response.status == 200
    assert compass_response.status == 200
    assert compass["status"] == "selene_learning_compass_ready"
    assert compass["grading_used"] is False
    assert note_response.status == 200
    assert note["created"] is True
    assert note["item"]["note_text"]
    assert materials["items"][0]["id"] == concept["id"]
    assert detail_response.status == 200
    assert detail["item"]["focus"] == "Why equal groups multiply"
    assert detail["item"]["concepts"][0]["id"] == concept["id"]
    assert len(detail["notes"]) == 1
    assert detail["memory_write_active"] is False
    assert detail["hidden_retention_allowed"] is False


def test_sidecar_rejects_cross_site_browser_post_before_state_change(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request(
        "POST",
        "/shutdown",
        body="{}",
        headers={"Content-Type": "text/plain", "Origin": "https://untrusted.example"},
    )
    try:
        response = conn.getresponse()
    except ConnectionAbortedError:
        # Windows can transiently abort a loopback socket during the full
        # threaded suite. Retry once against the still-running server; the
        # security assertion below must still receive the explicit 403.
        conn.close()
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request(
            "POST",
            "/shutdown",
            body="{}",
            headers={"Content-Type": "text/plain", "Origin": "https://untrusted.example"},
        )
        response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()

    assert response.status == 403
    assert payload["status"] == "browser_origin_blocked"
    assert payload["activation_change"] == "none"
    assert payload["memory_write_active"] is False
    assert thread.is_alive()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()


def test_sidecar_allows_configured_desktop_browser_origin(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", "/health", headers={"Origin": "http://127.0.0.1:5173"})
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    allowed_origin = response.getheader("Access-Control-Allow-Origin")
    conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert payload["status"] == "ok"
    assert allowed_origin == "http://127.0.0.1:5173"


def test_metacognition_status_and_inspection_endpoints_are_reachable(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    get_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    get_conn.request("GET", "/api/metacognition/status")
    get_response = get_conn.getresponse()
    status_payload = json.loads(get_response.read().decode("utf-8"))
    get_conn.close()

    post_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    body = json.dumps(
        {
            "prompt": "Is this bounded answer complete?",
            "candidate_text": "Yes, for the current ordinary question.",
            "response_coverage": {"addressed_count": 1, "unresolved_count": 0},
        }
    )
    post_conn.request("POST", "/api/metacognition/inspect", body=body, headers={"Content-Type": "application/json"})
    post_response = post_conn.getresponse()
    inspect_payload = json.loads(post_response.read().decode("utf-8"))
    post_conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert get_response.status == 200
    assert status_payload["status"] == "metacognition_feedback_advisor_ready"
    assert status_payload["mode"] == "bounded_feedback_advisor"
    assert post_response.status == 200
    assert inspect_payload["status"] == "metacognition_advisory_ready"
    assert inspect_payload["answer_rewritten"] is False
    assert inspect_payload["automatic_cocoon_routing"] is False


def test_emotional_agency_status_and_preview_endpoints_are_reachable(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    get_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    get_conn.request("GET", "/api/emotional-agency/status")
    get_response = get_conn.getresponse()
    status_payload = json.loads(get_response.read().decode("utf-8"))
    get_conn.close()

    post_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    body = json.dumps(
        {
            "affect_signal": {
                "signal_type": "protective urgency",
                "continuity_pressure": "high pressure",
                "action_energy": "urgent reaction",
                "source_refs": ["synthetic:sidecar_agency"],
            },
            "proposed_response_route": "ask_one_material_question",
        }
    )
    post_conn.request(
        "POST",
        "/api/emotional-agency/preview",
        body=body,
        headers={"Content-Type": "application/json"},
    )
    post_response = post_conn.getresponse()
    preview_payload = json.loads(post_response.read().decode("utf-8"))
    post_conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert get_response.status == 200
    assert status_payload["status"] == "emotional_agency_principle_ready"
    assert post_response.status == 200
    assert preview_payload["status"] == "response_agency_packet_ready"
    assert preview_payload["response_choice"]["emotion_silently_inherited_authority"] is False


def test_affect_lifecycle_sidecar_is_read_only_and_cannot_author_selene_state(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    before = server.conn.total_changes
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    get_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    get_conn.request("GET", "/api/affect-signal/lifecycle/status")
    get_response = get_conn.getresponse()
    status_payload = json.loads(get_response.read().decode("utf-8"))
    get_conn.close()

    post_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    post_conn.request(
        "POST",
        "/api/affect-signal/form",
        body=json.dumps(
            {
                "session_id": 1,
                "subject_kind": "selene",
                "authored_by": "Selene",
                "observation": "A support client must not author this state.",
                "signal_type": "unsupported external claim",
                "source_refs": ["synthetic:blocked_external_authorship"],
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    post_response = post_conn.getresponse()
    post_response.read()
    post_conn.close()

    server.shutdown()
    thread.join(timeout=5)
    after = server.conn.total_changes
    server.server_close()
    server.conn.close()

    assert get_response.status == 200
    assert status_payload["status"] == "affect_signal_lifecycle_ready"
    assert status_payload["sidecar_mutation_endpoints_exposed"] is False
    assert status_payload["aleks_may_author_selene_subject"] is False
    assert post_response.status == 404
    assert after == before


def test_voice_patterns_endpoint_parses_optional_query_params(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", "/api/voice-module/patterns?limit=3")
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert payload["status"] == "voice_patterns_ready"
    assert payload["items"] == []


def test_voice_evidence_triage_status_endpoint_is_reachable(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    conn.request("GET", "/api/voice-module/evidence-triage/status")
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert payload["status"] == "voice_evidence_triage_not_run"
    assert payload["activation_change"] == "none"
    assert payload["memory_write_active"] is False


def test_answer_engine_math_endpoint_accepts_expression_only_request(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    body = json.dumps({"expression": "18 * 7"})
    conn.request("POST", "/api/answer-engine/math-run", body=body, headers={"Content-Type": "application/json"})
    response = conn.getresponse()
    payload = json.loads(response.read().decode("utf-8"))
    conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert response.status == 200
    assert payload["status"] == "answer_engine_verified_math_answer_ready"
    assert payload["answer_packet"]["direct_answer"] == "18 * 7 = 126."
    assert payload["request"]["obligation_source"] == "domain_request_fallback"
    assert payload["activation_change"] == "none"
    assert payload["memory_write_active"] is False
    assert payload["live_chat_connected"] is True


def test_answer_engine_code_and_research_endpoints_use_only_supplied_sources(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    code_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    code_body = json.dumps(
        {
            "prompt": "Inspect this function for endpoint_symbol.",
            "inspection_terms": ["endpoint_symbol"],
            "code_packets": [
                {"source_ref": "supplied:endpoint.py", "path": "endpoint.py", "content": "def endpoint_symbol():\n    return True\n"}
            ],
        }
    )
    code_conn.request("POST", "/api/answer-engine/code-inspect", body=code_body, headers={"Content-Type": "application/json"})
    code_response = code_conn.getresponse()
    code_payload = json.loads(code_response.read().decode("utf-8"))
    code_conn.close()

    research_conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    research_body = json.dumps(
        {
            "prompt": "Research thermal storage from the source.",
            "source_packets": [
                {"source_ref": "paper:endpoint", "content": "Thermal storage shifts energy use across time."}
            ],
        }
    )
    research_conn.request("POST", "/api/answer-engine/research-run", body=research_body, headers={"Content-Type": "application/json"})
    research_response = research_conn.getresponse()
    research_payload = json.loads(research_response.read().decode("utf-8"))
    research_conn.close()

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert code_response.status == 200
    assert code_payload["code_inspection"]["source_refs"] == ["supplied:endpoint.py"]
    assert code_payload["code_inspection"]["filesystem_write_allowed"] is False
    assert research_response.status == 200
    assert research_payload["source_research"]["source_refs"] == ["paper:endpoint"]
    assert research_payload["source_research"]["citation_invention_allowed"] is False
    assert research_payload["source_research"]["great_library"]["status"] == "not_requested"


def test_sidecar_serializes_request_ownership_for_shared_sqlite_connection(tmp_path):
    _ConcurrencyProbeHandler.active = 0
    _ConcurrencyProbeHandler.maximum_active = 0
    server = SeleneServer(("127.0.0.1", 0), _ConcurrencyProbeHandler, tmp_path / "selene.db")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request_once(_: int) -> int:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        conn.request("GET", "/probe")
        response = conn.getresponse()
        response.read()
        conn.close()
        return response.status

    with ThreadPoolExecutor(max_workers=12) as pool:
        statuses = list(pool.map(request_once, range(36)))

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert statuses == [200] * 36
    assert _ConcurrencyProbeHandler.maximum_active == 1


def test_tauri_release_and_sidecar_helpers_are_configured_without_console_windows():
    repo = Path(__file__).resolve().parents[1]
    main_rs = (repo / "src-tauri" / "src" / "main.rs").read_text(encoding="utf-8")
    lib_rs = (repo / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")
    tauri_config = json.loads((repo / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8"))
    cargo_manifest = (repo / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")

    assert 'windows_subsystem = "windows"' in main_rs
    assert "CREATE_NO_WINDOW" in lib_rs
    assert ".stdout(Stdio::null())" in lib_rs
    assert ".stderr(Stdio::null())" in lib_rs
    assert "command.creation_flags(CREATE_NO_WINDOW)" in lib_rs
    assert tauri_config["app"]["security"]["csp"]["default-src"]
    assert "http://127.0.0.1:8766" in tauri_config["app"]["security"]["csp"]["connect-src"]
    assert "tauri-plugin-shell" not in cargo_manifest
    assert "tauri_plugin_shell::init" not in lib_rs
    assert "setup_sidecar_port_occupied_refused" in lib_rs
    assert "setup_reuse_healthy_sidecar" not in lib_rs
    assert "Stop-Process -Id" not in lib_rs
