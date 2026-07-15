from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .registry import truncate


LOCAL_CODE_BOUNDARY = (
    "local_code_inspection_explicit_supplied_or_approved_workspace_files_only_"
    "read_only_no_scan_write_execution_memory_identity_law_or_authority_change"
)

MAX_FILES = 8
MAX_FILE_BYTES = 200_000
MAX_TOTAL_BYTES = 800_000
MAX_MATCHES = 60

ALLOWED_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".rs",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}

BLOCKED_NAMES = {".env", "credentials.json", "secrets.json"}
BLOCKED_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}

_TERM_STOPWORDS = {
    "and",
    "code",
    "does",
    "file",
    "files",
    "find",
    "for",
    "function",
    "how",
    "inspect",
    "inspection",
    "into",
    "local",
    "source",
    "that",
    "the",
    "this",
    "what",
    "where",
    "which",
    "with",
}


def local_code_inspection_status() -> dict[str, Any]:
    return {
        "status": "local_code_inspection_ready",
        "version": "v1_explicit_sources_static_observation",
        "accepted_inputs": ["attributed inline code_packets", "exact approved_workspace_files under PROJECT_ROOT"],
        "max_files": MAX_FILES,
        "max_file_bytes": MAX_FILE_BYTES,
        "max_total_bytes": MAX_TOTAL_BYTES,
        "directory_scan_allowed": False,
        "glob_allowed": False,
        "code_execution_allowed": False,
        "filesystem_write_allowed": False,
        "arbitrary_workspace_root_allowed": False,
        "observation_interpretation_separated": True,
        "citations_required": True,
        "review_status": "status_only",
        "provenance_boundary": LOCAL_CODE_BOUNDARY,
    }


def inspect_local_code(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 3000).strip()
    terms = _inspection_terms(payload.get("inspection_terms"), prompt)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    total_bytes = 0
    seen_refs: set[str] = set()

    for index, packet in enumerate((payload.get("code_packets") or [])[:MAX_FILES]):
        normalized, reason = _inline_packet(packet, index)
        if reason:
            rejected.append({"source": f"code_packet:{index + 1}", "reason": reason})
            continue
        assert normalized is not None
        if normalized["source_ref"] in seen_refs:
            rejected.append({"source": normalized["path"], "reason": "duplicate source_ref"})
            continue
        size = len(normalized["content"].encode("utf-8"))
        if total_bytes + size > MAX_TOTAL_BYTES:
            rejected.append({"source": normalized["path"], "reason": "total inspection byte limit exceeded"})
            continue
        total_bytes += size
        seen_refs.add(normalized["source_ref"])
        accepted.append(normalized)

    remaining = max(0, MAX_FILES - len(accepted))
    for index, item in enumerate((payload.get("approved_workspace_files") or [])[:remaining]):
        normalized, reason = _workspace_packet(item)
        source = str(item.get("path") if isinstance(item, dict) else item)
        if reason:
            rejected.append({"source": source or f"workspace_file:{index + 1}", "reason": reason})
            continue
        assert normalized is not None
        if normalized["source_ref"] in seen_refs:
            rejected.append({"source": normalized["path"], "reason": "duplicate source_ref"})
            continue
        size = len(normalized["content"].encode("utf-8"))
        if total_bytes + size > MAX_TOTAL_BYTES:
            rejected.append({"source": normalized["path"], "reason": "total inspection byte limit exceeded"})
            continue
        total_bytes += size
        seen_refs.add(normalized["source_ref"])
        accepted.append(normalized)

    if not accepted:
        return _unable(
            "No attributed inline code packet or exact approved workspace file was available for inspection.",
            rejected=rejected,
            terms=terms,
        )

    observations: list[dict[str, Any]] = []
    interpretations: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []
    inspected_sources: list[dict[str, Any]] = []
    match_count = 0
    for source in accepted:
        content = source["content"]
        lines = content.splitlines() or [""]
        inspected_sources.append(
            {
                "path": source["path"],
                "source_ref": source["source_ref"],
                "source_kind": source["source_kind"],
                "line_count": len(lines),
                "language": _language(source["path"]),
            }
        )
        observations.append(
            {
                "kind": "file_observation",
                "observation": f"Inspected {source['path']} as {source['source_kind']} with {len(lines)} visible line(s).",
                "source_ref": source["source_ref"],
                "path": source["path"],
                "line_start": 1,
                "line_end": len(lines),
            }
        )
        symbol_observations = _python_symbols(source, content)
        observations.extend(symbol_observations)
        for term in terms:
            for line_number, line in enumerate(lines, start=1):
                if term.lower() not in line.lower():
                    continue
                citation = _citation(source, line_number, line_number)
                citations.append(citation)
                observations.append(
                    {
                        "kind": "text_match_observation",
                        "observation": f"The exact inspection term '{term}' appears on this line.",
                        "matched_term": term,
                        "excerpt": truncate(line.strip(), 320),
                        **citation,
                    }
                )
                if re.search(rf"\b(?:def|class|function)\s+{re.escape(term)}\b", line, flags=re.IGNORECASE):
                    interpretations.append(
                        {
                            "interpretation": f"This location appears to define the requested symbol '{term}'.",
                            "basis": "visible definition syntax in the inspected line",
                            "confidence": "bounded",
                            **citation,
                        }
                    )
                match_count += 1
                if match_count >= MAX_MATCHES:
                    break
            if match_count >= MAX_MATCHES:
                break
        if match_count >= MAX_MATCHES:
            break

    citations = _unique_citations(citations)
    source_refs = list(dict.fromkeys(item["source_ref"] for item in inspected_sources))
    if terms and not citations:
        interpretations.append(
            {
                "interpretation": "None of the requested inspection terms appeared in the inspected sources.",
                "basis": "bounded exact-text inspection only",
                "confidence": "bounded",
                "scope_limit": "This does not establish absence outside the inspected files.",
            }
        )
    direct = (
        f"The inspected code contains {len(citations)} cited location(s) matching: {', '.join(terms)}."
        if citations
        else f"Inspected {len(inspected_sources)} approved or supplied code source(s); no requested term was established in that bounded set."
    )
    return {
        "status": "local_code_inspection_ready",
        "inspected": True,
        "result_summary": direct,
        "inspection_terms": terms,
        "inspected_sources": inspected_sources,
        "rejected_sources": rejected,
        "observations": observations[:120],
        "interpretations": interpretations[:40],
        "citations": citations[:MAX_MATCHES],
        "source_refs": source_refs,
        "assumptions": ["Only visible supplied or explicitly approved file content was inspected."],
        "limitations": [
            "No claim is made about files outside the inspected set.",
            "Static text and syntax observations do not establish runtime behavior.",
            "No code was executed and no dependency or repository-wide scan occurred.",
        ],
        "evidence_confidence": "direct_inspected_code_observation",
        "answer_confidence": "bounded_to_inspected_locations" if citations else "insufficient_matching_code_evidence",
        "reads_only_explicit_sources": True,
        "directory_scan_allowed": False,
        "glob_allowed": False,
        "code_execution_allowed": False,
        "filesystem_write_allowed": False,
        "autonomous_filesystem_authority": False,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": LOCAL_CODE_BOUNDARY,
    }


def _inline_packet(packet: Any, index: int) -> tuple[dict[str, Any] | None, str]:
    if not isinstance(packet, dict):
        return None, "inline code packet must be an object"
    source_ref = truncate(str(packet.get("source_ref") or ""), 500).strip()
    path = truncate(str(packet.get("path") or packet.get("label") or f"supplied_{index + 1}.txt"), 500).strip()
    content = str(packet.get("content") or "")
    if not source_ref:
        return None, "inline code packet requires source_ref"
    if not content:
        return None, "inline code packet requires content"
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        return None, "inline code packet exceeds per-file byte limit"
    return {
        "source_ref": source_ref,
        "path": path,
        "content": content,
        "source_kind": "explicitly_supplied_packet",
    }, ""


def _workspace_packet(item: Any) -> tuple[dict[str, Any] | None, str]:
    if isinstance(item, dict):
        raw_path = str(item.get("path") or "").strip()
        if item.get("approved") is not True:
            return None, "workspace file requires approved=true"
    else:
        raw_path = str(item or "").strip()
    if not raw_path:
        return None, "workspace file path is required"
    if any(marker in raw_path for marker in ("*", "?", "[", "]")):
        return None, "globs and wildcard paths are not allowed"
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    try:
        resolved = candidate.resolve(strict=True)
        root = PROJECT_ROOT.resolve(strict=True)
    except OSError:
        return None, "workspace file does not exist"
    if resolved != root and root not in resolved.parents:
        return None, "workspace file is outside the approved project root"
    if not resolved.is_file():
        return None, "directories and non-file paths are not inspectable"
    if _sensitive_path(resolved):
        return None, "credential or secret-bearing file types are blocked"
    if resolved.suffix.lower() not in ALLOWED_SUFFIXES:
        return None, "file type is outside the bounded text-code allowlist"
    try:
        raw = resolved.read_bytes()
    except OSError:
        return None, "workspace file could not be read"
    if len(raw) > MAX_FILE_BYTES:
        return None, "workspace file exceeds per-file byte limit"
    if b"\x00" in raw:
        return None, "binary files are not inspectable"
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, "workspace file is not UTF-8 text"
    relative = resolved.relative_to(root).as_posix()
    return {
        "source_ref": f"workspace:{relative}",
        "path": relative,
        "content": content,
        "source_kind": "approved_workspace_file",
    }, ""


def _sensitive_path(path: Path) -> bool:
    lower_name = path.name.lower()
    return (
        lower_name in BLOCKED_NAMES
        or lower_name.startswith(".env.")
        or path.suffix.lower() in BLOCKED_SUFFIXES
        or any(marker in lower_name for marker in ("credential", "private_key", "secret_key"))
    )


def _inspection_terms(value: Any, prompt: str) -> list[str]:
    if isinstance(value, (list, tuple)):
        terms = [truncate(str(item), 120).strip() for item in value if str(item).strip()]
    elif isinstance(value, str) and value.strip():
        terms = [truncate(value, 120).strip()]
    else:
        identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", prompt)
        terms = [item for item in identifiers if item.lower() not in _TERM_STOPWORDS]
    return list(dict.fromkeys(terms))[:12]


def _python_symbols(source: dict[str, Any], content: str) -> list[dict[str, Any]]:
    if Path(source["path"]).suffix.lower() != ".py":
        return []
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        line = int(exc.lineno or 1)
        return [
            {
                "kind": "syntax_observation",
                "observation": truncate(f"Python parsing reported: {exc.msg}", 320),
                **_citation(source, line, line),
            }
        ]
    result: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result.append(
                {
                    "kind": "symbol_observation",
                    "observation": f"Visible {type(node).__name__} named '{node.name}'.",
                    "symbol": node.name,
                    **_citation(source, int(node.lineno), int(getattr(node, "end_lineno", node.lineno))),
                }
            )
    return result[:80]


def _citation(source: dict[str, Any], line_start: int, line_end: int) -> dict[str, Any]:
    return {
        "source_ref": source["source_ref"],
        "path": source["path"],
        "line_start": max(1, int(line_start)),
        "line_end": max(1, int(line_end)),
    }


def _unique_citations(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for item in citations:
        key = (item["source_ref"], item["path"], item["line_start"], item["line_end"])
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result


def _language(path: str) -> str:
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix or "text"


def _unable(reason: str, *, rejected: list[dict[str, str]], terms: list[str]) -> dict[str, Any]:
    return {
        "status": "local_code_inspection_unable",
        "inspected": False,
        "result_summary": "",
        "no_answer_reason": truncate(reason, 1000),
        "inspection_terms": terms,
        "inspected_sources": [],
        "rejected_sources": rejected,
        "observations": [],
        "interpretations": [],
        "citations": [],
        "source_refs": [],
        "assumptions": ["No code claim is allowed without an inspectable attributed source."],
        "limitations": ["No file outside an explicitly supplied or approved source was inspected."],
        "evidence_confidence": "no_inspected_code_evidence",
        "answer_confidence": "unable_to_inspect",
        "reads_only_explicit_sources": True,
        "directory_scan_allowed": False,
        "glob_allowed": False,
        "code_execution_allowed": False,
        "filesystem_write_allowed": False,
        "autonomous_filesystem_authority": False,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": LOCAL_CODE_BOUNDARY,
    }
