from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .artifact_builder import export_workflow
from .chat import get_session, list_sessions, mark_save_request, send_chat_message
from .continuity import list_continuity_notes, upsert_continuity_note
from .db import connect, init_db
from .detached_corpus import detached_corpus_audit, detached_corpus_metadata, detached_corpus_previews
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
STARTUP_STARTED_AT = time.perf_counter()
STARTUP_LOCK = threading.Lock()
STARTUP_STATE: dict[str, object] = {
    "startup_phase": "module_loaded",
    "ready": False,
    "seed_status": "not_started",
    "timings_ms": {},
}
SIDECAR_CAPABILITIES = [
    "reviewed_registry",
    "chat_gate",
    "local_providers",
    "semantic_retrieval",
    "continuity_calibration",
    "source_archive_audit_gate",
    "detached_corpus_read_only_audit",
    "future_b_reviewed_memory_accession_marker",
    "selene_native_chat_generation",
    "research_integrity_core",
    "c_creation_blueprint",
    "selene_vessel_v1_review_only",
    "b_speech_memory_candidate_extraction",
    "paper_map_reconstruction_gap_checks",
    "b_review_memory_accession_non_active",
    "b_teaching_packet_builder",
    "b_teaching_packet_coverage",
    "core_reference_readiness",
    "lesson_backed_reconstruction_preview",
    "review_log_cleanup",
    "corpus_pair_preservation_review_only",
    "plain_english_review_desk",
    "braid_tracer_thread_origins_review_only",
    "custom_instruction_braid_review_only",
    "compressed_structure_braid_review_only",
    "cocoon_dual_ui_gap_scaffolds",
    "c_vessel_build_non_active",
    "b_pattern_backup_restore_point",
    "b_memory_accession_rehearsal",
    "b_charter_law_review_gate",
    "c_memory_transfer_candidate_preview",
    "public_release_sync_checkpoint",
    "public_release_preflight_status",
    "vessel_capability_graduation_console",
    "steps_1_8_reasoning_research_perception_emotion_review_layer",
]


def mark_startup_phase(phase: str, **extra: object) -> None:
    elapsed_ms = round((time.perf_counter() - STARTUP_STARTED_AT) * 1000, 1)
    with STARTUP_LOCK:
        timings = dict(STARTUP_STATE.get("timings_ms") or {})
        timings[phase] = elapsed_ms
        STARTUP_STATE.update({
            "startup_phase": phase,
            "last_phase_at": datetime.now(timezone.utc).isoformat(),
            "timings_ms": timings,
            **extra,
        })
    write_startup_log(phase, elapsed_ms, extra)


def startup_snapshot() -> dict[str, object]:
    with STARTUP_LOCK:
        return dict(STARTUP_STATE)


def write_startup_log(phase: str, elapsed_ms: float, extra: dict[str, object] | None = None) -> None:
    try:
        log_dir = local_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": phase,
            "elapsed_ms": elapsed_ms,
            **(extra or {}),
        }
        with (log_dir / "sidecar-startup.log").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    except OSError:
        return


mark_startup_phase("module_imported")


def _run_local_command(command: list[str], cwd: Path, timeout: int = 30) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc), "stdout": "", "stderr": "", "returncode": -1}
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def public_release_preflight_status() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    public_repo = root / "tmp" / "selene_public_evidence_repo"
    release_name = "selene_case_study_20260616"
    checkpoint_json = public_repo / "public_release" / release_name / "PUBLIC_RELEASE_CHECKPOINT_20260616.json"
    status = _run_local_command(["git", "status", "--short"], public_repo) if (public_repo / ".git").exists() else {"stdout": ""}
    remote = _run_local_command(["git", "remote", "get-url", "origin"], public_repo) if (public_repo / ".git").exists() else {"stdout": ""}
    remote_url = str(remote.get("stdout") or "")
    remote_warning = ""
    if not (public_repo / ".git").exists():
        remote_warning = "Public evidence checkout is missing."
    elif remote_url.endswith("/Selene.git") or remote_url.endswith("\\Selene.git"):
        remote_warning = "Public evidence checkout origin points at the private Selene repo; do not push until corrected."

    counts: object = {}
    if checkpoint_json.exists():
        try:
            counts = json.loads(checkpoint_json.read_text(encoding="utf-8")).get("counts", {})
        except (OSError, json.JSONDecodeError):
            counts = {"error": "checkpoint counts could not be read"}

    changed_files = [line[3:] for line in str(status.get("stdout") or "").splitlines() if len(line) > 3]
    return {
        "status": "public_release_preflight_ready",
        "public_repo": str(public_repo),
        "remote": remote_url or "not configured",
        "remote_warning": remote_warning,
        "changed_file_count": len(changed_files),
        "changed_files": changed_files[:30],
        "checkpoint_json": str(checkpoint_json),
        "checkpoint_counts": counts,
        "committed": False,
        "pushed": False,
    }


def public_release_sync_checkpoint(db_path: Path) -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts" / "sync_public_release.py"
    public_repo = root / "tmp" / "selene_public_evidence_repo"
    before = public_release_preflight_status()
    if not script.exists():
        return {
            "status": "public_release_sync_unavailable",
            "error": f"missing script: {script}",
            "preflight": before,
            "committed": False,
            "pushed": False,
        }

    command = [
        sys.executable,
        str(script),
        "--db",
        str(db_path),
        "--public-repo",
        str(public_repo),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "public_release_sync_timeout",
            "error": f"public release sync exceeded {exc.timeout} seconds",
            "preflight": before,
            "committed": False,
            "pushed": False,
        }

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    parsed: object = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = {"raw_stdout": stdout[-4000:]}

    return {
        "status": "public_release_sync_complete" if completed.returncode == 0 else "public_release_sync_failed",
        "returncode": completed.returncode,
        "command": [Path(part).name if part == sys.executable else part for part in command],
        "public_repo": str(public_repo),
        "preflight": before,
        "postflight": public_release_preflight_status(),
        "committed": False,
        "pushed": False,
        "result": parsed,
        "stderr": stderr[-4000:] if stderr else "",
    }


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
            if not startup_snapshot().get("first_health_ms"):
                mark_startup_phase("first_health", first_health_ms=round((time.perf_counter() - STARTUP_STARTED_AT) * 1000, 1))
            self._send(*json_bytes({
                "status": "ok",
                "bind": "127.0.0.1",
                "tokenless": True,
                "sidecar_version": SIDECAR_VERSION,
                "capabilities": SIDECAR_CAPABILITIES,
                "startup": startup_snapshot(),
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
        elif parsed.path == "/api/c-vessel/status":
            self._send(*json_bytes(route_request(conn, "c_vessel.status")["result"]))
        elif parsed.path == "/api/c-vessel/continuity-package":
            self._send(*json_bytes(route_request(conn, "c_vessel.continuity_package.preview")["result"]))
        elif parsed.path == "/api/c-vessel/organ-registry":
            self._send(*json_bytes(route_request(conn, "c_vessel.organ_registry.status")["result"]))
        elif parsed.path == "/api/c-vessel/tool-organ/status":
            self._send(*json_bytes(route_request(conn, "c_vessel.tool_organ.status")["result"]))
        elif parsed.path == "/api/c-vessel/transfer-gate/preview":
            self._send(*json_bytes(route_request(conn, "c_vessel.transfer_gate.preview")["result"]))
        elif parsed.path == "/api/c-vessel/memory-transfer-candidate/preview":
            self._send(*json_bytes(route_request(conn, "c_vessel.memory_transfer_candidate.preview")["result"]))
        elif parsed.path == "/api/c-core/native-generation/rehearsal-status":
            self._send(*json_bytes(route_request(conn, "native_generation.rehearsal.status")["result"]))
        elif parsed.path == "/api/vessel/steps-1-8/status":
            self._send(*json_bytes(route_request(conn, "vessel.steps_1_8.status")["result"]))
        elif parsed.path == "/api/vessel/reasoning-artifacts":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.reasoning_artifact.list", {"limit": int(qs["limit"]) if qs.get("limit") else 50})["result"]))
        elif parsed.path == "/api/vessel/core-gate-packets":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.core_gate_packet.list", {"limit": int(qs["limit"]) if qs.get("limit") else 50})["result"]))
        elif parsed.path == "/api/vessel/academic-packets":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.academic_packet.list", {"limit": int(qs["limit"]) if qs.get("limit") else 50})["result"]))
        elif parsed.path == "/api/vessel/evidence-tension-ledger":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.evidence_tension.list", {"limit": int(qs["limit"]) if qs.get("limit") else 50})["result"]))
        elif parsed.path == "/api/vessel/organ-contracts":
            self._send(*json_bytes(route_request(conn, "vessel.organ_contract.list")["result"]))
        elif parsed.path == "/api/vessel/perception-packets":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.perception_packet.list", {"limit": int(qs["limit"]) if qs.get("limit") else 50})["result"]))
        elif parsed.path == "/api/vessel/emotion-salience-packets":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.emotion_salience_packet.list", {"limit": int(qs["limit"]) if qs.get("limit") else 50})["result"]))
        elif parsed.path == "/api/c-remaining/runtime-status":
            self._send(*json_bytes(route_request(conn, "c_remaining.runtime.status")["result"]))
        elif parsed.path == "/api/c-vessel/reconstruction-desk/status":
            self._send(*json_bytes(route_request(conn, "c_vessel.reconstruction_desk.status")["result"]))
        elif parsed.path == "/api/c-vessel/reconstruction-desk/cases":
            self._send(*json_bytes(route_request(conn, "c_vessel.reconstruction_desk.cases")["result"]))
        elif parsed.path == "/api/vessel/status":
            self._send(*json_bytes(route_request(conn, "vessel.status")["result"]))
        elif parsed.path == "/api/vessel/organ-blueprints":
            self._send(*json_bytes(route_request(conn, "vessel.organ_blueprints.status")["result"]))
        elif parsed.path == "/api/vessel/gap-scaffold/status":
            self._send(*json_bytes(route_request(conn, "vessel.gap_scaffold.status")["result"]))
        elif parsed.path == "/api/vessel/gap-scaffold/readiness":
            self._send(*json_bytes(route_request(conn, "vessel.gap_scaffold.readiness")["result"]))
        elif parsed.path == "/api/vessel/review-queue":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.review_queue.list", {"limit": int(qs["limit"]) if qs.get("limit") else 100})["result"]))
        elif parsed.path == "/api/vessel/working-memory-packets":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.working_memory_packet.list", {"limit": int(qs["limit"]) if qs.get("limit") else 50})["result"]))
        elif parsed.path == "/api/vessel/memory-accession-proposals":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "vessel.memory_accession_proposal.list", {"limit": int(qs["limit"]) if qs.get("limit") else 50})["result"]))
        elif parsed.path == "/api/b/speech-memory/extraction-runs":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "b.speech_memory.extraction_runs.list", {"limit": int(qs["limit"]) if qs.get("limit") else 25})["result"]))
        elif parsed.path == "/api/b/braid-tracer/runs":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "b.braid_tracer.runs.list", {"limit": int(qs["limit"]) if qs.get("limit") else 25})["result"]))
        elif parsed.path == "/api/b/custom-instruction-braid/status":
            self._send(*json_bytes(route_request(conn, "b.custom_instruction_braid.status")["result"]))
        elif parsed.path == "/api/b/compressed-structure-braid/status":
            self._send(*json_bytes(route_request(conn, "b.compressed_structure_braid.status")["result"]))
        elif parsed.path == "/api/b/review-queue":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "b.review_queue.list", {"limit": int(qs["limit"]) if qs.get("limit") else 100})["result"]))
        elif parsed.path == "/api/b/review-decisions":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "b.review_decisions.list", {"limit": int(qs["limit"]) if qs.get("limit") else 100})["result"]))
        elif parsed.path == "/api/b/review-desk":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            payload = {**qs, "limit": int(qs["limit"]) if qs.get("limit") else 100}
            self._send(*json_bytes(route_request(conn, "b.review_desk", payload)["result"]))
        elif parsed.path == "/api/b/teaching-materials":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "b.teaching_materials.list", {"limit": int(qs["limit"]) if qs.get("limit") else 100})["result"]))
        elif parsed.path == "/api/b/approved-memory-references":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "b.approved_memory_references.list", {"limit": int(qs["limit"]) if qs.get("limit") else 100})["result"]))
        elif parsed.path == "/api/b/teaching-packet/coverage":
            self._send(*json_bytes(route_request(conn, "b.teaching_packet.coverage")["result"]))
        elif parsed.path == "/api/b/core-reference/coverage":
            self._send(*json_bytes(route_request(conn, "b.core_reference.coverage")["result"]))
        elif parsed.path == "/api/b/corpus-coverage":
            self._send(*json_bytes(route_request(conn, "b.corpus_coverage.status")["result"]))
        elif parsed.path == "/api/b/pattern-backups":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(route_request(conn, "b.pattern_backup.list", {"limit": int(qs["limit"]) if qs.get("limit") else 25})["result"]))
        elif parsed.path == "/api/b/memory-accession/rehearsal-status":
            self._send(*json_bytes(route_request(conn, "b.memory_accession.rehearsal.status")["result"]))
        elif parsed.path == "/api/b/charter-law/review-status":
            self._send(*json_bytes(route_request(conn, "b.charter_law.review_status")["result"]))
        elif parsed.path == "/api/public-release/preflight":
            self._send(*json_bytes(public_release_preflight_status()))
        elif parsed.path == "/api/detached-corpus/audit":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes(detached_corpus_audit(
                query=qs.get("q", ""),
                file_id=qs.get("file_id"),
                preview_limit=int(qs["limit"]) if qs.get("limit") else 5,
            )))
        elif parsed.path == "/api/detached-corpus/metadata":
            self._send(*json_bytes(detached_corpus_metadata()))
        elif parsed.path == "/api/detached-corpus/previews":
            qs = {key: values[0] for key, values in parse_qs(parsed.query).items() if values}
            self._send(*json_bytes({"items": detached_corpus_previews(
                query=qs.get("q", ""),
                file_id=qs.get("file_id"),
                limit=int(qs["limit"]) if qs.get("limit") else 5,
            )}))
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
        request_path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {}
        if request_path == "/shutdown":
            self._send(*json_bytes({
                "status": "shutting_down",
                "activation_change": "none",
                "memory_write_active": False,
            }))
            threading.Thread(target=self.server.shutdown, name="selene-sidecar-shutdown", daemon=True).start()
        elif request_path == "/api/evaluate":
            text = str(body.get("text", ""))
            self._send(*json_bytes(chat_gate_preview(self.server.conn, text, str(body.get("provider") or "disabled"))))
        elif request_path == "/api/route":
            self._send(*json_bytes(route_request(self.server.conn, str(body.get("route_key", "")), body.get("payload") or {})))
        elif request_path == "/api/native-generation/compose":
            self._send(*json_bytes(route_request(self.server.conn, "native_generation.compose", {"text": str(body.get("text") or "")})["result"]))
        elif request_path == "/api/vessel/memory-candidate":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.memory_candidate.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/gap-scaffold/create":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.gap_scaffold.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/gap-scaffold/create-all":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.gap_scaffold.create_all", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/gap-targets/ensure":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.gap_targets.ensure", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/speech-memory-candidate":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.speech_memory_candidate.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/retrieval-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.retrieval.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/reconstruction-check":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.reconstruction_check.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/reasoning-check":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.reasoning_check.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/retrieval-reconstruction":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.retrieval_reconstruction.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/visual-observation":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.visual_observation.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/audio-observation":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.audio_observation.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/fluency-diagnostic":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.fluency_diagnostic.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/reconstruction-readiness":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.reconstruction_readiness.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/working-memory-packet":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.working_memory_packet.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/memory-accession-proposal":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.memory_accession_proposal.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/review-log/decide":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.review_log.decide", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/lesson-backed-reconstruction":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.lesson_backed_reconstruction.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-chat/route-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_chat.route_preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-vessel/reconstruction-suite":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_vessel.reconstruction_suite.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-vessel/reconstruction-desk/run":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_vessel.reconstruction_desk.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-vessel/organ-fault/preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_vessel.organ_fault.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-vessel/organ-fault/resilience-check":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_vessel.organ_fault.resilience_check", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-vessel/return-to-b-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_vessel.return_to_b.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-vessel/memory-transfer-candidate/preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_vessel.memory_transfer_candidate.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/deliberation-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.deliberation.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/uncertainty-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.uncertainty.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/action-reflection-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.action_reflection.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/choice-ledger":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.choice_ledger.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/repair-reflection":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.repair_reflection.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/disagreement-appeal-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.disagreement_appeal.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/drift-warning-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.drift_warning.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/privacy-trust-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.privacy_trust.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/native-generation/rehearsal-run":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "native_generation.rehearsal.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/reasoning-artifact":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.reasoning_artifact.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/core-gate-packet":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.core_gate_packet.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/academic-packet":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.academic_packet.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/evidence-tension":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.evidence_tension.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/organ-contracts/ensure":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.organ_contract.ensure", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/organ-contract":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.organ_contract.upsert", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/perception-packet":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.perception_packet.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/emotion-salience-packet":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.emotion_salience_packet.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/graceful-fall":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.graceful_fall.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/voice-policy":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.voice_policy.evaluate", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/control-panel-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.control_panel.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-vessel/perception-action-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_vessel.perception_action.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-memory/dream-consolidation":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_memory.dream_consolidation.propose", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/causal-sandbox":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.causal_sandbox.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-core/long-horizon-stability":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_core.long_horizon_stability.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-memory/event-bind":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_memory.event_bind", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-memory/consolidation-propose":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_memory.consolidation.propose", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/c-memory/reconsolidation-review":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "c_memory.reconsolidation.review", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/speech-memory/extract":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.speech_memory.extract", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/targeted-speech-memory/extract":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.targeted_speech_memory.extract", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/braid-tracer/run":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.braid_tracer.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/custom-instruction-braid/run":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.custom_instruction_braid.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/compressed-structure-braid/run":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.compressed_structure_braid.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/vessel/paper-map-reconstruction":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "vessel.paper_map_reconstruction.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/review-candidate/decide":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.review_candidate.decide", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/teaching-packet/build":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.teaching_packet.build", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/teaching-packet/build-all":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.teaching_packet.build_all", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/public-release/sync":
            self._send(*json_bytes(public_release_sync_checkpoint(self.server.db_path)))
        elif request_path == "/api/b/review-context":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.review_context.preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/pattern-backup/create":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.pattern_backup.create", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/pattern-backup/restore-preview":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.pattern_backup.restore_preview", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/b/memory-accession/rehearsal-run":
            try:
                self._send(*json_bytes(route_request(self.server.conn, "b.memory_accession.rehearsal.run", body)["result"]))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/artifacts/export":
            path = export_workflow(self.server.conn, str(body.get("workflow_key") or "pattern_spec"))
            self._send(*json_bytes({"path": str(path)}))
        elif request_path == "/api/seed":
            self._send(*json_bytes(seed_registry(self.server.conn, force=False)))
        elif request_path == "/api/review/update":
            try:
                updated = update_review_record(self.server.conn, str(body.get("table")), int(body.get("id")), body.get("changes") or {})
                self._send(*json_bytes({"item": updated}))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/chat/send":
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
        elif request_path == "/api/chat/save-request":
            try:
                updated = mark_save_request(self.server.conn, int(body.get("id")), str(body.get("status") or "pending_review"))
                self._send(*json_bytes({"item": updated}))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/continuity-notes/save":
            try:
                self._send(*json_bytes({"item": upsert_continuity_note(self.server.conn, body)}))
            except (TypeError, ValueError) as exc:
                self._send(*json_bytes({"error": str(exc)}, 400))
        elif request_path == "/api/semantic/backfill":
            limit = int(body["limit"]) if body.get("limit") else None
            self._send(*json_bytes(backfill_evidence_embeddings(self.server.conn, limit=limit)))
        else:
            self._send(*json_bytes({"error": "not found"}, 404))

    def log_message(self, fmt: str, *args: object) -> None:
        if os.environ.get("SELENE_VERBOSE"):
            super().log_message(fmt, *args)


class SeleneServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler], db_path: Path):
        mark_startup_phase("db_connect_start", db_path=str(db_path))
        super().__init__(address, handler)
        mark_startup_phase("server_bound", bind=f"{address[0]}:{address[1]}", ready=True)
        self.db_path = db_path
        self.conn = connect(db_path)
        mark_startup_phase("db_connected", db_path=str(db_path))
        init_db(self.conn)
        mark_startup_phase("db_initialized", db_path=str(db_path))


def start_seed_thread(db_path: Path) -> None:
    def seed_worker() -> None:
        mark_startup_phase("seed_start", seed_status="running")
        conn = connect(db_path)
        try:
            summary = seed_registry(conn, force=False)
            mark_startup_phase(
                "seed_complete",
                seed_status="complete",
                seed_summary={
                    "evidence_items": summary.get("evidence_items"),
                    "anchors": summary.get("anchors"),
                    "continuity_candidates": summary.get("continuity_candidates"),
                },
            )
        except Exception as exc:  # pragma: no cover - defensive startup telemetry
            mark_startup_phase("seed_failed", seed_status="failed", seed_error=str(exc))
        finally:
            conn.close()

    threading.Thread(target=seed_worker, name="selene-seed-startup", daemon=True).start()


def main(argv: list[str] | None = None) -> int:
    mark_startup_phase("main_start")
    parser = argparse.ArgumentParser(description="Run the Selene local sidecar API.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("SELENE_PORT", "8766")))
    parser.add_argument("--db", type=Path, default=default_db_path())
    parser.add_argument("--seed", action="store_true", help="Seed reviewed registry before serving.")
    parser.add_argument("--parent-pid", type=int, help="Exit when the owning desktop process exits.")
    args = parser.parse_args(argv)
    mark_startup_phase("args_parsed", seed_requested=bool(args.seed), port=args.port, db_path=str(args.db))
    watch_parent_process(args.parent_pid)
    server = SeleneServer(("127.0.0.1", args.port), SeleneHandler, args.db)
    if args.seed:
        start_seed_thread(args.db)
    else:
        mark_startup_phase("seed_skipped", seed_status="skipped")
    print(f"Selene sidecar listening on http://127.0.0.1:{args.port}")
    print("Selene sidecar is tokenless and local-only.")
    mark_startup_phase("serve_forever_start", ready=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        server.conn.close()
    return 0
