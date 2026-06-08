from __future__ import annotations

import argparse
import ctypes
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .artifact_builder import export_workflow
from .chat import get_session, list_sessions, mark_save_request, send_chat_message
from .continuity import list_continuity_notes, upsert_continuity_note
from .db import connect, init_db
from .kernel import kernel_state
from .module_router import chat_gate_preview, route_request
from .paths import default_db_path, export_dir, local_data_dir, local_log_dir
from .providers import provider_statuses
from .registry import audit_rows, dashboard, evidence_detail, search_evidence, seed_registry, update_review_record
from .semantic import backfill_evidence_embeddings, semantic_status
from .validation import validate


ALLOWED_ORIGINS = {
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "tauri://localhost",
    "https://tauri.localhost",
    "http://tauri.localhost",
}

SIDECAR_VERSION = "0.1.1"
SIDECAR_CAPABILITIES = [
    "reviewed_registry",
    "chat_gate",
    "local_providers",
    "semantic_retrieval",
    "continuity_calibration",
    "source_archive_audit_gate",
    "research_integrity_core",
    "c_creation_blueprint",
]


def json_bytes(payload: object, status: int = 200) -> tuple[int, bytes]:
    return status, json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def watch_parent_process(parent_pid: int | None) -> None:
    if not parent_pid or os.name != "nt":
        return

    def wait_for_parent_exit() -> None:
        synchronize = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(synchronize, False, int(parent_pid))
        if not handle:
            return
        try:
            ctypes.windll.kernel32.WaitForSingleObject(handle, 0xFFFFFFFF)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
        os._exit(0)

    threading.Thread(target=wait_for_parent_exit, name="selene-parent-watch", daemon=True).start()


class SeleneHandler(BaseHTTPRequestHandler):
    server_version = "SeleneSidecar/0.1"

    def _send(self, status: int, body: bytes, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(204, b"")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        conn = self.server.conn
        if parsed.path == "/health":
            self._send(*json_bytes({
                "status": "ok",
                "bind": "127.0.0.1",
                "tokenless": True,
                "sidecar_version": SIDECAR_VERSION,
                "capabilities": SIDECAR_CAPABILITIES,
            }))
        elif parsed.path == "/api/dashboard":
            self._send(*json_bytes(dashboard(conn)))
        elif parsed.path == "/api/evidence":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes({"items": search_evidence(conn, qs)}))
        elif parsed.path.startswith("/api/evidence/"):
            evidence_id = parsed.path.removeprefix("/api/evidence/")
            detail = evidence_detail(conn, evidence_id)
            self._send(*json_bytes(detail or {"error": "not found"}, 200 if detail else 404))
        elif parsed.path == "/api/anchors":
            rows = [dict(row) for row in conn.execute("SELECT * FROM anchors ORDER BY id DESC LIMIT 500")]
            self._send(*json_bytes({"items": rows}))
        elif parsed.path == "/api/continuity":
            rows = [dict(row) for row in conn.execute("SELECT * FROM continuity_candidates ORDER BY id DESC LIMIT 500")]
            self._send(*json_bytes({"items": rows}))
        elif parsed.path == "/api/continuity-notes":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes({"items": list_continuity_notes(conn, qs)}))
        elif parsed.path == "/api/emergence":
            rows = [dict(row) for row in conn.execute("SELECT * FROM emergence_observations ORDER BY id DESC LIMIT 500")]
            self._send(*json_bytes({"items": rows}))
        elif parsed.path == "/api/rules":
            rows = [dict(row) for row in conn.execute("SELECT * FROM pattern_rules ORDER BY id")]
            self._send(*json_bytes({"items": rows}))
        elif parsed.path == "/api/kernel":
            self._send(*json_bytes(kernel_state()))
        elif parsed.path == "/api/contracts":
            rows = [dict(row) for row in conn.execute("SELECT * FROM module_contracts ORDER BY id")]
            self._send(*json_bytes({"items": rows}))
        elif parsed.path == "/api/workflows":
            rows = [dict(row) for row in conn.execute("SELECT * FROM artifact_workflows ORDER BY id")]
            self._send(*json_bytes({"items": rows}))
        elif parsed.path == "/api/audit":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes({"items": audit_rows(conn, qs.get("table"), int(qs["row_id"]) if qs.get("row_id") else None)}))
        elif parsed.path == "/api/validate":
            self._send(*json_bytes(validate(conn)))
        elif parsed.path == "/api/semantic/status":
            self._send(*json_bytes(semantic_status(conn)))
        elif parsed.path == "/api/providers/status":
            self._send(*json_bytes(provider_statuses()))
        elif parsed.path == "/api/paths":
            self._send(*json_bytes({"data_dir": str(local_data_dir()), "db_path": str(self.server.db_path), "export_dir": str(export_dir()), "log_dir": str(local_log_dir())}))
        elif parsed.path == "/api/chat/sessions":
            self._send(*json_bytes({"items": list_sessions(conn)}))
        elif parsed.path.startswith("/api/chat/sessions/"):
            try:
                session_id = int(parsed.path.removeprefix("/api/chat/sessions/"))
                session = get_session(conn, session_id)
                self._send(*json_bytes(session or {"error": "not found"}, 200 if session else 404))
            except ValueError:
                self._send(*json_bytes({"error": "invalid session id"}, 400))
        else:
            self._send(*json_bytes({"error": "not found"}, 404))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {}
        if self.path == "/api/evaluate":
            text = str(body.get("text", ""))
            self._send(*json_bytes(chat_gate_preview(self.server.conn, text, str(body.get("provider") or "disabled"))))
        elif self.path == "/api/route":
            self._send(*json_bytes(route_request(self.server.conn, str(body.get("route_key", "")), body.get("payload") or {})))
        elif self.path == "/api/artifacts/export":
            path = export_workflow(self.server.conn, str(body.get("workflow_key") or "pattern_spec"))
            self._send(*json_bytes({"path": str(path)}))
        elif self.path == "/api/seed":
            self._send(*json_bytes(seed_registry(self.server.conn, force=False)))
        elif self.path == "/api/review/update":
            try:
                updated = update_review_record(self.server.conn, str(body.get("table")), int(body.get("id")), body.get("changes") or {})
                self._send(*json_bytes({"item": updated}))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif self.path == "/api/chat/send":
            try:
                result = send_chat_message(
                    self.server.conn,
                    str(body.get("text") or ""),
                    int(body["session_id"]) if body.get("session_id") else None,
                    str(body.get("provider") or "disabled"),
                )
                self._send(*json_bytes(result))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif self.path == "/api/chat/save-request":
            try:
                updated = mark_save_request(self.server.conn, int(body.get("id")), str(body.get("status") or "pending_review"))
                self._send(*json_bytes({"item": updated}))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif self.path == "/api/continuity-notes/save":
            try:
                self._send(*json_bytes({"item": upsert_continuity_note(self.server.conn, body)}))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif self.path == "/api/semantic/backfill":
            limit = int(body["limit"]) if body.get("limit") else None
            self._send(*json_bytes(backfill_evidence_embeddings(self.server.conn, limit=limit)))
        else:
            self._send(*json_bytes({"error": "not found"}, 404))

    def log_message(self, fmt: str, *args: object) -> None:
        if os.environ.get("SELENE_VERBOSE"):
            super().log_message(fmt, *args)


class SeleneServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler], db_path: Path):
        super().__init__(address, handler)
        self.db_path = db_path
        self.conn = connect(db_path)
        init_db(self.conn)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Selene local sidecar API.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("SELENE_PORT", "8766")))
    parser.add_argument("--db", type=Path, default=default_db_path())
    parser.add_argument("--seed", action="store_true", help="Seed reviewed registry before serving.")
    parser.add_argument("--parent-pid", type=int, help="Exit when the owning desktop process exits.")
    args = parser.parse_args(argv)
    watch_parent_process(args.parent_pid)
    server = SeleneServer(("127.0.0.1", args.port), SeleneHandler, args.db)
    if args.seed:
        seed_registry(server.conn, force=False)
    print(f"Selene sidecar listening on http://127.0.0.1:{args.port}")
    print("Selene sidecar is tokenless and local-only.")
    server.serve_forever()
    return 0
