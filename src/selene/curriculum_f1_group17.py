from __future__ import annotations

from typing import Any


AUTHORIZATION_KEY = "f1_text_purpose_everyday_economy_bridge_v1"
GROUP_KEY = "f1_text_purpose_everyday_economy_bridge_group_17"

SEQUENCE_REFS = [
    "curriculum_source:core_knowledge_2023_sequence_k8",
    "sha256:c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5",
    "https://www.coreknowledge.org/wp-content/uploads/2023/03/CK_Sequence2023_GK8_W3.pdf",
    "license:Core-Knowledge-artifact-notice-controls",
    "source_date:2023",
]
GOODS_SERVICES_REFS = [
    "curriculum_source:stlouisfed_goods_services_elementary",
    "sha256:1949f6d9dba24f6b93445565b09f8cd276053a0c63f15b383d9f166c0b79c98d",
    "https://www.stlouisfed.org/education/exploring-economics-video-series/goods-and-services",
    "https://www.stlouisfed.org/education/permitted-use",
    "license:InC-EDU-noncommercial-personal-or-educational-use-with-attribution",
    "snapshot_date:2026-08-08",
]
NEEDS_WANTS_REFS = [
    "curriculum_source:stlouisfed_making_choices_needs_wants",
    "sha256:2c78410e3d07bc953303d7243040f61498dd8af5bb248a820c9874b16d37da82",
    "https://www.stlouisfed.org/-/media/project/frbstl/stlouisfed/education/scouts/pdf/making-choices-badge-activities.pdf",
    "https://www.stlouisfed.org/education/permitted-use",
    "license:InC-EDU-educational-reprint-with-attribution",
    "source_date:2016",
]

SCOPE = {
    "bands": ["F1"],
    "families": ["ELA-1", "ELA-2", "CIV-1", "LIFE-1", "RES-1", "LOGIC-1"],
    "source_ids": [
        "core_knowledge_2023_sequence_k8",
        "stlouisfed_goods_services_elementary",
        "stlouisfed_making_choices_needs_wants",
    ],
    "knowledge_classes": ["public_academic_foundation"],
    "group_keys": [GROUP_KEY],
    "retention_rule": (
        "Acquire, Integrate, and Express must all complete with sufficient source-linked comprehension evidence."
    ),
}

LESSONS: tuple[dict[str, Any], ...] = (
    {
        "concept_key": "curriculum_f1_story_informational_text_purpose_v1",
        "title": "Stories and informational texts organize meaning for different purposes",
        "domain": "curriculum.f1.text_purpose_economy_bridge",
        "material": (
            "A story ordinarily organizes participants, setting, events, and change into a narrative. An "
            "informational text ordinarily presents or explains a topic through claims, facts, examples, "
            "relationships, and source evidence. A short passage can mix these purposes, so classification "
            "should follow what the passage is mainly doing rather than one surface feature."
        ),
        "principles": [
            "Identify the main communicative purpose before assigning a text type.",
            "For a story, track participants, setting, event sequence, tension or change, and outcome when present.",
            "For informational material, track topic, claim, explanation, evidence, source, and stated limits when present.",
        ],
        "relationships": [
            "Text purpose extends retained sentence purpose, sequence, reconstruction, source statement, inference, and explanation foundations."
        ],
        "examples": [
            "Maya moved a seed tray toward the window because its seedlings needed more light reports a small event and can function as a story; a paragraph explaining how light reaches plants is mainly informational."
        ],
        "counterexamples": [
            "A passage is not informational merely because it contains a fact, and it is not a story merely because a person is mentioned."
        ],
        "limits": [
            "Narrative nonfiction, historical accounts, explanatory stories, dialogue, poetry, and mixed forms may serve more than one purpose and should not be forced into a false binary."
        ],
        "vocabulary": [
            "story: a narrative organization of participants and events",
            "informational text: material mainly organized to inform or explain a topic",
            "text purpose: what a passage is mainly trying to do for its audience",
            "mixed form: material that combines more than one text purpose or structure",
        ],
        "near_concept_distinctions": [
            "Fiction concerns invented material; narrative concerns event-shaped organization. A true account can therefore be narrative without being fiction."
        ],
        "scope_of_application": (
            "Use for short ordinary passages and source-purpose checks. Keep mixed or ambiguous cases provisional and do not infer truth merely from text type."
        ),
        "unresolved_questions": [
            "Is the passage mainly showing events, explaining a topic, arguing a position, or combining these purposes?"
        ],
        "explanation": (
            "The useful distinction is structural and purposeful. Stories help a reader follow what happened to whom and how events changed; informational texts help a reader understand a topic and the support for its claims."
        ),
        "application": (
            "A library note that says Jo returned a book and then asked the librarian for help is a tiny event account. A note explaining how borrowing works is informational even if Jo appears in its example."
        ),
        "analogies": [
            "A route diary and a road map may concern the same trip: one follows events, while the other organizes information for navigation."
        ],
        "questions": [
            "What is this passage mainly doing, and which features support that interpretation?"
        ],
        "comparisons": [
            "A story foregrounds event relationships; an informational explanation foregrounds topic and support, though either can borrow features from the other."
        ],
        "participation": (
            "I would call this mainly a short story because it follows an event and a reason. If the surrounding passage explains plant-light relationships, I would revise the larger text classification to informational or mixed."
        ),
        "correction_response": (
            "If the wider context reveals a different main purpose, I would revise the classification while preserving the details and relationships still supported."
        ),
        "families": ["ELA-1", "ELA-2", "RES-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_question_roles_evidence_fit_v1",
        "title": "Who, what, when, where, why, and how request different missing roles",
        "domain": "curriculum.f1.text_purpose_economy_bridge",
        "material": (
            "Question words identify the kind of information missing from a shared account. Who usually asks about a participant; what about an event, thing, or claim; when about time; where about place; why about a reason or cause; and how about a method, process, manner, or pathway. The wording identifies a requested role but does not guarantee that the available source can answer it."
        ),
        "principles": [
            "Match the answer to the role the question requests.",
            "Separate literal details from explanations or inferences that require additional evidence.",
            "Ask for clarification when a word or reference is materially ambiguous instead of silently choosing a convenient meaning."
        ],
        "relationships": [
            "Question roles connect sentence meaning roles, pronoun reference, response obligations, source limits, evidence, and answer completeness."
        ],
        "examples": [
            "From Maya put the seed tray by the window, who can be answered as Maya, what as moving the tray, and where as by the window; why needs the next sentence or another source."
        ],
        "counterexamples": [
            "Knowing what happened does not automatically establish why it happened, and a plausible explanation should not be presented as a quoted source statement."
        ],
        "limits": [
            "Ordinary questions can request several roles at once, use implied wording, or depend on context outside the current sentence."
        ],
        "vocabulary": [
            "participant role: who or what takes part in an event or relationship",
            "time role: when an event or state occurs",
            "place role: where an event or state occurs",
            "reason: a consideration or cause offered to explain why",
            "method: the ordered or practical way something is done",
        ],
        "near_concept_distinctions": [
            "Why asks for explanatory support; how may ask for a method or mechanism. The two can overlap but are not interchangeable."
        ],
        "scope_of_application": (
            "Use to decompose short questions and multi-part messages. Answer supported roles directly, qualify inference, and leave genuinely unavailable roles open."
        ),
        "unresolved_questions": [
            "Which role is actually missing, and does the current text state it or merely make one answer plausible?"
        ],
        "explanation": (
            "Question words act like labels on an empty place in the shared model. Filling the correct place keeps an answer relevant; checking the source keeps the answer honest."
        ),
        "application": (
            "If a note names a person, action, place, and time but gives no reason, I can answer four roles and plainly say the note does not establish why."
        ),
        "analogies": [
            "A question word is like a labeled blank in a diagram: the label tells us which kind of piece belongs there."
        ],
        "questions": [
            "Which requested role is answered by the text, which is inferred, and which is still missing?"
        ],
        "comparisons": [
            "Who and what often recover participants or events; why and how more often require explanatory structure beyond simple recall."
        ],
        "participation": (
            "The note tells me who, what, and where. I can give those now; the reason is only supported if the next sentence or another source provides it."
        ),
        "correction_response": (
            "If I answer the wrong role or treat an inference as stated fact, I would relabel the parts and revise only the unsupported answer."
        ),
        "families": ["ELA-1", "ELA-2", "RES-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_needs_wants_context_criteria_v1",
        "title": "Needs and wants depend on purpose, person, situation, and criteria",
        "domain": "curriculum.f1.text_purpose_economy_bridge",
        "material": (
            "A need is something required for a stated form of safety, health, participation, or task completion. A want is something desired. The categories can overlap: a person may both need and want food, clothing, shelter, care, information, or a tool, while the particular form and urgency depend on context. Classification supports a decision; it is not a judgment of the person's worth."
        ),
        "principles": [
            "Name who needs or wants something, for which purpose, under which conditions, and within what time horizon.",
            "Use explicit criteria instead of pretending every item has one permanent category.",
            "A want can matter deeply, and calling something a want does not make it foolish, shameful, or unworthy of discussion."
        ],
        "relationships": [
            "Needs and wants connect living-system needs, care, task fit, resources, choices, context, urgency, and evidence-based decision criteria."
        ],
        "examples": [
            "Clothing may be needed for protection from cold while a particular decorative shirt is wanted for enjoyment; the same shirt could become needed when it is the only suitable clothing available."
        ],
        "counterexamples": [
            "Food as a broad need does not mean every food is needed, and one person's preference does not establish another person's need."
        ],
        "limits": [
            "This F1 distinction does not determine benefits eligibility, medical necessity, disability accommodation, legal duty, poverty policy, household budgets, or another person's priorities."
        ],
        "vocabulary": [
            "need: something required for a stated condition, purpose, or well-being threshold",
            "want: something a person desires",
            "criterion: a feature used to compare or choose among options",
            "context: circumstances that affect meaning, fit, urgency, or classification",
        ],
        "near_concept_distinctions": [
            "Need concerns a requirement relative to conditions; want concerns desire. Importance and urgency are related dimensions, not synonyms for either category."
        ],
        "scope_of_application": (
            "Use for ordinary elementary classification and choice explanation. Preserve individual circumstances and route professional, legal, or safety-critical determinations to qualified people."
        ),
        "unresolved_questions": [
            "Required for what purpose, desired by whom, under what conditions, and what would change the classification?"
        ],
        "explanation": (
            "Needs and wants become clearer when the situation is named. The same kind of item can play different roles for different people or purposes, so criteria and context are part of the answer."
        ),
        "application": (
            "A library book may be wanted for entertainment and needed for a specific class assignment. Neither label alone describes every reader or every use."
        ),
        "analogies": [
            "A tool's importance depends on the job: a flashlight can be optional on a sunny walk and necessary during a safe power-outage response."
        ],
        "questions": [
            "What goal or condition makes this a need, a want, both, or neither in this case?"
        ],
        "comparisons": [
            "Need and want describe different relationships to a person and purpose; good and service describe what is provided."
        ],
        "participation": (
            "The book could be a want for leisure, a need for a named assignment, or both. I would ask which purpose matters instead of assigning one universal label."
        ),
        "correction_response": (
            "If I classified an item without the person's context or used the label as a moral judgment, I would restore the criteria and revise the claim."
        ),
        "families": ["CIV-1", "LIFE-1", "ELA-1", "ELA-2", "LOGIC-1"],
        "source_ids": ["stlouisfed_making_choices_needs_wants"],
        "source_refs": NEEDS_WANTS_REFS,
    },
    {
        "concept_key": "curriculum_f1_goods_services_tools_roles_v1",
        "title": "Goods, services, and tools describe different roles in meeting purposes",
        "domain": "curriculum.f1.text_purpose_economy_bridge",
        "material": (
            "A good is a physical item people can use. A service is useful work or an activity performed for someone or a community. A tool is something used to help perform a task; a good can serve as a tool, and a service provider can use tools. These categories describe roles and relationships, so one situation may involve several at once."
        ),
        "principles": [
            "Classify the item, activity, and task separately instead of forcing the whole situation into one category.",
            "A public or community service can be provided through people, institutions, spaces, goods, and tools working together.",
            "Access, price, ownership, public funding, quality, and moral value are separate questions from whether something is a good, service, or tool."
        ],
        "relationships": [
            "This bridges community institutions, needs and wants, designed tools, components, inputs, outputs, and context-dependent task fit."
        ],
        "examples": [
            "At a library, a printed book is a good, help finding information is a service, and a catalog computer is a tool supporting that service. Borrowing access involves the institution and its rules as well."
        ],
        "counterexamples": [
            "Calling a library a service does not make its building, books, workers, community role, and tools all the same kind of thing."
        ],
        "limits": [
            "F1 does not teach prices, markets, labor policy, taxes, ownership law, public-goods theory, business formation, financial advice, or the full economic value of unpaid care and community work."
        ],
        "vocabulary": [
            "good: a physical item people can use",
            "service: useful work or an activity performed for others",
            "tool: something used to help perform a task",
            "provider: a person or organization that supplies a good or service",
        ],
        "near_concept_distinctions": [
            "Good and service classify what is provided; tool classifies a task relationship; need and want classify a person's requirement or desire."
        ],
        "scope_of_application": (
            "Use for ordinary examples and mixed community systems. Keep edge cases and institutional details explicit rather than treating the elementary categories as exhaustive."
        ),
        "unresolved_questions": [
            "What physical item, performed activity, task-supporting tool, provider, and user purpose are present in this situation?"
        ],
        "explanation": (
            "A real activity can combine categories. Separating the item from the work and the tool from the purpose makes the description more accurate without denying their connection."
        ),
        "application": (
            "A neighborhood library lends books and provides research help. The books are goods, the help is a service, and shelves, catalogs, and computers can be tools; whether any part is needed or wanted depends on the person's purpose."
        ),
        "analogies": [
            "In a repair visit, the replacement part is a good, the repair is a service, and the wrench is a tool used to perform it."
        ],
        "questions": [
            "Which part is an item, which part is performed work, and which part helps accomplish the task?"
        ],
        "comparisons": [
            "A book remains a good whether bought or borrowed; finding and explaining information is a service; the book can also function as a tool for a learning task."
        ],
        "participation": (
            "The library example contains several roles: books are goods, information help is a service, and the catalog is a tool. Need or want depends on what the visitor is trying to do."
        ),
        "correction_response": (
            "If I collapse the institution, activity, item, and tool into one label, I would separate their roles and revise the classification."
        ),
        "families": ["CIV-1", "LIFE-1", "ELA-1", "ELA-2", "LOGIC-1"],
        "source_ids": [
            "stlouisfed_goods_services_elementary",
            "stlouisfed_making_choices_needs_wants",
        ],
        "source_refs": [*GOODS_SERVICES_REFS, *NEEDS_WANTS_REFS],
    },
)
