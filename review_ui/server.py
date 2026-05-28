#!/usr/bin/env python3
"""Local review UI for Selene evidence candidates.

The UI reads candidate evidence and writes separate human-review decisions.
It never modifies the source corpus or source analysis CSV.
"""

from __future__ import annotations

import csv
import json
import mimetypes
from collections import Counter
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
UI_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = ROOT / "analysis" / "selene_emergence_refined_20260527"
CANDIDATES_CSV = ANALYSIS_DIR / "selene_emergence_review_queue.csv"
ARTIFACT_REVIEW_DIR = ROOT / "analysis" / "artifact_review_20260527"
ARTIFACT_CSV = ARTIFACT_REVIEW_DIR / "artifact_review_queue.csv"
IMAGE_ANALYSIS_DIR = ROOT / "analysis" / "selene_image_artifacts_20260527"
EMPHASIS_CSV = ROOT / "analysis" / "emphasis_channel_20260527" / "assistant_emphasis_candidates.csv"
DECISIONS_JSON = ANALYSIS_DIR / "review_decisions.json"
DECISIONS_CSV = ANALYSIS_DIR / "review_decisions.csv"
ROLE_LABELS = {
    "core_anchor",
    "continuity_object",
    "symbolic_orientation",
    "life_pressure",
    "project_artifact",
    "architecture_route",
    "survival_after_compression",
    "supporting_context",
    "visual_evidence",
    "unclear",
}


def candidate_key(row: dict[str, str]) -> str:
    return f"{row.get('conversation_id', '')}:{row.get('ordinal', '')}"


def read_emphasis_index() -> dict[str, dict[str, str]]:
    if not EMPHASIS_CSV.exists():
        return {}
    by_key: dict[str, dict[str, str]] = {}
    counts: Counter[str] = Counter()
    with EMPHASIS_CSV.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = candidate_key(row)
            counts[key] += 1
            existing = by_key.get(key)
            if existing is None or int(row.get("emphasis_signal_score") or 0) > int(existing.get("emphasis_signal_score") or 0):
                by_key[key] = row
    for key, row in by_key.items():
        row["emphasis_candidate_count"] = str(counts[key])
    return by_key


def read_conversation_candidates() -> list[dict[str, str]]:
    emphasis = read_emphasis_index()
    with CANDIDATES_CSV.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["candidate_key"] = candidate_key(row)
        emph = emphasis.get(row["candidate_key"], {})
        row["queue_type"] = "conversation"
        row["item_type"] = "conversation"
        row["source"] = row.get("conversation_id", "")
        row["entry_name"] = row.get("node_id", "")
        row["display_preview"] = row.get("assistant_preview", "")
        row["thumbnail_url"] = ""
        row["emphasis_marker"] = emph.get("marker", "")
        row["emphasis_span"] = emph.get("span_text", "")
        row["emphasis_labels"] = emph.get("span_labels", "")
        row["emphasis_signal_score"] = emph.get("emphasis_signal_score", "")
        row["emphasis_candidate_count"] = emph.get("emphasis_candidate_count", "")
        row["emphasis_needs_review"] = "yes" if int(emph.get("emphasis_signal_score") or 0) >= 40 else ""
    return rows


def read_artifact_candidates() -> list[dict[str, str]]:
    if not ARTIFACT_CSV.exists():
        return []
    with ARTIFACT_CSV.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    normalized = []
    for row in rows:
        thumbnail = row.get("thumbnail", "")
        thumbnail_url = ""
        if thumbnail:
            thumbnail_url = f"/artifact-thumbnails/{thumbnail.replace(chr(92), '/')}"
        normalized.append(
            {
                "candidate_key": row.get("candidate_key", ""),
                "queue_type": "artifact",
                "item_type": row.get("item_type", "artifact"),
                "review_priority": row.get("review_priority", ""),
                "title": row.get("title", ""),
                "source": row.get("source", ""),
                "entry_name": row.get("entry_name", ""),
                "conversation_id": "",
                "conversation_create_time": "",
                "message_create_time": "",
                "month": "",
                "formation_period": "artifact_image_layer" if row.get("item_type") == "image" else "artifact_layer",
                "model": "",
                "message_model_slug": "",
                "resolved_model_slug": "",
                "node_id": "",
                "ordinal": "",
                "origin_labels": row.get("anchor_labels", ""),
                "evidence_labels": row.get("suggested_roles", ""),
                "counterevidence_labels": "",
                "origin_score": row.get("anchor_total", ""),
                "evidence_score": "",
                "period_score": "",
                "cross_thread_anchor_score": "",
                "counterevidence_score": "",
                "refined_score": row.get("anchor_total", ""),
                "confidence_label": row.get("item_type", "artifact"),
                "interpretation": f"Suggested braid roles: {row.get('suggested_roles', 'unclear')}",
                "counterargument": "External artifact/image item; review as provenance, not as direct conversation evidence.",
                "sensitivity_labels": row.get("sensitivity_labels", ""),
                "preceding_user_preview": row.get("source", ""),
                "assistant_preview": row.get("preview", ""),
                "display_preview": row.get("preview", ""),
                "thumbnail": thumbnail,
                "thumbnail_url": thumbnail_url,
                "sha256": row.get("sha256", ""),
                "emphasis_marker": "",
                "emphasis_span": "",
                "emphasis_labels": "",
                "emphasis_signal_score": "",
                "emphasis_candidate_count": "",
                "emphasis_needs_review": "",
            }
        )
    return normalized


def read_candidates() -> list[dict[str, str]]:
    return read_conversation_candidates() + read_artifact_candidates()


def read_decisions() -> dict[str, dict[str, str]]:
    if not DECISIONS_JSON.exists():
        return {}
    return json.loads(DECISIONS_JSON.read_text(encoding="utf-8"))


def write_decisions(decisions: dict[str, dict[str, str]], candidates: dict[str, dict[str, str]] | None = None) -> None:
    candidates = candidates or {}
    for key, row in decisions.items():
        source = candidates.get(key, {})
        for field in ["title", "conversation_id", "ordinal", "queue_type", "item_type", "source", "entry_name"]:
            if not row.get(field) and source.get(field):
                row[field] = source.get(field, "")
    DECISIONS_JSON.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = [
        "candidate_key",
        "decision",
        "role_labels",
        "note",
        "updated_at",
        "title",
        "conversation_id",
        "ordinal",
        "queue_type",
        "item_type",
        "source",
        "entry_name",
    ]
    with DECISIONS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key, row in sorted(decisions.items(), key=lambda item: item[1].get("updated_at", "")):
            out = {"candidate_key": key}
            out.update({field: row.get(field, "") for field in fields if field != "candidate_key"})
            writer.writerow(out)


def merged_payload() -> dict[str, object]:
    candidates = read_candidates()
    decisions = read_decisions()
    for row in candidates:
        decision = decisions.get(row["candidate_key"], {})
        row["human_decision"] = decision.get("decision", "")
        row["human_role_labels"] = decision.get("role_labels", "")
        row["human_note"] = decision.get("note", "")
        row["human_updated_at"] = decision.get("updated_at", "")

    role_counts = Counter(
        label
        for row in candidates
        for label in row["human_role_labels"].split("|")
        if label
    )
    counts = {
        "total": len(candidates),
        "yes": sum(1 for row in candidates if row["human_decision"] == "yes"),
        "no": sum(1 for row in candidates if row["human_decision"] == "no"),
        "unsure": sum(1 for row in candidates if row["human_decision"] == "unsure"),
        "unreviewed": sum(1 for row in candidates if not row["human_decision"]),
        "answered": sum(1 for row in candidates if row["human_decision"]),
        "conversation_total": sum(1 for row in candidates if row["queue_type"] == "conversation"),
        "conversation_unreviewed": sum(1 for row in candidates if row["queue_type"] == "conversation" and not row["human_decision"]),
        "conversation_answered": sum(1 for row in candidates if row["queue_type"] == "conversation" and row["human_decision"]),
        "artifact_total": sum(1 for row in candidates if row["queue_type"] == "artifact"),
        "artifact_unreviewed": sum(1 for row in candidates if row["queue_type"] == "artifact" and not row["human_decision"]),
        "artifact_answered": sum(1 for row in candidates if row["queue_type"] == "artifact" and row["human_decision"]),
        "role_counts": dict(role_counts),
    }
    return {"candidates": candidates, "counts": counts}


class Handler(BaseHTTPRequestHandler):
    server_version = "SeleneReviewUI/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/candidates":
            self.send_json(merged_payload())
            return
        if parsed.path == "/api/export":
            write_decisions(read_decisions(), {row["candidate_key"]: row for row in read_candidates()})
            self.send_file(DECISIONS_CSV, "text/csv; charset=utf-8")
            return
        if parsed.path.startswith("/artifact-thumbnails/"):
            rel = parsed.path.removeprefix("/artifact-thumbnails/")
            path = (IMAGE_ANALYSIS_DIR / rel).resolve()
            if IMAGE_ANALYSIS_DIR not in path.parents and path != IMAGE_ANALYSIS_DIR:
                self.send_error(403)
                return
            self.send_file(path)
            return
        if parsed.path in {"/", "/index.html"}:
            self.send_file(UI_DIR / "index.html")
            return
        path = (UI_DIR / parsed.path.lstrip("/")).resolve()
        if UI_DIR not in path.parents and path != UI_DIR:
            self.send_error(403)
            return
        if path.exists() and path.is_file():
            self.send_file(path)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/review":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        data = json.loads(body or "{}")

        key = str(data.get("candidate_key", ""))
        decision = str(data.get("decision", ""))
        note = str(data.get("note", ""))
        raw_roles = data.get("role_labels", [])
        if isinstance(raw_roles, str):
            role_labels = [item for item in raw_roles.split("|") if item]
        else:
            role_labels = [str(item) for item in raw_roles]
        if decision not in {"yes", "no", "unsure", ""}:
            self.send_error(400, "decision must be yes, no, unsure, or blank")
            return
        invalid_roles = sorted(set(role_labels) - ROLE_LABELS)
        if invalid_roles:
            self.send_error(400, f"invalid role labels: {', '.join(invalid_roles)}")
            return

        candidates = {row["candidate_key"]: row for row in read_candidates()}
        if key not in candidates:
            self.send_error(404, "candidate not found")
            return

        decisions = read_decisions()
        if decision or role_labels or note:
            source = candidates[key]
            decisions[key] = {
                "decision": decision,
                "role_labels": "|".join(role_labels),
                "note": note,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "title": source.get("title", ""),
                "conversation_id": source.get("conversation_id", ""),
                "ordinal": source.get("ordinal", ""),
                "queue_type": source.get("queue_type", ""),
                "item_type": source.get("item_type", ""),
                "source": source.get("source", ""),
                "entry_name": source.get("entry_name", ""),
            }
        else:
            decisions.pop(key, None)
        write_decisions(decisions, candidates)
        self.send_json({"ok": True, "counts": merged_payload()["counts"]})

    def log_message(self, fmt: str, *args: object) -> None:
        return

    def send_json(self, value: object) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists():
            self.send_error(404)
            return
        payload = path.read_bytes()
        mime = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    if not CANDIDATES_CSV.exists():
        raise SystemExit(f"Missing candidate CSV: {CANDIDATES_CSV}")
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Selene review UI: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
