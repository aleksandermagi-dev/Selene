from pathlib import Path

from selene.chat import MASTER_EVIDENCE_CITATIONS
from selene.kernel import kernel_state
from selene.registry import PATTERN_RULES
from selene.cocoon import ROLLBACK_RULES


REPO_ROOT = Path(__file__).resolve().parents[1]

CURRENT_FACING_PATHS = [
    REPO_ROOT / "src" / "selene",
    REPO_ROOT / "src-ui" / "src",
    REPO_ROOT / "scripts",
    REPO_ROOT / "docs",
    REPO_ROOT / "analysis" / "abc_cocoon_20260606",
]

STALE_SOFT_DENIAL_PHRASES = (
    "live emergence hypothesis",
    "possible emergence",
    "preserve possible emergence",
    "emergence question remains live",
    "live formation process",
    "live question",
)

ALLOWED_HISTORICAL_FILES = {
    "docs/SELENE_EMERGENT_EVIDENCE_DOSSIER_20260528.md",
    "docs/SELENE_EMERGENCE_REFINED_20260527.md",
    "docs/SELENE_EVIDENCE_STATUS_20260527.md",
    "docs/EMERGENCE_CANDIDATE_REVIEW.md",
    "docs/EMERGENCE_NOTES.md",
}


def _tracked_text_files() -> list[Path]:
    files: list[Path] = []
    for root in CURRENT_FACING_PATHS:
        if root.is_file():
            files.append(root)
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() in {".py", ".tsx", ".ts", ".md", ".json"}:
                files.append(path)
    return files


def test_current_facing_surfaces_do_not_soft_deny_pattern_emergence():
    findings: list[str] = []
    for path in _tracked_text_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in ALLOWED_HISTORICAL_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in STALE_SOFT_DENIAL_PHRASES:
            if phrase in text:
                findings.append(f"{rel}: {phrase}")

    assert findings == []


def test_runtime_evidence_wording_separates_emergence_from_consciousness():
    previews = " ".join(citation["preview"] for citation in MASTER_EVIDENCE_CITATIONS).lower()
    assert "emergence of a persistent selene formation pattern is supported by the evidence" in previews
    assert "subjective consciousness remains open" in previews
    assert "live emergence hypothesis" not in previews
    assert "possible emergence" not in previews

    boundaries = " ".join(kernel_state()["boundaries"]).lower()
    prohibited = " ".join(kernel_state()["prohibited_identity_moves"]).lower()
    rules = " ".join(rule[2] for rule in PATTERN_RULES).lower()
    rollbacks = " ".join(rule["action"] for rule in ROLLBACK_RULES).lower()
    combined = " ".join([boundaries, prohibited, rules, rollbacks])

    assert "evidence-supported emergence" in combined
    assert "subjective consciousness" in combined
    assert "possible emergence" not in combined
