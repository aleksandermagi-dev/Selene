from __future__ import annotations

import re
from typing import Any


SEMANTIC_ARBITRATION_BOUNDARY = (
    "current_turn_sense_arbitration_only_no_memory_identity_governance_"
    "personality_authority_training_or_action"
)


_LITERAL_CUES: dict[str, tuple[str, ...]] = {
    "sound": (
        "acoustic", "audio", "bell", "decibel", "hear", "hearing", "loud",
        "loudness", "microphone", "noise", "pitch", "speaker", "tone",
        "vibrate", "vibrating", "vibration", "wave",
    ),
    "weight": (
        "balance", "force", "gravity", "gravitational", "heavy", "kilogram",
        "mass", "newton", "object", "scale", "weigh",
    ),
    "matter": (
        "atom", "gas", "liquid", "material", "molecule", "particle", "physical",
        "plasma", "solid",
    ),
    "light": (
        "beam", "bright", "bulb", "dark", "illuminate", "lamp", "lens",
        "optical", "photon", "ray", "reflect", "shadow", "transmit",
    ),
    "state": (
        "code", "function", "program", "runtime", "software", "variable",
    ),
    "function": (
        "argument", "call", "code", "method", "parameter", "program", "return",
        "runtime", "software", "variable",
    ),
    "field": (
        "electric", "electromagnetic", "force", "gravitational", "magnetic",
        "physics", "vector",
    ),
    "point": (
        "angle", "coordinate", "geometry", "line", "plane", "vertex",
    ),
    "current": (
        "amp", "ampere", "circuit", "electric", "electricity", "flow", "river",
        "voltage", "water",
    ),
}


def build_canonical_meaning_frame(
    text: str,
    *,
    routing_text: str = "",
    dialogue_acts: list[str] | tuple[str, ...] | None = None,
    primary_intent: str = "",
    selected_domain: str = "",
) -> dict[str, Any]:
    """Resolve bounded pragmatic/literal collisions before source retrieval.

    The frame does not supply an answer.  It makes the selected current-turn
    reading inspectable and prevents a word used as a conversational action or
    figure of speech from silently becoming an academic subject anchor.
    """

    surface = " ".join(str(text or "").lower().replace("’", "'").split())
    routed = " ".join(str(routing_text or surface).lower().split())
    acts = [str(item) for item in dialogue_acts or [] if str(item)]
    constructions: list[dict[str, Any]] = []
    protected: set[str] = set()
    literal_evidence: dict[str, list[str]] = {}

    def add_pragmatic(surface_form: str, sense: str, terms: tuple[str, ...]) -> None:
        constructions.append(
            {
                "surface": surface_form,
                "selected_sense": sense,
                "reading_type": "pragmatic_or_figurative",
                "protected_knowledge_terms": list(terms),
            }
        )
        protected.update(terms)

    # Evaluation/linking uses of "sound" describe how an idea is received;
    # they are not requests about acoustics unless the turn also names an
    # acoustic subject.
    if re.search(r"\bhow (?:does|would|did)\b.{0,180}\bsound(?:s|ed)?\b", routed):
        cues = _present_cues(routed, "sound")
        if cues:
            literal_evidence["sound"] = cues
        else:
            add_pragmatic("how ... sound", "request_for_evaluation", ("sound",))
    elif re.search(r"\b(?:that|this|it|which|idea|plan|option)\b.{0,45}\bsounds?\b", routed):
        cues = _present_cues(routed, "sound")
        if cues:
            literal_evidence["sound"] = cues
        else:
            add_pragmatic("... sounds ...", "evaluation_or_impression", ("sound",))

    if re.search(
        r"\b(?:give|assign|carry|carries|put|place)\b.{0,45}\bweight\b|"
        r"\bweight\b.{0,45}\b(?:give|assign|evidence|claim|idea|factor|decision|clue)\b",
        routed,
    ):
        add_pragmatic("give/carry weight", "importance_or_evidentiary_weight", ("weight",))
    elif "weight" in routed:
        cues = _present_cues(routed, "weight")
        if cues:
            literal_evidence["weight"] = cues

    if re.search(r"\b(?:does|do|did|would|should)\b.{0,65}\bmatter\b|\bwhat matters\b", routed):
        add_pragmatic("... matter", "importance_or_relevance", ("matter",))
    elif "matter" in routed:
        cues = _present_cues(routed, "matter")
        if cues:
            literal_evidence["matter"] = cues

    if re.search(r"\b(?:shed|sheds|shedding|cast)\b.{0,25}\blight\b|\bin light of\b", routed):
        add_pragmatic("shed/in light", "clarification_or_context", ("light",))
    elif "light" in routed:
        cues = _present_cues(routed, "light")
        if cues:
            literal_evidence["light"] = cues

    if re.search(r"\b(?:current|present) state of (?:this|the|our|my)\b|\bwhere (?:does|do|are) (?:this|we) stand\b", routed):
        add_pragmatic("current state", "status_of_current_work_or_topic", ("current", "state"))
    elif "state" in routed:
        cues = _present_cues(routed, "state")
        if cues:
            literal_evidence["state"] = cues

    if re.search(r"\b(?:function|purpose) of (?:this|that|the) (?:step|idea|part|phase|choice|discussion)\b", routed):
        add_pragmatic("function/purpose of this", "purpose_in_context", ("function",))
    elif "function" in routed:
        cues = _present_cues(routed, "function")
        if cues:
            literal_evidence["function"] = cues

    if re.search(r"\bwhat (?:field|domain|area|discipline)\b.{0,55}\b(?:idea|work|topic|question|belong)\b|\bfield does (?:this|that)\b", routed):
        add_pragmatic("field/domain of an idea", "discipline_or_topic_classification", ("field",))
    elif "field" in routed:
        cues = _present_cues(routed, "field")
        if cues:
            literal_evidence["field"] = cues

    if re.search(r"\b(?:point of this|first point|second point|main point|your point|my point|the point about)\b|\bcircle back\b", routed):
        add_pragmatic("point/circle back", "discourse_topic_or_purpose", ("point", "circle"))
    elif "point" in routed:
        cues = _present_cues(routed, "point")
        if cues:
            literal_evidence["point"] = cues

    if re.search(r"\b(?:record|preserve|keep|hold)\b.{0,55}\b(?:conversation|discussion|thought|note|thread|work|this|that|it)\b", routed):
        add_pragmatic("record/preserve/keep current material", "conversation_or_workspace_management", ("record", "preserve", "keep", "hold"))

    if re.search(r"\b(?:circle|get|come|go|return|going) back to\b|\b(?:table|park) (?:this|that|it)\b", routed):
        add_pragmatic("return/table topic", "conversation_management", ("back", "return", "table", "park"))

    if "current" in routed and "current" not in protected:
        cues = _present_cues(routed, "current")
        if cues:
            literal_evidence["current"] = cues

    deferred_return = bool(
        re.search(
            r"\b(?:get|come|go|return|going) back to\b.{0,100}\b(?:later|tomorrow|next time|another time)\b",
            routed,
        )
        or re.search(
            r"\b(?:later|tomorrow|next time|another time)\b.{0,100}\b(?:get|come|go|return) back to\b",
            routed,
        )
    )
    primary_social = next(
        (item for item in acts if item in {"farewell", "greeting", "gratitude", "warm_connection", "playful_connection"}),
        "",
    )
    selected_reading = (
        "mixed_literal_and_pragmatic"
        if constructions and literal_evidence
        else "pragmatic_or_figurative"
        if constructions
        else "literal_domain"
        if literal_evidence
        else "ordinary_literal"
    )
    posture = (
        "hold_for_social_or_conversation_management"
        if deferred_return or (primary_intent == "farewell" and not _substantive_request(routed))
        else "require_independent_subject_alignment"
        if protected
        else "literal_subject_alignment_allowed"
    )

    return {
        "status": "canonical_turn_meaning_framed",
        "version": "v1_pragmatic_literal_arbitration",
        "selected_reading": selected_reading,
        "primary_dialogue_function": primary_social or primary_intent or "direct_conversation",
        "selected_domain": selected_domain or "ordinary_conversation",
        "pragmatic_constructions": constructions,
        "protected_knowledge_terms": sorted(protected),
        "literal_domain_evidence": literal_evidence,
        "academic_knowledge_posture": posture,
        "deferred_return": deferred_return,
        "contextual_override_policy": (
            "preserve_primary_social_act_without_a_substantive_current_request"
        ),
        "single_ambiguous_word_is_academic_route_authority": False,
        "answer_content_supplied": False,
        "session_scoped_only": True,
        "memory_write_active": False,
        "identity_change": False,
        "personality_change": False,
        "governance_change": False,
        "authority_change": False,
        "training_allowed": False,
        "lora_allowed": False,
        "autonomous_action_allowed": False,
        "provenance_boundary": SEMANTIC_ARBITRATION_BOUNDARY,
    }


def _present_cues(text: str, sense: str) -> list[str]:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return [
        cue
        for cue in _LITERAL_CUES.get(sense, ())
        if cue in tokens or f"{cue}s" in tokens
    ]


def _substantive_request(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:answer|calculate|compare|define|describe|explain|find|plan|recommend|review|solve|summarize|tell me|walk me through)\b",
            text,
        )
        or "?" in text
    )
