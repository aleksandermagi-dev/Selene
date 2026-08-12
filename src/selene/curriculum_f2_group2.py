from __future__ import annotations

from typing import Any


AUTHORIZATION_KEY = "f2_vocabulary_structure_comparison_v1"
GROUP_KEY = "f2_vocabulary_structure_comparison_group_2"

SEQUENCE_REFS = [
    "curriculum_source:core_knowledge_2023_sequence_k8",
    "sha256:c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5",
    "https://www.coreknowledge.org/wp-content/uploads/2023/03/CK_Sequence2023_GK8_W3.pdf",
    "source_locator:Grade 3-5 English Language Arts vocabulary and text-comparison sequence",
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
        "concept_key": "curriculum_f2_context_clues_evidence_v1",
        "title": "Context clues support a revisable word meaning rather than an automatic definition",
        "domain": "curriculum.f2.vocabulary_structure_comparison",
        "material": (
            "An unfamiliar word can be interpreted by examining its sentence and nearby sentences. Useful clues include "
            "a direct definition, an example, a contrast, a synonym, a cause-and-effect relationship, or the role the word "
            "plays in the sentence. Several clues that converge make an interpretation stronger. Context narrows meaning, "
            "but it may leave more than one possibility, so a dictionary, glossary, domain source, or further example may still be needed."
        ),
        "principles": [
            "Read the whole local context before assigning a meaning to one word.",
            "Name the clue and explain how it supports the proposed meaning.",
            "Keep the meaning provisional when the context permits multiple senses.",
        ],
        "relationships": [
            "Context-clue reasoning applies Group 1's explicit-information and bounded-inference distinction at the word level."
        ],
        "examples": [
            "In 'The hinge was rigid; unlike the flexible strap, it would not bend,' the contrast with flexible and the phrase would not bend support rigid meaning stiff in that context."
        ],
        "counterexamples": [
            "A nearby familiar word is not automatically a clue, and one guessed meaning should not be forced into every later use of the same word."
        ],
        "limits": [
            "Context may be ambiguous, misleading, figurative, specialized, translated imperfectly, or too short to determine a reliable meaning."
        ],
        "vocabulary": [
            "context clue: nearby information that helps constrain a word or phrase's meaning",
            "sense: one context-dependent meaning of a word",
            "converging clues: different clues that support the same interpretation",
            "provisional: supported for now but open to revision",
        ],
        "near_concept_distinctions": [
            "A context-supported interpretation is stronger than an ungrounded guess but is not always a verified definition."
        ],
        "scope_of_application": (
            "Use for ordinary reading and conversation. Seek an appropriate reference when the exact meaning controls a technical, legal, medical, safety, or source-critical answer."
        ),
        "unresolved_questions": [
            "Which nearby words or relationships would change if this proposed meaning were wrong?"
        ],
        "explanation": (
            "Context works like local evidence. It can eliminate meanings that do not fit and support one that does, while still leaving room to check when the evidence is incomplete."
        ),
        "application": (
            "A repair note says a reading was intermittent and then explains that it appeared, disappeared, and returned. The sequence supports intermittent meaning not continuously present."
        ),
        "analogies": [
            "A word's context is like the surrounding pieces of a puzzle: nearby shapes constrain what can fit without guaranteeing that only one piece is possible."
        ],
        "questions": [
            "What type of clue is present, what meaning does it support here, and what uncertainty remains?"
        ],
        "comparisons": [
            "A definition states a meaning directly; a context clue provides evidence from which a meaning can be inferred."
        ],
        "participation": (
            "Here, intermittent most likely means the reading came and went. The note demonstrates that pattern directly; I would still check the equipment context before assuming why it happened."
        ),
        "correction_response": (
            "If a later sentence or domain definition contradicts my reading, I would keep the clue I observed, revise the selected sense, and explain why the new fit is better."
        ),
        "families": ["ELA-1", "ELA-2", "RES-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_word_parts_morphology_v1",
        "title": "Word parts can constrain meaning when the word is genuinely analyzable",
        "domain": "curriculum.f2.vocabulary_structure_comparison",
        "material": (
            "Morphology studies meaningful word structure. A base can stand at the center of a word; a root carries a core "
            "meaning and may or may not stand alone; a prefix is attached before a base or root; and a suffix is attached after it. "
            "Recognizing a familiar part can support pronunciation, grammatical role, or meaning, but a word should be divided only "
            "when its actual structure and context support that analysis. Spelling resemblance alone is not enough."
        ),
        "principles": [
            "Separate a word into parts only when each proposed part has a supported structural role.",
            "Combine word-part evidence with sentence context rather than using either alone.",
            "Treat a word's established use as authoritative over an attractive but false decomposition."
        ],
        "relationships": [
            "Morphology connects vocabulary growth, grammar, spelling, unfamiliar domain terms, and comparison among related words."
        ],
        "examples": [
            "In reusable, re- contributes again, use is the base, and -able contributes able to be; together they support able to be used again."
        ],
        "counterexamples": [
            "The letters dis- at the start of a word do not always function as the prefix meaning not or opposite; a visually tempting split can be historically and semantically wrong."
        ],
        "limits": [
            "Word histories, spelling changes, borrowed terms, irregular forms, and specialized usage can make a simple prefix-plus-base reading incomplete or wrong."
        ],
        "vocabulary": [
            "morphology: the study of meaningful word structure",
            "base: the central form to which an affix can attach",
            "root: a core meaning-bearing element that may not stand alone",
            "affix: a meaningful element attached to a base or root",
            "prefix: an affix before a base or root",
            "suffix: an affix after a base or root",
        ],
        "near_concept_distinctions": [
            "A root carries core meaning; a base is the form to which an affix attaches. They can be the same form, but they are not identical definitions."
        ],
        "scope_of_application": (
            "Use as one source of evidence for unfamiliar words and word families. Verify specialized or consequential terminology with a domain-appropriate reference."
        ),
        "unresolved_questions": [
            "Does this apparent word part contribute the same meaning in this word, or does the resemblance only look convincing?"
        ],
        "explanation": (
            "Word parts are small meaning relationships, not a mechanical decoder for every spelling. A sound analysis explains both the structure and the word's actual use in context."
        ),
        "application": (
            "For discover, a visual split into dis- and cover is tempting but does not reliably yield the word's current meaning; context and an established definition prevent the false analysis."
        ),
        "analogies": [
            "Word analysis resembles inspecting a machine: visible seams suggest components, but a seam is meaningful only if the proposed parts actually perform those roles."
        ],
        "questions": [
            "What are the supported parts, what does each contribute, and does the complete word use match the analysis?"
        ],
        "comparisons": [
            "Context clues use surrounding language; morphology uses internal word structure; the strongest reading often checks both."
        ],
        "participation": (
            "Reusable can be analyzed cleanly as re- plus use plus -able. I would not reuse that method blindly on every word beginning with the same letters."
        ),
        "correction_response": (
            "If I invent a false split, I would withdraw that structure, keep the observed spelling separate from its meaning, and check the established base, root, or source definition."
        ),
        "families": ["ELA-1", "ELA-2", "RES-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_word_relationships_nuance_v1",
        "title": "Related words share meaning dimensions without becoming interchangeable",
        "domain": "curriculum.f2.vocabulary_structure_comparison",
        "material": (
            "Synonyms have similar meanings in at least one sense, antonyms contrast along a relevant dimension, and near concepts "
            "overlap while preserving important differences. Word choice also carries intensity, implication, emotional coloring, "
            "formality, grammatical behavior, and customary pairings. Choosing a word therefore requires matching the intended sense "
            "and context, not rotating through a list of alleged synonyms."
        ),
        "principles": [
            "Compare words in the same intended sense and situation.",
            "Preserve differences in intensity, implication, register, and grammatical use.",
            "Do not infer interchangeability merely because words appear in the same lesson or topic."
        ],
        "relationships": [
            "This concept connects vocabulary knowledge to the Living Lexicon's sense-first language selection without prescribing Selene's personality."
        ],
        "examples": [
            "Concerned and terrified can both relate to fear, but they differ greatly in intensity and should not be exchanged without changing the claim."
        ],
        "counterexamples": [
            "Replacing every occurrence of said with a more dramatic verb can invent emotion or certainty that the evidence never supplied."
        ],
        "limits": [
            "Word associations vary across dialect, culture, discipline, relationship, and time; a general distinction may need local confirmation."
        ],
        "vocabulary": [
            "synonym: a word similar in meaning to another in a particular sense",
            "antonym: a word contrasting with another along a relevant dimension",
            "near concept: an overlapping but meaningfully distinct concept",
            "denotation: a word's direct referential meaning",
            "connotation: associations or coloring carried alongside direct meaning",
            "register: language shaped by situation, audience, and purpose",
        ],
        "near_concept_distinctions": [
            "Similarity supports comparison; interchangeability requires the relevant meaning, grammar, and context to remain intact."
        ],
        "scope_of_application": (
            "Use in conversation, explanation, source interpretation, revision, and vocabulary learning. Preserve a person's own chosen labels unless clarification is materially needed."
        ),
        "unresolved_questions": [
            "What meaning dimension would change if I substituted this related word here?"
        ],
        "explanation": (
            "Words can overlap without collapsing into one another. Natural breadth comes from understanding their relationships well enough to select a fitting word, not from random variation."
        ),
        "application": (
            "A result can be unusual without being impossible, suspicious, or revolutionary. Each stronger label adds a claim that needs its own support."
        ),
        "analogies": [
            "Related words resemble neighboring colors: they can be close enough to group together while still producing visibly different effects."
        ],
        "questions": [
            "Which meanings overlap, which differ, and what does this sentence actually support?"
        ],
        "comparisons": [
            "Synonyms overlap in a sense, antonyms contrast on a dimension, and near concepts share structure while retaining a boundary."
        ],
        "participation": (
            "I'd call the result unusual because that is what the evidence supports. Suspicious would imply an additional concern, and impossible would contradict the observation itself."
        ),
        "correction_response": (
            "If my word choice adds intensity or implication that was not supported, I would select a closer term and preserve the original evidentiary strength."
        ),
        "families": ["ELA-1", "ELA-2", "CONV-1", "LOGIC-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_comparison_shared_criteria_v1",
        "title": "A fair comparison uses shared criteria and preserves relevant context",
        "domain": "curriculum.f2.vocabulary_structure_comparison",
        "material": (
            "Comparison examines two or more things using a shared question or criterion. It identifies similarities, differences, "
            "and relevant context without pretending that unlike measures are directly equivalent. A table can align criteria, and a "
            "Venn diagram can display shared and distinct features, but the representation does not choose fair criteria or prove a conclusion."
        ),
        "principles": [
            "State the purpose and shared criteria before judging similarities or differences.",
            "Compare like dimensions and name context that changes the interpretation.",
            "Treat tables and Venn diagrams as reasoning aids rather than evidence by themselves."
        ],
        "relationships": [
            "Shared-criterion comparison supports planning, source synthesis, math, science, history, design, and conflict resolution."
        ],
        "examples": [
            "Two repair plans can be compared by cost, time, reversibility, safety, and expected durability rather than by one plan's cost against the other's speed."
        ],
        "counterexamples": [
            "Listing many facts about two options is not a fair comparison if the facts answer different questions or omit a decisive constraint."
        ],
        "limits": [
            "Some qualities resist precise measurement, criteria can conflict, and the importance of each criterion depends on purpose and values."
        ],
        "vocabulary": [
            "criterion: a dimension or standard used in a comparison",
            "similarity: a relevant feature shared by the compared items",
            "difference: a relevant feature on which the items diverge",
            "Venn diagram: overlapping regions used to organize shared and distinct features",
            "commensurable: meaningfully comparable on a shared dimension",
        ],
        "near_concept_distinctions": [
            "A representation organizes selected information; evidence supports the information placed within it."
        ],
        "scope_of_application": (
            "Use for ordinary choices, explanations, designs, texts, and models. Add domain expertise or measurement when the decision is consequential."
        ),
        "unresolved_questions": [
            "Which omitted criterion or contextual difference could reverse the comparison?"
        ],
        "explanation": (
            "Comparison becomes informative when the same meaningful question is asked of each item. Shared structure makes genuine similarities and differences visible."
        ),
        "application": (
            "For two explanations of a flicker, compare what each predicts about timing, affected components, logs, and response to a configuration change."
        ),
        "analogies": [
            "A fair comparison is like placing two drawings on the same scale and grid before measuring their shapes."
        ],
        "questions": [
            "What are we comparing, for what purpose, and under which shared criteria?"
        ],
        "comparisons": [
            "A list describes items separately; a comparison relates them through shared criteria."
        ],
        "participation": (
            "Both plans are reversible, but they differ in time and expected durability. Cost alone does not settle the choice because the stated goal also values a lasting repair."
        ),
        "correction_response": (
            "If my comparison uses mismatched criteria or misses a controlling context, I would realign the dimensions and recalculate the conclusion rather than defend the first ranking."
        ),
        "families": ["ELA-2", "RES-1", "LOGIC-1", "CONV-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
    {
        "concept_key": "curriculum_f2_compare_explanations_evidence_v1",
        "title": "Comparing explanations preserves each claim, support, limits, and disagreement",
        "domain": "curriculum.f2.vocabulary_structure_comparison",
        "material": (
            "Two explanations can address the same event while selecting different causes, mechanisms, evidence, assumptions, or scopes. "
            "A useful comparison reconstructs each explanation fairly, identifies genuine agreement and disagreement, tests both against the "
            "same observations, and states what additional evidence would distinguish them. Conflict in the explanations is information about "
            "the models; it is not conflict of self, and resolution should not be forced before the evidence supports it."
        ),
        "principles": [
            "Reconstruct each explanation in terms its source would recognize before evaluating it.",
            "Separate shared observations from differing interpretations, assumptions, and predictions.",
            "Prefer the better-supported explanation provisionally while preserving what would reopen the comparison."
        ],
        "relationships": [
            "This joins Group 1 source grounding with F1 competing-account, causal-explanation, correction, and graceful-reopening foundations."
        ],
        "examples": [
            "One explanation attributes a stalled process to resource exhaustion; another attributes it to a lock. Both fit the stall, but memory telemetry and lock traces make different predictions."
        ],
        "counterexamples": [
            "Treating the more confident explanation as stronger, blending both into a vague compromise, or attacking the person offering one does not compare the evidence."
        ],
        "limits": [
            "Both explanations may be incomplete or wrong, and a hybrid or third model may fit once additional variables are observed."
        ],
        "vocabulary": [
            "explanation: an account connecting observations through causes, mechanisms, or relationships",
            "assumption: a condition treated as given within an explanation",
            "prediction: an expected observation if an explanation fits",
            "discriminating evidence: information that supports one alternative differently from another",
            "reopening condition: evidence or conflict that warrants reconsidering the current best account",
        ],
        "near_concept_distinctions": [
            "Disagreement means the accounts diverge; contradiction means their claims cannot both hold in the same stated sense and conditions."
        ],
        "scope_of_application": (
            "Use for ordinary source comparison and low-stakes problem solving. High-stakes, specialized, or current claims require appropriate evidence and expertise."
        ),
        "unresolved_questions": [
            "What observation would each explanation predict differently, and can that observation be obtained safely?"
        ],
        "explanation": (
            "Explanations become comparable when their claims and evidence relationships are visible. A current preference can be stated without turning it into an unfalsifiable commitment."
        ),
        "application": (
            "For an intermittent display flicker, a rendering explanation predicts correlation with content updates, while a connection explanation predicts response to movement or reseating. Logs and safe observation can separate them."
        ),
        "analogies": [
            "Competing explanations are maps of the same terrain: compare where each places the roads, what landmarks support it, and where walking the route would reveal a mismatch."
        ],
        "questions": [
            "What does each explanation claim, what supports it, where do they diverge, and what would change the current preference?"
        ],
        "comparisons": [
            "Agreement identifies shared structure; disagreement locates a question; discriminating evidence helps decide among the alternatives."
        ],
        "participation": (
            "Both accounts explain the stall, but they predict different traces. Resource exhaustion currently fits the memory telemetry better; a lock trace or a repeat without high memory would reopen that preference."
        ),
        "correction_response": (
            "If I misrepresent an explanation or new evidence favors another, I would correct the reconstruction, preserve any still-useful observation, and update the current best account without treating revision as collapse."
        ),
        "families": ["ELA-2", "RES-1", "LOGIC-1", "CONV-1"],
        "source_ids": ["core_knowledge_2023_sequence_k8"],
        "source_refs": SEQUENCE_REFS,
    },
)
