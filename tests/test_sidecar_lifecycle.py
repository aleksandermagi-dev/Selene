from __future__ import annotations

import http.client
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from selene.sidecar import SeleneHandler, SeleneServer


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

    assert 'windows_subsystem = "windows"' in main_rs
    assert "CREATE_NO_WINDOW" in lib_rs
    assert ".stdout(Stdio::null())" in lib_rs
    assert ".stderr(Stdio::null())" in lib_rs
    assert "command.creation_flags(CREATE_NO_WINDOW)" in lib_rs
    assert ".creation_flags(CREATE_NO_WINDOW)" in lib_rs
