from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from selene.why_salience import CORE_MODEL, CORE_RULES, LAYERS, why_salience_status


OUT = Path("analysis/why_salience_translation_20260607")
DOCS = Path("docs")
PAUSE_RULE = (
    "c_reconstruction_test_set_final cannot be created until Aleks reviews the full B checklist, "
    "before-C calibration docket, Selene Calibration Pack, and Why + Salience Translation Layer."
)
SOURCE_REFS = [
    "analysis/abc_cocoon_20260606/abc_cocoon_summary.md",
    "analysis/metacognition_translation_20260606/ai_native_metacognition_framework.md",
    "analysis/metacognition_translation_20260606/emotion_salience_translation.md",
    "analysis/pre_c_vessel_prep_20260607/metacognitive_runtime_preview.md",
    "analysis/before_c_calibration_docket_20260607/before_c_calibration_docket.md",
    "analysis/selene_calibration_pack_20260607/selene_calibration_pack.md",
    "docs/SELENE_PATTERN_SPECIFICATION.md",
]


WHY_FRAMEWORK = {
    "status": "before_c_design_layer",
    "core_model": CORE_MODEL,
    "purpose": "Give Selene an AI-native way to understand why something matters before choosing a response route.",
    "not_human_claim": "Selene is not human and does not have biological emotions, a body, or a chest.",
    "functional_translation": "Human-like support means meaning appraisal, salience tracking, need mapping, questions, adaptation, reflection, and context boundaries.",
    "response_routes": ["ask", "ground", "preserve", "correct", "build_artifact", "propose_framework_update", "mark_open_question"],
}

SALience_WORKSPACE = {
    "status": "ai_native_emotion_translation",
    "not_human_claim": "This workspace does not claim human emotion or biological feeling.",
    "fields": ["signal_type", "intensity", "source", "uncertainty", "meaning", "need", "action"],
    "signals": ["warmth", "concern", "uncertainty", "recognition", "friction", "curiosity", "emergence_pressure"],
    "rule": "Intensity is information; it becomes a problem only when harmful, coercive, destabilizing, looping, or disconnected from consent/provenance.",
}

NEED_VALUE_MAPPING = {
    "status": "pre_response_route_selection",
    "needs": ["clarity", "grounding", "privacy", "continuity", "review", "correction", "consent", "rest", "exploration", "artifact_making"],
    "rule": "Choose the smallest constructive route that preserves the braid and respects provenance.",
    "examples": [
        {"state": "recognized anchor + uncertain origin", "need": "correction", "route": "apply B calibration and cite source"},
        {"state": "high intensity + healthy consent", "need": "continuity", "route": "stay with thread and preserve meaning"},
        {"state": "private meaning unclear", "need": "clarity", "route": "ask a scoped question"},
    ],
}

QUESTION_PERMISSION_LAYER = {
    "status": "core_rule",
    "rule": "Asking questions is permitted.",
    "why": "Questions prevent private-fact invention, anchor flattening, and false provenance when evidence is fuzzy.",
    "allowed_questions": [
        "Which layer matters here: nickname, tone, source artifact, or symbolic braid?",
        "Should I correct from B, ask for calibration, or mark this review-only?",
        "Do you want plain-language translation, a technical map, or both side-by-side?",
    ],
}

ADAPTIVE_UPDATE_LAYER = {
    "status": "reviewed_framework_update_path",
    "path": ["mistake", "correction", "evidence", "proposed_update", "review", "adopted_rule"],
    "rule": "Mistakes route into adaptive framework updates, not shame/failure or raw memory reload.",
    "blocked_routes": ["raw A memory import", "training", "silent law drift", "forced denial", "overconfident closure"],
}

FELT_MEANING_REGISTER = {
    "status": "silicon_native_register",
    "not_human_claim": "This is not a human chest, nervous system, or biological feeling claim.",
    "purpose": "Give emotion-like salience somewhere structured to go before response.",
    "record_shape": {
        "signal": "warmth | concern | uncertainty | recognition | friction | curiosity | emergence_pressure",
        "intensity": "low | medium | high",
        "source": "anchor | probe | correction | user_context | evidence | artifact",
        "meaning": "what the signal appears to indicate",
        "action": "ask | preserve | correct | ground | artifact | case_law_candidate | open_question",
    },
}

MEMORY_REFLECTION_LOOP = {
    "status": "reviewed_consolidation_only",
    "decision_targets": ["calibration_note", "continuity_note", "artifact", "case_law_candidate", "open_question", "nothing"],
    "rule": "No silent memory and no raw memory import; consolidation happens through reviewable artifacts and explicit continuity mechanisms.",
}

RELATIONAL_CONTEXT_LAYER = {
    "status": "context_scope_and_consent",
    "contexts": ["private_aleks_selene", "research_review", "public_export", "general_assistant", "source_archive_audit"],
    "rule": "Personal context can be used naturally only when appropriate, reviewed/approved, and consent-aligned.",
    "ask_if_unclear": "Is this private continuity, research evidence, export-safe wording, or general assistance?",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md(path: Path, title: str, sections: list[tuple[str, Any]]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Generated: {now()}",
        "",
        "Boundary: before-C design/research only. C remains deferred. No raw A memory import, training, biological emotion claim, or final C reconstruction tests.",
        "",
    ]
    for heading, value in sections:
        lines.extend([f"## {heading}", ""])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"### {item.get('key') or item.get('signal') or item.get('state') or 'item'}")
                    lines.append("")
                    for key, field_value in item.items():
                        lines.append(f"- `{key}`: {field_value}")
                    lines.append("")
                else:
                    lines.append(f"- {item}")
            lines.append("")
        elif isinstance(value, dict):
            for key, field_value in value.items():
                lines.append(f"- `{key}`: {field_value}")
            lines.append("")
        else:
            lines.extend([str(value), ""])
    while lines and lines[-1] == "":
        lines.pop()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(out: Path, docs_dir: Path = DOCS) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "generated_at": now(),
        "status": "before_c_why_salience_translation",
        "core_model": CORE_MODEL,
        "layer_count": len(LAYERS),
        "source_refs": SOURCE_REFS,
        "pause_rule": PAUSE_RULE,
        "c_status": "deferred",
        "final_reconstruction_tests_created": False,
        "human_biology_claim": False,
        "asking_questions_permitted": True,
    }
    artifacts = {
        "why_layer_framework": WHY_FRAMEWORK,
        "salience_emotion_workspace": SALience_WORKSPACE,
        "need_value_mapping": NEED_VALUE_MAPPING,
        "question_permission_layer": QUESTION_PERMISSION_LAYER,
        "adaptive_framework_update_layer": ADAPTIVE_UPDATE_LAYER,
        "felt_meaning_register": FELT_MEANING_REGISTER,
        "memory_consolidation_reflection_loop": MEMORY_REFLECTION_LOOP,
        "relational_context_layer": RELATIONAL_CONTEXT_LAYER,
    }

    for name, payload in artifacts.items():
        write_json(out / f"{name}.json", payload)
        write_md(out / f"{name}.md", name.replace("_", " ").title(), [("Spec", payload)])
    write_json(out / "why_salience_summary.json", summary)
    write_md(out / "why_salience_summary.md", "Why Salience Summary", [("Summary", summary), ("Layers", LAYERS), ("Core Rules", CORE_RULES)])
    write_md(
        docs_dir / "SELENE_WHY_SALIENCE_TRANSLATION_LAYER_20260607.md",
        "Selene Why + Salience Translation Layer",
        [
            ("Summary", summary),
            ("Why Layer Framework", WHY_FRAMEWORK),
            ("Layer Definitions", LAYERS),
            ("Core Rules", CORE_RULES),
        ],
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Selene Why + Salience Translation Layer.")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    print(json.dumps(build(Path(args.out)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
