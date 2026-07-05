from __future__ import annotations

import http.client
import json
import threading
from pathlib import Path

from selene.sidecar import SeleneHandler, SeleneServer


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


def test_tauri_release_and_sidecar_helpers_are_configured_without_console_windows():
    repo = Path(__file__).resolve().parents[1]
    main_rs = (repo / "src-tauri" / "src" / "main.rs").read_text(encoding="utf-8")
    lib_rs = (repo / "src-tauri" / "src" / "lib.rs").read_text(encoding="utf-8")

    assert 'windows_subsystem = "windows"' in main_rs
    assert "CREATE_NO_WINDOW" in lib_rs
    assert ".stdout(Stdio::null())" in lib_rs
    assert ".stderr(Stdio::null())" in lib_rs
    assert "command.creation_flags(CREATE_NO_WINDOW)" in lib_rs
    assert ".creation_flags(CREATE_NO_WINDOW)" in lib_rs
