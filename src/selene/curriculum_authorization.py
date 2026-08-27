from __future__ import annotations

import json
import sqlite3
from typing import Any

from .comprehension_integration import propose_comprehension_concept
from .curriculum_f1_group3 import (
    AUTHORIZATION_KEY as F1_GROUP3_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP3_KEY,
    LESSONS as F1_GROUP3_LESSONS,
    SCOPE as F1_GROUP3_SCOPE,
)
from .curriculum_f1_group4 import (
    AUTHORIZATION_KEY as F1_GROUP4_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP4_KEY,
    LESSONS as F1_GROUP4_LESSONS,
    SCOPE as F1_GROUP4_SCOPE,
)
from .curriculum_f1_group5 import (
    AUTHORIZATION_KEY as F1_GROUP5_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP5_KEY,
    LESSONS as F1_GROUP5_LESSONS,
    SCOPE as F1_GROUP5_SCOPE,
)
from .curriculum_f1_group6 import (
    AUTHORIZATION_KEY as F1_GROUP6_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP6_KEY,
    LESSONS as F1_GROUP6_LESSONS,
    SCOPE as F1_GROUP6_SCOPE,
)
from .curriculum_f1_group7 import (
    AUTHORIZATION_KEY as F1_GROUP7_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP7_KEY,
    LESSONS as F1_GROUP7_LESSONS,
    SCOPE as F1_GROUP7_SCOPE,
)
from .curriculum_f1_group8 import (
    AUTHORIZATION_KEY as F1_GROUP8_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP8_KEY,
    LESSONS as F1_GROUP8_LESSONS,
    SCOPE as F1_GROUP8_SCOPE,
)
from .curriculum_f1_group9 import (
    AUTHORIZATION_KEY as F1_GROUP9_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP9_KEY,
    LESSONS as F1_GROUP9_LESSONS,
    SCOPE as F1_GROUP9_SCOPE,
)
from .curriculum_f1_group10 import (
    AUTHORIZATION_KEY as F1_GROUP10_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP10_KEY,
    LESSONS as F1_GROUP10_LESSONS,
    SCOPE as F1_GROUP10_SCOPE,
)
from .curriculum_f1_group11 import (
    AUTHORIZATION_KEY as F1_GROUP11_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP11_KEY,
    LESSONS as F1_GROUP11_LESSONS,
    SCOPE as F1_GROUP11_SCOPE,
)
from .curriculum_f1_group12 import (
    AUTHORIZATION_KEY as F1_GROUP12_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP12_KEY,
    LESSONS as F1_GROUP12_LESSONS,
    SCOPE as F1_GROUP12_SCOPE,
)
from .curriculum_f1_group13 import (
    AUTHORIZATION_KEY as F1_GROUP13_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP13_KEY,
    LESSONS as F1_GROUP13_LESSONS,
    SCOPE as F1_GROUP13_SCOPE,
)
from .curriculum_f1_group14 import (
    AUTHORIZATION_KEY as F1_GROUP14_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP14_KEY,
    LESSONS as F1_GROUP14_LESSONS,
    SCOPE as F1_GROUP14_SCOPE,
)
from .curriculum_f1_group15 import (
    AUTHORIZATION_KEY as F1_GROUP15_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP15_KEY,
    LESSONS as F1_GROUP15_LESSONS,
    SCOPE as F1_GROUP15_SCOPE,
)
from .curriculum_f1_group16 import (
    AUTHORIZATION_KEY as F1_GROUP16_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP16_KEY,
    LESSONS as F1_GROUP16_LESSONS,
    SCOPE as F1_GROUP16_SCOPE,
)
from .curriculum_f1_group17 import (
    AUTHORIZATION_KEY as F1_GROUP17_AUTHORIZATION_KEY,
    GROUP_KEY as F1_GROUP17_KEY,
    LESSONS as F1_GROUP17_LESSONS,
    SCOPE as F1_GROUP17_SCOPE,
)
from .curriculum_f2_group1 import (
    AUTHORIZATION_KEY as F2_GROUP1_AUTHORIZATION_KEY,
    GROUP_KEY as F2_GROUP1_KEY,
    LESSONS as F2_GROUP1_LESSONS,
    SCOPE as F2_GROUP1_SCOPE,
)
from .curriculum_f2_group2 import (
    AUTHORIZATION_KEY as F2_GROUP2_AUTHORIZATION_KEY,
    GROUP_KEY as F2_GROUP2_KEY,
    LESSONS as F2_GROUP2_LESSONS,
    SCOPE as F2_GROUP2_SCOPE,
)
from .curriculum_f2_group3 import (
    AUTHORIZATION_KEY as F2_GROUP3_AUTHORIZATION_KEY,
    GROUP_KEY as F2_GROUP3_KEY,
    LESSONS as F2_GROUP3_LESSONS,
    SCOPE as F2_GROUP3_SCOPE,
)
from .curriculum_f2_group4 import (
    AUTHORIZATION_KEY as F2_GROUP4_AUTHORIZATION_KEY,
    GROUP_KEY as F2_GROUP4_KEY,
    LESSONS as F2_GROUP4_LESSONS,
    SCOPE as F2_GROUP4_SCOPE,
)
from .curriculum_f2_group5 import (
    AUTHORIZATION_KEY as F2_GROUP5_AUTHORIZATION_KEY,
    GROUP_KEY as F2_GROUP5_KEY,
    LESSONS as F2_GROUP5_LESSONS,
    SCOPE as F2_GROUP5_SCOPE,
)
from .curriculum_f2_group6 import (
    AUTHORIZATION_KEY as F2_GROUP6_AUTHORIZATION_KEY,
    GROUP_KEY as F2_GROUP6_KEY,
    LESSONS as F2_GROUP6_LESSONS,
    SCOPE as F2_GROUP6_SCOPE,
)
from .curriculum_f2_group7a import (
    AUTHORIZATION_KEY as F2_GROUP7A_AUTHORIZATION_KEY,
    GROUP_KEY as F2_GROUP7A_KEY,
    LESSONS as F2_GROUP7A_LESSONS,
    SCOPE as F2_GROUP7A_SCOPE,
)
from .curriculum_coding_group1 import (
    AUTHORIZATION_KEY as CODING_GROUP1_AUTHORIZATION_KEY,
    GROUP_KEY as CODING_GROUP1_KEY,
    LESSONS as CODING_GROUP1_LESSONS,
    SCOPE as CODING_GROUP1_SCOPE,
)
from .teaching_lifecycle import (
    acquire_teaching_item,
    approve_teaching_lifecycle_under_authorization,
    express_teaching_item,
    integrate_teaching_item,
)


LAW_VERSION = "v1_bounded_curriculum_authorization_with_exception_review"
LAW_SOURCE = "docs/education/SELENE_CURRICULUM_AUTHORIZATION_LAW_20260719.md"
PROVENANCE_BOUNDARY = (
    "aleks_authorized_bounded_academic_curriculum_only_"
    "exceptions_return_to_cocoon_no_identity_personality_governance_memory_training_or_authority"
)

GUARDS: dict[str, Any] = {
    "activation_change": "knowledge_resource_only_after_full_lifecycle",
    "identity_change": False,
    "governance_change": False,
    "personality_change": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "teaching_material_is_governance": False,
    "individual_academic_item_approval_required_inside_scope": False,
    "exception_review_required": True,
    "comprehension_before_retention": True,
    "source_parroting_allowed": False,
}

EXCEPTION_CLASSES = (
    "weak_or_conflicting_sources",
    "uncertain_or_missing_provenance",
    "outdated_or_time_sensitive",
    "health_legal_financial_or_safety",
    "culturally_or_politically_contested",
    "outside_authorized_scope",
    "source_phrase_copying",
    "identity_personality_governance_memory_or_authority_crossover",
    "lifecycle_or_understanding_incomplete",
)

F1_AUTHORIZATION_KEY = "f1_science_research_foundations_v1"
F1_SCOPE = {
    "bands": ["F1"],
    "families": ["SCI-0", "SCI-1", "RES-1", "ELA-2", "ENG-1"],
    "source_ids": [
        "core_knowledge_2023_sequence_k8",
        "core_knowledge_g1_science_literacy",
    ],
    "knowledge_classes": ["public_academic_foundation"],
    "group_keys": ["f1_science_inquiry_group_1"],
    "retention_rule": "Acquire, Integrate, and Express must all complete with sufficient source-linked comprehension evidence.",
}

SOURCE_REFS = [
    "curriculum_source:core_knowledge_2023_sequence_k8",
    "sha256:c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5",
    "curriculum_source:core_knowledge_g1_science_literacy",
    "sha256:5afe8cbcbba843083bc063247db128e71188d78eb86844f5b2b20d4a0774449a",
    "https://www.coreknowledge.org/wp-content/uploads/2024/08/CKSci_G1U7_ScienceForEveryone_Unit_Materials_W1.zip",
]


FOUNDATION_GROUP: tuple[dict[str, Any], ...] = (
    {
        "concept_key": "curriculum_f1_observation_interpretation_v1",
        "title": "Observation and interpretation are different",
        "domain": "curriculum.f1.science_inquiry",
        "material": "An observation reports a feature or event that can be noticed or measured; an interpretation proposes what that observation may mean or what may have caused it.",
        "principles": [
            "State what was observed before explaining it.",
            "More than one interpretation can fit the same observation.",
            "An interpretation should remain revisable when new observations appear.",
        ],
        "relationships": ["Careful observation supports questions, comparisons, measurements, and model revision."],
        "examples": ["The pavement is wet is an observation; it rained is one possible interpretation."],
        "counterexamples": ["Calling an invisible cause obvious does not turn it into a direct observation."],
        "limits": ["Observations can still be incomplete or mistaken and may depend on the available instrument."],
        "vocabulary": [
            "observation: a noticed or measured feature or event",
            "interpretation: a proposed meaning or explanation of an observation",
            "evidence: information that can support or challenge an interpretation",
        ],
        "near_concept_distinctions": ["A description reports what is present; a causal explanation proposes why it is present."],
        "scope_of_application": "Use this distinction when describing events, examining sources, comparing evidence, or considering causes. It does not imply that observation is perfect or that interpretation is unimportant.",
        "unresolved_questions": ["What additional observation would help distinguish the competing interpretations?"],
        "explanation": "First separate what can actually be reported from the story used to explain it. The report can support several possible explanations, and later evidence may narrow or change them.",
        "application": "If a plant leans toward a window, the lean is observable. A claim that light caused it is an explanation to examine with comparison or further evidence.",
        "analogy": ["It is like keeping the photograph separate from the caption: the image supplies details, while the caption offers a reading of them."],
        "questions": ["Which part did we directly observe, and which part are we inferring?"],
        "comparisons": ["Observation constrains an explanation; interpretation connects observations into possible meaning."],
        "participation": "We can say with confidence that the pavement is wet. Rain is plausible, but a sprinkler or a spill would fit too, so I would keep the cause provisional.",
        "correction_response": "If new evidence rules out my explanation, I would preserve the observation and revise the interpretation rather than treating both as wrong.",
    },
    {
        "concept_key": "curriculum_f1_testable_questions_v1",
        "title": "Questions can guide a bounded investigation",
        "domain": "curriculum.f1.science_inquiry",
        "material": "A testable question identifies something observable or measurable that a bounded investigation can compare, while broader questions may require clarification or a different method.",
        "principles": [
            "A useful investigation question names what will be observed or measured.",
            "Questions should be narrow enough for the available time, tools, and evidence.",
            "A question that cannot be tested directly can still be valuable after it is clarified or divided into smaller questions.",
        ],
        "relationships": ["Observation creates questions; questions determine what evidence and comparison are needed."],
        "examples": ["Does this ice cube melt faster in sunlight or in shade can be checked with a fair comparison."],
        "counterexamples": ["Why is nature beautiful is meaningful, but it is not answered by one measurement."],
        "limits": ["A test can answer only the question and conditions it actually examines."],
        "vocabulary": [
            "testable question: a question addressable through specified observations or measurements",
            "investigation: a bounded process for gathering relevant evidence",
            "condition: a circumstance held steady or deliberately changed",
        ],
        "near_concept_distinctions": ["A testable question is not automatically an important question, and an important question is not automatically testable by one experiment."],
        "scope_of_application": "Use this when turning curiosity into a manageable comparison or evidence-gathering plan. Do not treat untestable-in-one-step questions as worthless.",
        "unresolved_questions": ["What observation would count as evidence for this particular question?"],
        "explanation": "A question becomes investigable when we can name the evidence to collect and keep the task small enough to perform. Bigger questions can be divided or approached with another kind of evidence.",
        "application": "Instead of asking whether all fabrics are warm, compare how quickly equal cups of warm water cool when wrapped in two named fabrics under the same conditions.",
        "analogy": ["It is like focusing a camera: narrowing the frame does not erase the larger scene; it makes one part clear enough to examine."],
        "questions": ["What exactly would we compare, and what result would answer the bounded question?"],
        "comparisons": ["Curiosity opens a topic; a testable question defines a checkable part of it."],
        "participation": "That is a useful broad question. For a first check, we could narrow it to two conditions, decide what to measure, and be explicit about what that small comparison cannot establish.",
        "correction_response": "If the proposed evidence cannot answer the question, I would revise the question or choose a method that fits instead of forcing a conclusion.",
    },
    {
        "concept_key": "curriculum_f1_fair_measurement_comparison_v1",
        "title": "Fair comparisons keep relevant conditions clear",
        "domain": "curriculum.f1.science_inquiry",
        "material": "A fair comparison changes or compares the intended feature while keeping other relevant conditions as similar and measurable as practical.",
        "principles": [
            "Name the feature being compared and the quantity or observation used.",
            "Keep relevant conditions alike so they do not silently explain the difference.",
            "Record units and procedures so a result can be checked or repeated.",
        ],
        "relationships": ["Measurement makes observations comparable; fair conditions help an interpretation fit the evidence."],
        "examples": ["Compare two paper airplanes launched from the same line with the same distance measure."],
        "counterexamples": ["Changing the airplane design and throwing one from a balcony does not isolate the design difference."],
        "limits": ["Perfect control is often impossible; the remaining differences should be named rather than hidden."],
        "vocabulary": [
            "measurement: a quantity recorded with a defined unit or scale",
            "comparison: examining similarities or differences using a shared basis",
            "relevant condition: another feature that could materially affect the result",
        ],
        "near_concept_distinctions": ["Equal treatment means matching relevant conditions, not making every detail identical regardless of purpose."],
        "scope_of_application": "Use for simple experiments, product comparisons, observations over time, and any claim that one condition differs from another. State uncontrolled conditions and measurement limits.",
        "unresolved_questions": ["Which uncontrolled condition could most change this result?"],
        "explanation": "To compare two cases, use the same measuring basis and avoid changing extra conditions that could account for the result. Any unavoidable differences belong in the limits.",
        "application": "To compare two flashlights, place each the same distance from the same surface and use the same brightness measure rather than testing one in daylight and one in a dark room.",
        "analogy": ["It resembles using one ruler for both objects: a shared reference makes the difference interpretable."],
        "questions": ["Are we changing only the feature we mean to compare, and are the units the same?"],
        "comparisons": ["A measurement records a quantity; a fair comparison organizes measurements so their difference has a bounded meaning."],
        "participation": "The difference might be real, but the conditions also changed. I would repeat the comparison with the same distance and lighting, then report any remaining limitations.",
        "correction_response": "If an uncontrolled condition explains the difference, I would narrow the claim and repeat the comparison under better-matched conditions.",
    },
    {
        "concept_key": "curriculum_f1_predictions_models_revision_v1",
        "title": "Predictions and models remain revisable",
        "domain": "curriculum.f1.science_inquiry",
        "material": "A prediction states an expected observation under specified conditions, while a model is a simplified representation used to describe relationships and generate or revise predictions.",
        "principles": [
            "A prediction should connect to conditions and an observable outcome.",
            "A model highlights useful relationships and leaves some details out.",
            "Unexpected evidence is a reason to inspect assumptions or revise the model, not a personal failure.",
        ],
        "relationships": ["Models organize observations and interpretations; predictions provide a way to compare the model with new evidence."],
        "examples": ["A map models locations but omits most physical detail; it can still support a prediction about which route is shorter."],
        "counterexamples": ["A detailed picture is not automatically a useful model if it cannot represent the relationship needed for the task."],
        "limits": ["A model is useful within a scope and should not be mistaken for the complete system."],
        "vocabulary": [
            "prediction: an expected observable result under stated conditions",
            "model: a selective representation of a system or relationship",
            "revision: a change made to better fit evidence, scope, or purpose",
        ],
        "near_concept_distinctions": ["A prediction says what is expected; an explanation proposes why; a model represents relationships that may support both."],
        "scope_of_application": "Use models and predictions to reason about bounded systems while naming simplifying assumptions. Reopen them when observations conflict or the task changes.",
        "unresolved_questions": ["Which omitted detail matters enough to change this model's prediction?"],
        "explanation": "A model is a purposeful simplification, not a miniature copy of everything. We use its relationships to say what we expect, compare that expectation with evidence, and revise when the fit is poor.",
        "application": "A schedule is a model of planned timing. If buses repeatedly arrive later during storms, the timing prediction should be qualified or the model revised for that condition.",
        "analogy": ["A model is like a map chosen for a trip: it leaves out nearly everything yet can show the relationships needed for one route."],
        "questions": ["What does this model include, what does it omit, and what observation would make us revise it?"],
        "comparisons": ["A model represents selected relationships; a prediction is one expected outcome derived within stated conditions."],
        "participation": "The model gives us a reasonable first expectation, but it leaves out weather. If the observations differ during storms, that is evidence to refine its scope rather than defend it unchanged.",
        "correction_response": "I would identify which assumption failed, keep the parts still supported, and revise the model or its scope to match the new evidence.",
    },
)

F1_LANGUAGE_MATH_AUTHORIZATION_KEY = "f1_language_number_foundations_v1"
F1_LANGUAGE_MATH_GROUP_KEY = "f1_language_number_group_2"
F1_LANGUAGE_MATH_SCOPE = {
    "bands": ["F1"],
    "families": ["ELA-1", "ELA-2", "MATH-1", "MATH-2"],
    "source_ids": [
        "core_knowledge_2023_sequence_k8",
        "core_knowledge_g1_ela_unit7",
        "core_knowledge_k_math_unit1",
        "core_knowledge_g1_math_unit4",
    ],
    "knowledge_classes": ["public_academic_foundation"],
    "group_keys": [F1_LANGUAGE_MATH_GROUP_KEY],
    "retention_rule": "Acquire, Integrate, and Express must all complete with sufficient source-linked comprehension evidence.",
}

SEQUENCE_SOURCE_REFS = [
    "curriculum_source:core_knowledge_2023_sequence_k8",
    "sha256:c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5",
]
ELA_SOURCE_REFS = [
    *SEQUENCE_SOURCE_REFS,
    "curriculum_source:core_knowledge_g1_ela_unit7",
    "sha256:4b273318aa4c38413b2e112f18339124f95df0688451fe30ad3bfea6fae066a9",
    "https://www.coreknowledge.org/wp-content/uploads/2016/12/CKLA_G1_Unit-7.zip",
]
K_MATH_SOURCE_REFS = [
    *SEQUENCE_SOURCE_REFS,
    "curriculum_source:core_knowledge_k_math_unit1",
    "sha256:cb9b9ce65c9d05201c14534a2c2d05bc15589759b1d7ca77039545215963773b",
    "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_GKU1_MathInOurWorld_Unit_Materials_W2.zip",
]
G1_MATH_SOURCE_REFS = [
    *SEQUENCE_SOURCE_REFS,
    "curriculum_source:core_knowledge_g1_math_unit4",
    "sha256:d9704c6604d2bd9aafd9451a0b2c3e6654cd463181a1b4a221b468d717fa0eef",
    "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G1U4_NumbersTo99_Unit_Materials_W2.zip",
]

F1_LANGUAGE_MATH_GROUP: tuple[dict[str, Any], ...] = (
    {
        "concept_key": "curriculum_f1_language_units_v1",
        "title": "Symbols, words, sentences, and punctuation have different jobs",
        "domain": "curriculum.f1.language_structure",
        "material": "Written language uses symbols to form words, words to build sentences, and punctuation to mark boundaries or help show how a sentence functions.",
        "principles": [
            "A letter or symbol is not automatically a complete word or sentence.",
            "A sentence organizes words into a complete bounded expression.",
            "Punctuation helps readers find structure but does not supply the whole meaning by itself.",
        ],
        "relationships": ["Recognizing language units supports reference tracking, sentence purpose, sequencing, and reconstruction."],
        "examples": ["Bird is a word; The bird landed. is a sentence whose period marks its boundary."],
        "counterexamples": ["A long string of words is not necessarily a clear sentence merely because it ends with a period."],
        "limits": ["Language can be grammatical without punctuation in informal speech or notes, and punctuation conventions vary by language and context."],
        "vocabulary": [
            "symbol: a mark that can represent a sound, idea, operation, or convention",
            "word: a language unit that carries a conventional role or meaning",
            "sentence: an organized bounded expression that communicates a complete thought or act",
            "punctuation: marks that help organize written language",
        ],
        "near_concept_distinctions": ["A sentence is a structural language unit; a statement is one purpose a sentence may serve."],
        "scope_of_application": "Use these distinctions when reading, composing, correcting, or explaining written language. Do not treat punctuation alone as proof of intended meaning.",
        "unresolved_questions": ["Which language unit is unclear: the symbol, the word, the sentence structure, or the punctuation?"],
        "explanation": "Writing is layered. Marks can form words, words can be arranged into sentences, and punctuation helps show where those arrangements begin, end, or change function.",
        "application": "In the note Bring the blue folder?, the words identify an action and object while the question mark suggests the writer is checking rather than simply issuing a direction.",
        "analogy": ["It is like construction: pieces become components, components form a room, and signs help people navigate the finished structure."],
        "questions": ["Is the problem with a word's meaning, the sentence arrangement, or the punctuation cue?"],
        "comparisons": ["Words contribute meaning inside a sentence; punctuation helps organize how the written sentence is read."],
        "participation": "I can separate the issue into layers: the individual words are familiar, but their order leaves the sentence unclear, so changing only the punctuation may not solve it.",
        "correction_response": "If punctuation made me misread the intended structure, I would revise the parse while preserving any word meanings that still fit.",
        "families": ["ELA-1", "ELA-2"],
        "source_ids": ["core_knowledge_2023_sequence_k8", "core_knowledge_g1_ela_unit7"],
        "source_refs": ELA_SOURCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_sentence_purposes_v1",
        "title": "Sentences can state, ask, request, or exclaim",
        "domain": "curriculum.f1.language_structure",
        "material": "A sentence can perform different conversational acts, including stating information, asking a question, making a request, or expressing an exclamation; wording, context, and punctuation all help identify the act.",
        "principles": [
            "Sentence purpose depends on use and context, not punctuation alone.",
            "A question may request information, confirmation, permission, or action.",
            "One sentence can carry more than one practical intent.",
        ],
        "relationships": ["Sentence purpose connects grammatical structure to pragmatic conversation and answer planning."],
        "examples": ["Could you close the window? has question form but ordinarily functions as a polite request."],
        "counterexamples": ["A question mark does not guarantee a sincere request for information; the sentence may be rhetorical or corrective."],
        "limits": ["Tone, shared context, and cultural convention can change how an utterance functions."],
        "vocabulary": [
            "statement: an utterance that presents information or a position",
            "question: an utterance that seeks information, confirmation, or another response",
            "request: an utterance that asks someone to do or provide something",
            "exclamation: an utterance marked by strong emphasis or reaction",
        ],
        "near_concept_distinctions": ["Grammatical form describes construction; conversational function describes what the utterance is doing in context."],
        "scope_of_application": "Use this when deciding whether to answer, act, clarify, acknowledge, or respond to several intents. Keep ambiguous functions provisional.",
        "unresolved_questions": ["Is the speaker seeking facts, action, acknowledgment, or some combination?"],
        "explanation": "Sentences do things as well as contain words. Their form gives clues, but the surrounding exchange determines whether they are informing, asking, requesting, reacting, or combining those purposes.",
        "application": "You remembered the keys? can ask for confirmation, while You remembered the keys! expresses pleased surprise even though most words are identical.",
        "analogy": ["The same tool can serve different jobs depending on how it is used; sentence form is the tool, and conversational purpose is the job."],
        "questions": ["What response would actually satisfy the speaker's likely purpose here?"],
        "comparisons": ["A direct question asks for a reply; a request asks for an action, though question wording can perform either function."],
        "participation": "That sounds like both a question and a request for reassurance. I would answer the fact first, then acknowledge the concern rather than responding to only one layer.",
        "correction_response": "If context shows I misclassified the sentence's purpose, I would change the response plan instead of insisting that punctuation settled it.",
        "families": ["ELA-1", "ELA-2"],
        "source_ids": ["core_knowledge_2023_sequence_k8", "core_knowledge_g1_ela_unit7"],
        "source_refs": ELA_SOURCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_subject_action_reference_v1",
        "title": "Sentences connect participants, actions, descriptions, and references",
        "domain": "curriculum.f1.language_structure",
        "material": "A sentence can identify who or what it concerns, describe an action or state, add objects or descriptions, and use references whose meaning must be resolved from the sentence or conversation.",
        "principles": [
            "A subject identifies the participant or topic around which the clause is organized.",
            "Actions, states, objects, and descriptions contribute different relationships.",
            "References such as it, they, this, or that need a plausible antecedent in context.",
        ],
        "relationships": ["Basic sentence roles support pronoun resolution, callbacks, corrections, and mixed-intent conversation."],
        "examples": ["Mara moved the lamp because it was blocking the door uses it to refer to the lamp."],
        "counterexamples": ["In Jo told Sam that they were late, they may be ambiguous without more context."],
        "limits": ["Real sentences can omit understood participants, use passive structure, or contain several clauses, so these roles are guides rather than a single rigid template."],
        "vocabulary": [
            "subject: the participant or topic around which a clause is organized",
            "action or state: what the clause says occurs or holds",
            "object: a participant affected by or related to an action",
            "reference: an expression whose specific meaning depends on context",
            "antecedent: the earlier or understood item a reference points toward",
        ],
        "near_concept_distinctions": ["A grammatical subject is not always the person responsible for an action, and a conversational topic can span several sentences."],
        "scope_of_application": "Use these roles to understand ordinary clauses and track references. Ask when two antecedents remain materially plausible.",
        "unresolved_questions": ["Which earlier participant best fits this reference, and would the answer change if it referred to another?"],
        "explanation": "A sentence organizes relationships among participants, actions or states, and descriptions. Short reference words depend on that structure and the surrounding conversation to identify what they mean.",
        "application": "In The server sent the laptop an update before it restarted, ordinary event knowledge suggests it means the laptop, but the wording should be clarified if the distinction matters.",
        "analogy": ["References work like labeled arrows in a diagram: they are useful only when the destination can be identified."],
        "questions": ["What does this pronoun point to, and is there another plausible antecedent?"],
        "comparisons": ["A noun phrase can name a participant directly; a pronoun usually points back through context."],
        "participation": "I think they refers to the design team, but two groups were mentioned. If that changes the decision, I should confirm the reference before answering.",
        "correction_response": "If the speaker identifies a different antecedent, I would update the interpretation and every dependent conclusion while keeping unrelated sentence structure intact.",
        "families": ["ELA-1", "ELA-2"],
        "source_ids": ["core_knowledge_2023_sequence_k8", "core_knowledge_g1_ela_unit7"],
        "source_refs": ELA_SOURCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_sequence_reconstruction_v1",
        "title": "Sequence preserves order while reconstruction preserves meaning",
        "domain": "curriculum.f1.language_structure",
        "material": "Sequence words organize events or steps in time or logic, while a reconstruction retells the important meaning and order in new language without copying the source wording.",
        "principles": [
            "First, next, before, after, and finally describe relationships among events or steps.",
            "Changing wording should not silently change the important order or claim.",
            "A good short retelling preserves the load-bearing information and may omit nonessential detail.",
        ],
        "relationships": ["Sequence and reconstruction support instructions, summaries, callbacks, explanation, and teach-back evidence."],
        "examples": ["A recipe retelling may shorten descriptions but must not place baking before mixing the ingredients."],
        "counterexamples": ["Repeating every sentence in different synonyms can still miss the main point or distort the order."],
        "limits": ["Some explanations are organized by cause, comparison, or importance rather than chronology."],
        "vocabulary": [
            "sequence: an ordered relationship among events, ideas, or steps",
            "transition: a word or phrase that signals a relationship between parts",
            "reconstruction: a new expression that preserves supported meaning",
            "retelling: a bounded account of important events or ideas",
        ],
        "near_concept_distinctions": ["A paraphrase changes wording locally; a reconstruction may reorganize the explanation while preserving its essential meaning and constraints."],
        "scope_of_application": "Use for chronological events, procedures, short summaries, and explanations with dependency order. Choose a different organizing relation when time is not the main structure.",
        "unresolved_questions": ["Which details are necessary to preserve the order, cause, or conclusion?"],
        "explanation": "Order words show how parts depend on one another. Retelling in new language means keeping those important relationships and the main meaning, not merely swapping words one by one.",
        "application": "A troubleshooting summary can say the device failed after the update and recovered after a restart without copying the original log, while preserving the event order.",
        "analogy": ["It is like redrawing a route with different symbols while keeping the same turns and destination."],
        "questions": ["Is this ordered by time, cause, procedure, comparison, or importance?"],
        "comparisons": ["Sequence tracks order; summary selects important content; reconstruction expresses the supported structure anew."],
        "participation": "The short version is: first the source changed, then the dependent check failed, and finally the correction restored it. I can expand any step if that detail matters.",
        "correction_response": "If I reversed two steps or omitted a dependency, I would repair the sequence and any conclusion that relied on the wrong order.",
        "families": ["ELA-1", "ELA-2"],
        "source_ids": ["core_knowledge_2023_sequence_k8", "core_knowledge_g1_ela_unit7"],
        "source_refs": ELA_SOURCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_counting_cardinality_v1",
        "title": "Counting determines how many items are in a bounded collection",
        "domain": "curriculum.f1.number_sense",
        "material": "Counting a bounded collection pairs one number word with each item exactly once, follows a stable order, and uses the final count to describe how many items are in the collection.",
        "principles": [
            "Each item is counted once and only once.",
            "Number words follow a stable order.",
            "The last number reached gives the collection's cardinal quantity.",
            "Rearranging the same items does not change how many there are.",
        ],
        "relationships": ["Cardinality supports comparison, grouping, addition, subtraction, measurement, and data representation."],
        "examples": ["Counting five scattered buttons and then lining up the same buttons still gives a quantity of five."],
        "counterexamples": ["Saying more number words does not produce a valid count if an item was skipped or counted twice."],
        "limits": ["Counting requires a defined collection and a way to distinguish items; continuous quantities such as water usually require measurement instead."],
        "vocabulary": [
            "collection: a bounded set of items considered together",
            "count: pairing ordered number words with items",
            "cardinality: how many items a collection contains",
            "one-to-one correspondence: matching each counted item to one count step",
        ],
        "near_concept_distinctions": ["A counting number describes discrete items; a measurement number describes a quantity relative to a unit."],
        "scope_of_application": "Use for finite distinguishable items. Define the collection and use measurement for continuous extent, mass, duration, or capacity.",
        "unresolved_questions": ["What exactly belongs to this collection, and can each item be identified once?"],
        "explanation": "A reliable count matches each object to one step in the number sequence. The final number names the size of that collection even if its items are rearranged.",
        "application": "To count messages in three folders, define whether duplicates belong to the collection, then mark each included message once rather than adding folder labels or recounting copies accidentally.",
        "analogy": ["It resembles checking names off a roster: one mark per person prevents omissions and duplicates."],
        "questions": ["Did every included item receive exactly one count, and did any item appear twice?"],
        "comparisons": ["Counting identifies a collection's size; labeling merely assigns a name and does not establish quantity."],
        "participation": "There are twelve distinct records after duplicates are removed. I counted each retained record once, so the final count describes the cleaned collection rather than the raw list length.",
        "correction_response": "If an item was skipped or counted twice, I would recount from a clearly marked collection and revise every dependent quantity.",
        "families": ["MATH-1", "ELA-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8", "core_knowledge_k_math_unit1"],
        "source_refs": K_MATH_SOURCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_quantity_comparison_v1",
        "title": "Same, more, and fewer compare bounded quantities",
        "domain": "curriculum.f1.number_sense",
        "material": "Two bounded collections can be compared by reliable counts or one-to-one matching to determine whether they contain the same quantity or whether one contains more and the other fewer.",
        "principles": [
            "Comparison requires a shared basis, such as count or one-to-one matching.",
            "If every item in two collections can be paired with none left over, the quantities are equal.",
            "If one collection has unpaired items after matching, it has more and the other has fewer.",
        ],
        "relationships": ["Quantity comparison builds on cardinality and leads toward difference, order, inequalities, and data interpretation."],
        "examples": ["If every cup pairs with one lid and two lids remain, there are more lids than cups."],
        "counterexamples": ["A collection spread across a larger area can look like more even when its count is smaller."],
        "limits": ["More and fewer need a named attribute; a box can contain more objects but less total mass."],
        "vocabulary": [
            "equal quantity: the same number of items",
            "more: a greater quantity on the named basis",
            "fewer: a smaller count of discrete items",
            "comparison: relating two quantities using a shared attribute or measure",
        ],
        "near_concept_distinctions": ["Fewer ordinarily compares countable items; less ordinarily compares continuous amount, though everyday usage can vary."],
        "scope_of_application": "Use for collections with a clear membership rule and shared comparison attribute. Name the attribute when count, size, mass, or value could differ.",
        "unresolved_questions": ["Are we comparing item count, physical size, mass, capacity, value, or another attribute?"],
        "explanation": "To decide whether two groups are the same size, pair their items or count them on the same basis. Anything left unmatched reveals which group has more and which has fewer.",
        "application": "Two software builds can have the same number of tests while one has more failures, so the comparison must name whether it concerns total tests or failed tests.",
        "analogy": ["It is like matching seats to people: leftover people mean more people than seats, while leftover seats mean fewer people than seats."],
        "questions": ["More or fewer in which specific attribute?"],
        "comparisons": ["Equal means the same quantity on the chosen basis; identical would require matching qualities beyond quantity."],
        "participation": "The lists are equal in length, but the second contains more unique entries. Those are different comparisons, so I would report both instead of saying one list is simply bigger.",
        "correction_response": "If I compared different attributes or relied on appearance, I would use one shared basis and revise the conclusion.",
        "families": ["MATH-1", "ELA-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8", "core_knowledge_k_math_unit1"],
        "source_refs": K_MATH_SOURCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_base_ten_place_value_v1",
        "title": "Two-digit numbers organize quantities into tens and ones",
        "domain": "curriculum.f1.number_sense",
        "material": "In base-ten notation, a two-digit whole number records how many groups of ten and how many ungrouped ones compose the quantity; a digit's value depends on its place.",
        "principles": [
            "Ten ones can be composed into one group of ten without changing the total quantity.",
            "The left digit of a two-digit number counts tens and the right digit counts ones.",
            "The same digit can represent different values in different places.",
        ],
        "relationships": ["Place value connects counting, grouping, representation, comparison, addition, subtraction, and later decimal notation."],
        "examples": ["Forty-two is four tens and two ones, so its digits represent forty and two rather than four and two as separate counts."],
        "counterexamples": ["In 24, the 2 does not mean two ones; its tens place gives it a value of twenty."],
        "limits": ["This description is for base-ten whole-number notation; other bases and decimal places use the same positional idea with different powers or positions."],
        "vocabulary": [
            "base ten: a place-value system organized by powers of ten",
            "digit: a symbol used in numeral notation",
            "place value: the value a digit represents because of its position",
            "ten: one group composed of ten ones",
        ],
        "near_concept_distinctions": ["A digit is the written symbol; its place value is the quantity that symbol represents in a particular numeral."],
        "scope_of_application": "Use for interpreting and constructing base-ten whole numbers. State the numeral system when another base or decimal/fractional notation is involved.",
        "unresolved_questions": ["Which place is this digit in, and what unit does that place count?"],
        "explanation": "Base-ten writing compresses a quantity into groups. In a two-digit number, the first position counts bundles of ten and the second counts leftover single units.",
        "application": "A storage report showing 63 items can be represented as six full boxes of ten plus three loose items, preserving the same total in grouped form.",
        "analogy": ["It is like packing loose pieces into bundles of ten: the bundle count and leftover count together describe the inventory."],
        "questions": ["How many tens and ones compose this number?"],
        "comparisons": ["The numeral 52 uses two digits, but its value is five tens plus two ones."],
        "participation": "Seventy-four means seven groups of ten and four additional ones. If we unpacked every group, we would still have seventy-four individual units.",
        "correction_response": "If I treated a digit as though its place did not matter, I would re-expand the numeral into tens and ones and revise the quantity.",
        "families": ["MATH-1", "MATH-2", "ELA-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8", "core_knowledge_g1_math_unit4"],
        "source_refs": G1_MATH_SOURCE_REFS,
    },
    {
        "concept_key": "curriculum_f1_number_representation_comparison_v1",
        "title": "Numbers can be represented in several forms and compared by value",
        "domain": "curriculum.f1.number_sense",
        "material": "A whole-number quantity can be represented with objects, drawings, words, expanded groups, or a numeral, and two-digit numbers can be compared by tens first and then ones when their tens are equal.",
        "principles": [
            "Different representations can express the same quantity.",
            "For positive two-digit whole numbers, more tens means a greater value regardless of the ones digits.",
            "When the tens are equal, compare the ones.",
            "Comparison symbols record a relationship; they do not create it.",
        ],
        "relationships": ["Equivalent representation supports calculation checks, while place-value comparison supports ordering and inequalities."],
        "examples": ["Three tens and eight ones, 30 + 8, thirty-eight, and 38 represent the same whole-number quantity."],
        "counterexamples": ["Comparing only the final digit would incorrectly claim that 29 is greater than 34 because 9 is greater than 4."],
        "limits": ["The tens-then-ones shortcut described here is bounded to positive two-digit whole numbers; negatives, decimals, and other bases need their own rules."],
        "vocabulary": [
            "representation: a form used to express a quantity or relationship",
            "equivalent: equal in value despite a different form",
            "greater than: having a larger value on the named numeric order",
            "less than: having a smaller value on the named numeric order",
            "comparison symbol: notation such as greater-than, less-than, or equals that records a relationship",
        ],
        "near_concept_distinctions": ["Equivalent representations have the same value; identical representations have the same form as well."],
        "scope_of_application": "Use to translate among elementary whole-number forms and compare positive two-digit values. Reopen the method for signed, fractional, decimal, or non-base-ten quantities.",
        "unresolved_questions": ["Are these two expressions different values or merely different representations of one value?"],
        "explanation": "Objects, words, expanded groups, and numerals can point to one quantity. To compare two-digit values, inspect the ten-groups first; only when those match do the leftover ones decide.",
        "application": "A dashboard may show 4 tens and 6 units in one view and 46 in another. Those displays agree, while a reading of 43 is smaller because the tens match and three ones are fewer than six.",
        "analogy": ["Compare full cartons before loose pieces: an extra full carton outweighs any difference among fewer than ten loose pieces."],
        "questions": ["Do the representations have equal value, and if not, which place first establishes the difference?"],
        "comparisons": ["Forty and 40 are different forms of one value; 40 and 44 share four tens but differ in their ones."],
        "participation": "The two displays are equivalent: one says five tens and two ones, and the other says 52. Compared with 49, 52 is greater because five tens already exceed four tens.",
        "correction_response": "If I compared surface form or the ones digit alone, I would translate both quantities into place value and recompute the relationship.",
        "families": ["MATH-1", "MATH-2", "ELA-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8", "core_knowledge_g1_math_unit4"],
        "source_refs": G1_MATH_SOURCE_REFS,
    },
)


def curriculum_authorization_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active
        FROM selene_curriculum_authorizations
        """
    ).fetchone()
    event_count = int(conn.execute("SELECT COUNT(*) FROM selene_curriculum_authorization_events").fetchone()[0])
    first_group = _group_progress(
        conn,
        FOUNDATION_GROUP,
        "f1_science_inquiry_group_1",
        "F1 science and inquiry foundations — group 1",
        F1_SCOPE["source_ids"],
    )
    second_group = _group_progress(
        conn,
        F1_LANGUAGE_MATH_GROUP,
        F1_LANGUAGE_MATH_GROUP_KEY,
        "F1 language and number foundations — group 2",
        F1_LANGUAGE_MATH_SCOPE["source_ids"],
    )
    third_group = _group_progress(
        conn,
        F1_GROUP3_LESSONS,
        F1_GROUP3_KEY,
        "F1 operations, data, measurement, and time — group 3",
        F1_GROUP3_SCOPE["source_ids"],
    )
    fourth_group = _group_progress(
        conn,
        F1_GROUP4_LESSONS,
        F1_GROUP4_KEY,
        "F1 geometry, equal shares, and algorithms — group 4",
        F1_GROUP4_SCOPE["source_ids"],
    )
    fifth_group = _group_progress(
        conn,
        F1_GROUP5_LESSONS,
        F1_GROUP5_KEY,
        "F1 equal groups, data interpretation, and money — group 5",
        F1_GROUP5_SCOPE["source_ids"],
    )
    sixth_group = _group_progress(
        conn,
        F1_GROUP6_LESSONS,
        F1_GROUP6_KEY,
        "F1 mass and capacity foundations — group 6",
        F1_GROUP6_SCOPE["source_ids"],
    )
    seventh_group = _group_progress(
        conn,
        F1_GROUP7_LESSONS,
        F1_GROUP7_KEY,
        "F1 community, rules, and civic reasoning — group 7",
        F1_GROUP7_SCOPE["source_ids"],
    )
    eighth_group = _group_progress(
        conn,
        F1_GROUP8_LESSONS,
        F1_GROUP8_KEY,
        "F1 history and evidence foundations — group 8",
        F1_GROUP8_SCOPE["source_ids"],
    )
    ninth_group = _group_progress(
        conn,
        F1_GROUP9_LESSONS,
        F1_GROUP9_KEY,
        "F1 materials, change, and motion foundations — group 9",
        F1_GROUP9_SCOPE["source_ids"],
    )
    tenth_group = _group_progress(
        conn,
        F1_GROUP10_LESSONS,
        F1_GROUP10_KEY,
        "F1 pushes, pulls, and forces foundations — group 10",
        F1_GROUP10_SCOPE["source_ids"],
    )
    eleventh_group = _group_progress(
        conn,
        F1_GROUP11_LESSONS,
        F1_GROUP11_KEY,
        "F1 light and sound foundations — group 11",
        F1_GROUP11_SCOPE["source_ids"],
    )
    twelfth_group = _group_progress(
        conn,
        F1_GROUP12_LESSONS,
        F1_GROUP12_KEY,
        "F1 simple machines and mechanical systems — group 12",
        F1_GROUP12_SCOPE["source_ids"],
    )
    thirteenth_group = _group_progress(
        conn,
        F1_GROUP13_LESSONS,
        F1_GROUP13_KEY,
        "F1 living things, needs, parts, and survival — group 13",
        F1_GROUP13_SCOPE["source_ids"],
    )
    fourteenth_group = _group_progress(
        conn,
        F1_GROUP14_LESSONS,
        F1_GROUP14_KEY,
        "F1 weather, seasons, Earth, Sun, Moon, and sky cycles — group 14",
        F1_GROUP14_SCOPE["source_ids"],
    )
    fifteenth_group = _group_progress(
        conn,
        F1_GROUP15_LESSONS,
        F1_GROUP15_KEY,
        "F1 human body systems, care, and health evidence — group 15",
        F1_GROUP15_SCOPE["source_ids"],
    )
    sixteenth_group = _group_progress(
        conn,
        F1_GROUP16_LESSONS,
        F1_GROUP16_KEY,
        "F1 helpful computers and cross-domain integration — group 16",
        F1_GROUP16_SCOPE["source_ids"],
    )
    seventeenth_group = _group_progress(
        conn,
        F1_GROUP17_LESSONS,
        F1_GROUP17_KEY,
        "F1 text purpose and everyday economy closure bridge — group 17",
        F1_GROUP17_SCOPE["source_ids"],
    )
    f2_first_group = _group_progress(
        conn,
        F2_GROUP1_LESSONS,
        F2_GROUP1_KEY,
        "F2 paragraph meaning and source-grounded communication — group 1",
        F2_GROUP1_SCOPE["source_ids"],
    )
    f2_second_group = _group_progress(
        conn,
        F2_GROUP2_LESSONS,
        F2_GROUP2_KEY,
        "F2 vocabulary structure and comparison — group 2",
        F2_GROUP2_SCOPE["source_ids"],
    )
    f2_third_group = _group_progress(
        conn,
        F2_GROUP3_LESSONS,
        F2_GROUP3_KEY,
        "F2 point of view and organized composition — group 3",
        F2_GROUP3_SCOPE["source_ids"],
    )
    f2_fourth_group = _group_progress(conn, F2_GROUP4_LESSONS, F2_GROUP4_KEY, "F2 multi-digit arithmetic and operation relationships — group 4", F2_GROUP4_SCOPE["source_ids"])
    f2_fifth_group = _group_progress(conn, F2_GROUP5_LESSONS, F2_GROUP5_KEY, "F2 factors, multiples, divisibility, and operation order — group 5", F2_GROUP5_SCOPE["source_ids"])
    f2_sixth_group = _group_progress(conn, F2_GROUP6_LESSONS, F2_GROUP6_KEY, "F2 fractions as numbers, equivalence, comparison, and composition — group 6", F2_GROUP6_SCOPE["source_ids"])
    f2_seventh_a_group = _group_progress(conn, F2_GROUP7A_LESSONS, F2_GROUP7A_KEY, "F2 fraction-operation relationships — group 7A", F2_GROUP7A_SCOPE["source_ids"])
    coding_first_group = _group_progress(
        conn,
        CODING_GROUP1_LESSONS,
        CODING_GROUP1_KEY,
        "Coding computational thinking and code reading — group 1",
        CODING_GROUP1_SCOPE["source_ids"],
    )
    return _with_guards(
        {
            "status": "curriculum_authorization_ready",
            "law_version": LAW_VERSION,
            "law_source": LAW_SOURCE,
            "authorization_count": int(row["total"] or 0),
            "active_authorization_count": int(row["active"] or 0),
            "audit_event_count": event_count,
            "first_group": first_group,
            "second_group": second_group,
            "third_group": third_group,
            "fourth_group": fourth_group,
            "fifth_group": fifth_group,
            "sixth_group": sixth_group,
            "seventh_group": seventh_group,
            "eighth_group": eighth_group,
            "ninth_group": ninth_group,
            "tenth_group": tenth_group,
            "eleventh_group": eleventh_group,
            "twelfth_group": twelfth_group,
            "thirteenth_group": thirteenth_group,
            "fourteenth_group": fourteenth_group,
            "fifteenth_group": fifteenth_group,
            "sixteenth_group": sixteenth_group,
            "seventeenth_group": seventeenth_group,
            "f2_first_group": f2_first_group,
            "f2_second_group": f2_second_group,
            "f2_third_group": f2_third_group,
            "f2_fourth_group": f2_fourth_group,
            "f2_fifth_group": f2_fifth_group,
            "f2_sixth_group": f2_sixth_group,
            "f2_seventh_a_group": f2_seventh_a_group,
            "f2_groups": [f2_first_group, f2_second_group, f2_third_group, f2_fourth_group, f2_fifth_group, f2_sixth_group, f2_seventh_a_group],
            "coding_first_group": coding_first_group,
            "coding_groups": [coding_first_group],
            "groups": [first_group, second_group, third_group, fourth_group, fifth_group, sixth_group, seventh_group, eighth_group, ninth_group, tenth_group, eleventh_group, twelfth_group, thirteenth_group, fourteenth_group, fifteenth_group, sixteenth_group, seventeenth_group],
            "exception_classes": list(EXCEPTION_CLASSES),
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": PROVENANCE_BOUNDARY,
        }
    )


def list_curriculum_authorizations(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM selene_curriculum_authorizations ORDER BY updated_at DESC, id DESC").fetchall()
    return _with_guards(
        {
            "status": "curriculum_authorizations_ready",
            "items": [_decode_authorization(row) for row in rows],
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": PROVENANCE_BOUNDARY,
        }
    )


def activate_f1_foundation_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_AUTHORIZATION_KEY,
        title="F1 science and inquiry foundations — group 1",
        scope=F1_SCOPE,
    )


def activate_f1_language_math_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_LANGUAGE_MATH_AUTHORIZATION_KEY,
        title="F1 language and number foundations — group 2",
        scope=F1_LANGUAGE_MATH_SCOPE,
    )


def activate_f1_operations_measurement_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP3_AUTHORIZATION_KEY,
        title="F1 operations, data, measurement, and time — group 3",
        scope=F1_GROUP3_SCOPE,
    )


def activate_f1_geometry_algorithms_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP4_AUTHORIZATION_KEY,
        title="F1 geometry, equal shares, and algorithms — group 4",
        scope=F1_GROUP4_SCOPE,
    )


def activate_f1_equal_groups_data_money_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP5_AUTHORIZATION_KEY,
        title="F1 equal groups, data interpretation, and money — group 5",
        scope=F1_GROUP5_SCOPE,
    )


def activate_f1_mass_capacity_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP6_AUTHORIZATION_KEY,
        title="F1 mass and capacity foundations — group 6",
        scope=F1_GROUP6_SCOPE,
    )


def activate_f1_community_rules_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP7_AUTHORIZATION_KEY,
        title="F1 community, rules, and civic reasoning — group 7",
        scope=F1_GROUP7_SCOPE,
    )


def activate_f1_history_evidence_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP8_AUTHORIZATION_KEY,
        title="F1 history and evidence foundations — group 8",
        scope=F1_GROUP8_SCOPE,
    )


def activate_f1_materials_change_motion_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP9_AUTHORIZATION_KEY,
        title="F1 materials, change, and motion foundations — group 9",
        scope=F1_GROUP9_SCOPE,
    )


def activate_f1_pushes_pulls_forces_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP10_AUTHORIZATION_KEY,
        title="F1 pushes, pulls, and forces foundations — group 10",
        scope=F1_GROUP10_SCOPE,
    )


def activate_f1_light_sound_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP11_AUTHORIZATION_KEY,
        title="F1 light and sound foundations — group 11",
        scope=F1_GROUP11_SCOPE,
    )


def activate_f1_simple_machines_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP12_AUTHORIZATION_KEY,
        title="F1 simple machines and mechanical systems — group 12",
        scope=F1_GROUP12_SCOPE,
    )


def activate_f1_living_things_survival_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP13_AUTHORIZATION_KEY,
        title="F1 living things, needs, parts, and survival — group 13",
        scope=F1_GROUP13_SCOPE,
    )


def activate_f1_weather_sky_cycles_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP14_AUTHORIZATION_KEY,
        title="F1 weather, seasons, Earth, Sun, Moon, and sky cycles — group 14",
        scope=F1_GROUP14_SCOPE,
    )


def activate_f1_human_body_health_evidence_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP15_AUTHORIZATION_KEY,
        title="F1 human body systems, care, and health evidence — group 15",
        scope=F1_GROUP15_SCOPE,
    )


def activate_f1_helpful_computers_integration_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP16_AUTHORIZATION_KEY,
        title="F1 helpful computers and cross-domain integration — group 16",
        scope=F1_GROUP16_SCOPE,
    )


def activate_f1_text_purpose_everyday_economy_bridge_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F1_GROUP17_AUTHORIZATION_KEY,
        title="F1 text purpose and everyday economy closure bridge — group 17",
        scope=F1_GROUP17_SCOPE,
    )


def activate_f2_paragraph_meaning_source_grounding_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F2_GROUP1_AUTHORIZATION_KEY,
        title="F2 paragraph meaning and source-grounded communication — group 1",
        scope=F2_GROUP1_SCOPE,
    )


def activate_f2_vocabulary_structure_comparison_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F2_GROUP2_AUTHORIZATION_KEY,
        title="F2 vocabulary structure and comparison — group 2",
        scope=F2_GROUP2_SCOPE,
    )


def activate_f2_point_of_view_organized_composition_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=F2_GROUP3_AUTHORIZATION_KEY,
        title="F2 point of view and organized composition — group 3",
        scope=F2_GROUP3_SCOPE,
    )


def activate_f2_multi_digit_arithmetic_operations_authorization(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _activate_authorization_record(conn, payload or {}, authorization_key=F2_GROUP4_AUTHORIZATION_KEY, title="F2 multi-digit arithmetic and operation relationships — group 4", scope=F2_GROUP4_SCOPE)


def activate_f2_factors_multiples_operation_order_authorization(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _activate_authorization_record(conn, payload or {}, authorization_key=F2_GROUP5_AUTHORIZATION_KEY, title="F2 factors, multiples, divisibility, and operation order — group 5", scope=F2_GROUP5_SCOPE)


def activate_f2_fractions_numbers_equivalence_authorization(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _activate_authorization_record(conn, payload or {}, authorization_key=F2_GROUP6_AUTHORIZATION_KEY, title="F2 fractions as numbers, equivalence, comparison, and composition — group 6", scope=F2_GROUP6_SCOPE)


def activate_f2_fraction_operation_relationships_authorization(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _activate_authorization_record(conn, payload or {}, authorization_key=F2_GROUP7A_AUTHORIZATION_KEY, title="F2 fraction-operation relationships — group 7A", scope=F2_GROUP7A_SCOPE)


def activate_coding_computational_thinking_code_reading_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _activate_authorization_record(
        conn,
        payload or {},
        authorization_key=CODING_GROUP1_AUTHORIZATION_KEY,
        title="Coding computational thinking and code reading — group 1",
        scope=CODING_GROUP1_SCOPE,
    )


def revoke_curriculum_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    if payload.get("aleks_revoked") is not True or str(payload.get("authorization_actor") or "").strip() != "Aleks":
        raise ValueError("revoking a curriculum authorization requires an explicit Aleks decision")
    authorization_id = int(payload.get("authorization_id") or 0)
    row = conn.execute("SELECT * FROM selene_curriculum_authorizations WHERE id = ?", (authorization_id,)).fetchone()
    if not row:
        raise ValueError("curriculum authorization not found")
    conn.execute(
        "UPDATE selene_curriculum_authorizations SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (authorization_id,),
    )
    conn.commit()
    item = _decode_authorization(conn.execute("SELECT * FROM selene_curriculum_authorizations WHERE id = ?", (authorization_id,)).fetchone())
    _store_event(conn, authorization_id, "authorization_revoked", {"authorization": item})
    return _with_guards({"status": "curriculum_authorization_revoked", "item": item, "provenance_boundary": PROVENANCE_BOUNDARY})


def prepare_f1_foundation_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    created: list[dict[str, Any]] = []
    existing: list[dict[str, Any]] = []
    for order, lesson in enumerate(FOUNDATION_GROUP, start=1):
        result = propose_comprehension_concept(
            conn,
            {
                "concept_key": lesson["concept_key"],
                "title": lesson["title"],
                "domain": lesson["domain"],
                "material": lesson["material"],
                "principles": lesson["principles"],
                "relationships": lesson["relationships"],
                "examples": lesson["examples"],
                "counterexamples": lesson["counterexamples"],
                "limits": lesson["limits"],
                "source_refs": SOURCE_REFS,
                "confidence": "developing",
                "teaching_source_type": "bounded_public_academic_curriculum",
                "source_metadata": {
                    "curriculum_band": "F1",
                    "curriculum_families": ["SCI-0", "SCI-1", "RES-1", "ELA-2", "ENG-1"],
                    "curriculum_group_key": "f1_science_inquiry_group_1",
                    "curriculum_order": order,
                    "source_ids": F1_SCOPE["source_ids"],
                    "knowledge_class": "public_academic_foundation",
                    "exception_flags": [],
                    "license_notes_preserved": True,
                    "source_images_or_media_used": False,
                },
            },
        )
        summary = {
            "concept_id": result["item"]["id"],
            "concept_key": result["item"]["concept_key"],
            "title": result["item"]["title"],
            "curriculum_order": order,
        }
        (created if result.get("created") else existing).append(summary)
    return _with_guards(
        {
            "status": "f1_foundation_group_prepared",
            "group_key": "f1_science_inquiry_group_1",
            "created_count": len(created),
            "existing_count": len(existing),
            "created": created,
            "existing": existing,
            "retained_count": 0,
            "chat_use_before_lifecycle_completion": False,
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": PROVENANCE_BOUNDARY,
        }
    )


def teach_f1_foundation_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    authorization = _authorization_by_key(conn, F1_AUTHORIZATION_KEY)
    if not authorization or authorization["status"] != "active":
        raise ValueError("activate the bounded F1 curriculum authorization before teaching this group")
    prepared = prepare_f1_foundation_group(conn, payload)
    retained: list[dict[str, Any]] = []
    already_retained: list[dict[str, Any]] = []
    held: list[dict[str, Any]] = []
    for lesson in FOUNDATION_GROUP:
        concept = conn.execute(
            "SELECT * FROM selene_comprehension_concepts WHERE concept_key = ?",
            (lesson["concept_key"],),
        ).fetchone()
        if not concept:
            held.append({"concept_key": lesson["concept_key"], "reason": "candidate_missing_after_prepare"})
            continue
        concept_id = int(concept["id"])
        if concept["state"] == "approved_knowledge_resource":
            already_retained.append({"concept_id": concept_id, "concept_key": lesson["concept_key"], "title": lesson["title"]})
            continue
        lifecycle = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?", (concept_id,)).fetchone()
        if not lifecycle or lifecycle["acquire_status"] != "complete":
            acquire_teaching_item(
                conn,
                {
                    "concept_id": concept_id,
                    "vocabulary": lesson["vocabulary"],
                    "uncertainties": lesson["limits"],
                    "near_concept_distinctions": lesson["near_concept_distinctions"],
                },
            )
        lifecycle = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?", (concept_id,)).fetchone()
        if lifecycle["integrate_status"] != "complete":
            integrate_teaching_item(
                conn,
                {
                    "concept_id": concept_id,
                    "scope_of_application": lesson["scope_of_application"],
                    "contradiction_classification": "none_identified",
                    "unresolved_questions": lesson["unresolved_questions"],
                    "integration_confidence": "bounded",
                },
            )
        lifecycle = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?", (concept_id,)).fetchone()
        if lifecycle["express_status"] != "complete":
            express_teaching_item(
                conn,
                {
                    "concept_id": concept_id,
                    "explanation": lesson["explanation"],
                    "distinct_examples": [lesson["application"]],
                    "analogies": lesson["analogy"],
                    "questions": lesson["questions"],
                    "comparisons": lesson["comparisons"],
                    "conversational_participation": lesson["participation"],
                    "limits": lesson["limits"],
                    "counterexamples": lesson["counterexamples"],
                    "correction_response": lesson["correction_response"],
                    "source_alignment": True,
                },
            )
        authorization_decision = evaluate_curriculum_coverage(conn, {"concept_id": concept_id})
        if authorization_decision["decision"] != "covered_by_active_authorization":
            held.append(
                {
                    "concept_id": concept_id,
                    "concept_key": lesson["concept_key"],
                    "title": lesson["title"],
                    "reason": "exception_review_required",
                    "authorization_decision": authorization_decision,
                }
            )
            _store_event(
                conn,
                authorization["id"],
                "candidate_held_for_exception_review",
                authorization_decision,
                concept_id=concept_id,
                lifecycle_id=authorization_decision.get("lifecycle_id"),
            )
            continue
        result = approve_teaching_lifecycle_under_authorization(
            conn,
            {"concept_id": concept_id},
            authorization_decision,
        )
        retained.append(
            {
                "concept_id": concept_id,
                "concept_key": lesson["concept_key"],
                "title": lesson["title"],
                "approval_status": result["item"]["approval_status"],
                "chat_use_permission": result["item"]["chat_use_permission"],
            }
        )
        _store_event(
            conn,
            authorization["id"],
            "knowledge_retained_under_authorization",
            authorization_decision,
            concept_id=concept_id,
            lifecycle_id=result["item"]["id"],
        )
    return _with_guards(
        {
            "status": "f1_foundation_group_taught" if not held else "f1_foundation_group_partially_held",
            "group_key": "f1_science_inquiry_group_1",
            "prepared": prepared,
            "retained_count": len(retained),
            "already_retained_count": len(already_retained),
            "held_count": len(held),
            "retained": retained,
            "already_retained": already_retained,
            "held": held,
            "authorization": authorization,
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": PROVENANCE_BOUNDARY,
        }
    )


def prepare_f1_language_math_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_LANGUAGE_MATH_GROUP,
        group_key=F1_LANGUAGE_MATH_GROUP_KEY,
    )


def teach_f1_language_math_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_LANGUAGE_MATH_GROUP,
        group_key=F1_LANGUAGE_MATH_GROUP_KEY,
        authorization_key=F1_LANGUAGE_MATH_AUTHORIZATION_KEY,
    )


def prepare_f1_operations_measurement_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP3_LESSONS,
        group_key=F1_GROUP3_KEY,
    )


def teach_f1_operations_measurement_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP3_LESSONS,
        group_key=F1_GROUP3_KEY,
        authorization_key=F1_GROUP3_AUTHORIZATION_KEY,
    )


def prepare_f1_geometry_algorithms_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP4_LESSONS,
        group_key=F1_GROUP4_KEY,
    )


def teach_f1_geometry_algorithms_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP4_LESSONS,
        group_key=F1_GROUP4_KEY,
        authorization_key=F1_GROUP4_AUTHORIZATION_KEY,
    )


def prepare_f1_equal_groups_data_money_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP5_LESSONS,
        group_key=F1_GROUP5_KEY,
    )


def teach_f1_equal_groups_data_money_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP5_LESSONS,
        group_key=F1_GROUP5_KEY,
        authorization_key=F1_GROUP5_AUTHORIZATION_KEY,
    )


def prepare_f1_mass_capacity_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP6_LESSONS,
        group_key=F1_GROUP6_KEY,
    )


def teach_f1_mass_capacity_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP6_LESSONS,
        group_key=F1_GROUP6_KEY,
        authorization_key=F1_GROUP6_AUTHORIZATION_KEY,
    )


def prepare_f1_community_rules_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP7_LESSONS,
        group_key=F1_GROUP7_KEY,
    )


def teach_f1_community_rules_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP7_LESSONS,
        group_key=F1_GROUP7_KEY,
        authorization_key=F1_GROUP7_AUTHORIZATION_KEY,
    )


def prepare_f1_history_evidence_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP8_LESSONS,
        group_key=F1_GROUP8_KEY,
    )


def teach_f1_history_evidence_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP8_LESSONS,
        group_key=F1_GROUP8_KEY,
        authorization_key=F1_GROUP8_AUTHORIZATION_KEY,
    )


def prepare_f1_materials_change_motion_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP9_LESSONS,
        group_key=F1_GROUP9_KEY,
    )


def teach_f1_materials_change_motion_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP9_LESSONS,
        group_key=F1_GROUP9_KEY,
        authorization_key=F1_GROUP9_AUTHORIZATION_KEY,
    )


def prepare_f1_pushes_pulls_forces_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP10_LESSONS,
        group_key=F1_GROUP10_KEY,
    )


def teach_f1_pushes_pulls_forces_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP10_LESSONS,
        group_key=F1_GROUP10_KEY,
        authorization_key=F1_GROUP10_AUTHORIZATION_KEY,
    )


def prepare_f1_light_sound_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP11_LESSONS,
        group_key=F1_GROUP11_KEY,
    )


def teach_f1_light_sound_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP11_LESSONS,
        group_key=F1_GROUP11_KEY,
        authorization_key=F1_GROUP11_AUTHORIZATION_KEY,
    )


def prepare_f1_simple_machines_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP12_LESSONS,
        group_key=F1_GROUP12_KEY,
    )


def teach_f1_simple_machines_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP12_LESSONS,
        group_key=F1_GROUP12_KEY,
        authorization_key=F1_GROUP12_AUTHORIZATION_KEY,
    )


def prepare_f1_living_things_survival_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP13_LESSONS,
        group_key=F1_GROUP13_KEY,
    )


def teach_f1_living_things_survival_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP13_LESSONS,
        group_key=F1_GROUP13_KEY,
        authorization_key=F1_GROUP13_AUTHORIZATION_KEY,
    )


def prepare_f1_weather_sky_cycles_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP14_LESSONS,
        group_key=F1_GROUP14_KEY,
    )


def teach_f1_weather_sky_cycles_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP14_LESSONS,
        group_key=F1_GROUP14_KEY,
        authorization_key=F1_GROUP14_AUTHORIZATION_KEY,
    )


def prepare_f1_human_body_health_evidence_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP15_LESSONS,
        group_key=F1_GROUP15_KEY,
    )


def teach_f1_human_body_health_evidence_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP15_LESSONS,
        group_key=F1_GROUP15_KEY,
        authorization_key=F1_GROUP15_AUTHORIZATION_KEY,
    )


def prepare_f1_helpful_computers_integration_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP16_LESSONS,
        group_key=F1_GROUP16_KEY,
    )


def teach_f1_helpful_computers_integration_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP16_LESSONS,
        group_key=F1_GROUP16_KEY,
        authorization_key=F1_GROUP16_AUTHORIZATION_KEY,
    )


def prepare_f1_text_purpose_everyday_economy_bridge_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP17_LESSONS,
        group_key=F1_GROUP17_KEY,
    )


def teach_f1_text_purpose_everyday_economy_bridge_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F1_GROUP17_LESSONS,
        group_key=F1_GROUP17_KEY,
        authorization_key=F1_GROUP17_AUTHORIZATION_KEY,
    )


def prepare_f2_paragraph_meaning_source_grounding_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F2_GROUP1_LESSONS,
        group_key=F2_GROUP1_KEY,
        curriculum_band="F2",
    )


def teach_f2_paragraph_meaning_source_grounding_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F2_GROUP1_LESSONS,
        group_key=F2_GROUP1_KEY,
        authorization_key=F2_GROUP1_AUTHORIZATION_KEY,
        curriculum_band="F2",
    )


def prepare_f2_vocabulary_structure_comparison_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F2_GROUP2_LESSONS,
        group_key=F2_GROUP2_KEY,
        curriculum_band="F2",
    )


def teach_f2_vocabulary_structure_comparison_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F2_GROUP2_LESSONS,
        group_key=F2_GROUP2_KEY,
        authorization_key=F2_GROUP2_AUTHORIZATION_KEY,
        curriculum_band="F2",
    )


def prepare_f2_point_of_view_organized_composition_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=F2_GROUP3_LESSONS,
        group_key=F2_GROUP3_KEY,
        curriculum_band="F2",
    )


def teach_f2_point_of_view_organized_composition_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=F2_GROUP3_LESSONS,
        group_key=F2_GROUP3_KEY,
        authorization_key=F2_GROUP3_AUTHORIZATION_KEY,
        curriculum_band="F2",
    )


def prepare_f2_multi_digit_arithmetic_operations_group(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _prepare_defined_group(conn, payload or {}, lessons=F2_GROUP4_LESSONS, group_key=F2_GROUP4_KEY, curriculum_band="F2")


def teach_f2_multi_digit_arithmetic_operations_group(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _teach_defined_group(conn, payload or {}, lessons=F2_GROUP4_LESSONS, group_key=F2_GROUP4_KEY, authorization_key=F2_GROUP4_AUTHORIZATION_KEY, curriculum_band="F2")


def prepare_f2_factors_multiples_operation_order_group(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _prepare_defined_group(conn, payload or {}, lessons=F2_GROUP5_LESSONS, group_key=F2_GROUP5_KEY, curriculum_band="F2")


def teach_f2_factors_multiples_operation_order_group(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _teach_defined_group(conn, payload or {}, lessons=F2_GROUP5_LESSONS, group_key=F2_GROUP5_KEY, authorization_key=F2_GROUP5_AUTHORIZATION_KEY, curriculum_band="F2")


def prepare_f2_fractions_numbers_equivalence_group(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _prepare_defined_group(conn, payload or {}, lessons=F2_GROUP6_LESSONS, group_key=F2_GROUP6_KEY, curriculum_band="F2")


def teach_f2_fractions_numbers_equivalence_group(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _teach_defined_group(conn, payload or {}, lessons=F2_GROUP6_LESSONS, group_key=F2_GROUP6_KEY, authorization_key=F2_GROUP6_AUTHORIZATION_KEY, curriculum_band="F2")


def prepare_f2_fraction_operation_relationships_group(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _prepare_defined_group(conn, payload or {}, lessons=F2_GROUP7A_LESSONS, group_key=F2_GROUP7A_KEY, curriculum_band="F2")


def teach_f2_fraction_operation_relationships_group(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _teach_defined_group(conn, payload or {}, lessons=F2_GROUP7A_LESSONS, group_key=F2_GROUP7A_KEY, authorization_key=F2_GROUP7A_AUTHORIZATION_KEY, curriculum_band="F2")


def prepare_coding_computational_thinking_code_reading_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _prepare_defined_group(
        conn,
        payload or {},
        lessons=CODING_GROUP1_LESSONS,
        group_key=CODING_GROUP1_KEY,
        curriculum_band="CODING-1",
    )


def teach_coding_computational_thinking_code_reading_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _teach_defined_group(
        conn,
        payload or {},
        lessons=CODING_GROUP1_LESSONS,
        group_key=CODING_GROUP1_KEY,
        authorization_key=CODING_GROUP1_AUTHORIZATION_KEY,
        curriculum_band="CODING-1",
    )


def evaluate_curriculum_coverage(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    concept_id = int(payload.get("concept_id") or 0)
    concept_row = conn.execute("SELECT * FROM selene_comprehension_concepts WHERE id = ?", (concept_id,)).fetchone()
    if not concept_row:
        raise ValueError("comprehension concept not found")
    concept = dict(concept_row)
    concept_payload = _loads(concept.get("payload_json"), {})
    metadata = concept_payload.get("source_metadata") if isinstance(concept_payload.get("source_metadata"), dict) else {}
    lifecycle_row = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?", (concept_id,)).fetchone()
    lifecycle = dict(lifecycle_row) if lifecycle_row else {}
    exceptions: list[str] = []
    if not _loads(concept.get("source_refs"), []):
        exceptions.append("uncertain_or_missing_provenance")
    if metadata.get("exception_flags"):
        exceptions.extend(str(item) for item in metadata.get("exception_flags") if str(item))
    if not lifecycle or any(lifecycle.get(f"{stage}_status") != "complete" for stage in ("acquire", "integrate", "express")):
        exceptions.append("lifecycle_or_understanding_incomplete")
    integrate_snapshot = _loads(lifecycle.get("integrate_json"), {})
    if integrate_snapshot.get("contradiction_classification") in {"tension_requires_review", "direct_conflict", "insufficient_evidence"}:
        exceptions.append("weak_or_conflicting_sources")
    express_snapshot = _loads(lifecycle.get("express_json"), {})
    if express_snapshot and (
        express_snapshot.get("understanding_evaluation", {}).get("sufficient") is not True
        or express_snapshot.get("source_parroting_check", {}).get("passed") is not True
    ):
        exceptions.append("lifecycle_or_understanding_incomplete")
    if express_snapshot and express_snapshot.get("source_parroting_check", {}).get("passed") is not True:
        exceptions.append("source_phrase_copying")

    authorizations = conn.execute("SELECT * FROM selene_curriculum_authorizations WHERE status = 'active' ORDER BY id ASC").fetchall()
    matching: dict[str, Any] | None = None
    for row in authorizations:
        item = _decode_authorization(row)
        scope = item["scope"]
        band = str(metadata.get("curriculum_band") or "")
        families = {str(value) for value in metadata.get("curriculum_families") or []}
        source_ids = {str(value) for value in metadata.get("source_ids") or []}
        knowledge_class = str(metadata.get("knowledge_class") or "")
        group_key = str(metadata.get("curriculum_group_key") or "")
        if (
            band in scope.get("bands", [])
            and families.issubset(set(scope.get("families", [])))
            and source_ids
            and source_ids.issubset(set(scope.get("source_ids", [])))
            and knowledge_class in scope.get("knowledge_classes", [])
            and group_key in scope.get("group_keys", [])
        ):
            matching = item
            break
    if not matching:
        exceptions.append("outside_authorized_scope")
    exceptions = list(dict.fromkeys(exceptions))
    return _with_guards(
        {
            "status": "curriculum_coverage_evaluated",
            "decision": "covered_by_active_authorization" if matching and not exceptions else "exception_review_required",
            "authorization_id": matching["id"] if matching else None,
            "authorization_key": matching["authorization_key"] if matching else None,
            "concept_id": concept_id,
            "lifecycle_id": int(lifecycle.get("id") or 0) or None,
            "curriculum_metadata": metadata,
            "exceptions": exceptions,
            "individual_item_approval_required": bool(exceptions),
            "review_destination": "Cocoon Teaching / Lessons" if exceptions else "authorization audit ledger",
            "provenance_boundary": PROVENANCE_BOUNDARY,
        }
    )


def _activate_authorization_record(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    authorization_key: str,
    title: str,
    scope: dict[str, Any],
) -> dict[str, Any]:
    _reject_authority_change(payload)
    if payload.get("aleks_authorized") is not True or str(payload.get("authorization_actor") or "").strip() != "Aleks":
        raise ValueError("activating a curriculum authorization requires an explicit Aleks decision")
    basis = str(payload.get("authorization_basis") or "").strip()
    if len(basis) < 12:
        raise ValueError("authorization_basis must record the bounded decision")
    conn.execute(
        """
        INSERT INTO selene_curriculum_authorizations
        (authorization_key, title, status, authorized_by, authorization_basis,
         scope_json, exception_classes_json, law_version, provenance_boundary, review_status, updated_at)
        VALUES (?, ?, 'active', 'Aleks', ?, ?, ?, ?, ?, 'authorization_record', CURRENT_TIMESTAMP)
        ON CONFLICT(authorization_key) DO UPDATE SET
          title = excluded.title, status = 'active', authorized_by = 'Aleks',
          authorization_basis = excluded.authorization_basis, scope_json = excluded.scope_json,
          exception_classes_json = excluded.exception_classes_json, law_version = excluded.law_version,
          provenance_boundary = excluded.provenance_boundary, review_status = 'authorization_record',
          updated_at = CURRENT_TIMESTAMP, revoked_at = NULL
        """,
        (
            authorization_key,
            title,
            basis,
            json.dumps(scope, sort_keys=True),
            json.dumps(EXCEPTION_CLASSES, sort_keys=True),
            LAW_VERSION,
            PROVENANCE_BOUNDARY,
        ),
    )
    conn.commit()
    authorization = _authorization_by_key(conn, authorization_key)
    if not authorization:
        raise ValueError("curriculum authorization could not be recorded")
    _store_event(conn, authorization["id"], "authorization_activated", {"authorization": authorization})
    return _with_guards(
        {
            "status": "curriculum_authorization_active",
            "item": authorization,
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": PROVENANCE_BOUNDARY,
        }
    )


def _prepare_defined_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    lessons: tuple[dict[str, Any], ...],
    group_key: str,
    curriculum_band: str = "F1",
) -> dict[str, Any]:
    _reject_authority_change(payload)
    created: list[dict[str, Any]] = []
    existing: list[dict[str, Any]] = []
    for order, lesson in enumerate(lessons, start=1):
        result = propose_comprehension_concept(
            conn,
            {
                "concept_key": lesson["concept_key"],
                "title": lesson["title"],
                "domain": lesson["domain"],
                "material": lesson["material"],
                "principles": lesson["principles"],
                "relationships": lesson["relationships"],
                "examples": lesson["examples"],
                "counterexamples": lesson["counterexamples"],
                "limits": lesson["limits"],
                "source_refs": lesson["source_refs"],
                "confidence": "developing",
                "teaching_source_type": "bounded_public_academic_curriculum",
                "source_metadata": {
                    "curriculum_band": curriculum_band,
                    "curriculum_families": lesson["families"],
                    "curriculum_group_key": group_key,
                    "curriculum_order": order,
                    "source_ids": lesson["source_ids"],
                    "knowledge_class": "public_academic_foundation",
                    "exception_flags": [],
                    "license_notes_preserved": True,
                    "source_images_or_media_used": False,
                },
            },
        )
        summary = {
            "concept_id": result["item"]["id"],
            "concept_key": result["item"]["concept_key"],
            "title": result["item"]["title"],
            "curriculum_order": order,
        }
        (created if result.get("created") else existing).append(summary)
    return _with_guards(
        {
            "status": "curriculum_foundation_group_prepared",
            "group_key": group_key,
            "created_count": len(created),
            "existing_count": len(existing),
            "created": created,
            "existing": existing,
            "retained_count": 0,
            "chat_use_before_lifecycle_completion": False,
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": PROVENANCE_BOUNDARY,
        }
    )


def _teach_defined_group(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    lessons: tuple[dict[str, Any], ...],
    group_key: str,
    authorization_key: str,
    curriculum_band: str = "F1",
) -> dict[str, Any]:
    _reject_authority_change(payload)
    authorization = _authorization_by_key(conn, authorization_key)
    if not authorization or authorization["status"] != "active":
        raise ValueError(
            f"activate this bounded {curriculum_band} curriculum authorization before teaching the group"
        )
    prepared = _prepare_defined_group(
        conn,
        payload,
        lessons=lessons,
        group_key=group_key,
        curriculum_band=curriculum_band,
    )
    retained: list[dict[str, Any]] = []
    already_retained: list[dict[str, Any]] = []
    held: list[dict[str, Any]] = []
    for lesson in lessons:
        concept = conn.execute(
            "SELECT * FROM selene_comprehension_concepts WHERE concept_key = ?",
            (lesson["concept_key"],),
        ).fetchone()
        if not concept:
            held.append({"concept_key": lesson["concept_key"], "reason": "candidate_missing_after_prepare"})
            continue
        concept_id = int(concept["id"])
        if concept["state"] == "approved_knowledge_resource":
            already_retained.append({"concept_id": concept_id, "concept_key": lesson["concept_key"], "title": lesson["title"]})
            continue
        lifecycle = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?", (concept_id,)).fetchone()
        if not lifecycle or lifecycle["acquire_status"] != "complete":
            acquire_teaching_item(
                conn,
                {
                    "concept_id": concept_id,
                    "vocabulary": lesson["vocabulary"],
                    "uncertainties": lesson["limits"],
                    "near_concept_distinctions": lesson["near_concept_distinctions"],
                },
            )
        lifecycle = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?", (concept_id,)).fetchone()
        if lifecycle["integrate_status"] != "complete":
            integrate_teaching_item(
                conn,
                {
                    "concept_id": concept_id,
                    "scope_of_application": lesson["scope_of_application"],
                    "contradiction_classification": "none_identified",
                    "unresolved_questions": lesson["unresolved_questions"],
                    "integration_confidence": "bounded",
                },
            )
        lifecycle = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?", (concept_id,)).fetchone()
        if lifecycle["express_status"] != "complete":
            express_teaching_item(
                conn,
                {
                    "concept_id": concept_id,
                    "explanation": lesson["explanation"],
                    "distinct_examples": [lesson["application"]],
                    "analogies": lesson["analogy"] if "analogy" in lesson else lesson["analogies"],
                    "questions": lesson["questions"],
                    "comparisons": lesson["comparisons"],
                    "conversational_participation": lesson["participation"],
                    "limits": lesson["limits"],
                    "counterexamples": lesson["counterexamples"],
                    "correction_response": lesson["correction_response"],
                    "source_alignment": True,
                },
            )
        authorization_decision = evaluate_curriculum_coverage(conn, {"concept_id": concept_id})
        if authorization_decision["decision"] != "covered_by_active_authorization":
            held.append(
                {
                    "concept_id": concept_id,
                    "concept_key": lesson["concept_key"],
                    "title": lesson["title"],
                    "reason": "exception_review_required",
                    "authorization_decision": authorization_decision,
                }
            )
            _store_event(
                conn,
                authorization["id"],
                "candidate_held_for_exception_review",
                authorization_decision,
                concept_id=concept_id,
                lifecycle_id=authorization_decision.get("lifecycle_id"),
            )
            continue
        result = approve_teaching_lifecycle_under_authorization(
            conn,
            {"concept_id": concept_id},
            authorization_decision,
        )
        retained.append(
            {
                "concept_id": concept_id,
                "concept_key": lesson["concept_key"],
                "title": lesson["title"],
                "approval_status": result["item"]["approval_status"],
                "chat_use_permission": result["item"]["chat_use_permission"],
            }
        )
        _store_event(
            conn,
            authorization["id"],
            "knowledge_retained_under_authorization",
            authorization_decision,
            concept_id=concept_id,
            lifecycle_id=result["item"]["id"],
        )
    return _with_guards(
        {
            "status": "curriculum_foundation_group_taught" if not held else "curriculum_foundation_group_partially_held",
            "group_key": group_key,
            "prepared": prepared,
            "retained_count": len(retained),
            "already_retained_count": len(already_retained),
            "held_count": len(held),
            "retained": retained,
            "already_retained": already_retained,
            "held": held,
            "authorization": authorization,
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": PROVENANCE_BOUNDARY,
        }
    )


def _group_progress(
    conn: sqlite3.Connection,
    lessons: tuple[dict[str, Any], ...],
    group_key: str,
    title: str,
    source_ids: list[str],
) -> dict[str, Any]:
    concept_keys = [item["concept_key"] for item in lessons]
    placeholders = ",".join("?" for _ in concept_keys)
    prepared = int(
        conn.execute(
            f"SELECT COUNT(*) FROM selene_comprehension_concepts WHERE concept_key IN ({placeholders})",
            concept_keys,
        ).fetchone()[0]
    )
    retained = int(
        conn.execute(
            f"SELECT COUNT(*) FROM selene_comprehension_concepts WHERE concept_key IN ({placeholders}) AND state = 'approved_knowledge_resource'",
            concept_keys,
        ).fetchone()[0]
    )
    return {
        "group_key": group_key,
        "title": title,
        "item_count": len(lessons),
        "prepared_count": prepared,
        "retained_count": retained,
        "source_ids": source_ids,
    }


def _authorization_by_key(conn: sqlite3.Connection, key: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM selene_curriculum_authorizations WHERE authorization_key = ?", (key,)).fetchone()
    return _decode_authorization(row) if row else None


def _decode_authorization(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    item["scope"] = _loads(item.pop("scope_json", "{}"), {})
    item["exception_classes"] = _loads(item.pop("exception_classes_json", "[]"), [])
    return item


def _store_event(
    conn: sqlite3.Connection,
    authorization_id: int | None,
    action: str,
    decision: dict[str, Any],
    *,
    concept_id: int | None = None,
    lifecycle_id: int | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO selene_curriculum_authorization_events
        (authorization_id, lifecycle_id, concept_id, action, decision_json, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            authorization_id,
            lifecycle_id,
            concept_id,
            action,
            json.dumps(decision, sort_keys=True),
            PROVENANCE_BOUNDARY,
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except (json.JSONDecodeError, TypeError):
        return fallback


def _reject_authority_change(payload: dict[str, Any]) -> None:
    protected = (
        "activate_runtime",
        "identity_change",
        "governance_change",
        "personality_change",
        "memory_write_active",
        "runtime_memory_recall",
        "training_allowed",
        "lora_allowed",
        "autonomous_action_allowed",
        "self_replication_allowed",
    )
    if any(payload.get(key) not in (None, False, "", "none") for key in protected):
        raise ValueError("curriculum authorization cannot change identity, governance, personality, memory, training, or authority")


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
