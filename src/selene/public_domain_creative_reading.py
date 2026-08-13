from __future__ import annotations

from typing import Any


TEACHING_GROUP = "G11 · Public-Domain Reading and Creative Transfer"

SOURCE_WORKS: tuple[dict[str, Any], ...] = (
    {
        "key": "blake_tyger",
        "form": "poetry",
        "title": "The Tyger",
        "author": "William Blake",
        "work": "Songs of Innocence and of Experience",
        "source_url": "https://www.gutenberg.org/files/1934/1934-h/1934-h.htm",
        "source_record": "Project Gutenberg eBook 1934",
        "public_domain_status": "public_domain_in_the_USA",
        "bounded_excerpt": "Tiger, tiger, burning bright / In the forests of the night",
        "reading_focus": "repetition, driving rhythm, linked questions, fire and making imagery, and unresolved wonder",
    },
    {
        "key": "shakespeare_midsummer",
        "form": "drama",
        "title": "A Midsummer Night's Dream",
        "author": "William Shakespeare",
        "work": "A Midsummer Night's Dream, Act 1, Scene 1",
        "source_url": "https://www.gutenberg.org/ebooks/1514",
        "source_record": "Project Gutenberg eBook 1514",
        "public_domain_status": "public_domain_in_the_USA",
        "bounded_excerpt": "The course of true love never did run smooth.",
        "reading_focus": "spoken obstacle, contrast, shared planning, character goals, and the difference between a line and its dramatic situation",
    },
    {
        "key": "carroll_alice_chapter_one",
        "form": "prose",
        "title": "Alice's Adventures in Wonderland",
        "author": "Lewis Carroll",
        "work": "Alice's Adventures in Wonderland, Chapter I",
        "source_url": "https://www.gutenberg.org/ebooks/928",
        "source_record": "Project Gutenberg eBook 928",
        "public_domain_status": "public_domain_in_the_USA",
        "bounded_excerpt": "what is the use of a book ... without pictures or conversation?",
        "reading_focus": "close viewpoint, curiosity-led attention, escalating oddity, scene continuity, and transition from reflection into motion",
    },
)


def _source_refs(source: dict[str, Any]) -> list[str]:
    return [
        "source:bounded_public_domain_reading_application_20260813",
        f"attribution:{source['author']} — {source['work']}",
        f"source_record:{source['source_record']}",
        f"license_status:{source['public_domain_status']}",
        str(source["source_url"]),
        "reading_boundary:bounded_excerpt_and_project_authored_analysis_not_whole_work_import",
        "recall_boundary:technique_transfer_not_quotation_recall",
        "style_boundary:no_author_persona_or_signature_style_imitation",
    ]


LESSONS: tuple[dict[str, Any], ...] = (
    {
        "key": "public_domain_poetry_mechanism_and_transfer",
        "title": "Read a poem for the relationship among sound, image, question, and unresolved meaning",
        "category": "creative_reading_poetry",
        "teaching_group": TEACHING_GROUP,
        "group_order": 11,
        "lesson_order": 1,
        "prerequisites": ["creative_rhythm_pacing_by_meaning", "figurative_mapping_with_limits"],
        "purpose": "Use a bounded attributed reading of Blake's poem to identify how repeated sound, image clusters, and accumulating questions shape attention, then transfer the mechanism into original language without recalling or imitating the poem.",
        "apply_when": ["poetry_reading", "poem_analysis", "rhythm_analysis", "image_pattern", "creative_transfer"],
        "response_moves": ["separate_source_observation_from_interpretation", "trace_repetition_and_question_motion", "identify_image_relationship_and_uncertainty", "transfer_poetic_mechanism_into_original_material", "avoid_quotation_recall_and_author_imitation"],
        "constraints": ["Do not treat one interpretation as the poem's only possible meaning.", "Do not reproduce the poem or imitate Blake's recognizable surface choices."],
        "teaching_source_type": "attributed_public_domain_reading_application_lesson",
        "source_refs": _source_refs(SOURCE_WORKS[0]),
        "source_work": SOURCE_WORKS[0],
    },
    {
        "key": "public_domain_drama_situation_and_transfer",
        "title": "Read dramatic language through speaker, pressure, goal, and changing situation",
        "category": "creative_reading_drama",
        "teaching_group": TEACHING_GROUP,
        "group_order": 11,
        "lesson_order": 2,
        "prerequisites": ["dialogue_subtext_and_turn_motion", "public_domain_poetry_mechanism_and_transfer"],
        "purpose": "Use a bounded attributed scene from Shakespeare to distinguish a memorable line from the speakers, constraints, goals, and decisions that give it dramatic force, then build an original exchange from a different conflict.",
        "apply_when": ["drama_reading", "scene_analysis", "dialogue_analysis", "subtext", "character_goal", "creative_transfer"],
        "response_moves": ["identify_speaker_situation_and_local_goal", "separate_spoken_claim_from_dramatic_function", "track_turn_by_turn_change", "transfer_scene_mechanism_into_original_conflict", "avoid_archaic_surface_imitation"],
        "constraints": ["Do not infer a character's private motive beyond what the scene supports.", "Do not mistake archaic vocabulary or quotation for understanding dramatic construction."],
        "teaching_source_type": "attributed_public_domain_reading_application_lesson",
        "source_refs": _source_refs(SOURCE_WORKS[1]),
        "source_work": SOURCE_WORKS[1],
    },
    {
        "key": "public_domain_prose_viewpoint_and_transfer",
        "title": "Read prose through viewpoint, attention, escalation, and continuity",
        "category": "creative_reading_prose",
        "teaching_group": TEACHING_GROUP,
        "group_order": 11,
        "lesson_order": 3,
        "prerequisites": ["viewpoint_scene_continuity", "public_domain_drama_situation_and_transfer"],
        "purpose": "Use a bounded attributed reading from Carroll to trace how a close viewpoint selects details, lets curiosity redirect attention, and carries a scene from ordinary stillness into unusual motion, then apply the same structure to an unrelated original scene.",
        "apply_when": ["prose_reading", "narrative_analysis", "viewpoint", "scene_transition", "escalation", "creative_transfer"],
        "response_moves": ["locate_viewpoint_and_information_boundary", "trace_attention_and_scene_state", "identify_escalation_steps", "transfer_narrative_mechanism_into_original_scene", "preserve_source_and_invention_boundary"],
        "constraints": ["Do not add source events that were not inspected or supported.", "Do not reproduce Carroll's diction, characters, world, or comic persona in the transfer example."],
        "teaching_source_type": "attributed_public_domain_reading_application_lesson",
        "source_refs": _source_refs(SOURCE_WORKS[2]),
        "source_work": SOURCE_WORKS[2],
    },
)


EVIDENCE: dict[str, dict[str, Any]] = {
    "public_domain_poetry_mechanism_and_transfer": {
        "vocabulary": ["textual observation", "interpretation", "repetition", "image cluster", "rhetorical question", "creative transfer"],
        "uncertainties": ["The poem's questions create several plausible relations among creation, beauty, danger, power, and wonder without resolving them into one declared answer."],
        "near_concept_distinctions": ["A textual observation identifies a visible or audible pattern; an interpretation proposes what that pattern may make available in the work."],
        "examples": ["The cited opening repeats the creature and uses paired light-and-dark imagery. Reading the full poem shows questions accumulating rather than a speaker delivering a settled explanation."],
        "counterexamples": ["Repeating an opening phrase in a new poem is surface copying if the writer has not identified what the repetition is doing in the new material."],
        "scope_of_application": "Use this method to discuss attributed poems and to develop original rhythm, imagery, or question structures. Source-specific claims remain bounded to inspected text; interpretations remain revisable.",
        "explanation": "The poem makes inquiry felt through form: recurring sound stabilizes attention while images and questions repeatedly enlarge the unknown. The useful lesson is not its wording but the relationship between recurrence and unresolved inquiry.",
        "distinct_examples": ["An original poem about a silent observatory could return to one image of an unlit monitor while each stanza asks a different kind of question about absence; the setting, diction, and meaning remain new."],
        "analogies": ["Repetition can act like returning to the same observation point while each question turns the instrument toward a different part of the problem."],
        "questions": ["What pattern is directly present, what interpretation does it support, and what remains deliberately unanswered?"],
        "comparisons": ["Quotation recall reproduces source wording; creative transfer carries an understood relationship into distinct material."],
        "conversational_participation": "I can point first to the repeated address, rhythmic recurrence, connected images, and sequence of questions. My reading is that they keep wonder and danger present together, but that interpretation should remain open rather than becoming the poem's single official answer.",
        "correction_response": "If an interpretation outruns the text, return to the observable pattern, narrow the claim, and preserve other readings that fit the same evidence.",
    },
    "public_domain_drama_situation_and_transfer": {
        "vocabulary": ["dramatic situation", "speaker", "local goal", "obstacle", "turn", "subtext", "scene function"],
        "uncertainties": ["A line can express a general idea while also performing reassurance, persuasion, resistance, or planning inside its immediate scene."],
        "near_concept_distinctions": ["A line's proposition is what it says; its dramatic function is what saying it changes between these speakers at this moment."],
        "examples": ["The cited statement names difficulty, but its force comes from the lovers facing an immediate social obstacle and moving from shared recognition toward a plan."],
        "counterexamples": ["Copying old vocabulary into a new exchange does not recreate the pressure, goals, turn structure, or relationship that make a dramatic scene move."],
        "scope_of_application": "Use speaker, pressure, goal, and turn analysis for attributed drama and original dialogue. Treat motives as text-supported interpretations, not facts about real people.",
        "explanation": "Dramatic language works in action. A line matters because a particular speaker says it under pressure to another speaker, and the exchange changes what the pair understands, chooses, or risks next.",
        "distinct_examples": ["Two technicians discover a failed launch check. One names the deadline; the other places the faulty part on the table and proposes a smaller test. The exchange moves from pressure to a decision without borrowing the source scene."],
        "analogies": ["A dramatic line is a force applied inside a system: its effect depends on where, when, and against what resistance it acts."],
        "questions": ["Who speaks, what pressure is active, what does each speaker want locally, and what changes after the turn?"],
        "comparisons": ["A memorable line can stand alone as language; dramatic understanding reconnects it to speaker, obstacle, relationship, and consequence."],
        "conversational_participation": "The line expresses a broad truth about difficulty, but I would not stop there. In the scene it also helps the speakers name their obstacle together and move toward action, which is where much of its dramatic work happens.",
        "correction_response": "If a reading assigns an unsupported motive or ignores the next turn, restore the scene evidence and describe the function as a plausible interpretation.",
    },
    "public_domain_prose_viewpoint_and_transfer": {
        "vocabulary": ["close viewpoint", "attention path", "scene state", "escalation", "transition", "narrative continuity"],
        "uncertainties": ["A close viewpoint can make an event feel surprising without establishing that the event is objectively inexplicable outside the viewpoint's present knowledge."],
        "near_concept_distinctions": ["Viewpoint selects what becomes available now; continuity tracks what remains true as attention and location change."],
        "examples": ["The cited thought begins inside Alice's boredom and preference. The chapter then redirects her attention through increasingly unusual details before physical movement carries the scene elsewhere."],
        "counterexamples": ["Listing strange events without tracking the viewpoint's noticing, choice, and movement creates novelty but not a coherent escalation."],
        "scope_of_application": "Use viewpoint-and-escalation analysis for attributed prose and original narrative construction. Preserve the difference among source events, interpretation, and new fictional invention.",
        "explanation": "The prose transition works because oddity arrives through a stable attention path. Each noticed detail changes the viewpoint's curiosity and next action, so escalation grows from continuity rather than replacing it.",
        "distinct_examples": ["A mechanic waiting beside an ordinary idle pump notices a gauge twitch, then a tool vibrating without contact, then follows the sound below the floor. The new scene uses attention-led escalation without borrowing source characters or diction."],
        "analogies": ["Viewpoint is the camera's permitted position; attention is what moves within the frame; continuity keeps the world from resetting between cuts."],
        "questions": ["What does the viewpoint notice first, what new detail changes priority, and how does each step make the next action plausible?"],
        "comparisons": ["Random surprise adds unrelated novelty; escalation changes the scene through a connected sequence of attention, interpretation, and action."],
        "conversational_participation": "What I would transfer is the attention path: ordinary state, one detail that almost fits, a second that clearly does not, then a choice to follow it. The new scene should keep its own world and voice.",
        "correction_response": "If the transfer copies source characters or if the scene jumps without a supported attention path, return to the last stable state and rebuild the escalation with original details.",
    },
}
