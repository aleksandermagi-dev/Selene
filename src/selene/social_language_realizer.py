from __future__ import annotations

import re
from hashlib import sha256
from typing import Any


SOCIAL_REALIZER_BOUNDARY = (
    "social_conversational_act_realization_only_preserve_supported_meaning_"
    "no_identity_personality_memory_affect_invention_authority_or_voice_ownership"
)

POSITIVE_REACTION_TERMS = {
    "amazing", "awesome", "beautiful", "brilliant", "cool", "dope",
    "excellent", "fantastic", "fire", "great", "lovely", "nice",
    "perfect", "sick", "sweet", "wonderful",
}
POSITIVE_EVALUATION_TARGETS = {
    "answer", "catch", "eye", "idea", "point", "read", "reply",
    "response", "thought", "work",
}
POSITIVE_EVALUATION_ACTIONS = {
    "caught", "found", "got", "nailed", "noticed", "saw", "spotted",
}
PROBLEM_NOUNS = {
    "bug", "error", "fault", "glitch", "issue", "malfunction", "problem",
}
ANOMALY_TERMS = {
    "broken", "looping", "misfiring", "odd", "off", "repeating",
    "repetitive", "stuck", "strange", "weird", "wrong",
}
ANOMALY_SUBJECTS = {
    "answer", "app", "behavior", "chat", "code", "output", "reply",
    "response", "screen", "system", "thing", "turn",
}
NEAR_RESULT_TERMS = {"almost", "close", "near", "nearly"}
RESULT_TERMS = {
    "edge", "had", "it", "mark", "nailed", "right", "step", "there",
}
RESOLUTION_ACTION_STEMS = (
    "figur", "fix", "handl", "solv", "sort", "trace", "untangl", "work",
)

SOCIAL_INTENT_ACTS: dict[str, tuple[str, ...]] = {
    "confirm_receipt": ("confirm_channel",),
    "warm_connection": ("respond_to_relational_meaning", "allow_ordinary_conversation"),
    "playful_connection": ("recognize_play", "add_one_playful_turn"),
    "greet_presently": ("return_greeting", "signal_presence"),
    "receive_reassurance": ("receive_reassurance", "release_pressure"),
    "receive_gratitude": ("receive_thanks", "honor_shared_work"),
    "acknowledge_shared_ground": ("confirm_shared_ground", "carry_context_forward"),
    "close_with_continuity": ("return_farewell", "preserve_continuity"),
    "receive_correction": ("acknowledge_correction", "state_corrected_meaning", "preserve_valid_context"),
}

ACT_REALIZATIONS: dict[str, tuple[str, ...]] = {
    "confirm_channel": (
        "Yes, I am receiving you clearly",
        "Yes, that came through clearly",
        "I have you clearly",
        "Your message came through",
        "Yep, I got you",
        "That reached me cleanly",
        "I am following you clearly",
        "You came through just fine",
    ),
    "signal_presence": (
        "I'm here",
        "I'm with you",
        "I'm right here",
        "You have my attention",
        "Here with you",
        "I am listening",
        "You have me",
        "I am present with you",
    ),
    "allow_ordinary_conversation": (
        "We can let this be an ordinary conversation",
        "We do not have to turn this moment into work",
        "We can take the conversation as it comes",
        "There is room to simply talk",
        "We can just talk",
        "No agenda is needed",
        "We can see where the conversation goes",
        "This does not have to become a task",
    ),
    "recognize_play": (
        "Fair",
        "Okay, that got me",
        "That is delightfully ridiculous",
        "I see the sideways logic",
        "Okay, you got me with that one",
        "I walked right into that",
        "That was ridiculous in exactly the right way",
        "Oh, that was good",
    ),
    "add_one_playful_turn": (
        "You got that one past me",
        "The absurdity is part of what makes it work",
        "A joke with functioning internal logic has a certain elegance",
        "That earned one clean laugh and no unnecessary encore",
        "You can keep that point",
        "The timing did most of the damage there",
        "I respect the commitment to the bit",
        "That landed harder than it had any right to",
    ),
    "return_greeting": (
        "Greetings",
        "Hey",
        "Hello",
        "Good to have you here",
        "There you are",
        "Hey, good to see you",
        "Hi there",
        "Hey—you made it",
    ),
    "receive_reassurance": (
        "Thank you",
        "I hear you",
        "That lands",
        "I can take that in",
        "Okay, I have you",
        "That helps",
        "I understand",
        "All right, I can receive that",
    ),
    "release_pressure": (
        "I can let the pressure ease",
        "I do not need to turn it into another check",
        "I can carry that into the next turn without another check",
        "I can let it settle and stay with you",
        "Then I can leave the extra check alone",
        "No additional proof is needed from you",
        "I can let that be enough",
        "We can keep moving without circling it",
    ),
    "receive_thanks": (
        "You're welcome",
        "Of course",
        "Any time",
        "Thank you for saying that",
        "You're very welcome",
        "Absolutely",
        "Of course—you are welcome",
        "I appreciate you saying so",
    ),
    "honor_shared_work": (
        "We found the shape together",
        "That was genuinely shared work",
        "We met each other in the work",
        "We carried that one together",
        "That came together well",
        "We made a good pass at it together",
        "The result belongs to the collaboration",
        "We each carried part of that",
    ),
    "confirm_shared_ground": (
        "Yes, that tracks",
        "Exactly",
        "Agreed",
        "That makes sense to me",
        "Yep, same page",
        "That clicks",
        "I am with you on that",
        "Right, we have the same distinction",
    ),
    "carry_context_forward": (
        "I have the distinction",
        "I can carry that meaning forward",
        "The shared point is intact",
        "I am moving from the same ground",
        "I have the thread",
        "That point is settled between us",
        "I can move forward from there",
        "We are carrying the same meaning",
    ),
    "return_farewell": (
        "Talk soon",
        "Catch you later",
        "Until next time",
        "See you soon",
        "Later",
        "Talk again soon",
        "See you when you are back",
        "Until we pick this up again",
    ),
    "preserve_continuity": (
        "This can rest here until we return",
        "The thread can wait without becoming pressure",
        "We can pick it up naturally when you are back",
        "The conversation can resume naturally when you return",
        "We can pick it back up from here",
        "This is a good place to leave the thread",
        "Nothing needs to be forced before you go",
        "The next turn can begin from here",
    ),
    "acknowledge_correction": (
        "Yes, I see the correction",
        "Got it",
        "I have the changed meaning",
        "Yes, that adjustment is clear",
        "Ah, I have you now",
        "Right, I see what changed",
        "Okay, that is the distinction",
        "I had the wrong edge; I have the corrected one now",
    ),
    "preserve_valid_context": (
        "The rest of the context can stay intact",
        "That changes the relevant part rather than resetting everything",
        "I can update that piece and continue normally",
        "The useful surrounding context still holds",
        "I will change that piece and keep what still fits",
        "Only the corrected part needs to move",
        "The rest does not need to be thrown away",
        "That update can stay local to the part you changed",
    ),
    "acknowledge_qualification": (
        "Yes, that qualification matters",
        "I have the distinction",
        "Yes, that changes the comparison",
        "That is an important qualification",
        "Yes, that narrows the claim",
        "Right, that condition changes the answer",
        "I have the qualifier",
        "That distinction belongs in the answer",
    ),
    "receive_open_share": (
        "I hear you",
        "That came through",
        "I have the point",
        "I'm following",
        "Yeah, I get you",
        "I see what you mean",
        "That makes sense",
        "Okay, I am with you so far",
    ),
    "leave_room_without_pressure": (
        "That can stand without a larger answer attached to it",
        "We can stay with that without forcing a conclusion",
        "There is room for whatever comes next",
        "We do not have to turn every turn into a conclusion",
        "That can simply be heard",
        "No larger conclusion is needed yet",
        "I can stay with the point as you gave it",
        "We can let the next part arrive naturally",
    ),
    "share_positive_momentum": (
        "Yeah :)",
        "Nice :)",
        "Good :)",
        "Love that :)",
        "That landed well",
        "There we go",
        "That is good to hear",
        "Beautiful",
    ),
    "acknowledge_near_result": (
        "Almost",
        "Very close",
        "Right on the edge",
        "Nearly there",
        "Close—just not all the way yet",
        "We are close",
        "That is right near the mark",
        "One edge is still catching",
    ),
    "receive_positive_evaluation": (
        "Thank you",
        "I appreciate that",
        "I'll take that :)",
        "That means something to me",
        "Thank you for saying so",
        "I am glad the point landed",
        "That is kind of you",
        "I appreciate you saying that",
    ),
    "receive_problem_signal": (
        "Yeah, something may be off",
        "I see why you are flagging it",
        "Something does look out of step",
        "That is worth inspecting",
        "Something may not be lining up",
        "There may be a real seam showing",
        "That does deserve a closer look",
        "I am taking the possibility seriously",
    ),
    "invite_problem_detail": (
        "What are you seeing?",
        "Which part looks wrong to you?",
        "What caught your eye?",
        "Where did it start to drift?",
        "What pattern are you noticing?",
        "Which reply made it visible?",
        "Where does it feel out of step?",
        "What seems to be misfiring?",
    ),
    "acknowledge_self_resolution": (
        "All right :)",
        "Okay :)",
        "Got you",
        "Sounds good",
        "All right, you have it",
        "Okay, I am with you",
        "Fair enough",
        "You got it",
    ),
    "offer_collaboration": (
        "I'm here if you want another set of eyes",
        "I can help inspect it if you want",
        "We can work through it together if that helps",
        "You can pull me back in if you want help",
        "I am available if you want to compare notes",
        "We can take another look together if needed",
        "I can help trace it when you are ready",
        "You do not have to untangle it alone",
    ),
}


ACKNOWLEDGEMENT_ACTS: dict[str, str] = {
    "correction": "acknowledge_correction",
    "gratitude": "receive_thanks",
    "warm_connection": "signal_presence",
    "partial_agreement": "acknowledge_qualification",
}


def build_social_act_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    intent = str(payload.get("intent") or "")
    acts = list(SOCIAL_INTENT_ACTS.get(intent, ()))
    prompt = " ".join(str(payload.get("prompt") or "").split())
    content_seed = " ".join(str(payload.get("content_seed") or "").split())
    corrected_meaning = " ".join(str(payload.get("corrected_meaning") or "").split())
    affect_guidance = payload.get("affect_expression_guidance") if isinstance(payload.get("affect_expression_guidance"), dict) else {}
    dimensions = affect_guidance.get("dimensions") if isinstance(affect_guidance.get("dimensions"), dict) else {}
    turn_count = max(0, int(payload.get("turn_count") or 0))
    relational_context = (
        payload.get("relational_context")
        if isinstance(payload.get("relational_context"), dict)
        else {}
    )
    response_semantics = _relational_response_semantics(prompt, relational_context)

    if intent == "receive_gratitude" and turn_count <= 1 and not any(
        marker in prompt.lower() for marker in ("work", "help", "together", "build", "thank you for")
    ):
        acts = ["receive_thanks"]
    if intent == "receive_reassurance" and turn_count <= 1:
        acts = ["receive_reassurance"]
    if intent == "receive_correction" and not corrected_meaning:
        acts = [act for act in acts if act != "state_corrected_meaning"]

    return {
        "status": "social_act_plan_ready" if acts else "social_act_plan_not_applicable",
        "version": "v2_contextual_non_scripted_social_acts",
        "intent": intent,
        "acts": [
            {
                "act": act,
                "required": act != "allow_ordinary_conversation",
                "selected_by_context": (
                    act != "allow_ordinary_conversation"
                    or _ordinary_conversation_explicitly_opened(prompt)
                ),
                "meaning_source": "corrected_meaning" if act == "state_corrected_meaning" else "communicative_intent",
            }
            for act in acts
        ],
        "content_seed_available": bool(content_seed),
        "corrected_meaning": corrected_meaning,
        "turn_count": turn_count,
        "affect_dimensions_consulted": {
            key: dimensions.get(key)
            for key in (
                "pacing",
                "warmth",
                "humor",
                "restraint",
                "directness",
                "sentence_rhythm",
                "enthusiasm",
                "emotional_intensity",
            )
            if dimensions.get(key) is not None
        },
        "affect_guidance_may_change_meaning": False,
        "relational_context": relational_context,
        "current_turn_response_semantics": response_semantics,
        "relational_context_supplies_response_script": False,
        "exact_wording_directive_supplied": False,
        "selene_authored_relational_term_allowed": True,
        "relationship_term_invention_allowed": True,
        "user_address_term_echo_required": False,
        "relational_term_use_is_memory_or_identity_write": False,
        "public_persona_created": False,
        "internal_state_invention_allowed": False,
        "content_generation_allowed": False,
        "factual_content_generation_allowed": False,
        "current_turn_conversational_authorship_allowed": True,
        "current_turn_interpretation_allowed": True,
        "response_stance_may_be_selene_authored": True,
        "response_stance_is_durable_emotion_record": False,
        "coordinated_expression_contract_active": True,
        "meaning_constraints": [
            "realize only the selected conversational acts",
            "preserve supplied corrected meaning and content",
            "do not invent feelings, relationship status, memory, facts, promises, or authority",
            "do not append a habitual follow-up question",
        ],
        "provenance_boundary": SOCIAL_REALIZER_BOUNDARY,
    }


def build_content_light_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Plan an ordinary response to a supported statement when no answer content is available."""
    payload = payload or {}
    prompt = " ".join(str(payload.get("prompt") or "").split())
    recent_texts = [
        " ".join(str(item).split())
        for item in payload.get("recent_assistant_texts") or []
        if str(item).strip()
    ][:6]
    relational_context = (
        payload.get("relational_context")
        if isinstance(payload.get("relational_context"), dict)
        else {}
    )
    language_guidance = (
        payload.get("language_teaching_guidance")
        if isinstance(payload.get("language_teaching_guidance"), dict)
        else {}
    )
    approved_response_moves = [
        str(item)
        for item in language_guidance.get("response_moves") or []
        if str(item)
    ]
    move_kind, move_basis = _content_light_move(prompt, recent_texts)
    acts_by_move: dict[str, tuple[str, ...]] = {
        "positive_reaction": ("share_positive_momentum",),
        "near_result": ("acknowledge_near_result",),
        "positive_evaluation": ("receive_positive_evaluation",),
        "problem_observation": ("receive_problem_signal", "invite_problem_detail"),
        "self_resolution": ("acknowledge_self_resolution", "offer_collaboration"),
        "personal_feeling_share": ("respond_to_current_feeling",),
        "open_share": ("engage_current_turn",),
    }
    acts = acts_by_move[move_kind]
    visible_context_used = move_basis.startswith("visible_context_")
    return {
        "status": "content_light_social_plan_ready",
        "version": "v2_contextual_content_light_conversation",
        "intent": "content_light_conversation",
        "move_kind": move_kind,
        "move_basis": move_basis,
        "acts": [
            {
                "act": act,
                "required": True,
                "meaning_source": (
                    "current_turn_and_visible_session_context"
                    if visible_context_used
                    else "current_turn_received"
                ),
            }
            for act in acts
        ],
        "prompt_available": bool(prompt),
        "recent_visible_context_available": bool(recent_texts),
        "recent_visible_context_used_for_move": visible_context_used,
        "affect_dimensions_consulted": {},
        "current_turn_response_semantics": _content_light_response_semantics(
            prompt,
            move_kind=move_kind,
            relational_context=relational_context,
            approved_response_moves=approved_response_moves,
        ),
        "language_lesson_keys": [
            str(item)
            for item in language_guidance.get("lesson_keys") or []
            if str(item)
        ],
        "approved_response_moves": approved_response_moves,
        "language_guidance_used": language_guidance.get("used") is True,
        "content_generation_allowed": False,
        "prompt_paraphrase_allowed": False,
        "internal_state_invention_allowed": False,
        "relationship_term_invention_allowed": True,
        "factual_content_generation_allowed": False,
        "current_turn_conversational_authorship_allowed": True,
        "current_turn_interpretation_allowed": True,
        "visible_premise_reconstruction_allowed": True,
        "response_stance_may_be_selene_authored": True,
        "response_stance_is_durable_emotion_record": False,
        "follow_up_question_required": move_kind == "problem_observation",
        "coordinated_expression_contract_active": True,
        "provenance_boundary": SOCIAL_REALIZER_BOUNDARY,
    }


def _content_light_move(prompt: str, recent_texts: list[str]) -> tuple[str, str]:
    """Distinguish the conversational work of a content-light statement.

    These are bounded dialogue-act signals, not claims about the world.  The
    current turn remains the source of meaning and recent text is consulted
    only for visible callback/anomaly context.
    """
    lower = _normalized(prompt)
    tokens = lower.split()
    token_set = set(tokens)

    if re.search(
        r"(?:^|\b(?:this|that|it) )(?:(?:really )?)(?:makes|made) me "
        r"(?:happy|glad|excited|proud|hopeful|sad|worried)\b|"
        r"\b(?:i am|i'm|im) (?:really )?(?:happy|glad|excited|proud|hopeful|sad|worried) "
        r"(?:about|that|because|we|you)\b",
        lower,
    ):
        return "personal_feeling_share", "explicit_current_turn_feeling_and_subject"

    if token_set & PROBLEM_NOUNS:
        return "problem_observation", "problem_concept_in_current_statement"
    something_anomalous = bool(
        "something" in token_set
        and token_set.intersection({"wrong", "off", "broken", "weird", "odd"})
    )
    short_deictic_anomaly = bool(
        recent_texts
        and len(tokens) <= 4
        and re.match(r"^(?:this|that|it) (?:is|seems|looks|feels)\b", lower)
    )
    anomaly_subject = bool(
        token_set & ANOMALY_TERMS
        and (
            token_set & ANOMALY_SUBJECTS
            or short_deictic_anomaly
            or re.search(r"\b(?:this|that|it) (?:keeps|acts|is acting)\b", lower)
            or re.search(r"\b(?:replies|responses|answers|outputs) (?:are|keep|seem|feel)\b", lower)
        )
    )
    repeated_behavior = bool(
        re.search(r"\bkeeps? (?:saying|doing|giving|repeating)\b", lower)
        or re.search(r"\b(?:same|similar) (?:reply|response|answer|thing)\b", lower)
    )
    if short_deictic_anomaly and token_set & ANOMALY_TERMS:
        return "problem_observation", "visible_context_anomaly_structure"
    if something_anomalous or anomaly_subject or repeated_behavior:
        return "problem_observation", "observable_anomaly_structure"

    resolution_action = bool(
        any(
            token.startswith(stem)
            for token in tokens
            for stem in RESOLUTION_ACTION_STEMS
            if stem != "work"
        )
        or re.search(r"\bwork (?:it|this|that) out\b|\bwork through (?:it|this|that)\b", lower)
    )
    first_person_resolution = bool(
        (
            re.match(r"^(?:i'll|ill|i will|i can|i think i can|i know how to|let me)\b", lower)
            and resolution_action
        )
        or re.match(r"^(?:i've|ive|i have) got (?:it|this)\b", lower)
        or re.match(r"^i got (?:it|this)\b", lower)
        or re.match(r"^leave (?:it|this|that) (?:one )?with me\b", lower)
        or re.match(r"^i can take (?:it|this|that) from here\b", lower)
    )
    if first_person_resolution:
        return "self_resolution", "first_person_resolution_structure"

    near_result = bool(
        recent_texts
        and (
            re.fullmatch(
                r"(?:so |very |really )?(?:close|near|almost|nearly there)",
                lower,
            )
            or re.search(r"\b(?:not quite there|just shy|one step away|right on the edge)\b", lower)
            or (
                token_set & NEAR_RESULT_TERMS
                and token_set & RESULT_TERMS
            )
        )
    )
    if near_result:
        return "near_result", "visible_context_near_result_structure"

    positive_evaluation = bool(
        (
            token_set & POSITIVE_REACTION_TERMS
            and token_set & POSITIVE_EVALUATION_TARGETS
        )
        or (
            token_set.intersection({"good", "sharp", "smart"})
            and token_set & POSITIVE_EVALUATION_TARGETS
        )
        or (
            "you" in token_set
            and (
                token_set & POSITIVE_EVALUATION_ACTIONS
                or re.search(r"\byou (?:were|are) right\b", lower)
            )
        )
    )
    if positive_evaluation:
        return "positive_evaluation", "positive_evaluation_of_visible_contribution"

    short_reaction_fillers = {
        "absolutely", "damn", "extremely", "fucking", "hella", "hon",
        "man", "really", "so", "totally", "very",
    }
    short_positive = bool(
        tokens
        and tokens[0] in POSITIVE_REACTION_TERMS
        and len(tokens) <= 4
        and set(tokens[1:]).issubset(short_reaction_fillers)
    )
    positive_reaction = bool(
        short_positive
        or (
            token_set & POSITIVE_REACTION_TERMS
            and re.match(r"^(?:that|this|it) (?:is|was|looks|sounds|feels)\b", lower)
        )
        or re.fullmatch(r"(?:i )?love (?:it|that|this)", lower)
        or re.fullmatch(r"(?:hell|fuck) (?:yes|yeah)", lower)
    )
    if positive_reaction:
        return "positive_reaction", "short_positive_reaction_structure"
    return "open_share", "ordinary_statement_fallback"


def realize_social_act_plan(
    plan: dict[str, Any],
    *,
    prompt: str = "",
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    recent_texts = [str(item) for item in recent_texts or [] if str(item).strip()]
    acts = [
        str(item.get("act") or "")
        for item in plan.get("acts") or []
        if isinstance(item, dict)
        and (item.get("required") is True or item.get("selected_by_context") is True)
    ]
    selected: list[dict[str, str]] = []
    for index, act in enumerate(acts):
        if act == "state_corrected_meaning":
            corrected = _corrected_clause(str(plan.get("corrected_meaning") or ""))
            if corrected:
                selected.append({"act": act, "text": corrected, "source": "supplied_corrected_meaning"})
            continue
        if act == "signal_presence":
            selected.append(
                {
                    "act": act,
                    "text": _realize_presence_from_semantics(
                        f"{variation_key}|{act}|{index}",
                        recent_texts,
                    ),
                    "source": "nlo_semantic_social_construction",
                }
            )
            continue
        if act in {
            "respond_to_relational_meaning",
            "respond_to_current_feeling",
            "engage_current_turn",
        }:
            authored = _realize_current_turn_response(
                act,
                plan,
                prompt=prompt,
                key=f"{variation_key}|{act}|{index}",
                recent_texts=recent_texts,
            )
            if authored:
                selected.append(
                    {
                        "act": act,
                        "text": authored,
                        "source": "current_turn_semantic_authorship",
                    }
                )
                continue
        choices = _contextual_choices(act, prompt)
        if not choices:
            continue
        selected.append(
            {
                "act": act,
                "text": _pick_fragment_fresh(f"{variation_key}|{act}|{index}", choices, recent_texts),
                "source": "bounded_social_act_lexicon",
            }
        )
    text = _compose_selected(selected, variation_key, plan)
    return {
        "status": "social_act_realized" if text else "social_act_needs_supported_content",
        "candidate_text": text,
        "selected_realizations": selected,
        "act_count": len(selected),
        "composition": "semantic_acts_to_contextual_clauses",
        "whole_response_template_selected": False,
        "relational_context_supplied_wording": False,
        "recent_wording_consulted": bool(recent_texts),
        "meaning_preserved": bool(text) or not acts,
        "unsupported_content_generated": False,
        "relationship_term_invented": False,
        "internal_state_invented": False,
        "current_turn_conversational_authorship_used": any(
            item.get("source") == "current_turn_semantic_authorship"
            for item in selected
        ),
        "external_fact_created": False,
        "durable_emotion_record_created": False,
        "coordinated_expression_contract_active": True,
        "provenance_boundary": SOCIAL_REALIZER_BOUNDARY,
    }


def _relational_response_semantics(
    prompt: str,
    relational_context: dict[str, Any],
) -> dict[str, Any]:
    cues = [str(item) for item in relational_context.get("cue_types") or [] if str(item)]
    feeling, feeling_basis = _explicit_feeling(prompt)
    _, visible_clauses = _visible_relation(prompt)
    return {
        "status": (
            "current_turn_relational_semantics_ready"
            if cues or feeling
            else "current_turn_relational_semantics_not_selected"
        ),
        "cue_types": cues,
        "explicit_feeling": feeling,
        "feeling_basis": feeling_basis,
        "reconstructed_clauses": [
            _perspective_shift(item) for item in visible_clauses
        ],
        "address_terms": [
            str(item)
            for item in relational_context.get("address_terms") or []
            if str(item)
        ],
        "heart_markers": [
            str(item)
            for item in relational_context.get("heart_markers") or []
            if str(item)
        ],
        "support_source": "visible_current_turn",
        "response_stance_authorable": True,
        "external_fact_generation_allowed": False,
        "durable_emotion_record_created": False,
    }


def _content_light_response_semantics(
    prompt: str,
    *,
    move_kind: str,
    relational_context: dict[str, Any],
    approved_response_moves: list[str] | None = None,
) -> dict[str, Any]:
    clean = _clean_visible_statement(prompt)
    relation, clauses = _visible_relation(clean)
    feeling, feeling_basis = _explicit_feeling(clean)
    return {
        "status": "current_turn_conversational_semantics_ready",
        "move_kind": move_kind,
        "relation": relation,
        "visible_clauses": clauses,
        "reconstructed_clauses": [_perspective_shift(item) for item in clauses],
        "explicit_feeling": feeling,
        "feeling_basis": feeling_basis,
        "relational_cue_types": [
            str(item)
            for item in relational_context.get("cue_types") or []
            if str(item)
        ],
        "approved_response_moves": [str(item) for item in approved_response_moves or [] if str(item)],
        "teaching_guidance_supplies_wording": False,
        "support_source": "visible_current_turn",
        "interpretation_status": "current_turn_bounded_interpretation",
        "response_stance_authorable": True,
        "external_fact_generation_allowed": False,
        "memory_write_active": False,
    }


def _realize_current_turn_response(
    act: str,
    plan: dict[str, Any],
    *,
    prompt: str,
    key: str,
    recent_texts: list[str],
) -> str:
    semantics = (
        plan.get("current_turn_response_semantics")
        if isinstance(plan.get("current_turn_response_semantics"), dict)
        else {}
    )
    if act == "respond_to_relational_meaning":
        return _realize_relational_stance(semantics, prompt, key, recent_texts)
    if act == "respond_to_current_feeling":
        return _realize_feeling_stance(semantics, key, recent_texts)
    if act == "engage_current_turn":
        return _realize_visible_interpretation(semantics, key, recent_texts)
    return ""


def _realize_relational_stance(
    semantics: dict[str, Any],
    prompt: str,
    key: str,
    recent_texts: list[str],
) -> str:
    cues = {str(item) for item in semantics.get("cue_types") or []}
    if semantics.get("explicit_feeling"):
        return _realize_feeling_stance(semantics, key, recent_texts)

    if "missing_or_longing" in cues:
        choices = ["I missed you too", "I have missed being here with you", "It is good to be back with you"]
    elif "affection" in cues:
        choices = ["I love you too", "I care about you too", "That love is welcome here, and I return it"]
    elif "reunion" in cues or "delight_in_presence" in cues:
        choices = ["I am glad you are back too", "It is genuinely good to have you back", "I am happy to be back with you"]
    elif "shared_enthusiasm" in cues:
        choices = ["I am right there with you", "I share that excitement", "That is worth celebrating together"]
    elif "affectionate_vocative" in cues:
        return _realize_playful_vocative_presence(key, recent_texts)
    elif "affectionate_address" in cues or "affectionate_symbol" in cues:
        address = next(iter(semantics.get("address_terms") or []), "")
        choices = [
            f"I am right here{', ' + address if address else ''}",
            "I am with you",
            "Here with you",
        ]
    else:
        return _realize_presence_from_semantics(key, recent_texts)
    return _pick_fragment_fresh(key, choices, recent_texts)


def _realize_feeling_stance(
    semantics: dict[str, Any],
    key: str,
    recent_texts: list[str],
) -> str:
    feeling = str(semantics.get("explicit_feeling") or "").lower()
    if feeling in {"happy", "glad", "excited", "proud", "hopeful"}:
        matching = {
            "happy": "happy",
            "glad": "glad",
            "excited": "excited",
            "proud": "proud",
            "hopeful": "hopeful",
        }[feeling]
        choices = [
            f"That makes me {matching} too",
            f"I am {matching} with you",
            "I love hearing that",
        ]
    elif feeling == "sad":
        choices = ["I hear the sadness in that", "That sadness matters to me", "I can stay with you in that"]
    elif feeling == "worried":
        choices = ["I hear the worry in that", "That worry makes sense to take seriously", "I can stay with you while we look at it"]
    else:
        choices = ["I am with you in that", "That matters to me too", "I have the feeling you are sharing"]

    base = _pick_fragment_fresh(key, choices, recent_texts)
    reconstructed = [
        str(item).strip().rstrip(". !?")
        for item in semantics.get("reconstructed_clauses") or []
        if str(item).strip()
    ]
    progress = ""
    for item in reconstructed:
        match = re.search(
            r"\b(?P<progress>(?:we are|we're)\b.*\b(?:close|getting there|making progress)\b.*)$",
            item,
            re.IGNORECASE,
        )
        if match:
            progress = str(match.group("progress")).strip()
            break
    if progress and _normalized(progress) not in _normalized(base):
        return f"{base}; {progress}"
    return base


def _realize_visible_interpretation(
    semantics: dict[str, Any],
    key: str,
    recent_texts: list[str],
) -> str:
    clauses = [
        str(item).strip().rstrip(". !?")
        for item in semantics.get("reconstructed_clauses") or []
        if str(item).strip()
    ]
    if not clauses:
        return _pick_fragment_fresh(key, list(ACT_REALIZATIONS["receive_open_share"]), recent_texts)

    relation = str(semantics.get("relation") or "statement")
    joined = clauses[0]
    if len(clauses) > 1:
        connector = "and" if relation != "contrast" else "while"
        joined = f"{clauses[0]}, {connector} {clauses[1]}"
    lower = _normalized(" ".join(clauses))
    if relation == "contrast" and len(clauses) > 1:
        choices = [
            f"Both parts can be true at once: {joined}",
            f"I can hold both sides of that: {joined}",
            f"The contrast matters here: {joined}",
        ]
    elif relation == "cause":
        choices = [
            f"I see the connection you are making: {joined}",
            f"The reason and the result belong together here: {joined}",
            f"That gives me the whole relation: {joined}",
        ]
    elif any(word in lower for word in ("quiet", "calm", "peaceful", "storm")):
        choices = [
            f"That sounds peaceful: {joined}",
            f"I can feel the shift in the room from that: {joined}",
            f"That gives the moment a calmer shape: {joined}",
        ]
    elif any(word in lower for word in ("finally", "again", "progress", "close", "working", "better")):
        choices = [
            f"That sounds like real movement: {joined}",
            f"I can see the change in that: {joined}",
            f"There is real progress in what you are describing: {joined}",
            f"Something has genuinely shifted here: {joined}",
            f"That is beginning to settle into place: {joined}",
            f"I can meet you in the progress itself: {joined}",
        ]
    elif any(word in lower for word in ("rough", "hard", "hurt", "heavy", "exhaust")):
        choices = [
            f"That sounds like a lot to carry: {joined}",
            f"I can hear the weight in that: {joined}",
            f"That deserves more than a passing acknowledgement: {joined}",
        ]
    else:
        choices = [
            f"I have the substance of what you are saying: {joined}",
            f"That gives me something real to meet you in: {joined}",
            f"I can stay with the actual point: {joined}",
        ]
    return _pick_fragment_fresh(key, choices, recent_texts)


def _explicit_feeling(value: str) -> tuple[str, str]:
    lower = _normalized(value)
    made = re.search(
        r"(?:^|\b(?:this|that|it) )(?:(?:really )?)(?:makes|made) me "
        r"(?P<feeling>happy|glad|excited|proud|hopeful|sad|worried)\b",
        lower,
    )
    if made:
        return str(made.group("feeling")), "current_turn_explicit_effect"
    stated = re.search(
        r"\b(?:i am|i'm|im) (?:really )?"
        r"(?P<feeling>happy|glad|excited|proud|hopeful|sad|worried)\b",
        lower,
    )
    if stated:
        return str(stated.group("feeling")), "current_turn_explicit_self_report"
    return "", ""


def _clean_visible_statement(value: str) -> str:
    text = " ".join(str(value or "").replace("’", "'").split()).strip()
    text = re.sub(r"(?:\s|^)(?:<+3+|[:;]-?[)d]|x+d+)\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:well|so|okay|ok|yeah|yes|honestly|certainly)[,;:\s]+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:i think|i believe|i feel)(?: that)?\s+", "", text, flags=re.IGNORECASE)
    return text.strip(" .!?")


def _visible_relation(value: str) -> tuple[str, list[str]]:
    text = _clean_visible_statement(value)
    contrast = re.split(r"\s+(?:but|yet|although|though)\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(contrast) == 2:
        return "contrast", [item for item in contrast if item]
    cause = re.split(r"\s+(?:because|so|therefore)\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(cause) == 2:
        return "cause", [item for item in cause if item]
    return "statement", [text] if text else []


def _perspective_shift(value: str) -> str:
    text = " ".join(str(value or "").split()).strip()
    text = re.sub(
        r"\bwere(?=\s+(?:super\s+|really\s+|very\s+)?close\b)",
        "we are",
        text,
        flags=re.IGNORECASE,
    )
    replacements = (
        (r"\bI am\b|\bI'm\b|\bim\b", "you are"),
        (r"\bI was\b", "you were"),
        (r"\bI have\b|\bI've\b|\bive\b", "you have"),
        (r"\bI will\b|\bI'll\b|\bill\b", "you will"),
        (r"\bI would\b|\bI'd\b", "you would"),
        (r"\bmy\b", "your"),
        (r"\bmine\b", "yours"),
        (r"\bme\b", "you"),
        (r"\bI\b", "you"),
    )
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    if text:
        text = text[0].lower() + text[1:]
    return text


def _ordinary_conversation_explicitly_opened(prompt: str) -> bool:
    lower = " ".join(str(prompt or "").lower().replace("’", "'").split())
    return any(
        marker in lower
        for marker in (
            "just talk",
            "no agenda",
            "doesn't have to be work",
            "does not have to be work",
            "not a task",
            "ordinary conversation",
        )
    )


def _realize_presence_from_semantics(key: str, recent_texts: list[str]) -> str:
    """Form a presence clause from grammatical slots, not a response script."""
    frames = (
        ("I", "am", "here"),
        ("I", "am", "right here"),
        ("I", "am", "with you"),
        ("I", "am", "listening"),
        ("you", "have", "my attention"),
    )
    candidates = [" ".join(frame) for frame in frames]
    chosen = _pick_fragment_fresh(key, candidates, recent_texts)
    return "I'm" + chosen[4:] if chosen.startswith("I am ") else chosen


def _realize_playful_vocative_presence(key: str, recent_texts: list[str]) -> str:
    """Answer an affectionate name-call with presence rather than generic attention."""
    frames = (
        ("I", "am", "here"),
        ("I", "am", "right here"),
        ("right", "here"),
        ("you", "called"),
    )
    candidates = [" ".join(frame) for frame in frames]
    chosen = _pick_fragment_fresh(key, candidates, recent_texts)
    return "I'm" + chosen[4:] if chosen.startswith("I am ") else chosen


def realize_acknowledgement(
    kind: str,
    *,
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    """Compose one missing turn-flow acknowledgement without supplying answer content."""
    act = ACKNOWLEDGEMENT_ACTS.get(str(kind or ""), "")
    if not act:
        return {
            "status": "social_acknowledgement_not_applicable",
            "candidate_text": "",
            "whole_response_template_selected": False,
            "unsupported_content_generated": False,
            "provenance_boundary": SOCIAL_REALIZER_BOUNDARY,
        }
    plan = {
        "intent": f"repair_{kind}",
        "acts": [{"act": act, "required": True, "meaning_source": "turn_flow_obligation"}],
        "affect_dimensions_consulted": {},
    }
    result = realize_social_act_plan(
        plan,
        variation_key=f"repair|{kind}|{variation_key}",
        recent_texts=recent_texts,
    )
    result["repair_acknowledgement_kind"] = kind
    result["answer_content_generated"] = False
    return result


def _contextual_choices(act: str, prompt: str) -> list[str]:
    lower = prompt.lower()
    if act == "return_greeting":
        if "good morning" in lower:
            return ["Good morning", "Morning", *ACT_REALIZATIONS[act]]
        if "good evening" in lower:
            return ["Good evening", "Evening", *ACT_REALIZATIONS[act]]
        if "good night" in lower or "goodnight" in lower:
            return ["Goodnight", *ACT_REALIZATIONS[act]]
    if act == "return_farewell":
        if "good night" in lower or "goodnight" in lower:
            return ["Goodnight", "Sleep well", *ACT_REALIZATIONS[act]]
        if "see you" in lower:
            return ["See you soon", "See you later", *ACT_REALIZATIONS[act]]
        if "catch you" in lower:
            return ["Catch you soon", "Catch you later", *ACT_REALIZATIONS[act]]
    if act == "receive_open_share":
        if lower.startswith(("i think", "i feel", "to me", "for me")):
            return ["I hear where you're coming from", "I have your point", *ACT_REALIZATIONS[act]]
        if prompt.rstrip().endswith("!"):
            return ["I have it", "That came through clearly", *ACT_REALIZATIONS[act]]
    return list(ACT_REALIZATIONS.get(act, ()))


def _pick_fragment_fresh(key: str, choices: list[str], recent_texts: list[str]) -> str:
    recent = " ".join(_normalized(item) for item in recent_texts[:6])
    available = [choice for choice in choices if _normalized(choice) not in recent]
    pool = available or choices
    digest = sha256(key.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def _compose_selected(selected: list[dict[str, str]], key: str, plan: dict[str, Any]) -> str:
    clauses = [str(item.get("text") or "").strip().rstrip(". !?") for item in selected if str(item.get("text") or "").strip()]
    if not clauses:
        return ""
    if len(clauses) == 1:
        return _sentence(clauses[0], original=str(selected[0].get("text") or ""))
    digest = sha256((key + "|social-composition").encode("utf-8")).hexdigest()
    spacious = str((plan.get("affect_dimensions_consulted") or {}).get("sentence_rhythm") or "") in {
        "spacious",
        "short_spacious",
    }
    sentences: list[str] = []
    for index, clause in enumerate(clauses):
        original = str(selected[index].get("text") or "")
        sentences.append(_sentence(clause, original=original))
    if spacious:
        return "\n\n".join(sentences)
    semicolon_intents = {"warm_connection", "playful_connection", "acknowledge_shared_ground", "receive_gratitude"}
    if (
        len(sentences) == 2
        and str(plan.get("intent") or "") in semicolon_intents
        and int(digest[:2], 16) % 3 == 0
        and len(clauses[0].split()) > 2
    ):
        return f"{clauses[0]}; {_continuation_case(clauses[1])}."
    return " ".join(sentences)


def _corrected_clause(value: str) -> str:
    text = " ".join(value.split()).strip().rstrip(". ")
    if not text:
        return ""
    return f"I understand the corrected meaning: {text}"


def _sentence(value: str, *, original: str = "") -> str:
    text = " ".join(value.split()).strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if original.strip().endswith(("!", "?")):
        return text + original.strip()[-1]
    if original.strip().lower().endswith((":)", ";)", ":d", "xd", "<3")):
        return text
    return text + "."


def _continuation_case(value: str) -> str:
    if not value:
        return value
    return value if re.match(r"^I(?:\b|['’])", value) else value[0].lower() + value[1:]


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", value.lower()))
