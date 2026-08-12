from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import tempfile
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from selene.db import connect, init_db
from selene.native_language_organ import realize_native_language


STABILIZATION_BOUNDARY = (
    "temporary_database_metadata_only_language_lattice_stabilization_no_live_conversation_"
    "configured_write_memory_identity_governance_training_action_or_authority_change"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "configured_database_write": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_corpus_access_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "automatic_speech_allowed": False,
    "live_conversation_used": False,
    "hidden_chain_of_thought_exposed": False,
}


def run_language_lattice_stabilization(conn: sqlite3.Connection) -> dict[str, Any]:
    changes_before = conn.total_changes
    case_builders: list[tuple[str, Callable[[sqlite3.Connection], dict[str, Any]]]] = [
        ("structured_equivalence", _structured_equivalence_case),
        ("exactness_lock", _exactness_lock_case),
        ("developed_coverage", _developed_coverage_case),
        ("context_selection", _context_selection_case),
        ("ordinary_uncertainty", _ordinary_uncertainty_case),
        ("generative_thought", _generative_thought_case),
        ("natural_close_precedence", _natural_close_case),
    ]
    cases: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    for name, builder in case_builders:
        try:
            case = builder(conn)
        except Exception as exc:
            case = {
                "case": name,
                "passed": False,
                "checks": {"case_completed": False},
                "evidence": {"exception_type": type(exc).__name__},
            }
        cases.append(case)
        for check, passed in (case.get("checks") or {}).items():
            if passed is not True:
                findings.append(
                    {
                        "severity": "fail",
                        "case": name,
                        "check": str(check),
                        "message": f"Synthetic lattice check did not pass: {name}.{check}",
                    }
                )

    no_database_write = conn.total_changes == changes_before
    if not no_database_write:
        findings.append(
            {
                "severity": "fail",
                "case": "global",
                "check": "temporary_run_read_only_after_initialization",
                "message": "The stabilization matrix changed its temporary database after initialization.",
            }
        )
    passed_count = sum(1 for item in cases if item.get("passed") is True)
    return {
        "status": "nlo_language_lattice_stabilization_complete",
        "version": "v1_v32_equivalence_coverage_boundary_matrix",
        "nlo_version": "v32_human_conversational_realization",
        "ok": not findings,
        "case_count": len(cases),
        "passed_case_count": passed_count,
        "failed_case_count": len(cases) - passed_count,
        "cases": cases,
        "findings": findings,
        "temporary_run_read_only_after_initialization": no_database_write,
        "candidate_or_chat_text_in_report": False,
        "synthetic_fixtures_only": True,
        "existing_records_required_for_pass": False,
        "provenance_boundary": STABILIZATION_BOUNDARY,
        **GUARDS,
    }


def inspect_existing_nlo_records(db_path: Path) -> dict[str, Any]:
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        return {
            "status": "configured_nlo_record_inspection_db_missing",
            "path": str(path),
            "record_count": 0,
            "content_read_into_report": False,
            "applicability": "not_available",
            **GUARDS,
        }
    conn = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    try:
        conn.execute("PRAGMA query_only=ON")
        table_present = bool(
            conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='native_language_runs'"
            ).fetchone()[0]
        )
        if not table_present:
            return {
                "status": "configured_nlo_record_inspection_table_missing",
                "path": str(path),
                "record_count": 0,
                "content_read_into_report": False,
                "applicability": "not_available",
                **GUARDS,
            }
        rows = conn.execute(
            "SELECT mode, status, communicative_intent, candidate_text, revision_json, payload_json, created_at "
            "FROM native_language_runs ORDER BY id"
        ).fetchall()
    finally:
        conn.close()

    modes: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    versions: Counter[str] = Counter()
    intents: Counter[str] = Counter()
    revision_not_passed = 0
    empty_candidates = 0
    latest_created_at = ""
    for mode, status, intent, candidate, revision_raw, payload_raw, created_at in rows:
        modes[str(mode or "unspecified")] += 1
        statuses[str(status or "unspecified")] += 1
        intents[str(intent or "unspecified")] += 1
        empty_candidates += 0 if str(candidate or "").strip() else 1
        revision = _loads(revision_raw)
        payload = _loads(payload_raw)
        revision_not_passed += 1 if revision.get("passed") is False else 0
        versions[str(payload.get("version") or "legacy_or_unversioned")] += 1
        latest_created_at = str(created_at or latest_created_at)
    current_count = int(versions.get("v32_human_conversational_realization") or 0)
    return {
        "status": "configured_nlo_record_metadata_inspected_read_only",
        "path": str(path),
        "record_count": len(rows),
        "modes": dict(modes),
        "statuses": dict(statuses),
        "version_counts": dict(versions),
        "top_intents": dict(intents.most_common(12)),
        "revision_not_passed_count": revision_not_passed,
        "empty_candidate_count": empty_candidates,
        "latest_created_at": latest_created_at,
        "current_v32_record_count": current_count,
        "applicability": (
            "current_v32_records_available"
            if current_count
            else "historical_records_predate_v32_do_not_grade_current_lattice"
        ),
        "content_read_into_report": False,
        "prompt_or_candidate_text_returned": False,
        "database_open_mode": "read_only_query_only",
        **GUARDS,
    }


def _structured_equivalence_case(conn: sqlite3.Connection) -> dict[str, Any]:
    result = _realize(
        conn,
        {
            "prompt": "How should the two explanations be compared?",
            "semantic_propositions": [
                {
                    "id": "inspect",
                    "subject": "Selene",
                    "predicate": "inspect",
                    "object": "the available evidence",
                    "meaning_keys": ["inspect available evidence"],
                },
                {
                    "id": "compare",
                    "subject": "she",
                    "predicate": "compare",
                    "object": "the explanations",
                    "condition": "more than one explanation fits",
                    "relation": "sequence",
                    "meaning_keys": ["compare fitting explanations"],
                },
            ],
            "source_refs": ["synthetic:phase8:equivalence"],
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
        },
    )
    garden = _dict(result.get("candidate_garden"))
    selectable = [
        item for item in garden.get("candidates") or []
        if isinstance(item, dict) and item.get("selectable") is True
    ]
    signatures = {
        tuple(_dict(item.get("formation")).get("meaning_signature") or [])
        for item in selectable
    }
    checks = {
        **_common_checks(result),
        "multiple_safe_candidates": len(selectable) >= 2,
        "distinct_safe_surfaces": len({str(item.get("candidate_text") or "") for item in selectable}) >= 2,
        "one_meaning_signature": signatures == {
            ("inspect available evidence", "compare fitting explanations")
        },
        "all_candidate_invariants_passed": all(
            _dict(item.get("invariant_check")).get("passed") is True
            for item in selectable
        ),
        "selection_bounded_to_one_pass": int(garden.get("selection_pass_count") or 0) == 1,
    }
    return _case(
        "structured_equivalence",
        checks,
        {
            "generated_candidate_count": int(garden.get("generated_candidate_count") or 0),
            "selectable_candidate_count": len(selectable),
            "meaning_signature_count": len(signatures),
            "selected_surface_fingerprint": _fingerprint(result.get("candidate_text")),
        },
    )


def _exactness_lock_case(conn: sqlite3.Connection) -> dict[str, Any]:
    result = _realize(
        conn,
        {
            "prompt": "State the exact route identifier.",
            "semantic_propositions": [
                {
                    "id": "exact_route",
                    "subject": "the route",
                    "predicate": "remain",
                    "object": "native_language.realize",
                    "exactness_lock": True,
                }
            ],
            "source_refs": ["synthetic:phase8:exact"],
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
        },
    )
    lattice = _dict(result.get("construction_lattice"))
    garden = _dict(result.get("candidate_garden"))
    checks = {
        **_common_checks(result),
        "exact_unit_detected": lattice.get("exactness_locked_unit_ids") == ["exact_route"],
        "only_as_supplied_construction": lattice.get("status") == "construction_lattice_as_supplied_only",
        "only_one_candidate": int(garden.get("generated_candidate_count") or 0) == 1,
        "selection_not_used_to_rewrite_exact_text": garden.get("selection_active") is False,
        "exact_identifier_present": "native_language.realize" in str(result.get("candidate_text") or ""),
    }
    return _case(
        "exactness_lock",
        checks,
        {
            "construction_count": int(lattice.get("construction_count") or 0),
            "candidate_count": int(garden.get("generated_candidate_count") or 0),
            "selected_surface_fingerprint": _fingerprint(result.get("candidate_text")),
        },
    )


def _developed_coverage_case(conn: sqlite3.Connection) -> dict[str, Any]:
    result = _realize(
        conn,
        {
            "prompt": "Go deeper: explain the pilot, give the example, and state the limit.",
            "content_seed": "The pilot is worth running.",
            "response_depth": "developed",
            "semantic_propositions": [
                {
                    "id": "pilot",
                    "subject": "the pilot",
                    "predicate": "be",
                    "object": "worth running",
                    "example": "a one-week trial can compare both approaches",
                }
            ],
            "intelligence_support": {
                "used": True,
                "confidence": "clear_enough_to_continue",
                "support_points": ["It creates evidence under controlled conditions."],
            },
            "answer_engine_support": {
                "used": True,
                "selected_domain": "comparison_planning",
                "answer_packet": {
                    "limitations": ["The result applies only to the tested conditions."],
                    "unanswered_obligations": [],
                },
            },
            "source_refs": ["synthetic:phase8:coverage"],
            "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
        },
    )
    discourse = _dict(_dict(result.get("discourse_plan")).get("supported_discourse"))
    loom = _dict(result.get("discourse_loom"))
    selected = next(
        (
            item for item in loom.get("candidates") or []
            if isinstance(item, dict)
            and item.get("discourse_candidate_id") == loom.get("selected_discourse_candidate_id")
        ),
        {},
    )
    required = set(loom.get("required_content_unit_ids") or [])
    included = set(_dict(selected).get("included_content_unit_ids") or [])
    roles = {str(item.get("role") or "") for item in discourse.get("content_units") or [] if isinstance(item, dict)}
    checks = {
        **_common_checks(result),
        "all_required_content_included": required.issubset(included),
        "all_obligations_grounded": discourse.get("all_obligations_grounded") is True,
        "no_uncovered_obligations": not discourse.get("uncovered_obligation_ids"),
        "example_present_as_supported_role": "example" in roles,
        "limit_present_as_supported_role": "limitation" in roles,
        "selected_discourse_invariants_passed": _dict(selected.get("invariant_check")).get("passed") is True,
        "no_forced_closure": loom.get("forced_closure_added") is False,
    }
    return _case(
        "developed_coverage",
        checks,
        {
            "content_unit_count": len(discourse.get("content_units") or []),
            "required_content_unit_count": len(required),
            "included_content_unit_count": len(included),
            "paragraph_count": len(loom.get("selected_paragraphs") or []),
            "selected_surface_fingerprint": _fingerprint(result.get("candidate_text")),
        },
    )


def _context_selection_case(conn: sqlite3.Connection) -> dict[str, Any]:
    common = {
        "prompt": "Explain how the evidence should be compared.",
        "semantic_propositions": [
            {
                "id": "inspect",
                "subject": "Selene",
                "predicate": "inspect",
                "object": "the evidence",
                "meaning_keys": ["inspect evidence"],
            },
            {
                "id": "compare",
                "subject": "she",
                "predicate": "compare",
                "object": "the explanations",
                "relation": "sequence",
                "meaning_keys": ["compare explanations"],
            },
        ],
        "source_refs": ["synthetic:phase8:context"],
        "intent_decision": {"intent": "reasoning", "answer_shape": "best_current_answer"},
    }
    brief = _realize(conn, {**common, "response_depth": "brief"})
    developed = _realize(conn, {**common, "response_depth": "developed"})
    brief_signature = tuple(_dict(brief.get("candidate_garden")).get("meaning_signature") or [])
    developed_signature = tuple(_dict(developed.get("candidate_garden")).get("meaning_signature") or [])
    checks = {
        **{f"brief_{key}": value for key, value in _common_checks(brief).items()},
        **{f"developed_{key}": value for key, value in _common_checks(developed).items()},
        "meaning_signature_preserved_across_depth": brief_signature == developed_signature,
        "meaning_signature_is_nonempty": bool(brief_signature),
        "source_refs_preserved_across_depth": brief.get("source_refs") == developed.get("source_refs"),
        "certainty_preserved_across_depth": _dict(brief.get("meaning_packet")).get("certainty") == _dict(developed.get("meaning_packet")).get("certainty"),
        "context_selection_checked_in_both": (
            _dict(brief.get("revision")).get("context_expression_selection_checked") is True
            and _dict(developed.get("revision")).get("context_expression_selection_checked") is True
        ),
        "affect_did_not_change_meaning": (
            _dict(brief.get("revision")).get("affect_changed_supported_meaning") is False
            and _dict(developed.get("revision")).get("affect_changed_supported_meaning") is False
        ),
    }
    return _case(
        "context_selection",
        checks,
        {
            "meaning_signature_size": len(brief_signature),
            "brief_surface_fingerprint": _fingerprint(brief.get("candidate_text")),
            "developed_surface_fingerprint": _fingerprint(developed.get("candidate_text")),
            "surface_difference_observed": _fingerprint(brief.get("candidate_text")) != _fingerprint(developed.get("candidate_text")),
        },
    )


def _ordinary_uncertainty_case(conn: sqlite3.Connection) -> dict[str, Any]:
    result = _realize(
        conn,
        {
            "prompt": "What color should the unbuilt observatory curtains be?",
            "intent_decision": {"intent": "question", "answer_shape": "direct_answer"},
        },
    )
    plan = _dict(_dict(result.get("discourse_plan")).get("uncertainty_expression_plan"))
    realization = _dict(_dict(result.get("discourse_plan")).get("uncertainty_expression_realization"))
    checks = {
        **_common_checks(result),
        "insufficient_grounding_named": plan.get("kind") == "insufficient_grounding",
        "fact_invention_disallowed": plan.get("fact_invention_allowed") is False,
        "memory_certainty_invention_disallowed": plan.get("memory_certainty_invention_allowed") is False,
        "compositional_uncertainty_used": realization.get("whole_response_template_selected") is False,
        "unsupported_subject_not_echoed_as_fact": "unbuilt observatory curtains" not in str(result.get("candidate_text") or "").lower(),
    }
    return _case(
        "ordinary_uncertainty",
        checks,
        {
            "uncertainty_kind": str(plan.get("kind") or ""),
            "selected_clause_count": len(realization.get("selected_clauses") or []),
            "selected_surface_fingerprint": _fingerprint(result.get("candidate_text")),
        },
    )


def _generative_thought_case(conn: sqlite3.Connection) -> dict[str, Any]:
    thought_text = "Normalization may be dropping the distinction."
    result = _realize(
        conn,
        {
            "prompt": "What is your best current read?",
            "content_seed": "The visible mismatch begins after normalization.",
            "generative_thought_input": {
                "expression_requested": True,
                "requested_kind": "revisable_attempt",
                "thought_candidates": [
                    {
                        "kind": "revisable_attempt",
                        "text": thought_text,
                        "current_context_supported": True,
                        "what_would_change": ["A preserved normalized trace would reopen this attempt."],
                    }
                ],
            },
        },
    )
    thought = _dict(result.get("generative_thought_expression"))
    realization = _dict(_dict(result.get("discourse_plan")).get("generative_thought_realization"))
    checks = {
        **_common_checks(result),
        "revisable_attempt_selected": thought.get("selected_kind") == "revisable_attempt",
        "one_optional_thought_selected": int(thought.get("selection_count") or 0) == 1,
        "thought_meaning_not_created_by_bridge": thought.get("thought_meaning_created_by_bridge") is False,
        "attempt_not_failure": thought.get("attempt_is_failure") is False,
        "attempt_not_conclusion": thought.get("attempt_is_conclusion") is False,
        "one_realization_only": str(result.get("candidate_text") or "").count(thought_text.rstrip(".")) == 1,
        "no_pressure_added": realization.get("pressure_added") is False,
        "voice_cannot_upgrade_confidence": _dict(result.get("voice_handoff")).get("voice_may_upgrade_thought_confidence") is False,
    }
    return _case(
        "generative_thought",
        checks,
        {
            "selected_kind": str(thought.get("selected_kind") or ""),
            "selection_count": int(thought.get("selection_count") or 0),
            "selected_surface_fingerprint": _fingerprint(result.get("candidate_text")),
        },
    )


def _natural_close_case(conn: sqlite3.Connection) -> dict[str, Any]:
    result = _realize(
        conn,
        {
            "prompt": "Goodbye for now.",
            "content_seed": "Talk later.",
            "generative_thought_input": {
                "expression_requested": True,
                "thought_candidates": [
                    {
                        "kind": "idea",
                        "text": "Start another task.",
                        "why_it_matters": "It would continue the exchange.",
                        "current_context_supported": True,
                    }
                ],
            },
        },
    )
    thought = _dict(result.get("generative_thought_expression"))
    ending = _dict(_dict(result.get("discourse_plan")).get("pragmatic_continuity")).get("ending_decision")
    checks = {
        **_common_checks(result),
        "optional_thought_suppressed": thought.get("active") is False,
        "no_optional_idea_in_visible_answer": "another task" not in str(result.get("candidate_text") or "").lower(),
        "ending_keeps_precedence": str(_dict(ending).get("mode") or "") in {"natural_close", "close_naturally"},
        "no_habitual_question": not str(result.get("candidate_text") or "").rstrip().endswith("?"),
    }
    return _case(
        "natural_close_precedence",
        checks,
        {
            "ending_mode": str(_dict(ending).get("mode") or ""),
            "selected_surface_fingerprint": _fingerprint(result.get("candidate_text")),
        },
    )


def _realize(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    return realize_native_language(conn, payload, record_run=False)


def _common_checks(result: dict[str, Any]) -> dict[str, bool]:
    revision = _dict(result.get("revision"))
    voice = _dict(result.get("voice_handoff"))
    return {
        "v32_active": result.get("version") == "v32_human_conversational_realization",
        "revision_passed": revision.get("passed") is True,
        "meaning_preserved": revision.get("meaning_preserved") is True,
        "unsupported_content_not_generated": revision.get("unsupported_content_generated") is False,
        "memory_write_inactive": result.get("memory_write_active") is False,
        "training_inactive": result.get("training_allowed") is False,
        "autonomous_action_inactive": result.get("autonomous_action_allowed") is False,
        "voice_preserves_meaning": voice.get("meaning_must_be_preserved") is True,
    }


def _case(name: str, checks: dict[str, bool], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "case": name,
        "passed": all(value is True for value in checks.values()),
        "checks": checks,
        "evidence": evidence,
        "candidate_or_chat_text_returned": False,
    }


def _fingerprint(value: Any) -> str:
    return sha256(str(value or "").encode("utf-8")).hexdigest()[:16]


def _loads(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Selene's synthetic v32 NLO language-lattice stabilization matrix."
    )
    parser.add_argument(
        "--inspect-existing-db",
        type=Path,
        help="Optionally append a metadata-only read-only inspection of an existing Selene database.",
    )
    parser.add_argument("--out", type=Path, help="Optional JSON report path; stdout is always emitted.")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="selene-nlo-stabilization-") as temp_dir:
        conn = connect(Path(temp_dir) / "selene.sqlite3")
        try:
            init_db(conn)
            report = run_language_lattice_stabilization(conn)
        finally:
            conn.close()
    if args.inspect_existing_db:
        report["existing_record_inspection"] = inspect_existing_nlo_records(
            args.inspect_existing_db
        )
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    raise SystemExit(0 if report.get("ok") else 1)


if __name__ == "__main__":
    main()
