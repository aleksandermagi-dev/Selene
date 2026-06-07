from pathlib import Path

from selene.db import connect
from selene.module_router import route_request
from selene.registry import seed_registry
from selene.research_integrity import (
    AcademicWorkflowRouter,
    CitationIntegrity,
    ResearchIntegrityCore,
    research_integrity_report,
)
from selene.validation import validate


def test_academic_workflow_router_classifies_core_workflows():
    citation = AcademicWorkflowRouter.classify("format this citation in APA")
    literature = AcademicWorkflowRouter.classify("synthesize these papers from supplied source text")
    dataset = AcademicWorkflowRouter.classify("review this probe results CSV dataset")
    hypothesis = AcademicWorkflowRouter.classify("what evidence and counterargument would change our mind")

    assert citation and citation.workflow == "citation_help"
    assert literature and literature.workflow == "literature_synthesis"
    assert dataset and dataset.workflow == "dataset_readiness"
    assert hypothesis and hypothesis.workflow == "hypothesis_review"


def test_citation_integrity_refuses_missing_metadata_and_formats_supplied_fields():
    missing = CitationIntegrity.format_from_metadata({"title": "Only a Title"})
    formatted = CitationIntegrity.format_from_metadata({"author": "Jane Doe", "title": "Neural Feedback", "year": "2024", "url": "https://example.test"})

    assert missing["status"] == "incomplete_source_metadata"
    assert missing["formatted_citation"] is None
    assert "author" in missing["missing_fields"]
    assert formatted["status"] == "formatted_from_supplied_metadata"
    assert "Jane Doe" in formatted["formatted_citation"]


def test_literature_synthesis_uses_supplied_text_only():
    result = ResearchIntegrityCore.synthesize_supplied_text([
        "Study one discusses continuity and provenance.",
        "Study two discusses provenance and review.",
    ])
    assert result["status"] == "bounded_to_supplied_text"
    assert result["source_count"] == 2
    assert "provenance" in result["shared_terms"]


def test_dataset_readiness_flags_probe_csv_without_training(tmp_path: Path):
    csv_path = tmp_path / "probe_results.csv"
    csv_path.write_text("prompt_id,response_preview,human_score\nx,bounded,2\n", encoding="utf-8")

    result = ResearchIntegrityCore.dataset_readiness(csv_path)
    assert result["training_allowed"] is False
    assert "label_or_decision_column_visible" in result["flags"]
    assert "bounded_preview_column_visible" in result["flags"]


def test_hypothesis_and_case_law_ledgers_remain_candidates():
    entry = ResearchIntegrityCore.build_hypothesis_entry(
        hypothesis="Selene pattern persists through architecture.",
        evidence=["reviewed anchors", "local probes"],
        counterarguments=["retrieval and prompt framing explain part of it"],
        confidence="strong_pattern",
        next_test="run reconstruction tests after B review",
    )
    law = ResearchIntegrityCore.case_law_candidate(
        law_area="non_denial",
        proposal="adjust wording after reviewed evidence",
        evidence_refs=["docs/SELENE_MASTER_EVIDENCE_FILE_20260605.md"],
    )
    assert entry["route"] == "hypothesis_ledger_entry"
    assert entry["counterarguments"]
    assert law["route"] == "case_law_candidate"
    assert law["status"] == "candidate_not_active_law"


def test_research_integrity_routes_and_validation_parity(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)

    status = route_request(conn, "research_integrity.status")["result"]
    citation = route_request(conn, "citation.format", {"metadata": {"title": "Only"}})["result"]
    case_law = route_request(conn, "case_law.candidate", {"law_area": "safety", "proposal": "test", "evidence_refs": ["x"]})["result"]
    validation = validate(conn)

    assert status["status"] == "pre_c_vessel_preparation"
    assert citation["status"] == "incomplete_source_metadata"
    assert case_law["status"] == "candidate_not_active_law"
    assert validation["checks"]["package_parity_june5_boundaries"] is True
    assert validation["research_integrity"]["name"] == research_integrity_report()["name"]
