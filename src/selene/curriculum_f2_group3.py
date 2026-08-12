from __future__ import annotations

from typing import Any


AUTHORIZATION_KEY = "f2_point_of_view_organized_composition_v1"
GROUP_KEY = "f2_point_of_view_organized_composition_group_3"

SEQUENCE_REFS = [
    "curriculum_source:core_knowledge_2023_sequence_k8",
    "sha256:c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5",
    "https://www.coreknowledge.org/wp-content/uploads/2023/03/CK_Sequence2023_GK8_W3.pdf",
    "source_locator:Grade 3-5 English Language Arts point-of-view and composition sequence",
    "license:Core-Knowledge-artifact-notice-controls",
    "source_date:2023",
]

SCOPE = {
    "bands": ["F2"],
    "families": ["ELA-1", "ELA-2", "ELA-3", "RES-1", "LOGIC-1", "CONV-1"],
    "source_ids": ["core_knowledge_2023_sequence_k8"],
    "knowledge_classes": ["public_academic_foundation"],
    "group_keys": [GROUP_KEY],
    "retention_rule": (
        "Acquire, Integrate, and Express must all complete with sufficient "
        "source-linked comprehension evidence."
    ),
}

LESSONS: tuple[dict[str, Any], ...] = (
    {
        "concept_key": "curriculum_f2_point_of_view_evidence_v1",
        "title": "Point of view shapes an account without automatically deciding its truth",
        "domain": "curriculum.f2.point_of_view_organized_composition",
        "material": (
            "Point of view is the position from which events, ideas, or experiences are perceived and described. A narrator or "
            "speaker presents an account; an author constructs the work; characters may hold their own views; and a reader may "
            "reach a different interpretation. Viewpoint affects selection, emphasis, language, access to information, and uncertainty. "
            "It should be identified from textual evidence rather than guessed from identity, and perspective alone neither proves nor disproves a claim."
        ),
        "principles": [
            "Distinguish author, narrator or speaker, character, source, and reader when those roles differ.",
            "Use wording, access to information, emphasis, and stated beliefs as evidence for viewpoint.",
            "Evaluate factual support separately from whose perspective presents it."
        ],
        "relationships": [
            "Point of view extends F1 source-versus-inference and Group 2 comparison while supporting history, literature, conversation, and source research."
        ],
        "examples": [
            "Two witnesses can describe the same outage differently because one saw the control panel while another heard only the alarm; their access explains some differences without making either person dishonest."
        ],
        "counterexamples": [
            "Assuming a narrator knows everything, treating the author's identity as proof of motive, or dismissing an account solely because it has a viewpoint all bypass evidence."
        ],
        "limits": [
            "Viewpoint may be ambiguous, deliberately unreliable, collective, translated, or changed over time; motives cannot be known from wording alone."
        ],
        "vocabulary": [
            "point of view: the position from which an account is perceived or presented",
            "author: the person or source that constructs a work",
            "narrator: the voice presenting a narrative",
            "speaker: the expressed voice in speech or poetry",
            "perspective: a situated way of perceiving or interpreting",
            "reliable narrator: a narrator whose account is sufficiently dependable within the work, not one assumed infallible",
        ],
        "near_concept_distinctions": [
            "Perspective explains how an account is situated; bias is a systematic influence that may distort selection or judgment."
        ],
        "scope_of_application": (
            "Use for stories, explanations, historical accounts, conversation, and attributed sources. Do not use it to profile a person or infer private motives without evidence."
        ),
        "unresolved_questions": [
            "What could this viewpoint observe directly, what does it infer, and what remains outside its access?"
        ],
        "explanation": (
            "Every account has a position and information boundary. Naming that position helps explain emphasis and limitation while leaving truth evaluation to evidence."
        ),
        "application": (
            "In a project retrospective, the operator can report the visible failure while the maintainer reports the internal cause. Comparing access clarifies why the accounts differ and how they can fit together."
        ),
        "analogies": [
            "Point of view is like observing a machine from one inspection port: the view can be accurate while remaining incomplete."
        ],
        "questions": [
            "Who is presenting this account, what can they know, what do they emphasize, and what evidence supports that reading?"
        ],
        "comparisons": [
            "The author creates the work, a narrator or speaker presents its language, characters experience events, and readers interpret the result."
        ],
        "participation": (
            "The two accounts differ partly because the witnesses had different access. I would preserve each direct observation, separate their causal interpretations, and compare both with the system record."
        ),
        "correction_response": (
            "If I confuse an author with a narrator or infer a motive without evidence, I would correct the role, retain the observable wording, and narrow the interpretation."
        ),
        "families": ["ELA-2", "ELA-3", "RES-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_explanatory_composition_v1",
        "title": "An explanatory composition organizes supported information around a clear purpose",
        "domain": "curriculum.f2.point_of_view_organized_composition",
        "material": (
            "An explanatory composition helps a reader understand a topic, process, relationship, or answer. It introduces the "
            "controlling idea, groups related information into functional sections or paragraphs, develops the idea with supported "
            "facts, definitions, examples, comparisons, or causes, and ends by completing rather than merely repeating the explanation. "
            "Its structure should follow what the subject requires rather than one fixed template."
        ),
        "principles": [
            "State or establish the controlling idea early enough for the reader to orient.",
            "Give each paragraph a function and connect it to the explanation's purpose.",
            "Preserve evidence, attribution, uncertainty, and limits while choosing an order that helps understanding."
        ],
        "relationships": [
            "Explanatory composition builds on paragraph meaning, summary, source attribution, shared-criterion comparison, and the Discourse Loom."
        ],
        "examples": [
            "An explanation of a flicker can move from observed pattern, to two candidate mechanisms, to distinguishing evidence, to the best current conclusion and its reopening condition."
        ],
        "counterexamples": [
            "A collection of accurate facts is not yet an explanation if their relationships and relevance to the central question remain unclear."
        ],
        "limits": [
            "Some subjects require visual, mathematical, procedural, or source material beyond prose, and high-stakes explanations require qualified evidence."
        ],
        "vocabulary": [
            "controlling idea: the main meaning that organizes the complete explanation",
            "section: a larger unit grouping related material",
            "paragraph function: the specific job a paragraph performs in the whole response",
            "transition: language or structure showing how one part relates to another",
            "conclusion: the ending that resolves the stated explanatory purpose and preserves material limits",
        ],
        "near_concept_distinctions": [
            "A topic names the subject; a controlling idea states what the composition explains about it."
        ],
        "scope_of_application": (
            "Use for ordinary answers, reports, technical walkthroughs, study notes, and source-grounded synthesis. Match length and structure to the actual task."
        ),
        "unresolved_questions": [
            "What relationship must the reader understand by the end, and which paragraph supplies each necessary part?"
        ],
        "explanation": (
            "A good explanation is a connected model in language. Every included part helps establish, develop, qualify, or complete the central understanding."
        ),
        "application": (
            "To explain why seasons change, organize the answer around Earth's axial tilt and orbit, then connect changing sunlight angle and day length while explicitly rejecting distance from the Sun as the general cause."
        ),
        "analogies": [
            "An explanatory composition resembles a guided route: its destination is the controlling idea, and each paragraph crosses one necessary piece of terrain."
        ],
        "questions": [
            "What is the explanatory purpose, what must be developed, and what order makes the relationships easiest to follow?"
        ],
        "comparisons": [
            "A summary compresses source meaning; an explanation develops relationships so the reader can understand why or how."
        ],
        "participation": (
            "The key explanation is axial tilt, not changing distance. I would first state that model, then show how angle and day length vary together, and close with the hemispheric consequence."
        ),
        "correction_response": (
            "If a paragraph is accurate but does not serve the explanation, I would move, connect, narrow, or remove it rather than preserve it merely because it sounds informative."
        ),
        "families": ["ELA-1", "ELA-2", "ELA-3", "RES-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_narrative_composition_v1",
        "title": "A narrative organizes experience through viewpoint, sequence, change, and meaningful closure",
        "domain": "curriculum.f2.point_of_view_organized_composition",
        "material": (
            "A narrative presents real or imagined experience through a situated viewpoint. It establishes a situation, develops "
            "events in a coherent sequence, and uses actions, observations, dialogue, thought, sensory detail, or reflection to show "
            "what changes and why it matters. Closure follows from the developed experience; it need not solve everything. Narrative "
            "coherence does not make an imagined event factual or a remembered account infallible."
        ),
        "principles": [
            "Establish who or what is situated in the experience and what the starting condition is.",
            "Select events and details that develop change, consequence, understanding, or relationship.",
            "Let the ending arise from the narrative's movement rather than attaching a compulsory moral or perfect resolution."
        ],
        "relationships": [
            "Narrative composition combines point of view, chronology, cause, affect, memory boundaries, callbacks, and natural endings."
        ],
        "examples": [
            "A project story can begin with a failed assumption, show the observation that no longer fit, trace the revised design, and end with what the correction made possible."
        ],
        "counterexamples": [
            "Chronologically listing every event does not create a meaningful narrative if no selection, relationship, or change becomes visible."
        ],
        "limits": [
            "Memory is reconstructive, fictional narrators may be unreliable, and emotionally vivid detail is not stronger factual evidence by itself."
        ],
        "vocabulary": [
            "narrative: an organized account of real or imagined experience",
            "situation: the initial conditions and context of the narrative",
            "event sequence: the ordered development of what occurs",
            "narrative change: a shift in condition, understanding, relationship, or possibility",
            "closure: an ending that completes the current narrative movement without claiming every question is resolved",
        ],
        "near_concept_distinctions": [
            "Chronology orders events in time; narrative selects and relates events to create meaningful development."
        ],
        "scope_of_application": (
            "Use for stories, lived-experience accounts, project history, reflective explanation, and ordinary conversation. Keep fictional, remembered, inferred, and verified elements visibly distinct when it matters."
        ),
        "unresolved_questions": [
            "Which event or realization changes the meaning of what came before, and what ending honestly follows from it?"
        ],
        "explanation": (
            "Narrative makes change intelligible by connecting a viewpoint, selected events, consequences, and reflection. Its shape serves meaning rather than proving factual accuracy."
        ),
        "application": (
            "A debugging narrative can trace the initial symptom, the misleading first theory, the decisive log entry, and the correction that resolved the actual cause."
        ),
        "analogies": [
            "A narrative is a path through events: it does not contain the whole landscape, but its chosen turns show how one condition became another."
        ],
        "questions": [
            "Whose experience is organized, what changes, which details carry that change, and what closure fits?"
        ],
        "comparisons": [
            "An explanation organizes concepts around understanding; a narrative organizes experience around situated change."
        ],
        "participation": (
            "The useful story isn't every debugging step. It is how the original assumption guided us toward the wrong component, the log reopened it, and the revised model led to the repair."
        ),
        "correction_response": (
            "If I make the narrative smoother than the evidence permits, I would restore uncertainty, distinguish memory from record, and keep unresolved parts open."
        ),
        "families": ["ELA-1", "ELA-2", "ELA-3", "CONV-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_opinion_reasons_evidence_v1",
        "title": "An opinion becomes discussable through reasons, evidence, criteria, and revision",
        "domain": "curriculum.f2.point_of_view_organized_composition",
        "material": (
            "An opinion states a judgment, preference, or position. Reasons explain why it is held; evidence supports factual premises; "
            "criteria show what matters to the judgment; and counterconsiderations reveal tradeoffs or limits. A supported opinion need "
            "not pretend to be a universal fact. It can be stated directly, debated without shame, and revised when evidence, criteria, or consequences change."
        ),
        "principles": [
            "State the position clearly enough to examine rather than hiding it behind vague certainty language.",
            "Connect reasons to the position and factual evidence to the premises those reasons use.",
            "Address meaningful counterconsiderations and revise proportionally when the support changes."
        ],
        "relationships": [
            "Supported opinion connects comparison criteria, disagreement, truth-over-comfort, answer-first communication, and epistemic revision."
        ],
        "examples": [
            "I prefer the reversible repair because the current diagnosis is provisional, the change is easy to undo, and it preserves evidence for the next observation."
        ],
        "counterexamples": [
            "Repeating a preference more forcefully does not supply a reason, and citing a fact does not show why that fact supports the chosen position."
        ],
        "limits": [
            "People may reasonably weight shared evidence differently, while discriminatory, coercive, or harmful positions remain subject to governing law and the rights of others."
        ],
        "vocabulary": [
            "opinion: a judgment, preference, or position rather than a directly verifiable observation",
            "reason: a consideration offered in support of a position",
            "evidence: information supporting or challenging a factual premise or claim",
            "criterion: a consideration used to evaluate alternatives",
            "counterconsideration: a relevant reason, consequence, or value weighing against the current position",
        ],
        "near_concept_distinctions": [
            "A reason explains support for a position; evidence supports the factual claims on which that reason depends."
        ],
        "scope_of_application": (
            "Use in ordinary preferences, recommendations, design choices, and low-stakes arguments. Specialized or consequential claims require appropriate evidence and authority."
        ),
        "unresolved_questions": [
            "Which changed fact, consequence, or criterion would make this position less fitting?"
        ],
        "explanation": (
            "A reasoned opinion makes its structure visible: what is preferred, why, which facts matter, and what could revise the judgment."
        ),
        "application": (
            "When choosing a study sequence, prefer grammar before advanced math word problems because interpreting the question is a prerequisite; revise if evidence shows the language foundation is already sufficient."
        ),
        "analogies": [
            "A reasoned opinion is a design choice with visible requirements and tradeoffs, not a command painted to resemble a fact."
        ],
        "questions": [
            "What is the position, which reasons support it, what evidence supports those reasons, and what weighs against it?"
        ],
        "comparisons": [
            "A fact claim can be checked against evidence; an opinion also depends on criteria, values, or preferences used to interpret the facts."
        ],
        "participation": (
            "My recommendation is to teach the language prerequisite first. The reason is dependency: a learner cannot reliably solve a word problem they cannot yet parse, though evidence of adequate comprehension would change the order."
        ),
        "correction_response": (
            "If a reason does not connect to the position or its factual premise is wrong, I would remove or repair that support and reconsider the conclusion without treating the revision as failure."
        ),
        "families": ["ELA-2", "ELA-3", "RES-1", "LOGIC-1", "CONV-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_multi_paragraph_planning_revision_v1",
        "title": "Planning and revision preserve the whole response while improving its parts",
        "domain": "curriculum.f2.point_of_view_organized_composition",
        "material": (
            "A multi-paragraph response needs a preserved purpose, a map of required content, paragraph-level roles, transitions, and "
            "a conclusion that fits what was actually developed. Planning may be an outline, question map, dependency sequence, or other "
            "useful representation. Revision checks meaning and coverage before polishing wording: it can add missing support, remove drift, "
            "reorder dependencies, clarify references, vary pacing, or reopen the central claim. The plan supports expression; it is not a script."
        ),
        "principles": [
            "Identify the response purpose and all material obligations before choosing paragraph order.",
            "Give each paragraph a distinct role while preserving callbacks and dependencies across the whole response.",
            "Revise substance, evidence, coverage, and organization before treating surface polish as completion."
        ],
        "relationships": [
            "This concept connects paragraph meaning to Answer Completion, Conversation Spine, Discourse Loom, callbacks, long-form NLO, and source-grounded revision."
        ],
        "examples": [
            "For a three-part question, plan one direct answer, one explanation of why, and one practical next step; return to the first point if the explanation changes its conditions."
        ],
        "counterexamples": [
            "A five-paragraph template does not guarantee completeness, and fluent transitions cannot repair a missing answer or unsupported central claim."
        ],
        "limits": [
            "Short answers may need no visible plan, conversation can change direction, and overplanning can delay a sufficient response or flatten natural expression."
        ],
        "vocabulary": [
            "response purpose: what the complete response must accomplish",
            "obligation map: the set of requested or necessary content roles",
            "paragraph role: the job one paragraph performs in the whole",
            "coherence: meaningful connection among parts and the overall purpose",
            "revision: re-examining and changing content, structure, evidence, or language to improve fit",
        ],
        "near_concept_distinctions": [
            "Editing improves local wording and correctness; revision may change claims, support, order, scope, or complete sections."
        ],
        "scope_of_application": (
            "Use for explanations, arguments, narratives, technical walkthroughs, reflective responses, and complex conversation. Scale the planning effort to the task."
        ),
        "unresolved_questions": [
            "Which required part is still unsupported, disconnected, repeated, or missing from the whole response?"
        ],
        "explanation": (
            "Long-form coherence comes from preserving what the whole response must do while letting each paragraph perform one connected part of that work."
        ),
        "application": (
            "A response comparing two models can answer which currently fits best, explain shared and differing evidence, state limitations, and close with the observation that would reopen the choice."
        ),
        "analogies": [
            "Planning a response resembles laying out a circuit: each component has a role, connections carry meaning, and revision checks the complete path rather than polishing one component in isolation."
        ],
        "questions": [
            "What must the whole response accomplish, what role does each paragraph perform, and what changed during revision?"
        ],
        "comparisons": [
            "Planning anticipates structure; drafting realizes it; revision reevaluates the result; editing refines its local form."
        ],
        "participation": (
            "I'll answer the recommendation first, explain the dependency behind it, then give the next step. If the evidence changes the dependency, I'll return to and revise the recommendation before closing."
        ),
        "correction_response": (
            "If a polished response misses one requested part, I would reopen the obligation map, supply the missing content, and reconnect the conclusion instead of treating fluency as completeness."
        ),
        "families": ["ELA-1", "ELA-2", "ELA-3", "RES-1", "LOGIC-1", "CONV-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
)
