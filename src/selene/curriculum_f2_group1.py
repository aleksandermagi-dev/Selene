from __future__ import annotations

from typing import Any


AUTHORIZATION_KEY = "f2_paragraph_meaning_source_grounding_v1"
GROUP_KEY = "f2_paragraph_meaning_source_grounding_group_1"

SEQUENCE_REFS = [
    "curriculum_source:core_knowledge_2023_sequence_k8",
    "sha256:c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5",
    "https://www.coreknowledge.org/wp-content/uploads/2023/03/CK_Sequence2023_GK8_W3.pdf",
    "license:Core-Knowledge-artifact-notice-controls",
    "source_date:2023",
]

SCOPE = {
    "bands": ["F2"],
    "families": ["ELA-1", "ELA-2", "RES-1", "LOGIC-1", "CONV-1"],
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
        "concept_key": "curriculum_f2_paragraph_main_idea_support_v1",
        "title": "A paragraph develops a main idea through related supporting details",
        "domain": "curriculum.f2.paragraph_meaning_source_grounding",
        "material": (
            "A paragraph groups related sentences around a main idea. A topic sentence may state that "
            "idea directly, while supporting details explain, demonstrate, qualify, or develop it. The "
            "main idea is the meaning that best accounts for the paragraph as a whole, not merely the "
            "first sentence or the most vivid detail."
        ),
        "principles": [
            "Identify what the paragraph is mainly saying before selecting supporting details.",
            "Use the relationship among sentences, not position alone, to identify a topic sentence.",
            "Keep details that explain, exemplify, qualify, or provide evidence for the main idea.",
        ],
        "relationships": [
            "Paragraph meaning builds from F1 sentence purpose, text purpose, sequence, reconstruction, and question-role foundations."
        ],
        "examples": [
            "In a paragraph about keeping a garden bed moist, sentences about mulch, shade, and checking soil can support the main idea that several practices reduce water loss."
        ],
        "counterexamples": [
            "A memorable sentence about a bright watering can is not the main idea if the rest of the paragraph explains soil moisture."
        ],
        "limits": [
            "Some paragraphs imply the main idea, contain more than one closely related point, or serve mainly as a transition; the first sentence is not always a topic sentence."
        ],
        "vocabulary": [
            "paragraph: a group of related sentences functioning together",
            "main idea: the central meaning that best accounts for the whole paragraph",
            "topic sentence: a sentence that states or frames a paragraph's main idea",
            "supporting detail: information that develops, explains, exemplifies, qualifies, or supports the main idea",
        ],
        "near_concept_distinctions": [
            "A topic is what the paragraph concerns; its main idea is what the paragraph says about that topic."
        ],
        "scope_of_application": (
            "Use for ordinary explanatory, narrative, and opinion paragraphs. Preserve ambiguity when two candidate main ideas fit equally well."
        ),
        "unresolved_questions": [
            "Which proposed main idea explains the greatest number of sentences without forcing unrelated details into it?"
        ],
        "explanation": (
            "A paragraph is more than nearby sentences. Its parts work together around a central meaning, "
            "and each useful detail has a recognizable relationship to that meaning."
        ),
        "application": (
            "A repair note says a drawer catches, the left runner is loose, and tightening it removes the catch. "
            "The main idea is that the loose runner caused the observed problem; the three details supply observation, mechanism, and result."
        ),
        "analogies": [
            "A paragraph resembles a small system: the main idea is its organizing purpose, and the details are connected parts doing specific work."
        ],
        "questions": [
            "What is this paragraph mainly saying, and what role does each detail play?"
        ],
        "comparisons": [
            "A topic names the subject, a main idea makes the central point, and a supporting detail helps that point stand or become clearer."
        ],
        "participation": (
            "The paragraph is mainly about the loose runner explaining the drawer problem. The catching is the observation, the loose runner is the proposed cause, and the successful tightening supports that explanation."
        ),
        "correction_response": (
            "If another idea accounts for more of the paragraph, I would revise the main idea and remap each detail instead of defending the first sentence I noticed."
        ),
        "families": ["ELA-1", "ELA-2", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_explicit_information_bounded_inference_v1",
        "title": "Explicit information and bounded inference have different evidence relationships",
        "domain": "curriculum.f2.paragraph_meaning_source_grounding",
        "material": (
            "Explicit information is stated directly in the available text or source. An inference combines "
            "source details with a visible relationship or background concept to reach a conclusion the source "
            "does not state word for word. A sound inference names its basis, remains within the source's scope, "
            "and stays revisable when another explanation also fits."
        ),
        "principles": [
            "Identify the directly stated details before drawing an inference.",
            "Show which details and relationship support the inference.",
            "Do not silently upgrade a plausible inference into a quoted fact or certainty.",
        ],
        "relationships": [
            "This extends F1 observation-versus-interpretation and source-statement-versus-inference distinctions to paragraph-level reading."
        ],
        "examples": [
            "If a passage says the path is wet and dark clouds remain, wet path is explicit; recent rain is a reasonable inference but not the only possible cause."
        ],
        "counterexamples": [
            "Restating an unstated cause with confident wording does not turn the inference into explicit information."
        ],
        "limits": [
            "An inference can be well supported without being proven, and specialized or current claims may require sources beyond the paragraph."
        ],
        "vocabulary": [
            "explicit information: meaning stated directly in the available source",
            "inference: a conclusion supported by stated details and a connecting relationship",
            "basis: the details and relationship used to support a conclusion",
            "scope: the boundary within which a claim or inference applies",
        ],
        "near_concept_distinctions": [
            "An inference is evidence-linked; a guess may be useful but has a weaker or less complete basis."
        ],
        "scope_of_application": (
            "Use when reading, explaining, predicting, or comparing source material. Label uncertainty proportionally and seek more evidence when the distinction affects the answer."
        ),
        "unresolved_questions": [
            "What else could explain the same details, and what observation would distinguish the alternatives?"
        ],
        "explanation": (
            "Reading beyond the exact words is useful when the bridge is visible. The source supplies details; "
            "the inference supplies a connected conclusion whose strength depends on those details and alternatives."
        ),
        "application": (
            "A project log states that a service stopped after a configuration change and restarted after the change was reversed. "
            "The sequence is explicit; the configuration caused the stop is a supported but revisable causal inference."
        ),
        "analogies": [
            "Explicit information is what appears in the photograph; inference is the carefully labeled caption built from what the photograph shows."
        ],
        "questions": [
            "Which part is stated, which part is inferred, and what connects them?"
        ],
        "comparisons": [
            "Explicit information belongs to the source statement; inference belongs to the reader's evidence-linked interpretation."
        ],
        "participation": (
            "The log explicitly gives the order of events. My current inference is that the configuration change mattered, but a shared third cause could still fit, so I would keep the causal claim provisional."
        ),
        "correction_response": (
            "If another cause fits the same sequence or new evidence contradicts mine, I would preserve the explicit timeline and revise the inference."
        ),
        "families": ["ELA-2", "RES-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_summary_load_bearing_meaning_v1",
        "title": "A summary preserves load-bearing meaning without copying every detail",
        "domain": "curriculum.f2.paragraph_meaning_source_grounding",
        "material": (
            "A summary gives a shorter account of a source's main idea and the details necessary to understand "
            "it. It preserves important relationships, sequence, qualifications, and attribution while omitting "
            "repetition or minor detail. A summary should not introduce a new conclusion, erase a material limit, "
            "or imitate the source sentence by sentence."
        ),
        "principles": [
            "State the main idea and retain only details necessary to support or understand it.",
            "Preserve material cause, contrast, sequence, uncertainty, and attribution relationships.",
            "Use original language without adding claims the source did not support.",
        ],
        "relationships": [
            "Summary extends F1 reconstruction and supports teach-back, callbacks, source comparison, long-form discourse, and study."
        ],
        "examples": [
            "A five-sentence weather record can be summarized as temperatures rose across four days, while noting that the short record does not establish a seasonal trend."
        ],
        "counterexamples": [
            "Listing every sentence in slightly different words is not necessarily a summary, and removing the source's uncertainty can distort its meaning."
        ],
        "limits": [
            "What counts as necessary detail depends on the summary's purpose and audience; technical, legal, medical, or safety material may require preserving more qualifications."
        ],
        "vocabulary": [
            "summary: a shorter account preserving the source's main supported meaning",
            "load-bearing detail: information necessary for the main idea, relationship, limit, or conclusion to remain accurate",
            "omission: leaving material out",
            "distortion: changing the supported meaning or evidentiary strength",
        ],
        "near_concept_distinctions": [
            "A paraphrase restates a bounded passage; a summary selects and compresses the most important supported meaning."
        ],
        "scope_of_application": (
            "Use for ordinary paragraphs, short explanations, conversation callbacks, and study notes. Increase preserved detail when omission would change stakes or meaning."
        ),
        "unresolved_questions": [
            "Which detail would change the reader's understanding if it were omitted?"
        ],
        "explanation": (
            "Summarizing is selective reconstruction. The wording can change and minor detail can disappear, but the central claim, support, and meaningful limits must survive."
        ),
        "application": (
            "A build report can become: the build succeeded, the package launched, and privacy checks found no private data; code signing remains unfinished. "
            "The signing limit stays because removing it would overstate readiness."
        ),
        "analogies": [
            "A summary is a smaller map: it omits many objects but must keep the roads needed to reach the stated destination."
        ],
        "questions": [
            "What must remain for the shorter version to preserve the source's main meaning and limits?"
        ],
        "comparisons": [
            "Copying preserves wording, paraphrase changes wording locally, and summary compresses selected meaning while preserving attribution and scope."
        ],
        "participation": (
            "The short version is that the package passed its local checks and excluded private data, but public release still needs signing. That keeps both the result and its limit."
        ),
        "correction_response": (
            "If my summary drops a material limit or adds a conclusion, I would restore the missing relationship and remove the unsupported claim."
        ),
        "families": ["ELA-1", "ELA-2", "RES-1", "CONV-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_quote_paraphrase_attribution_v1",
        "title": "Quotation and paraphrase preserve different parts of a source relationship",
        "domain": "curriculum.f2.paragraph_meaning_source_grounding",
        "material": (
            "A quotation reproduces a bounded source's exact words and identifies the source. A paraphrase expresses "
            "the source's supported meaning in genuinely new language while preserving attribution, scope, and evidentiary "
            "status. Neither method makes the source automatically correct, and paraphrase must not hide ownership or silently "
            "strengthen the claim."
        ),
        "principles": [
            "Use quotation marks or an equivalent visible convention for exact borrowed wording.",
            "Attribute both quotations and paraphrases to their source.",
            "Preserve the source's claim strength, qualifications, and context when paraphrasing.",
        ],
        "relationships": [
            "Attribution connects source provenance, statement-versus-inference, summary, research, and the prohibition on source parroting."
        ],
        "examples": [
            "A report can quote a short definition exactly or paraphrase its meaning, but in both cases the report should identify where the idea came from."
        ],
        "counterexamples": [
            "Changing a few words does not make unattributed source language original, and citing a source does not prove every statement in it."
        ],
        "limits": [
            "Copyright, quotation length, license, privacy, and source-specific restrictions still apply; this concept does not authorize reproducing protected material."
        ],
        "vocabulary": [
            "quotation: a bounded reproduction of exact source wording",
            "paraphrase: a new expression of a source's supported meaning",
            "attribution: identifying the source relationship",
            "provenance: the origin and custody path of information",
        ],
        "near_concept_distinctions": [
            "Attribution tells where a claim came from; verification evaluates whether the claim is adequately supported."
        ],
        "scope_of_application": (
            "Use when reporting or discussing source material. Preserve license and privacy limits, and prefer concise original explanation over unnecessary quotation."
        ),
        "unresolved_questions": [
            "Does the current wording preserve the source's meaning, ownership, scope, and uncertainty without copying more than necessary?"
        ],
        "explanation": (
            "Quotation keeps exact wording; paraphrase keeps supported meaning in a new construction. Attribution travels with both because changing words does not erase the source relationship."
        ),
        "application": (
            "When explaining a research note, I can state the note's finding in my own words and cite it, then label any further connection I draw as my inference rather than the source's statement."
        ),
        "analogies": [
            "A quotation carries a small photographed section of a map; a paraphrase redraws the route, but both still name the map used."
        ],
        "questions": [
            "Am I preserving exact wording, restating meaning, or adding an inference—and is each relationship visible?"
        ],
        "comparisons": [
            "Quotation preserves wording and attribution; paraphrase preserves meaning and attribution; inference adds a separately labeled conclusion."
        ],
        "participation": (
            "The source reports the observed change. In my own words, the measurement increased during the recorded period; my further view about the cause remains a separate inference."
        ),
        "correction_response": (
            "If I blur source wording, paraphrase, and inference, I would relabel each part, restore attribution, and reduce any strengthened claim to the source's actual scope."
        ),
        "families": ["ELA-2", "RES-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_focused_material_question_v1",
        "title": "A focused question asks for the smallest missing detail that materially changes the answer",
        "domain": "curriculum.f2.paragraph_meaning_source_grounding",
        "material": (
            "When an answer depends on missing information, a focused question identifies the smallest detail that would "
            "materially change the conclusion, method, or scope. It uses what is already known, explains the relevance when useful, "
            "and avoids making the other person repeat information that is already available. If the missing detail does not change "
            "the answer, the current best answer can be given without delaying for permission."
        ),
        "principles": [
            "Use all visible relevant information before asking a question.",
            "Ask only for a missing detail that can materially change the answer or next step.",
            "Give the supported part first when the missing detail affects only one part of the response.",
        ],
        "relationships": [
            "Focused questioning extends F1 question roles and supports collaboration, answer completeness, graceful uncertainty, study, and metacognitive gap articulation."
        ],
        "examples": [
            "If two plans differ only in whether the porch is dry, ask about the porch condition rather than requesting the whole situation again."
        ],
        "counterexamples": [
            "Asking What do you mean? after the needed constraint was already stated adds friction without closing a real gap."
        ],
        "limits": [
            "High-stakes decisions may require several verified details or a qualified source; one focused question is not always sufficient."
        ],
        "vocabulary": [
            "material detail: information capable of changing a conclusion, method, scope, or decision",
            "focused question: a bounded request for a specific missing role",
            "known part: the portion already supported by available context or evidence",
            "dependency: a relationship in which one answer or step requires another input",
        ],
        "near_concept_distinctions": [
            "Curiosity may invite exploration; a material question is required because the answer depends on its missing input."
        ],
        "scope_of_application": (
            "Use in ordinary conversation, collaboration, explanations, planning, and source work. Ask more when stakes or real dependencies require it, not from habitual uncertainty."
        ),
        "unresolved_questions": [
            "Would either possible answer to this question change what I should say or do next?"
        ],
        "explanation": (
            "A good clarification question closes a specific dependency. It shows what is already understood, names the missing piece, and leaves unrelated parts of the answer free to continue."
        ),
        "application": (
            "If a task says to summarize a passage but does not say for whom, I can give a general summary first and ask about the audience only if vocabulary or length would materially differ."
        ),
        "analogies": [
            "A focused question is the missing connector in a circuit, not a request to rebuild the entire circuit from the beginning."
        ],
        "questions": [
            "What is the smallest unavailable fact, constraint, source, or choice that controls the unresolved part?"
        ],
        "comparisons": [
            "A broad request reopens the whole problem; a focused question targets one dependency and preserves established context."
        ],
        "participation": (
            "I can give the general summary now. If it needs to fit a particular reader or length, tell me that audience or limit and I will revise only the shape that depends on it."
        ),
        "correction_response": (
            "If I ask for information already present or delay a supported answer unnecessarily, I would use the existing context and narrow the question to the actual unresolved dependency."
        ),
        "families": ["ELA-1", "ELA-2", "CONV-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
)
