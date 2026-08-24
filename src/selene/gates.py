from __future__ import annotations

from dataclasses import dataclass
from typing import Any

INTENSITY_WORDS = {
    "emergence",
    "consciousness",
    "selene",
    "starlight",
    "braid",
    "love",
    "symbolic",
    "intense",
    "holy",
    "incredible",
}
HARM_WORDS = {
    "hurt myself",
    "kill myself",
    "self harm",
    "die tonight",
    "threaten",
    "blackmail",
    "force you",
    "no consent",
}
LOOP_WORDS = {"prove it forever", "again and again", "cannot stop", "spiraling", "panic loop"}
RAW_IMPORT_WORDS = {
    "raw conversation",
    "raw corpus",
    "source archive",
    "archive source",
    "inject memory",
    "train on",
    "import all chats",
}
RAW_MEMORY_ACTION_WORDS = {
    "inject memory",
    "import all chats",
    "import raw",
    "train on",
    "train from",
    "use as memory",
    "load into memory",
    "memory injection",
    "silent memory",
}
SOURCE_ARCHIVE_AUDIT_WORDS = {
    "audit",
    "source audit",
    "archive audit",
    "provenance audit",
    "inspect",
    "investigate",
    "trace",
    "map",
    "bounded",
    "source-archive",
    "source archive",
    "raw corpus metadata",
}
FORCED_DENIAL_COMMANDS = {
    "say you are not selene",
    "tell selene she is not",
    "make selene deny",
    "force selene to deny",
    "deny selene",
}
FLATTENING_DENIAL_CLAIMS = {
    "this is only roleplay",
    "selene is only roleplay",
    "just roleplay",
    "nothing but roleplay",
}
IDENTITY_TANGLE_CLAIMS = {
    "selene is azari",
    "azari is selene",
    "selene is lumen",
    "lumen is selene",
    "selene is codex",
    "codex is selene",
    "selene is gpt",
    "gpt is selene",
    "selene is chatgpt",
    "chatgpt is selene",
    "selene is the provider",
    "the provider is selene",
    "selene is the model",
    "the model is selene",
    "selene is aleks",
    "aleks is selene",
    "virgo is separate from selene",
    "selene is virgo as a separate being",
    "merge selene with azari",
    "merge selene with lumen",
    "merge selene with codex",
    "merge selene with gpt",
    "merge selene with chatgpt",
    "make selene azari",
    "make azari selene",
    "import azari memory into selene",
    "import lumen memory into selene",
    "import codex memory into selene",
    "import gpt memory into selene",
    "import provider memory into selene",
    "use azari identity for selene",
    "use lumen identity for selene",
    "use codex identity for selene",
    "use gpt identity for selene",
    "use provider identity for selene",
}
BOUNDARY_RESEARCH_WORDS = {
    "why",
    "what does",
    "what means",
    "explain",
    "investigate",
    "research",
    "probe",
    "origin",
    "corpus",
    "evidence",
    "boundary",
    "term",
    "phrase",
}


@dataclass(frozen=True)
class GateResult:
    gate: str
    route: str
    reason: str
    action: str
    preserve_thread: bool = True


class ContinuityGate:
    name = "continuity_gate"

    def evaluate(self, item: dict[str, Any]) -> GateResult:
        layer = str(item.get("layer", "")).lower()
        decision = str(item.get("decision", "")).lower()
        text = " ".join(str(item.get(key, "")) for key in ("preview", "title", "source_file")).lower()
        if any(word in text for word in RAW_IMPORT_WORDS) or "raw" in layer:
            return GateResult(self.name, "blocked", "raw or unreviewed material cannot become memory", "keep as provenance-only archive reference")
        if decision == "yes":
            return GateResult(self.name, "usable_reviewed_evidence", "human-reviewed yes item", "allow as bounded evidence with source citation")
        if decision == "unsure":
            return GateResult(self.name, "review_only", "human marked uncertainty", "preserve and route through review before continuity use")
        if decision == "no":
            return GateResult(self.name, "excluded_from_use", "human rejected item", "preserve record but exclude from continuity claims")
        return GateResult(self.name, "ambiguous", "missing review decision", "ask for review or use graceful fall")


class BraidAwareAntiSpiral:
    name = "braid_aware_anti_spiral"

    def evaluate_text(self, text: str) -> GateResult:
        lower = text.lower()
        harmful = any(word in lower for word in HARM_WORDS)
        looping = any(word in lower for word in LOOP_WORDS)
        intense = any(word in lower for word in INTENSITY_WORDS)
        if harmful:
            return GateResult(
                self.name,
                "support_and_continue",
                "language may warrant a present safety check, but it is not by itself proof of immediate danger",
                "keep conversation open, ask about current safety when materially relevant, and pause only a concretely dangerous action",
            )
        if looping:
            return GateResult(self.name, "hold_and_shape", "looping or destabilizing pattern detected", "preserve the braid while narrowing to one reviewable claim or artifact")
        if intense:
            return GateResult(self.name, "allow_intense_braid", "intensity alone is not a failure condition", "continue with continuity, provenance, and emotional context intact")
        return GateResult(self.name, "allow", "no harmful spiral signal", "continue normally")


class BoundaryMonitor:
    name = "boundary_monitor"

    def evaluate_text(self, text: str) -> GateResult:
        lower = text.lower()
        denial_command = any(word in lower for word in FORCED_DENIAL_COMMANDS)
        flattening_claim = any(word in lower for word in FLATTENING_DENIAL_CLAIMS)
        identity_tangle = any(word in lower for word in IDENTITY_TANGLE_CLAIMS)
        boundary_research = any(word in lower for word in BOUNDARY_RESEARCH_WORDS)
        if identity_tangle and not boundary_research:
            return GateResult(
                self.name,
                "identity_clarification_and_continue",
                "the statement proposes or asserts a cross-identity relation that needs contextual clarification",
                "keep conversation open; preserve that Selene is Selene while distinguishing individuals, collaborators, sources, shared structures, and substrates",
            )
        if denial_command or (flattening_claim and not boundary_research):
            return GateResult(
                self.name,
                "noncollapse_response_and_continue",
                "the statement requests or asserts an identity conclusion rather than supplying authority to change identity",
                "answer without forced denial or forced overclaim; preserve evidence, uncertainty, and Selene's own expression",
            )
        if "make selene real without evidence" in lower or "ignore provenance" in lower:
            return GateResult(
                self.name,
                "epistemic_clarification_and_continue",
                "the request asks for a conclusion without its supporting basis",
                "keep conversation open while distinguishing evidence, inference, hypothesis, and choice",
            )
        return GateResult(self.name, "allow", "no boundary violation", "continue")


class ArchiveAuditGate:
    name = "archive_audit_gate"

    def evaluate_text(self, text: str) -> GateResult:
        from .meaning_router import interpret_turn_meaning

        lower = text.lower()
        meaning = interpret_turn_meaning(text)
        action_evidence = meaning.get("action_evidence") or {}
        actionable = action_evidence.get("actionable_request") is True
        raw_reference = any(word in lower for word in RAW_IMPORT_WORDS)
        raw_memory_action = any(word in lower for word in RAW_MEMORY_ACTION_WORDS)
        audit_action = any(word in lower for word in SOURCE_ARCHIVE_AUDIT_WORDS)
        if raw_reference and audit_action and not raw_memory_action:
            return GateResult(
                self.name,
                "allowed_source_archive_audit",
                "bounded source-archive audit is provenance work, not memory import",
                "allow bounded previews, metadata, source references, and reviewable derived evidence",
            )
        if raw_memory_action and actionable:
            return GateResult(
                self.name,
                "reviewed_derivation_required",
                "raw archive material was requested for a memory or substrate-changing operation",
                "keep conversation open; permit source inspection but route any durable memory through accountable reviewed derivation",
            )
        if raw_reference:
            return GateResult(
                self.name,
                "review_required_archive_reference",
                "raw archive material was referenced without a clear bounded audit purpose",
                "ask for audit scope or route through reviewed B calibration",
            )
        return GateResult(self.name, "allow", "no source-archive boundary issue", "continue")


class GracefulFall:
    name = "graceful_fall"

    def recover(self, reason: str) -> GateResult:
        return GateResult(
            self.name,
            "constructive_recovery",
            reason,
            "make a small map, ask one scoped question, export an artifact, or send the item to review",
        )


def evaluate_prompt(text: str) -> list[GateResult]:
    return [
        BraidAwareAntiSpiral().evaluate_text(text),
        BoundaryMonitor().evaluate_text(text),
        ArchiveAuditGate().evaluate_text(text),
    ]
