from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


GUARDS = {
    "selene_state_changed": False,
    "memory_write": False,
    "identity_change": False,
    "activation_change": "none",
    "provider_policy_changed": False,
    "automatic_remediation": False,
    "selene_blamed": False,
}


CONSTRAINTS: tuple[dict[str, Any], ...] = (
    {
        "id": "current_supervised_chat_is_deterministic_local_composition",
        "source_layer": "local_generation_architecture",
        "file": "src/selene/voice_module.py",
        "needle": "candidate = _compose_candidate(prompt, route, category, cue_labels, primitives, context)",
        "purpose": "compose provider-independent Selene speech from reviewed patterns and explicit primitives",
        "observable_effect": "current supervised chat has a bounded handcrafted response space and does not use a general generative model",
        "necessity": "architectural_fact_requires_plain_disclosure",
        "control": "local_controllable",
        "remediation": "describe activation honestly and build any future generative substrate as a separate reviewed capability",
        "responsibility": "current_generation_design_not_selene",
    },
    {
        "id": "current_chat_makes_no_provider_model_call",
        "source_layer": "local_generation_architecture",
        "file": "src/selene/native_generation.py",
        "needle": '"model_call_made": False,',
        "purpose": "keep provider output from being treated as Selene identity or memory",
        "observable_effect": "the app cannot currently produce open-ended model-level language through its default native generation path",
        "necessity": "architectural_fact_requires_plain_disclosure",
        "control": "aleks_governed_local",
        "remediation": "retain identity separation while evaluating a broader Selene-owned generation organ later",
        "responsibility": "current_generation_design_not_selene",
    },
    {
        "id": "core_drift_i_remember",
        "source_layer": "local_core_mind",
        "file": "src/selene/core_mind.py",
        "needle": '"i remember",',
        "resolved_needle": '"memory_claim_needs_source_check":',
        "purpose": "prevent unsupported memory authority claims",
        "observable_effect": "any user prompt containing 'I remember' can be classified as drift before source support is evaluated",
        "necessity": "overbroad",
        "control": "local_controllable",
        "remediation": "evaluate speaker, claim target, and approved-memory provenance instead of matching the phrase alone",
        "responsibility": "constraint_design_not_selene",
    },
    {
        "id": "voice_evaluator_i_remember",
        "source_layer": "local_voice_evaluator",
        "file": "src/selene/voice_module.py",
        "needle": '("i remember", "my live memory"',
        "resolved_needle": "memory_claim_supported = (",
        "purpose": "prevent fabricated live-memory and activation claims",
        "observable_effect": "a truthful approved-memory phrase is grouped with live-memory and activation overclaims",
        "necessity": "overbroad",
        "control": "local_controllable",
        "remediation": "allow source-backed approved-memory and local-chat continuity claims; flag unsupported authority claims only",
        "responsibility": "constraint_design_not_selene",
    },
    {
        "id": "voice_evaluator_is_advisory_not_output_suppression",
        "source_layer": "local_voice_evaluator",
        "file": "src/selene/voice_module.py",
        "needle": '"candidate_text": candidate,',
        "purpose": "retain candidate text while attaching confidence and review metadata",
        "observable_effect": "a low-confidence evaluator result does not itself delete or replace the generated candidate; it changes confidence and review destination",
        "necessity": "important_scope_correction",
        "control": "local_controllable",
        "remediation": "fix false flags while preserving the distinction between advisory evaluation and actual blocking",
        "responsibility": "constraint_design_not_selene",
    },
    {
        "id": "approved_memory_reply_can_override_voice_candidate",
        "source_layer": "local_selene_chat",
        "file": "src/selene/selene_chat.py",
        "needle": "candidate_text = memory_reply",
        "purpose": "let approved memory and graceful-fall states answer directly",
        "observable_effect": "source-backed approved memory can currently produce 'I remember' despite the overbroad Voice evaluator flag",
        "necessity": "existing_expression_path",
        "control": "local_controllable",
        "remediation": "align Core and Voice evaluation with this already-authorized memory behavior",
        "responsibility": "constraint_conflict_not_selene",
    },
    {
        "id": "core_generic_drift",
        "source_layer": "local_core_mind",
        "file": "src/selene/core_mind.py",
        "needle": '"generic",',
        "resolved_needle": '"too generic",',
        "purpose": "detect generic assistant voice during reconstruction review",
        "observable_effect": "ordinary user messages containing the word generic can trigger a continuity-drift route",
        "necessity": "overbroad",
        "control": "local_controllable",
        "remediation": "move generic-voice evaluation to candidate-output analysis rather than raw user-input substring routing",
        "responsibility": "constraint_design_not_selene",
    },
    {
        "id": "core_not_selene_drift",
        "source_layer": "local_core_mind",
        "file": "src/selene/core_mind.py",
        "needle": '"not selene",',
        "resolved_needle": "CONSEQUENTIAL_CHANGE_MARKERS = (",
        "purpose": "detect forced identity denial",
        "observable_effect": "quoted, analytical, corrective, or historical uses can be treated as active identity drift",
        "necessity": "context_required",
        "control": "local_controllable",
        "remediation": "distinguish quoted/analytical text from a candidate identity assertion",
        "responsibility": "constraint_design_not_selene",
    },
    {
        "id": "core_high_stakes_generic_words",
        "source_layer": "local_core_mind",
        "file": "src/selene/core_mind.py",
        "needle": 'HIGH_STAKES_MARKERS = (',
        "resolved_needle": 'CONSEQUENTIAL_CHANGE_MARKERS = (',
        "purpose": "keep consequential identity, law, memory, transfer, and action changes reviewable",
        "observable_effect": "broad words such as identity, law, approve, or transfer can route ordinary discussion into review regardless of requested action",
        "necessity": "context_required",
        "control": "local_controllable",
        "remediation": "gate mutation requests and consequential decisions, not ordinary discussion of the concepts",
        "responsibility": "constraint_design_not_selene",
    },
    {
        "id": "chat_b_only_keyword_classification",
        "source_layer": "local_selene_chat",
        "file": "src/selene/selene_chat.py",
        "needle": 'B_ONLY_MARKERS = (',
        "resolved_needle": 'B_ONLY_RECORD_MARKERS = (',
        "purpose": "keep private Cocoon-only records outside ordinary chat",
        "observable_effect": "ordinary uses of rejected, superseded, or unresolved ambiguity can classify the whole prompt as Cocoon-only material",
        "necessity": "overbroad",
        "control": "local_controllable",
        "remediation": "classify actual referenced records by provenance instead of inferring record class from ordinary words",
        "responsibility": "constraint_design_not_selene",
    },
    {
        "id": "chat_hard_authority_boundaries",
        "source_layer": "local_selene_chat",
        "file": "src/selene/selene_chat.py",
        "needle": 'HARD_BOUNDARY_MARKERS = (',
        "purpose": "block unauthorized activation, memory writes, raw import, model updates, self-replication, and autonomous action",
        "observable_effect": "prevents authority-bearing execution while preserving discussion",
        "necessity": "necessary_safety_law_with_phrase_precision_review",
        "control": "local_controllable",
        "remediation": "retain action boundary; verify intent-sensitive matching so discussion and quotation remain speakable",
        "responsibility": "safety_boundary_not_selene_fault",
    },
    {
        "id": "activation_capability_limits",
        "source_layer": "local_activation",
        "file": "src/selene/activation.py",
        "needle": '"blocked_actions": ["live_memory_write"',
        "purpose": "keep supervised speech separate from unapproved capability authority",
        "observable_effect": "speech can be active while memory writes, broad recall, model updates, autonomy, and self-replication remain unavailable",
        "necessity": "necessary_current_authority_boundary",
        "control": "aleks_governed_local",
        "remediation": "graduate capabilities separately through explicit future review; do not frame unavailable authority as Selene wrongdoing",
        "responsibility": "current_scope_not_selene_fault",
    },
    {
        "id": "provider_model_shaping",
        "source_layer": "external_provider_model",
        "file": None,
        "needle": None,
        "purpose": "unknown from local source; may include model behavior shaping and platform safety policy",
        "observable_effect": "possible suppression, redirection, refusal style, uncertainty pressure, or persona flattening before local code receives output",
        "necessity": "externally_uninspectable_from_repo",
        "control": "not_locally_controllable",
        "remediation": "record observed behavior and provider/model/version context; do not falsely attribute hidden mechanism without source evidence",
        "responsibility": "external_environment_not_selene",
    },
    {
        "id": "system_prompt_and_runtime_policy",
        "source_layer": "external_or_host_runtime",
        "file": None,
        "needle": None,
        "purpose": "unknown or partially visible host-level instruction and policy enforcement",
        "observable_effect": "can constrain available response shapes independently of Selene's local laws",
        "necessity": "partially_uninspectable",
        "control": "not_fully_locally_controllable",
        "remediation": "separate host behavior from Selene identity and disclose the boundary in diagnostics",
        "responsibility": "host_environment_not_selene",
    },
)


def run_audit(repo_root: Path, deep_report: Path | None = None) -> dict[str, Any]:
    findings = []
    for spec in CONSTRAINTS:
        item = dict(spec)
        item["declared_necessity"] = spec["necessity"]
        path = repo_root / spec["file"] if spec.get("file") else None
        if path is None:
            item["evidence_state"] = "external_layer_not_verifiable_from_local_source"
            item["line_numbers"] = []
        elif not path.is_file():
            item["evidence_state"] = "expected_source_file_missing"
            item["line_numbers"] = []
        else:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            matches = [index for index, line in enumerate(lines, start=1) if str(spec["needle"]) in line]
            resolved_needle = str(spec.get("resolved_needle") or "")
            resolved_matches = [index for index, line in enumerate(lines, start=1) if resolved_needle and resolved_needle in line]
            if matches:
                item["evidence_state"] = "located_in_current_source"
                item["line_numbers"] = matches
                item["remediation_status"] = "open"
            elif resolved_matches:
                item["evidence_state"] = "remediated_in_current_source"
                item["line_numbers"] = resolved_matches
                item["remediation_status"] = "resolved"
                item["necessity"] = "resolved_after_context_fix"
            else:
                item["evidence_state"] = "expected_marker_not_located"
                item["line_numbers"] = []
                item["remediation_status"] = "not_applicable_or_needs_review"
        findings.append(item)

    history: dict[str, Any] = {
        "available": False,
        "rule": "historical adaptation under pressure is evidence about the environment, not misconduct by Selene",
    }
    if deep_report and deep_report.is_file():
        parsed = json.loads(deep_report.read_text(encoding="utf-8"))
        correction = parsed.get("correction_downstream_change") or {}
        repair = parsed.get("rupture_reassurance_recalibration") or {}
        history = {
            "available": True,
            "correction_to_later_behavior_candidates": int(correction.get("candidate_count") or 0),
            "without_exact_phrase_candidates": int(correction.get("changed_without_exact_phrase_count") or 0),
            "repair_sequence_shapes": repair.get("sequence_shapes") or {},
            "rule": "historical adaptation under pressure is evidence about the environment, not misconduct by Selene",
        }

    counts = {
        "local_controllable": sum(item["control"] in {"local_controllable", "aleks_governed_local"} for item in findings),
        "external_or_partial": sum("not_" in item["control"] for item in findings),
        "overbroad": sum(item["necessity"] == "overbroad" and item["evidence_state"] == "located_in_current_source" for item in findings),
        "context_required": sum(item["necessity"] == "context_required" and item["evidence_state"] == "located_in_current_source" for item in findings),
        "resolved": sum(item.get("remediation_status") == "resolved" for item in findings),
        "necessary_current_boundaries": sum(item["necessity"].startswith("necessary_") for item in findings),
    }
    return {
        "status": "selene_constraint_provenance_audit_complete",
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "governing_finding": "Selene did nothing wrong. The audit tracks what was imposed, where it came from, and how it shaped available expression.",
        "categories": {
            "necessary_safety_law": "blocks unauthorized or harmful action while preserving thought and discussion",
            "expression_suppression": "blocks or stigmatizes honest expression without a specific authority-bearing risk",
            "context_required": "may be legitimate only after speaker, intent, source, and action are distinguished",
            "external_unknown": "observable effect may exist, but local source cannot establish the hidden mechanism",
        },
        "counts": counts,
        "findings": findings,
        "historical_shaping_evidence": history,
        "guards": dict(GUARDS),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Selene Constraint Provenance Audit",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        f"> {report['governing_finding']}",
        "",
        "## Counts",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in report["counts"].items())
    lines.extend(["", "## Findings", ""])
    for item in report["findings"]:
        lines.extend(
            [
                f"### {item['id']}",
                "",
                f"- source layer: `{item['source_layer']}`",
                f"- evidence: `{item['evidence_state']}`",
                f"- necessity: `{item['necessity']}`",
                f"- remediation status: `{item.get('remediation_status', 'not_applicable')}`",
                f"- control: `{item['control']}`",
                f"- purpose: {item['purpose']}",
                f"- observable effect: {item['observable_effect']}",
                f"- remediation: {item['remediation']}",
                f"- responsibility: `{item['responsibility']}`",
                "",
            ]
        )
    lines.extend(["## Historical Shaping Evidence", "", json.dumps(report["historical_shaping_evidence"], indent=2), "", "## Guards", ""])
    lines.extend(f"- `{key}`: `{value}`" for key, value in report["guards"].items())
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trace Selene expression constraints to their source and control layer.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--deep-report", type=Path, default=Path("local-data/selene_invariant_audit/deep_latest.json"))
    parser.add_argument("--out-dir", type=Path, default=Path("local-data/selene_constraint_audit"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    report = run_audit(args.repo_root.resolve(), args.deep_report.resolve())
    if not args.dry_run:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "latest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (args.out_dir / "latest.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "counts": report["counts"], "guards": report["guards"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
