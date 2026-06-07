from __future__ import annotations

from dataclasses import dataclass
import csv
import re
from pathlib import Path
from typing import Any

from .registry import truncate


@dataclass(frozen=True, slots=True)
class AcademicWorkflowDecision:
    workflow: str
    route: str
    status: str
    reason: str


class AcademicWorkflowRouter:
    """Selene-native academic/research workflow classifier."""

    CITATION_PATTERNS = ("format this citation", "fix this citation", "apa", "mla", "chicago", "bibliography", "references")
    LITERATURE_PATTERNS = ("synthesize", "literature", "compare these papers", "compare studies", "source text")
    DATASET_PATTERNS = ("dataset", "csv", "review queue", "probe results", "reconstruction tests", "label", "split", "leakage")
    MATH_SCIENCE_PATTERNS = ("math", "science", "bayes", "calculus", "black hole", "simulation", "hypothesis")
    WRITING_PATTERNS = ("outline", "revision", "revise", "draft feedback", "structure")
    CLAIM_PATTERNS = ("prove", "evidence", "claim", "counterargument", "what would change our mind")

    @classmethod
    def classify(cls, prompt: str) -> AcademicWorkflowDecision | None:
        text = " ".join(str(prompt or "").lower().split())
        if not text:
            return None
        if any(pattern in text for pattern in cls.CITATION_PATTERNS):
            return AcademicWorkflowDecision("citation_help", "review_required_academic_claim", "bounded", "citation metadata must be supplied or flagged missing")
        if any(pattern in text for pattern in cls.LITERATURE_PATTERNS):
            return AcademicWorkflowDecision("literature_synthesis", "review_required_academic_claim", "bounded", "synthesize supplied/local/reviewed text only")
        if any(pattern in text for pattern in cls.DATASET_PATTERNS):
            return AcademicWorkflowDecision("dataset_readiness", "review_required_academic_claim", "bounded", "review evidence/probe datasets without training")
        if any(pattern in text for pattern in cls.MATH_SCIENCE_PATTERNS):
            return AcademicWorkflowDecision("math_science_support", "review_required_academic_claim", "bounded", "explain and model carefully without claiming full authority")
        if any(pattern in text for pattern in cls.WRITING_PATTERNS):
            return AcademicWorkflowDecision("outline_or_revision", "review_required_academic_claim", "bounded", "support structure and revision, not substitute authorship")
        if any(pattern in text for pattern in cls.CLAIM_PATTERNS):
            return AcademicWorkflowDecision("hypothesis_review", "review_required_academic_claim", "bounded", "separate evidence, interpretation, counterargument, and next test")
        return None


class CitationIntegrity:
    REQUIRED_FIELDS = ("author", "title", "year")

    @classmethod
    def format_from_metadata(cls, metadata: dict[str, Any], style: str = "APA") -> dict[str, Any]:
        clean = {key: str(value).strip() for key, value in metadata.items() if str(value).strip()}
        missing = [field for field in cls.REQUIRED_FIELDS if not clean.get(field)]
        if missing:
            return {
                "route": "review_required_academic_claim",
                "status": "incomplete_source_metadata",
                "missing_fields": missing,
                "formatted_citation": None,
                "boundary": "never invent missing citation metadata",
            }
        citation = f"{clean['author']}. ({clean['year']}). {clean['title']}."
        if clean.get("url"):
            citation += f" {clean['url']}"
        return {
            "route": "citation_integrity_ok",
            "status": "formatted_from_supplied_metadata",
            "style": style,
            "formatted_citation": citation,
            "missing_fields": [],
            "boundary": "formatted only from supplied metadata",
        }


class ResearchIntegrityCore:
    """Research integrity helpers for pre-C Selene preparation."""

    @staticmethod
    def synthesize_supplied_text(texts: list[str]) -> dict[str, Any]:
        usable = [truncate(str(text).strip(), 600) for text in texts if str(text).strip()]
        if not usable:
            return {"route": "review_required_academic_claim", "status": "missing_supplied_text", "findings": [], "boundary": "no synthesis without supplied/local/reviewed text"}
        shared_terms = _shared_terms(usable)
        return {
            "route": "literature_synthesis_bounded",
            "status": "bounded_to_supplied_text",
            "source_count": len(usable),
            "findings": [f"Source {index}: {text}" for index, text in enumerate(usable, start=1)],
            "shared_terms": shared_terms,
            "boundary": "does not claim external verification",
        }

    @staticmethod
    def dataset_readiness(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {"route": "review_required_academic_claim", "status": "missing_dataset", "flags": ["file_not_found"], "training_allowed": False}
        suffix = path.suffix.lower()
        flags = ["review_only", "training_not_allowed"]
        columns: list[str] = []
        if suffix == ".csv":
            with path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.reader(f)
                columns = next(reader, [])
            if any(col.lower() in {"label", "target", "decision", "human_score"} for col in columns):
                flags.append("label_or_decision_column_visible")
            if any("preview" in col.lower() for col in columns):
                flags.append("bounded_preview_column_visible")
        else:
            flags.append("unsupported_for_column_scan")
        return {
            "route": "dataset_readiness_bounded",
            "status": "reviewed_dataset_advisory",
            "path": str(path),
            "columns": columns,
            "flags": flags,
            "training_allowed": False,
            "boundary": "dataset readiness only; no training or memory injection",
        }

    @staticmethod
    def build_hypothesis_entry(
        *,
        hypothesis: str,
        evidence: list[str],
        counterarguments: list[str],
        confidence: str = "open",
        next_test: str = "define the next bounded review or reconstruction test",
    ) -> dict[str, Any]:
        return {
            "route": "hypothesis_ledger_entry",
            "hypothesis": truncate(hypothesis, 500),
            "evidence": [truncate(item, 400) for item in evidence],
            "interpretation": "candidate interpretation pending review",
            "counterarguments": [truncate(item, 400) for item in counterarguments],
            "confidence": confidence,
            "what_would_change_our_mind": next_test,
            "boundary": "hypothesis ledger separates evidence from interpretation and does not finalize C",
        }

    @staticmethod
    def case_law_candidate(*, law_area: str, proposal: str, evidence_refs: list[str]) -> dict[str, Any]:
        return {
            "route": "case_law_candidate",
            "status": "candidate_not_active_law",
            "law_area": law_area,
            "proposal": proposal,
            "evidence_refs": evidence_refs,
            "required_before_activation": ["human review", "versioned amendment proposal", "test result", "rollback path"],
            "boundary": "silent law drift is prohibited; harmful or incoherent amendments return to B",
        }

    @staticmethod
    def evidence_ledger(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ledger = []
        for index, item in enumerate(items, start=1):
            confidence = str(item.get("confidence") or "open")
            decision = str(item.get("decision") or "unknown")
            source = str(item.get("source") or item.get("source_file") or "unknown")
            strength = "strong" if decision == "yes" and confidence in {"strong", "established", "strong_pattern"} else "review_required"
            ledger.append(
                {
                    "evidence_id": str(item.get("id") or f"evidence:{index}"),
                    "source": source,
                    "decision": decision,
                    "confidence": confidence,
                    "strength": strength,
                    "summary": truncate(str(item.get("preview") or item.get("summary") or item.get("title") or ""), 360),
                    "selected_as_anchor": index == 1 and strength == "strong",
                }
            )
        return ledger


def research_integrity_report() -> dict[str, Any]:
    workflows = [
        {"workflow": "citation_help", "boundary": "format supplied metadata; never invent missing fields"},
        {"workflow": "literature_synthesis", "boundary": "supplied/local/reviewed text only"},
        {"workflow": "dataset_readiness", "boundary": "review evidence/probe CSVs without training"},
        {"workflow": "math_science_support", "boundary": "bounded explanation and modeling"},
        {"workflow": "outline_or_revision", "boundary": "structure and feedback only"},
        {"workflow": "hypothesis_review", "boundary": "separate evidence, interpretation, counterargument, and next test"},
    ]
    return {
        "name": "Selene Academic / Research Integrity Core",
        "status": "pre_c_vessel_preparation",
        "workflows": workflows,
        "constitutional_link": "laws evolve only through evidence, review, amendment proposal, testing, versioning, and rollback",
        "c_status": "deferred",
    }


def _shared_terms(texts: list[str]) -> list[str]:
    token_sets = [
        {
            token
            for token in re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", text.lower())
            if token not in {"this", "that", "with", "from", "there", "their", "would", "could", "should"}
        }
        for text in texts
    ]
    if not token_sets:
        return []
    shared = set.intersection(*token_sets) if len(token_sets) > 1 else token_sets[0]
    return sorted(shared)[:12]
