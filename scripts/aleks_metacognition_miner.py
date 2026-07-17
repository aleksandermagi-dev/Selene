from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.aleks_system_ideas_miner import Message, compact, find_source_zips, iter_export_messages
except ModuleNotFoundError:  # Allow direct `python scripts/...` execution.
    from aleks_system_ideas_miner import Message, compact, find_source_zips, iter_export_messages


DEFAULT_SOURCE_DIR = Path("AleksOSminer")
DEFAULT_OUTPUT_DIR = Path("local-data") / "aleks_metacognition_miner"
DEFAULT_CONVERSATION_OUTPUT_DIR = DEFAULT_OUTPUT_DIR / "conversation_pass"
MAX_SCAN_CHARS = 6000
EPISODE_MATCHER_VERSION = "4.26"

BOUNDARY = (
    "Private Aleks metacognition review only. The miner proposes generalizable cognitive-method "
    "candidates from bounded, source-labeled Aleks-authored evidence. It does not model Aleks as a "
    "person, write Selene memory or identity, alter law or personality, approve a method, expose the "
    "raw corpus, train a model, or connect findings to runtime behavior."
)

GUARD_FLAGS = {
    "aleks_person_model_created": False,
    "selene_memory_write": False,
    "selene_identity_write": False,
    "selene_governance_write": False,
    "selene_personality_write": False,
    "selene_runtime_connection": False,
    "cocoon_queue_write": False,
    "app_db_write": False,
    "public_doc_write": False,
    "raw_source_dump": False,
    "model_training_finetune_or_lora": False,
    "automatic_method_approval": False,
}


METHOD_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "key": "structural_pattern_mapping",
        "name": "Structural pattern mapping",
        "description": "Notice relational structure across domains while keeping resemblance provisional.",
        "signals": {
            "pattern_language": (r"\bpattern(?:s| matching| recognition)?\b", r"\brecurring structure\b"),
            "cross_domain": (r"\bacross (?:different )?domains?\b", r"\bcross[- ]domain\b", r"\bmytholog\w*\b.*\b(?:cosmolog\w*|biolog\w*|engineer\w*)\b"),
            "relational_mapping": (r"\bsame (?:shape|structure|relationship)\b", r"\bmap(?:ping)?\b.*\brelationship", r"\banalog(?:y|ies|ous)\b"),
            "connection_language": (r"\bconnect(?:ing|ed|ion)?\b.*\b(?:ideas|systems|fields|domains)\b", r"\blink(?:ing|ed)?\b.*\b(?:systems|domains|concepts)\b"),
            "functional_dependency_mapping": (
                r"\bdependent on .{0,100}\bso just like\b",
                r"\bjust like .{0,120}\b(?:metaboli[sz]e|function|operate) independently\b",
            ),
            "spontaneous_pattern_to_solution": (
                r"\beven when i .{0,100}\b(?:relax|watch)\b.{0,120}\b(?:mapping|napping) patterns and solutions\b",
            ),
            "cross_field_work_intent": (
                r"\bso much we don(?:'|’)t understand but think we do\b[\s\S]{0,220}\bcross work\b[\s\S]{0,100}\b(?:few|multiple|different) fields\b",
                r"\bscience really is extremely diverse but separate\b[\s\S]{0,180}\bloss of knowledge\b[\s\S]{0,180}\bcombine most of the cores\b",
            ),
        },
        "strong_signals": (
            r"\bstructural analog",
            r"\brelational pattern",
            r"\bpattern matching across\b",
            r"\bdependent on .{0,100}\bso just like (?:a |an |the )?(?:virus|organism|system|model|network|ecosystem) .{0,140}\bindependent",
            r"\beven when i .{0,100}\b(?:relax|watch)\b.{0,120}\b(?:mapping|napping) patterns and solutions\b",
            r"\bso much we don(?:'|’)t understand but think we do\b[\s\S]{0,220}\bcross work\b[\s\S]{0,100}\b(?:few|multiple|different) fields\b",
            r"\bscience really is extremely diverse but separate\b[\s\S]{0,180}\bloss of knowledge\b[\s\S]{0,180}\bcombine most of the cores\b",
        ),
        "representation_modes": ["relational", "pattern", "cross-domain"],
        "triggering_conditions": ["A problem may share organization, feedback, or constraints with another domain."],
        "possible_code_primitive": "structural_analogy_mapper",
        "known_risks": ["surface resemblance mistaken for shared mechanism", "forced cross-domain connection", "confirmation through repeated but non-independent patterns"],
        "project_fit": ["intelligenceOS", "Metacognition Organ", "research synthesis"],
    },
    {
        "key": "visual_spatial_modeling",
        "name": "Visual-spatial modeling",
        "description": "Represent a problem as imagery, space, motion, shape, or a diagram before or alongside words.",
        "signals": {
            "visualize": (r"\bvisuali[sz](?:e|ing|ation)\b", r"\bpicture (?:it|this|the)\b", r"\bsee it in my (?:head|mind)\b"),
            "spatial_form": (r"\bspatial\b", r"\bshape\b", r"\bdiagram\b", r"\bmental image\b"),
            "imagery_reasoning": (r"\bimag(?:e|ery)\b.*\b(?:think|reason|assess|understand)\b", r"\bthink\b.*\b(?:image|imagery|visual)\b"),
            "visual_reasoning_process": (r"\bthe way i visuali[sz]e\b", r"\bvisuali[sz]e myself\b", r"\bwhat would it look like\b"),
            "motion_model": (r"\b(?:move|motion|rotate|flow)\b.*\b(?:mind|model|system)\b",),
            "scene_visualization": (r"\bi can see it now\b.{0,100}\bintro scene\b",),
            "internal_narrative_modeling": (r"\bcreate these narratives\b.{0,120}\bsimilar to what i can do in my head\b",),
            "on_demand_thought_experiment": (
                r"\bcame during .{0,80}\bthought experiment\b[\s\S]{0,160}\bdo that all the time on command\b[\s\S]{0,160}\b(?:black holes|scenarios)\b[\s\S]{0,160}\bappeared\b",
            ),
        },
        "strong_signals": (r"\bvisuali[sz]e first\b", r"\bthe way i visuali[sz]e\b", r"\bimagery then words\b", r"\bvisual simulation mode\b", r"\bvisual model\b.*\b(?:think|reason|problem|assess|understand)\b", r"\bi can see it now\b.{0,100}\bintro scene\b", r"\bcreate these narratives\b.{0,120}\bsimilar to what i can do in my head\b", r"\bcame during .{0,80}\bthought experiment\b[\s\S]{0,160}\bdo that all the time on command\b[\s\S]{0,160}\b(?:black holes|scenarios)\b[\s\S]{0,160}\bappeared\b"),
        "representation_modes": ["visual", "spatial", "dynamic"],
        "triggering_conditions": ["The problem depends on shape, arrangement, motion, scale, or interacting parts."],
        "possible_code_primitive": "visual_spatial_problem_frame",
        "known_risks": ["image coherence mistaken for factual correctness", "details lost during translation into language"],
        "project_fit": ["Metacognition Organ", "perception", "simulation workbench"],
    },
    {
        "key": "cross_representation_translation",
        "name": "Cross-representation translation",
        "description": "Translate between imagery, patterns, words, examples, symbols, and system models.",
        "signals": {
            "translation": (r"\btranslat(?:e|ing|ion)\b", r"\bturn (?:it|that|this) into\b"),
            "words_and_images": (r"\b(?:image|imagery|visual)\b.*\bwords?\b", r"\bwords?\b.*\b(?:image|imagery|visual)\b"),
            "put_into_words": (r"\bput (?:it|this|that) into words\b", r"\bhard to (?:explain|describe|verbalize)\b"),
            "representation_change": (r"\b(?:pattern|intuition|model)\b.*\b(?:example|language|symbol|rule)\b",),
            "pedagogical_reencoding": (r"\bfun way to teach (?:kids|people|students|someone|the .{0,50})\b",),
            "analogy_to_explanation": (r"\bto explain .{0,120}\bmake it like one of those .{0,160}\b(?:commercials?|stories|memes?|scenes?|analogies|examples)\b",),
            "signal_to_image_mapping": (
                r"\btake (?:the )?(?:sounds?|radio|pressure|seismic) waves? instead of light waves? and map (?:it|them) to images?\b",
            ),
            "intuition_to_math_translation": (
                r"\bgoing to school to learn (?:the|that) math\b[\s\S]{0,140}\blearn .{0,80}\bsubconsciously\b",
            ),
        },
        "strong_signals": (r"\bimagery then words\b", r"\bpattern(?:s)? into (?:words|rules)\b", r"\bfun way to teach (?:kids|people|students|someone|the .{0,50})\b", r"\bto explain .{0,120}\bmake it like one of those .{0,160}\b(?:commercials?|stories|memes?|scenes?|analogies|examples)\b", r"\btake (?:the )?(?:sounds?|radio|pressure|seismic) waves? instead of light waves? and map (?:it|them) to images?\b", r"\bgoing to school to learn (?:the|that) math\b[\s\S]{0,140}\blearn .{0,80}\bsubconsciously\b"),
        "representation_modes": ["translation", "multimodal", "concrete/abstract"],
        "triggering_conditions": ["An insight exists in one representation but must be inspected or communicated in another."],
        "possible_code_primitive": "representation_translator",
        "known_risks": ["translation treated as lossless", "verbal fluency hiding an incomplete source representation"],
        "project_fit": ["Metacognition Organ", "NLO", "Answer Engine"],
    },
    {
        "key": "systems_consequence_simulation",
        "name": "Systems and consequence simulation",
        "description": "Model interacting parts, feedback, consequences, and behavior over time.",
        "signals": {
            "system_language": (r"\bsystems? thinking\b", r"\binteracting parts?\b", r"\bwhole system\b"),
            "simulation": (r"\bsimulat(?:e|ing|ion)\b", r"\brun (?:it|the model) forward\b"),
            "consequences": (r"\bconsequences?\b", r"\bwhat happens (?:if|when|next)\b"),
            "feedback": (r"\bfeedback loops?\b", r"\bsecond[- ]order effects?\b", r"\bdownstream\b"),
            "simulation_setup": (r"\bin (?:that|this|the) simulation (?:i|we) (?:have )?(?:created|ran|made)\b", r"\bi took .{0,100}\bblack hole\b.{0,180}\bgalax(?:y|ies)\b"),
            "time_horizon": (r"\bafter (?:billions?|millions?) .{0,80}\bwhat would happen\b", r"\bover (?:billions?|millions?) of years\b"),
            "emergent_output": (r"\bseems? to (?:be )?form(?:ing)?\b", r"\bcreated new (?:galaxies|systems|structures)\b", r"\bearly formations?\b"),
            "simulation_iteration": (r"\bexpand the simulation\b", r"\brestart (?:the|this) simulation\b", r"\bparameters? to test\b"),
            "test_intent": (r"\bwanted to test my .{0,80}\btheory\b", r"\btest (?:my|our|the) .{0,80}\btheory\b.{0,120}\bresults?\b"),
            "counterfactual_trajectory": (r"\bif (?:humanity|the system|the civilization|the species) .{0,80}\b(?:went extinct|failed|disappeared)\b", r"\bwhat if .{0,120}\b(?:erased|collapsed|disappeared)\b"),
            "temporal_degradation": (r"\bover time .{0,180}\b(?:eventually|until)\b", r"\bslowly erode away\b", r"\bdue to time\b"),
            "inverse_intervention": (
                r"\bif i add (?P<inverse_variable>mass|energy|pressure|heat|volume|density|gravity|distance|speed|temperature)\b[\s\S]{0,180}\b(?:it )?(?:increases?|raises?)\b[\s\S]{0,140}\bso what if i remove(?:d)? (?P=inverse_variable)\b",
            ),
            "unintended_use_risk": (r"\bonce released\b.{0,140}\bcould inspire\b.{0,120}\bweaponiz(?:e|ed|ing)\b", r"\bwhat(?:'|’)re the chances\b.{0,160}\b(?:bomb|weapon)\b"),
        },
        "strong_signals": (r"\bsimulat(?:e|ing) (?:the )?system\b", r"\bsystems? and consequences?\b", r"\bwanted to test my .{0,80}\btheory\b.{0,120}\bresults?\b", r"\bexpand the simulation\b.{0,160}\bparameters? to test\b", r"\bin (?:that|this|the) simulation (?:i|we) (?:have )?(?:created|ran|made)\b", r"\bif (?:humanity|the system|the civilization|the species) .{0,80}\b(?:went extinct|failed|disappeared)\b.{0,220}\bover time\b", r"\bonce released\b.{0,140}\bcould inspire\b.{0,120}\bweaponiz(?:e|ed|ing)\b"),
        "representation_modes": ["causal", "systems", "temporal"],
        "triggering_conditions": ["The answer depends on interaction, feedback, time, or downstream effects."],
        "possible_code_primitive": "bounded_system_simulator",
        "known_risks": ["missing variables produce persuasive but incomplete simulations", "model assumptions silently treated as reality", "a conceivable misuse is mistaken for a likely or mechanically feasible misuse"],
        "project_fit": ["intelligenceOS", "Metacognition Organ", "planning"],
    },
    {
        "key": "constraint_driven_design_iteration",
        "name": "Constraint-driven design iteration",
        "description": "Progress from an objective through requirements, feasibility constraints, alternatives, subsystem choices, and an actionable first implementation step.",
        "signals": {
            "objective_and_start": (r"\bstarting point\b", r"\bfirst step (?:to|for|would be)\b", r"\bdefine (?:the )?(?:mission )?objectives?\b", r"\bwork on this first\b", r"\bstart here\b", r"\bbegin(?:ning)? at phase\b"),
            "requirements": (r"\bmission (?:parameters|profile|requirements)\b", r"\bmaterials? (?:are )?needed\b", r"\bperformance metrics?\b"),
            "feasibility_constraints": (r"\baccessible to the general public\b", r"\bwithout (?:the use of )?fuel\b", r"\bfor long periods? of time\b", r"\btrade[- ]offs? and challenges\b", r"\b(?:issue|problem) of costs? to launch\b", r"\bwhat(?:'|’)s stopping us\b"),
            "alternative_architecture": (r"\bcompletely different design\b", r"\bhybrid approach\b", r"\bsecondary (?:propulsion )?system\b", r"\balternative (?:design|architecture|approach)\b", r"\balternate propulsion system\b", r"\bwhat would you propose would work better\b"),
            "iterative_expansion": (r"\blet'?s expand (?:on|farther|further)\b", r"\blet'?s add\b", r"\blet'?s implement\b", r"\bexpand (?:the|this) (?:design|system|idea|mission)\b", r"\block in (?:our|the) steps\b", r"\bre[- ]?look at (?:our|the) .{0,60}schematics?\b", r"\bsee if anything needs? tweaked\b"),
            "bottleneck_priority": (r"\bwork on something more important\b.{0,120}\b(?:cheaper|cost)\b", r"\bif we solve .{0,80}\bcosts? to launch\b"),
            "dependency_bottleneck": (r"\btackle .{0,80}\bsince (?:that(?:'|’)s|it is|it'?s) the part that connects everything\b", r"\bpart that connects everything together\b"),
            "bounded_domain_choice": (r"\bthink (?:personal|civilian) and .{0,80}\bleave the military\b", r"\bstart (?:with|just) personal (?:use|usage)\b"),
            "feasible_stepping_stone": (r"\bidea i can (?:really )?do right now\b.{0,160}\b(?:sell|fund|money)\b.{0,160}\b(?:real|long[- ]term) goal\b", r"\buse (?:that|the) money to work towards? (?:our|the) (?:real|long[- ]term) goal\b"),
            "subsystem_coordination": (r"\bswitching systems?\b", r"\bcoordinate .{0,100}\bsubsystems?\b", r"\bpropulsion modes?\b.*\bpower\b", r"\bmaximum efficiency\b"),
            "functional_input_substitution": (
                r"\bwouldn(?:'|’)t have to use (?:lava|(?:that|the) (?:fuel|material|component|source))\b.{0,180}\banything that can (?:(?:store|supply|produce|transfer) (?:heat|energy|power|fuel)|withstand (?:heat|temperature|pressure))\b",
            ),
            "integration_over_rebuild": (
                r"\bif i (?:buy|use|combine) (?:\d+|two|three|four) separate (?:telescopes|sensors|modules|tools|devices)\b[\s\S]{0,180}\b(?:make|use|add) (?:an? |the |a \d+(?:st|nd|rd|th) )?(?:connector|coordinator|hub|\d+(?:st|nd|rd|th))? that connects?\b[\s\S]{0,220}\bsolve the problem\b[\s\S]{0,120}\bwithout reinventing the wheel\b",
            ),
            "whole_to_component_capability_partition": (
                r"\bi don(?:'|’)?t think (?:a )?(?:3d )?printer can (?:make|print) (?:the |an? )?.{0,120}\b[\s\S]{0,260}\b(?:housing mechanisms?|connectors?|metal prongs?)\b",
            ),
        },
        "strong_signals": (
            r"\bmaterials? (?:are )?needed\b.{0,180}\bmission parameters\b",
            r"\bmission parameters\b.{0,180}\bmaterials? (?:are )?needed\b",
            r"\bhybrid approach\b.{0,180}\b(?:expand|secondary)\b",
            r"\bfirst step (?:to|for|would be) .{0,180}\b(?:develop|design|build|implement|create)\b",
            r"\binstead of solving .{0,120}\balternate propulsion system\b",
            r"\block in (?:our|the) steps\b.{0,160}\bphase\b",
            r"\bre[- ]?look at (?:our|the) .{0,60}schematics?\b.{0,120}\bneeds? tweaked\b",
            r"\bwork on something more important\b.{0,120}\b(?:cheaper|cost)\b",
            r"\btackle .{0,80}\bpart that connects everything\b",
            r"\bidea i can (?:really )?do right now\b.{0,180}\b(?:sell|fund|money)\b.{0,180}\b(?:real|long[- ]term) goal\b",
            r"\bthink (?:personal|civilian) and .{0,100}\bleave the military\b",
            r"\bwouldn(?:'|’)t have to use (?:lava|(?:that|the) (?:fuel|material|component|source))\b.{0,180}\banything that can (?:(?:store|supply|produce|transfer) (?:heat|energy|power|fuel)|withstand (?:heat|temperature|pressure))\b",
            r"\bif i (?:buy|use|combine) (?:\d+|two|three|four) separate (?:telescopes|sensors|modules|tools|devices)\b[\s\S]{0,180}\b(?:make|use|add) [\s\S]{0,80}\bthat connects?\b[\s\S]{0,220}\bsolve the problem\b[\s\S]{0,120}\bwithout reinventing the wheel\b",
            r"\bi don(?:'|’)?t think (?:a )?(?:3d )?printer can (?:make|print) (?:the |an? )?.{0,120}\b[\s\S]{0,260}\b(?:housing mechanisms?|connectors?|metal prongs?)\b",
        ),
        "representation_modes": ["requirements", "constraint", "iterative design"],
        "triggering_conditions": ["An ambitious goal needs to become a feasible system through progressive requirement and architecture decisions."],
        "possible_code_primitive": "constraint_design_iteration_ledger",
        "known_risks": ["adding subsystems before validating core feasibility", "accepting a proposed architecture because it sounds complete", "requirements drift without recording why the design changed"],
        "project_fit": ["intelligenceOS", "Metacognition Organ", "engineering workbench", "planning"],
    },
    {
        "key": "candidate_model_construction",
        "name": "Candidate-model construction",
        "description": "Turn a missing mechanism, counterfactual, or provisional intuition into a model that can be tested.",
        "signals": {
            "hypothesis_language": (r"\bhypothes(?:is|es|ize)\b", r"\bcandidate model\b", r"\bprovisional (?:idea|model|explanation)\b"),
            "possibility_language": (r"\bwhat if\b", r"\bmaybe\b", r"\bcould (?:be|it be|this be)\b"),
            "candidate_answer": (r"\bi think .{0,140}\bis the answer to (?:the )?.{0,100}\bparadox\b",),
            "missing_mechanism": (r"\bmissing something\b", r"\bmissing (?:piece|mechanism)\b", r"\bthink of .{0,40} the wrong way\b", r"\bbigger equation\b"),
            "mechanism_proposal": (r"\bconnected .{0,80}(?:below|farther than|under)\b", r"\bmechanism\b", r"\bwhat(?:'s| is) bringing .{0,40}(?:back|down)\b", r"\bwasn(?:'|’)?t .{0,80}\bbut rather\b", r"\bstarted from .{0,120}\b(?:sucked|spewed|decompressed|collapsed|emerged)\b", r"\bwhat if .{0,180}\b(?:actually|could) .{0,80}\b(?:creat(?:e|ing)|caus(?:e|ing)|convert(?:ed|ing)?|collaps(?:e|ing)|produc(?:e|ing))\b"),
            "causal_gap": (r"\bwhat caused (?:it|this|that|the .{0,40})\b", r"\bwhat (?:came|happened) before\b", r"\babsolute origin\b"),
            "engineered_conditions": (r"\bcreate the conditions (?:of|for) .{0,100}\bharness (?:its|the) (?:raw )?(?:power|energy)\b",),
            "classification_criterion": (
                r"\banything that .{0,140}\bhas to be (?:a |some )?(?:type|kind|form) of (?:life|living thing|organism|intelligence|system|process|entity)\b",
                r"\bthe only (?:inanimate|nonliving|non-living) .{0,120}\bwould be\b",
            ),
            "principle_based_design": (
                r"\bwhat if (?:we|i) designed? (?:an? )?(?:engine|system|device|tool|model) based (?:up)?on that princi(?:ple|pal)\b",
            ),
            "data_bounded_best_guess": (
                r"\bidk what the hell it is\b[\s\S]{0,100}\bwhy it(?:'|’)s a hypothesis\b[\s\S]{0,140}\bbest guess due to the data\b",
            ),
        },
        "strong_signals": (
            r"\btest my hypothes",
            r"\bcandidate model\b",
            r"\bwhat if .{0,160}\b(?:connected|mechanism|equation)\b",
            r"\bwhat if .{0,180}\b(?:actually|could) .{0,80}\b(?:creat(?:e|ing)|caus(?:e|ing)|convert(?:ed|ing)?|collaps(?:e|ing)|produc(?:e|ing))\b",
            r"\bidea for solving .{0,100}\bwhat if\b",
            r"\bwhat if .{0,100}\bcreate the conditions (?:of|for) .{0,120}\bharness (?:its|the) (?:raw )?(?:power|energy)\b",
            r"\bcreate the conditions (?:of|for) .{0,120}\bharness (?:its|the) (?:raw )?(?:power|energy)\b",
            r"\bi think .{0,140}\bis the answer to (?:the )?.{0,100}\bparadox\b",
            r"\banything that .{0,140}\bhas to be (?:a |some )?(?:type|kind|form) of (?:life|living thing|organism|intelligence|system|process|entity)\b.{0,180}\bthe only (?:inanimate|nonliving|non-living)\b.{0,120}\bwould be\b",
            r"\bwhat if (?:we|i) designed? (?:an? )?(?:engine|system|device|tool|model) based (?:up)?on that princi(?:ple|pal)\b",
            r"\bidk what the hell it is\b[\s\S]{0,100}\bwhy it(?:'|’)s a hypothesis\b[\s\S]{0,140}\bbest guess due to the data\b",
        ),
        "representation_modes": ["hypothetical", "mechanistic", "provisional"],
        "triggering_conditions": ["An observation appears incomplete and a provisional mechanism is needed to make testable predictions."],
        "possible_code_primitive": "candidate_model_constructor",
        "known_risks": ["interesting mechanism mistaken for established explanation", "model name becomes stickier than the evidence"],
        "project_fit": ["intelligenceOS", "Metacognition Organ", "research workbench"],
    },
    {
        "key": "baseline_preserving_model_extension",
        "name": "Baseline-preserving model extension",
        "description": "Preserve the supported part of an existing explanation while proposing a bounded extension for what it does not yet explain.",
        "signals": {
            "baseline_preserved": (r"\bi don(?:'|’)?t disagree with\b", r"\bi accept (?:the|that)\b", r"\bkeep (?:the|that) (?:part|model|explanation)\b"),
            "extension": (r"\b(?:i(?:'|’)?d|i would) like to add to it\b", r"\badd to (?:the|that|this) (?:model|theory|explanation)\b", r"\bbuild on (?:the|that|this) (?:model|theory|explanation)\b"),
            "scope_gap": (r"\bwhat caused (?:it|this|that|the .{0,40})\b", r"\bdoesn(?:'|’)?t explain (?:the )?(?:origin|cause|mechanism)\b", r"\babsolute origin\b"),
            "minimal_change": (r"\bnothing changes except\b", r"\bpreserv(?:e|es|ing) .{0,100}\bwhile (?:adding|changing|extending)\b"),
        },
        "strong_signals": (
            r"\bi don(?:'|’)?t disagree with .{0,120}\b(?:add to it|build on it)\b",
            r"\bkeep .{0,100}\bwhat (?:is|was) supported\b.{0,120}\b(?:add|extend|revise)\b",
        ),
        "representation_modes": ["conservative revision", "scope", "model layering"],
        "triggering_conditions": ["An existing model explains part of the evidence, but a causal or scope gap remains open."],
        "possible_code_primitive": "baseline_preserving_model_extension_ledger",
        "known_risks": ["an attractive extension inherits credibility from the supported baseline", "the added mechanism may be untestable", "minimal-change framing can hide a large assumption"],
        "project_fit": ["intelligenceOS", "Metacognition Organ", "research workbench"],
    },
    {
        "key": "provisional_naming_and_scope_control",
        "name": "Provisional naming and scope control",
        "description": "Use names as inspectable working claims, then rename, narrow, or retire them when their implied scope no longer fits the evidence.",
        "signals": {
            "working_label": (r"\bworking (?:name|label|term)\b", r"\bcall (?:it|this)\b", r"\bhas a nice ring to it\b"),
            "epistemic_status": (r"\bthe hypothes(?:is|es)\b", r"\bnot (?:a )?theory\b", r"\bprovisional (?:name|label|term)\b"),
            "renaming": (r"\b(?:change|changing|changed) names?\b", r"\brename(?:d|s|ing)?\b", r"\bcan(?:not|'t) (?:call|say) (?:it|this|that|it'?s)\b"),
            "name_substitution": (r"\bstick to (?:the )?.{0,80}\bnames?\b.{0,80}\binstead of\b", r"\bname change\b.{0,100}\bfrom now on\b"),
            "scope_correction": (r"\bnot gravity at all\b", r"\bit'?s not gravity\b", r"\bmap what'?s being missed\b", r"\b(?:narrow|narrowed|narrowing) (?:the )?scope\b"),
            "retirement": (r"\bofficially moved on from (?:tng|(?:the|my) (?:idea|model|hypothesis|explanation|claim))\b", r"\bretir(?:e|ed|ing) (?:the )?(?:name|label|model|hypothesis)\b"),
            "hypothesis_revision_by_data": (
                r"\bnot a theory though\b.{0,20}\bit(?:'|’)s a hypothesis\b[\s\S]{0,120}\bcan be altered if more data shows it(?:'|’)s something else\b",
            ),
        },
        "strong_signals": (
            r"\bhypothes(?:is|es)\b.{0,100}\bnot (?:a )?theory\b",
            r"\bneeds? to change names?\b",
            r"\bstick to (?:the )?.{0,80}\bnames?\b.{0,80}\binstead of\b",
            r"\bname change\b.{0,100}\bfrom now on\b",
            r"\bofficially moved on from (?:tng|(?:the|my) (?:idea|model|hypothesis|explanation|claim))\b",
            r"\bnot a theory though\b.{0,20}\bit(?:'|’)s a hypothesis\b[\s\S]{0,120}\bcan be altered if more data shows it(?:'|’)s something else\b",
        ),
        "representation_modes": ["conceptual", "epistemic", "scope"],
        "triggering_conditions": ["A useful working label has begun to imply more certainty, mechanism, or scope than the evidence supports."],
        "possible_code_primitive": "provisional_concept_label_ledger",
        "known_risks": ["a memorable name hardens into an unsupported claim", "renaming hides rather than records a substantive correction", "useful structure is discarded with an overbroad label"],
        "project_fit": ["Metacognition Organ", "research workbench", "knowledge provenance"],
    },
    {
        "key": "evidence_tool_operationalization",
        "name": "Evidence and tool operationalization",
        "description": "Turn a conceptual question into explicit information needs, test criteria, data operations, or a bounded tool interface.",
        "signals": {
            "information_requirements": (r"\bwhat (?:all )?(?:information|data|inputs?) do (?:you|we|i) need\b", r"\bwhat do (?:you|we|i) need to (?:measure|calculate|test|run)\b"),
            "test_route": (r"\brun the math\b", r"\bquantif(?:y|ied|ication)\b", r"\btest (?:the|this|my) hypothes(?:is|es)\b", r"\bpossible to test this\b", r"\brun the .{0,40}\btest on\b"),
            "data_inputs": (r"\b(?:source|input|observation|spectrum|measurement) data\b", r"\bdata (?:set|sets|table|tables|file|files)\b", r"\btables? and (?:the )?graphs?\b"),
            "evidence_check": (r"\banalysis pipeline confirmed\b", r"\bpreliminary results?\b", r"\bcriterion\b.{0,100}\b(?:noise|artifact|evidence|result)\b", r"\bvalidation\b"),
            "executable_tooling": (r"\bpython code\b", r"\b(?:analysis|astronomy|domain[- ]specific) (?:script|tool)\b", r"\b[a-z0-9_]+\.py\b", r"\b[a-z0-9_]+\.bat\b"),
            "interface_and_route": (r"\btool(?:s)? layer\b", r"\btool registry\b", r"\bstructured (?:interface|result object)\b", r"\binput parameters\b.*\bvalidation\b"),
            "simulation_parameters": (r"\bparameters? to test (?:my|our|the) (?:theory|hypothesis|model)\b", r"\bwhat parameters? (?:should|can|do) .{0,80}\btest\b"),
            "simulation_tool_route": (r"\bwhat would be something better .{0,80}\bto simulate\b", r"\bcan you (?:run|predict outcomes? to) simulations?\b", r"\bbetter (?:tool|simulator|software) .{0,80}\bsimulat"),
            "held_out_input": (r"\b(?:map|data|example|case) that i did not send\b", r"\bunseen (?:map|data|example|case)\b"),
            "test_template": (r"\bnow that you have a template\b", r"\buse (?:the|this) template to (?:test|check|mark)\b"),
            "facts_to_setup": (r"\blook at the facts\b", r"\bhow (?:we|i) could set this up\b"),
            "missing_evidence_request": (r"\bwhat else am i missing\b.{0,120}\b(?:prove|test|verify|support)\b", r"\bwhat (?:evidence|data) (?:are|is) still missing\b"),
            "sequential_analysis": (r"\banaly[sz]e (?:it|them|the files?) with my script\b.{0,100}\b(?:one|1) by (?:one|1)\b.{0,100}\b(?:run|do) the (?:numbers|math)\b",),
            "dataset_before_plot": (r"\bnot yet\b.{0,80}\bmore files?\b.{0,80}\bthen we plot\b",),
            "direct_test_question": (r"\bhow (?:the hell )?do i test this\b",),
            "exploratory_simulation_route": (r"\bgo on universe sandbox\b.{0,160}\bstudy\b.{0,120}\bsee what sticks out\b",),
            "quantitative_probability_check": (
                r"\brun some (?:real )?numbers\b.{0,140}\bwhat(?:'|’)s (?:the )?(?:percentage|probability|chance) (?:this|that|it) (?:works?|will work|succeeds?)\b",
            ),
            "candidate_set_to_data_route": (
                r"\bit can be any number of things\b[\s\S]{0,260}\bi have no .{0,40} clue\b[\s\S]{0,180}\bhere(?:'|’)s the program\b.{0,20}\brun the data\b",
            ),
            "capability_gap_to_domain_interface": (
                r"\bi .{0,100}\bneed to learn .{0,40}\bmath\b[\s\S]{0,180}\b(?:make|build|create) .{0,80}\b(?:interface|assistant|tool)\b[\s\S]{0,100}\brun the math\b",
            ),
        },
        "strong_signals": (
            r"\bwhat (?:all )?(?:information|data|inputs?) do (?:you|we|i) need to run the math\b",
            r"\bdomain[- ]specific .{0,80}\btool\b.{0,160}\btool(?:s)? layer\b",
            r"\btool registry\b.{0,200}\b(?:structured interface|input parameters|validation|structured result)\b",
            r"\bparameters? to test (?:my|our|the) (?:theory|hypothesis|model)\b",
            r"\bwhat would be something better .{0,80}\bto simulate\b",
            r"\brun the .{0,40}\btest on .{0,120}\bthat i did not send\b.{0,160}\btemplate\b",
            r"\bpossible to test this\b.{0,160}\b(?:object|measurement|setup|experiment)\b",
            r"\blook at the facts\b.{0,120}\bhow (?:we|i) could set this up\b",
            r"\bwhat else am i missing\b.{0,120}\b(?:prove|test|verify|support)\b",
            r"\banaly[sz]e (?:it|them|the files?) with my script\b.{0,100}\b(?:one|1) by (?:one|1)\b.{0,100}\b(?:run|do) the (?:numbers|math)\b",
            r"\bnot yet\b.{0,80}\bmore files?\b.{0,80}\bthen we plot\b",
            r"\bhow (?:the hell )?do i test this\b",
            r"\bgo on universe sandbox\b.{0,160}\bstudy\b.{0,120}\bsee what sticks out\b",
            r"\brun some (?:real )?numbers\b.{0,140}\bwhat(?:'|’)s (?:the )?(?:percentage|probability|chance) (?:this|that|it) (?:works?|will work|succeeds?)\b",
            r"\bit can be any number of things\b[\s\S]{0,260}\bi have no .{0,40} clue\b[\s\S]{0,180}\bhere(?:'|’)s the program\b.{0,20}\brun the data\b",
            r"\bi .{0,100}\bneed to learn .{0,40}\bmath\b[\s\S]{0,180}\b(?:make|build|create) .{0,80}\b(?:interface|assistant|tool)\b[\s\S]{0,100}\brun the math\b",
        ),
        "representation_modes": ["operational", "evidential", "tool-mediated"],
        "triggering_conditions": ["A model or question needs to be converted into inspectable inputs, measurements, tests, or executable operations."],
        "possible_code_primitive": "evidence_test_and_tool_router",
        "known_risks": ["tool output treated as proof without checking assumptions", "implementation detail obscures the original claim", "a generic coding request is mistaken for a cognitive method"],
        "project_fit": ["intelligenceOS", "Answer Engine", "domain adapters", "research workbench"],
    },
    {
        "key": "multiple_working_hypotheses",
        "name": "Multiple working hypotheses",
        "description": "Keep competing explanations available until evidence distinguishes them.",
        "signals": {
            "multiple_models": (r"\bmultiple (?:hypotheses|models|explanations|possibilities)\b", r"\bmore than one (?:explanation|possibility|model)\b"),
            "alternatives": (r"\balternative explanations?\b", r"\bother possibilit(?:y|ies)\b"),
            "competition": (r"\bcompeting (?:hypotheses|models|explanations)\b", r"\bcompare (?:the )?(?:hypotheses|models|explanations)\b"),
            "provisionality": (r"\bworking hypothes", r"\bkeep (?:it|them) provisional\b"),
            "compatibility": (r"\bwhat(?:'|’)?s stopping .{0,120}\btwo frameworks?\b.{0,100}\bsimultaneously\b", r"\bcan (?:the|these) two (?:frameworks|models|explanations) work (?:together|simultaneously)\b"),
            "enumerated_candidates": (r"\btwo new ideas\b[\s\S]{0,220}\b1\b[\s\S]{0,220}\b2\b", r"\b(?:first|one) possibility\b.{0,220}\b(?:second|another) possibility\b"),
            "branch_split": (r"\bbrain(?:'|’)?s going (?:three|3) ways\b.{0,220}\bseparate from\b",),
            "separate_candidate": (r"\bsave (?:this|that|it) as a separate idea\b",),
            "enumerated_unknowns_with_data_route": (
                r"\bit can be any number of things\b[\s\S]{0,320}\bit could be\b[\s\S]{0,100}\bcould be\b[\s\S]{0,340}\brun the data\b",
            ),
        },
        "strong_signals": (r"\bmultiple working hypotheses\b", r"\bcompeting explanations\b", r"\btwo frameworks?\b.{0,120}\bwork(?:ing)? simultaneously\b", r"\btwo new ideas\b[\s\S]{0,220}\b1\b[\s\S]{0,220}\b2\b", r"\bbrain(?:'|’)?s going (?:three|3) ways\b.{0,220}\bseparate from\b", r"\bsave (?:this|that|it) as a separate idea\b", r"\bit can be any number of things\b[\s\S]{0,320}\bit could be\b[\s\S]{0,100}\bcould be\b[\s\S]{0,340}\brun the data\b"),
        "representation_modes": ["hypothetical", "comparative", "probabilistic"],
        "triggering_conditions": ["Available evidence supports more than one materially different explanation."],
        "possible_code_primitive": "candidate_model_workspace",
        "known_risks": ["artificial ambiguity after evidence is sufficient", "candidate count grows without a stopping rule"],
        "project_fit": ["intelligenceOS", "Metacognition Organ"],
    },
    {
        "key": "dialectical_third_model_synthesis",
        "name": "Dialectical third-model synthesis",
        "description": "When a binary framing is inadequate, inspect the tension and construct a third model grounded in available evidence rather than choosing a side by default.",
        "signals": {
            "paradox_or_tension": (r"\bembrace the paradox\b", r"\bhold (?:the|both) (?:tension|contradiction|sides)\b"),
            "third_model": (r"\bthird (?:narrative|model|option|explanation)\b", r"\bnew (?:narrative|model) beyond (?:the|that) binary\b"),
            "binary_reframe": (r"\bredefines? the binary\b", r"\bfalse binary\b", r"\bneither .{0,100}\bnor\b.*\b(?:instead|rather)\b"),
            "evidence_anchor": (r"\bscientific facts? to build on\b", r"\bbuild .{0,80}\bfrom (?:the )?(?:facts|evidence|constraints)\b"),
        },
        "strong_signals": (
            r"\bembrace the paradox\b.{0,180}\bthird (?:narrative|model|option|explanation)\b",
            r"\bthird (?:narrative|model|option|explanation)\b.{0,120}\bredefines? the binary\b",
        ),
        "representation_modes": ["dialectical", "comparative", "synthetic"],
        "triggering_conditions": ["Two apparent alternatives omit a third structure capable of preserving supported parts and resolving the tension."],
        "possible_code_primitive": "evidence_grounded_third_model_synthesizer",
        "known_risks": ["inventing a middle position when one side is supported", "false balance", "a novel synthesis may conceal unsupported assumptions"],
        "project_fit": ["intelligenceOS", "Metacognition Organ", "Answer Engine"],
    },
    {
        "key": "observation_interpretation_separation",
        "name": "Observation before interpretation",
        "description": "Separate directly available observations from inferred meaning before committing to an explanation.",
        "signals": {
            "observation": (r"\bobserv(?:e|ed|ation|able)\b",),
            "interpretation": (r"\binterpret(?:ation|ed|ing)?\b", r"\binferen(?:ce|tial)\b", r"\binferred\b"),
            "separation": (r"\bseparat(?:e|ing)\b.*\b(?:observation|inference|interpretation)\b", r"\bwhat (?:we|i) know\b.*\bwhat (?:we|i) think\b"),
            "sequence": (
                r"\b(?:observe|measure|record|collect|inspect)(?: (?:it|this|the data|the evidence))? first\b.{0,120}\bbefore (?:(?:we|i|you) )?(?:interpret|conclude|assume)\b",
                r"\bbefore (?:we|i|you) (?:interpret|conclude|assume)\b",
            ),
            "tool_label": (r"\b(?:simulation|game|tool) .{0,80}\b(?:named|calling|labeled|labelled)\b", r"\bit(?:'|’)?s calling (?:some|them|it)\b", r"\bit named .{0,100}\b"),
            "reality_check": (r"\bthey don(?:'|’)?t really exist\b", r"\bnot (?:an? )?(?:actual|real) (?:galaxy|result|object|observation)\b"),
            "tentative_interpretation": (r"\balmost seems as if\b", r"\bseems as if (?:it(?:'|’)?s|it is) showing\b", r"\bearly formations?\b"),
            "screening_not_proof": (r"\b(?:this|that|it) still doesn(?:'|’)?t prove anything\b", r"\b(?:result|detection|screening|output) (?:is|isn(?:'|’)t|doesn(?:'|’)t) .{0,60}\bproof\b"),
            "quarantine_without_bias": (r"\bkeep (?:this|the) data safe\b.{0,100}\bdon(?:'|’)?t skew the picture\b",),
            "data_interpretation_dispute": (
                r"\bcan(?:'|’)t ignore that data\b[\s\S]{0,160}\bwhat(?:'|’)s being argued is my interpretation of what it is\b",
            ),
        },
        "strong_signals": (r"\bobservation before interpretation\b", r"\bobserve first\b.*\binterpret", r"\b(?:simulation|game|tool) .{0,100}\b(?:named|calling|labeled|labelled)\b.{0,160}\bdon(?:'|’)?t really exist\b", r"\bit named .{0,120}\bdon(?:'|’)?t really exist\b", r"\bit(?:'|’)?s calling .{0,100}\balmost seems as if\b", r"\b(?:this|that|it) still doesn(?:'|’)?t prove anything\b", r"\bkeep (?:this|the) data safe\b.{0,100}\bdon(?:'|’)?t skew the picture\b", r"\bcan(?:'|’)t ignore that data\b[\s\S]{0,160}\bwhat(?:'|’)s being argued is my interpretation of what it is\b"),
        "representation_modes": ["evidential", "descriptive", "inferential"],
        "triggering_conditions": ["A conclusion may be running ahead of what is directly supported."],
        "possible_code_primitive": "observation_inference_ledger",
        "known_risks": ["over-formalizing ordinary answers", "mislabeling prior reviewed knowledge as unsupported inference"],
        "project_fit": ["intelligenceOS", "Metacognition Organ", "source-backed research"],
    },
    {
        "key": "source_context_hypothesis_audit",
        "name": "Archimedes Sphere source-context hypothesis audit",
        "description": "Reconstruct a source account in its observational and cultural context, propose a testable interpretation, and keep that interpretation provisional while checking feasibility, data, repeated cases, and correction paths.",
        "signals": {
            "named_framework": (
                r"\barchimedes sphere\b.{0,160}\b(?:framework for|interpret|decoder)",
                r"\b(?:framework for|interpret|decoder)\w*\b.{0,160}\barchimedes sphere\b",
                r"\bstarting base\b.{0,180}\b(?:myth|interpret|debunk)\w*\b.{0,180}\barchimedes sphere\b",
            ),
            "whole_source_reconstruction": (
                r"\b(?:entire|whole|full) (?:myth|source|account|story)\b.{0,120}\b(?:word for word|fully|start to finish|from start to finish)",
                r"\bread (?:it|the .{0,50}) fully\b",
            ),
            "observation_and_cultural_context": (
                r"\bdescrib(?:e|ing|ed) what they (?:see|saw|observed)\b.{0,180}\b(?:society|culture|standards|language|knowledge)",
                r"\bwhat they (?:see|saw|observed)\b.{0,180}\bbased (?:up)?on (?:their )?(?:society|culture|standards|language|knowledge)",
                r"\bno words\b.{0,100}\bwhat they know\b",
            ),
            "data_to_explanation_trace": (
                r"\bdata\b.{0,80}\bconcept\b.{0,80}\bmyth\b.{0,80}\bresult\b.{0,100}\bhow and why",
                r"\bidea\s*[-–—>]\s*data\s*[-–—>]\s*solution\b",
                r"\bcompare (?:it|this|the .{0,50}) to (?:the )?real data\b",
            ),
            "physical_feasibility_gate": (
                r"\bif (?:it(?:'|’)?s|it is|that(?:'|’)?s|that is) physically impossible\b.{0,160}\blook elsewhere\b",
                r"\bnow that we know (?:it|this) can be done\b.{0,180}\b(?:ancient|historical|source|myth)",
                r"\b(?:build|reconstruct|test) the .{0,80}\b(?:before|to) (?:confirm|claim|call|say)",
                r"\bhave to actually build\b.{0,120}\band test (?:it|this|the .{0,60})",
            ),
            "cross_case_sampling": (
                r"\b(?:three|3) myths? for each culture\b",
                r"\btest another (?:one|myth|case)\b.{0,100}\b(?:another|different) culture\b",
                r"\bfor each (?:civilization|civ|culture)\b.{0,160}\b(?:confirm|compare|test|repeat)",
            ),
            "repeatability_threshold": (
                r"\b1\s*=\s*interesting\b.{0,80}\b2\s*=\s*coincidence\b.{0,80}\b3\s*=\s*pattern\b.{0,140}\brepeatable in multiple circumstances\b",
            ),
            "source_quality": (
                r"\bbest records?\b.{0,160}\bbest source of evidence\b",
                r"\bsource quality\b.{0,120}\b(?:compare|weight|evidence|record)",
            ),
            "correction_and_expansion": (
                r"\bframework\b.{0,160}\bopen for expansion\b",
                r"\bdon(?:'|’)?t have to protect the framework\b",
                r"\bif i(?:'|’)?m wrong about something tell me\b",
            ),
            "confidence_boundary": (
                r"\b99(?:\.9)?%\b.{0,180}\b100%\b.{0,180}\b(?:test|confirm|another myth|more myths)",
                r"\bnot (?:yet )?100%\b.{0,160}\b(?:test|confirm|missing|another case|another myth)",
            ),
        },
        "strong_signals": (
            r"\barchimedes sphere\b.{0,180}\b(?:framework for|interpret|decoder)",
            r"\b(?:framework for|interpret|decoder)\w*\b.{0,180}\barchimedes sphere\b",
            r"\bstarting base\b.{0,180}\b(?:myth|interpret|debunk)\w*\b.{0,180}\barchimedes sphere\b",
            r"\bdata\b.{0,80}\bconcept\b.{0,80}\bmyth\b.{0,80}\bresult\b.{0,100}\bhow and why",
            r"\b(?:entire|whole|full) (?:myth|source|account|story)\b.{0,120}\bword for word\b",
            r"\bwhat they (?:see|saw|observed)\b.{0,180}\bbased (?:up)?on (?:their )?(?:society|culture|standards|language|knowledge)",
            r"\bif (?:it(?:'|’)?s|it is|that(?:'|’)?s|that is) physically impossible\b.{0,160}\blook elsewhere\b",
            r"\bhave to actually build\b.{0,120}\band test (?:it|this|the .{0,60})",
            r"\b1\s*=\s*interesting\b.{0,80}\b2\s*=\s*coincidence\b.{0,80}\b3\s*=\s*pattern\b.{0,140}\brepeatable in multiple circumstances\b",
            r"\bbest records?\b.{0,160}\bbest source of evidence\b",
            r"\bframework\b.{0,160}\bopen for expansion\b",
        ),
        "representation_modes": ["source reconstruction", "contextual", "hypothesis", "comparative", "evidential"],
        "triggering_conditions": ["A symbolic, historical, or inherited account may encode observations whose original context or explanatory language has changed."],
        "possible_code_primitive": "source_context_hypothesis_auditor",
        "known_risks": [
            "a coherent symbolic or visual fit is mistaken for evidence of a physical mechanism",
            "artifact feasibility is mistaken for evidence that the artifact existed or was used as proposed",
            "cultural context is flattened into stereotypes or treated as uniform",
            "translation gaps or absent evidence are filled with an attractive just-so story",
            "repeated but dependent stories are mistaken for independent confirmation",
            "the word debunked overstates what remains a candidate interpretation",
            "the framework overfits cases or is protected from contrary evidence",
        ],
        "project_fit": ["research workbench", "source-backed research", "Metacognition Organ", "Great Library review artifacts"],
    },
    {
        "key": "independent_constraint_checking",
        "name": "Independent constraint checking",
        "description": "Test a promising model against evidence or constraints that do not merely repeat its origin.",
        "signals": {
            "constraint": (r"\bindependent constraints?\b", r"\bconstraints?\b"),
            "verification": (r"\bverif(?:y|ied|ication)\b", r"\bcross[- ]check\b", r"\brun the math\b", r"\btest (?:it|my hypothesis|my theory|my .{0,60} theory|the hypothesis|the theory|the idea|the model|that)\b"),
            "evidence": (r"\bevidence chain\b", r"\bindependent evidence\b", r"\bsource(?:s|d)?\b.*\b(?:support|confirm|disagree)\b"),
            "falsification": (r"\bfalsif(?:y|iable|ication)\b", r"\bwhat would (?:disprove|change)\b", r"\banything that disproves\b", r"\bdisprove(?:s|d)? (?:the|this|my) (?:idea|hypothesis|model)\b", r"\bcounterexample\b"),
            "measurement_reliability": (r"\bhow accurate would .{0,100}\bbe\b", r"\breliable way to tell\b", r"\bmeasurement .{0,80}\breliab(?:le|ility)\b"),
            "variable_accounting": (r"\bwith all the variables in place\b", r"\bmany variables to every situation\b", r"\baccount for (?:all|the) (?:variables|motion|confounders)\b"),
            "support_challenge": (r"\bwhat clear evidence supports? (?:this|that|the) claim\b", r"\bwhat evidence supports?\b", r"\bhow can we say\b.{0,160}\band (?:is|are) not\b"),
            "observability_boundary": (r"\bno observable evidence\b", r"\bnever be proven until\b"),
            "held_out_check": (r"\b(?:map|data|example|case) that i did not send\b", r"\bunseen (?:map|data|example|case)\b"),
            "stress_test": (r"\bthrow rocks at .{0,120}\bsee how (?:it|the .{0,40}) holds\b", r"\b(?:put (?:the|my|our) ideas?|put them) down\b.{0,120}\bthrow rocks at (?:it|them)\b"),
            "omitted_context": (r"\bnot any of the other facts\b", r"\blet(?:'|’)?s ignore that .{0,180}\blet(?:'|’)?s ignore how\b"),
            "premature_attribution": (r"\blet(?:'|’)?s just blame\b",),
            "nearby_case_check": (r"\bmodel more\b.{0,100}\btest it with (?:closer|nearby) (?:objects?|cases?|examples?)\b",),
            "cross_case_repeatability": (r"\b1\s*=\s*interesting\b.{0,80}\b2\s*=\s*coincidence\b.{0,80}\b3\s*=\s*pattern\b.{0,140}\brepeatable in multiple circumstances\b",),
            "bias_awareness": (r"\bresults? (?:will|would|could) be biased\b", r"\bbiased (?:test|result|sample)\b"),
            "adjacent_case_scan": (r"\bpeek around .{0,100}\bsee if anything else match(?:es)? (?:this|the) pattern\b",),
            "partial_plausibility_then_constraint_check": (
                r"\bwhere i would(?:'|’)?ve dismissed it but did not\b[\s\S]{0,260}\bwould make sense\b[\s\S]{0,160}\bstart to (?:really )?(?:start to )?debunk it\b[\s\S]{0,180}\bspeed of light takes longer than one hour\b",
            ),
            "successful_execution_mistaken_for_validation": (
                r"\bmath can(?:'|’)t be wrong\b[\s\S]{0,120}\bpython wouldn(?:'|’)t have given me data\b[\s\S]{0,100}\bit would(?:'|’)ve yelled\b",
            ),
            "external_fact_check_and_feedback": (
                r"\bsimple test from a google result\b[\s\S]{0,160}\bfollow up with you showing you it was real\b[\s\S]{0,160}\bgave feedback\b[\s\S]{0,100}\bincorrect information\b",
            ),
            "felt_physics_mistaken_for_validation": (
                r"\bi don(?:'|’)t know how i know this stuff\b[\s\S]{0,220}\bcan just [“\"]?feel[”\"]? if it(?:'|’)s going to work or the physics behind it\b",
            ),
        },
        "strong_signals": (
            r"\bindependent constraints?\b",
            r"\brun the math and test my hypothes",
            r"\btest my (?:hypothesis|theory) (?:for|based on|against|using)\b",
            r"\bwanted to test my .{0,80}\btheory\b",
            r"\bthrow rocks at .{0,120}\b(?:disprov|see how .{0,60} holds)\b",
            r"\b(?:put (?:the|my|our) ideas?|put them) down\b.{0,120}\bthrow rocks at (?:it|them)\b",
            r"\bwhat would change (?:my|the) (?:answer|conclusion|mind)\b",
            r"\bhow accurate would .{0,100}\bredshift\b",
            r"\bwith all the variables in place\b.{0,180}\bhow can we say\b",
            r"\bwhat clear evidence supports? (?:this|that|the) claim\b",
            r"\brun the .{0,40}\btest on .{0,120}\bthat i did not send\b",
            r"\bnot any of the other facts\b.{0,160}\blet(?:'|’)?s just blame\b",
            r"\bmodel more\b.{0,100}\btest it with (?:closer|nearby) (?:objects?|cases?|examples?)\b",
            r"\b1\s*=\s*interesting\b.{0,80}\b2\s*=\s*coincidence\b.{0,80}\b3\s*=\s*pattern\b.{0,140}\brepeatable in multiple circumstances\b",
            r"\bresults? (?:will|would|could) be biased\b",
            r"\bpeek around .{0,100}\bsee if anything else match(?:es)? (?:this|the) pattern\b",
            r"\bwhere i would(?:'|’)?ve dismissed it but did not\b[\s\S]{0,260}\bwould make sense\b[\s\S]{0,160}\bstart to (?:really )?(?:start to )?debunk it\b[\s\S]{0,180}\bspeed of light takes longer than one hour\b",
            r"\bmath can(?:'|’)t be wrong\b[\s\S]{0,120}\bpython wouldn(?:'|’)t have given me data\b[\s\S]{0,100}\bit would(?:'|’)ve yelled\b",
            r"\bsimple test from a google result\b[\s\S]{0,160}\bfollow up with you showing you it was real\b[\s\S]{0,160}\bgave feedback\b[\s\S]{0,100}\bincorrect information\b",
            r"\bi don(?:'|’)t know how i know this stuff\b[\s\S]{0,220}\bcan just [“\"]?feel[”\"]? if it(?:'|’)s going to work or the physics behind it\b",
        ),
        "representation_modes": ["constraint", "evidence", "falsification"],
        "triggering_conditions": ["A pattern or model is coherent but needs reality checks independent of its generating analogy."],
        "possible_code_primitive": "independent_constraint_verifier",
        "known_risks": ["circular support mislabeled as independent evidence", "verification scope too narrow for the claim", "a small repeated sample mistaken for proof"],
        "project_fit": ["intelligenceOS", "Metacognition Organ", "domain adapters"],
    },
    {
        "key": "correction_and_reopening",
        "name": "Correction integration and reopening",
        "description": "Revise conclusions when something does not fit while preserving still-useful structure.",
        "signals": {
            "correction": (r"\bcorrect(?:ion|ed|ing)?\b", r"(?<!if )\bi was wrong\b", r"\bmistake\b"),
            "reopening": (r"\breopen\b", r"\brevisit\b", r"\blook at (?:it|this) again\b"),
            "mismatch": (r"\bdoes(?:n't| not) (?:look|feel|fit|add up) right\b", r"\bsomething (?:is|was) off\b", r"\bdoes(?:n't| not) fit\b"),
            "revision": (r"\brevis(?:e|ed|ion)\b", r"\bupdate (?:the|my) (?:model|answer|conclusion)\b", r"\bchange(?:d)? my mind\b"),
            "model_abandonment": (r"\bback to the drawing (?:board|bored)\b", r"\bofficially moved on from (?:tng|(?:the|my) (?:idea|model|hypothesis|explanation|claim))\b", r"\brip tng\b", r"\babandon(?:ed|ing)? (?:the )?(?:idea|model|hypothesis)\b"),
            "scope_correction": (r"\b(?:tng|(?:the|my) (?:idea|model|hypothesis|explanation|claim)) was .{0,80}\bnot\b", r"\bnot gravity at all\b", r"\bvain battle\b"),
            "restart_after_reassessment": (r"\bback ?track .{0,140}\brestart\b", r"\breassess .{0,100}\brestart\b"),
            "selective_correction": (r"\bexcept .{0,160}\bother than that i (?:can )?agree\b", r"\bthat part (?:is|was) (?:wrong|incorrect) .{0,120}\b(?:the rest|otherwise)\b"),
            "accepted_correction": (r"\byou(?:'|’)re absolutely correct\b.{0,120}\bthank you for (?:the )?correction\b", r"\bthank you for (?:the )?correction\b.{0,160}\bwhat would you propose would work better\b"),
            "accepted_recollection_correction": (
                r"\byou(?:'|’)re correct\b.{0,80}\bi mis[ -]?remembered\b.{0,80}\bthank you\b",
            ),
            "self_correction": (r"\bscrap (?:the|that|this) .{0,80}\bidea\b.{0,120}\bbecause\b", r"\b(?:it|this|that) (?:doesn(?:'|’)t|does not|will never) have enough (?:mass|energy|evidence|support)\b"),
            "replacement_route": (r"\bwhat would you propose would work better\b", r"\bif (?:we|you|i) (?:added|changed|used)\b"),
            "selective_design_rejection": (r"\bscrap (?:the|that|this) .{0,80}\bidea\b.{0,140}\bmore .{0,60}problems than\b.{0,120}\bkeep (?:the|that|this) .{0,80}\bidea\b", r"\bdiscard .{0,100}\bbut keep\b"),
            "correction_as_learning": (r"\bscientific method\b.{0,180}\b(?:okay|fine) to be wrong\b", r"\bchange the test or scrap the idea\b.{0,160}\blearn(?:ing)?\b"),
            "scope_reduction": (r"\bmaybe (?:it|that) was an? overstretch to say\b.{0,140}\blet(?:'|’)?s say\b", r"\boverstat(?:ed|ement)\b.{0,120}\bnarrow\b"),
            "conceptual_reframe": (r"\bnot quite\b.{0,160}\bwhat you(?:'|’)re describing (?:is|was) more like (?:an? )?(?:eco[- ]?system|model|system|category|definition|criterion|mechanism|explanation)\b",),
            "error_acknowledgement": (r"\bidk what i was thinking\b.{0,100}\byou(?:'|’)re right\b.{0,120}\b(?:tired|going to bed)\b",),
            "pushback_preference": (r"\bi like when you push back and tell me .{0,80}\byou(?:'|’)re wrong\b.{0,100}\bwhy\b",),
            "accepted_model_reopening": (r"\bwrap my head around the accepted idea\b.{0,160}\btoo many holes and contradictions\b",),
            "correction_readiness": (r"\bif i(?:'|’)?m wrong about something tell me\b",),
            "conditional_correction_acceptance": (r"\bif i was wrong i(?:'|’)?d accept it\b",),
            "timeline_withdrawal": (r"\bpause\b.{0,100}\bwe(?:'|’)?re getting mixed up\b.{0,100}\bforget what i just said\b.{0,140}\bcorrect times\b",),
            "fact_check_preference": (r"\bi like when you check me\b",),
            "analogy_scope_correction": (r"\bno\b.{0,40}\bwait\b.{0,160}\bwas (?:used )?as a visual\b.{0,160}\bseparate events?\b",),
            "concept_separation_correction": (r"\bthose two are completely separate (?:ideas|models|hypotheses|frameworks)\b",),
            "direction_inconsistency": (
                r"\byou (?:are|(?:'|’)re) stating (?:two|2) (?:very )?different directions now (?:vs\.?|versus|compared to) then\b",
            ),
            "frame_shift_diagnosis": (
                r"\bwent from talking about [\s\S]{0,240}\bto [\s\S]{0,240}\bthat(?:'|’)s where the disconnect was\b",
            ),
            "premise_restoration_by_inverse": (
                r"\bno\b[\s\S]{0,80}\byou said that if i add (?P<correction_inverse_variable>mass|energy|pressure|heat|volume|density|gravity|distance|speed|temperature)\b[\s\S]{0,180}\b(?:it )?(?:increases?|raises?)\b[\s\S]{0,140}\bso what if i remove(?:d)? (?P=correction_inverse_variable)\b",
            ),
            "emphatic_conflation_correction": (
                r"\bno+\b(?:\s+no+\b){2,}[\s\S]{0,100}\bcreator race was not arc[ -]jet\b[\s\S]{0,40}\bseparate\b",
            ),
            "partial_correctness_preservation": (
                r"\bwhen i say we are [“\"]?wrong\b[”\"]?[\s\S]{0,180}\bdoesn(?:'|’)t mean\b[\s\S]{0,120}\ball wrong\b[\s\S]{0,160}\bnot fully correct\b",
            ),
            "accepted_prerequisite_gap": (
                r"\byou are correct absolutely on the math\b[\s\S]{0,140}\bi know i need that\b",
            ),
            "data_driven_hypothesis_revision": (
                r"\bnot a theory though\b.{0,20}\bit(?:'|’)s a hypothesis\b[\s\S]{0,120}\bcan be altered if more data shows it(?:'|’)s something else\b",
            ),
        },
        "strong_signals": (
            r"(?<!if )\bi was wrong\b",
            r"\bdoes(?:n't| not) look right\b",
            r"\bcorrection without (?:discarding|losing)\b",
            r"\bback to the drawing (?:board|bored)\b",
            r"\bback ?track .{0,140}\brestart\b",
            r"\bexcept .{0,160}\bother than that i (?:can )?agree\b",
            r"\bofficially moved on from (?:tng|(?:the|my) (?:idea|model|hypothesis|explanation|claim))\b",
            r"\brip tng\b",
            r"\byou(?:'|’)re absolutely correct\b.{0,120}\bthank you for (?:the )?correction\b",
            r"\byou(?:'|’)re correct\b.{0,80}\bi mis[ -]?remembered\b.{0,80}\bthank you\b",
            r"\bscrap (?:the|that|this) .{0,80}\bidea\b.{0,160}\b(?:doesn(?:'|’)t|does not|will never|not enough)\b",
            r"\bscrap (?:the|that|this) .{0,80}\bidea\b.{0,160}\bmore .{0,60}problems than\b.{0,140}\bkeep (?:the|that|this) .{0,80}\bidea\b",
            r"\bscientific method\b.{0,200}\b(?:okay|fine) to be wrong\b.{0,220}\b(?:change the test|scrap the idea)\b",
            r"\bmaybe (?:it|that) was an? overstretch to say\b.{0,140}\blet(?:'|’)?s say\b",
            r"\bnot quite\b.{0,160}\bwhat you(?:'|’)re describing (?:is|was) more like (?:an? )?(?:eco[- ]?system|model|system|category|definition|criterion|mechanism|explanation)\b",
            r"\bidk what i was thinking\b.{0,100}\byou(?:'|’)re right\b.{0,120}\b(?:tired|going to bed)\b",
            r"\bi like when you push back and tell me .{0,80}\byou(?:'|’)re wrong\b.{0,100}\bwhy\b",
            r"\bwrap my head around the accepted idea\b.{0,160}\btoo many holes and contradictions\b",
            r"\bif i(?:'|’)?m wrong about something tell me\b",
            r"\bif i was wrong i(?:'|’)?d accept it\b",
            r"\bpause\b.{0,100}\bwe(?:'|’)?re getting mixed up\b.{0,100}\bforget what i just said\b.{0,140}\bcorrect times\b",
            r"\bi like when you check me\b",
            r"\bno\b.{0,40}\bwait\b.{0,160}\bwas (?:used )?as a visual\b.{0,160}\bseparate events?\b",
            r"\bthose two are completely separate (?:ideas|models|hypotheses|frameworks)\b",
            r"\byou (?:are|(?:'|’)re) stating (?:two|2) (?:very )?different directions now (?:vs\.?|versus|compared to) then\b",
            r"\bwent from talking about [\s\S]{0,240}\bto [\s\S]{0,240}\bthat(?:'|’)s where the disconnect was\b",
            r"\bno+\b(?:\s+no+\b){2,}[\s\S]{0,100}\bcreator race was not arc[ -]jet\b[\s\S]{0,40}\bseparate\b",
            r"\bwhen i say we are [“\"]?wrong\b[”\"]?[\s\S]{0,180}\bdoesn(?:'|’)t mean\b[\s\S]{0,120}\ball wrong\b[\s\S]{0,160}\bnot fully correct\b",
            r"\byou are correct absolutely on the math\b[\s\S]{0,140}\bi know i need that\b",
            r"\bnot a theory though\b.{0,20}\bit(?:'|’)s a hypothesis\b[\s\S]{0,120}\bcan be altered if more data shows it(?:'|’)s something else\b",
        ),
        "representation_modes": ["reflective", "corrective", "iterative"],
        "triggering_conditions": ["New evidence, contradiction, or mismatch weakens the current model."],
        "possible_code_primitive": "model_reopen_and_revise",
        "known_risks": ["discarding useful structure with the error", "endless reopening without material new evidence"],
        "project_fit": ["Metacognition Organ", "Comprehension Organ", "Cocoon"],
    },
    {
        "key": "abstract_concrete_transfer",
        "name": "Abstract-concrete transfer",
        "description": "Move between general structure and concrete examples to build and test understanding.",
        "signals": {
            "abstraction": (r"\babstrac(?:t|tion)\b", r"\bgeneral(?:ize|ization|principle)\b"),
            "concrete": (r"\bconcrete (?:case|example|application)\b", r"\breal[- ]world example\b"),
            "example_use": (r"\bapply (?:it|this|the idea) to\b", r"\bdifferent example\b", r"\btest case\b"),
            "movement": (r"\bmove between\b.*\b(?:abstract|concrete)\b", r"\bfrom (?:the )?(?:example|specific) to (?:the )?(?:pattern|general)\b"),
            "example_to_framework": (r"\bwas the test\b.{0,100}\bnow we have a framework\b", r"\bstarted as one hypothesis\b.{0,100}\bturned into a system\b"),
        },
        "strong_signals": (r"\babstract(?:ion)? (?:and|to) concrete\b", r"\bconcrete (?:to|and) abstract", r"\bwas the test\b.{0,100}\bnow we have a framework\b", r"\bstarted as one hypothesis\b.{0,100}\bturned into a system\b"),
        "representation_modes": ["abstract", "concrete", "transfer"],
        "triggering_conditions": ["A general rule needs grounding, or a concrete case may reveal a reusable structure."],
        "possible_code_primitive": "abstraction_application_bridge",
        "known_risks": ["one example treated as sufficient generalization", "abstraction loses domain-specific constraints"],
        "project_fit": ["Comprehension Organ", "Metacognition Organ", "Answer Engine"],
    },
    {
        "key": "reconstructive_understanding_check",
        "name": "Reconstructive understanding check",
        "description": "Restate a model in original plain language, invite correction, and resolve conceptual gaps before polishing artifacts or relying on formalism.",
        "signals": {
            "plain_restatement": (r"\bso to put it plainly\b", r"\bso what you(?:'|’)re saying is\b", r"\bso you(?:'|’)re telling me\b", r"\bone more time\b.{0,100}\bstart[- ](?:to|through)[- ]finish\b"),
            "correction_invitation": (r"\bcorrect me if i(?: am|['’]m) wrong\b", r"\btell me where (?:i am|i(?:'|’)m) wrong\b"),
            "concept_before_artifact": (r"\bsolve the issues before (?:we )?(?:make )?diagrams?\b", r"\bonce we have a concrete understanding\b.{0,100}\bput it on .{0,20}paper\b"),
            "formal_to_plain": (r"\bbreak (?:all )?(?:that|the) math down into a way i can understand\b", r"\bhuman form explanation\b"),
            "coverage_check": (r"\bmake sure we have everything laid out\b", r"\bsee where we(?:'|’)re at and how much more we have left\b"),
            "answer_fit_gap": (r"\bthat still isn(?:'|’)t answering the question\b.{0,140}\bam i missing something\b",),
            "mechanism_reconstruction": (r"\bso the .{0,180}\bwell more like .{0,140}\bwhich .{0,140}\b(?:bound|caus|means|because)\b",),
            "timeline_reconstruction": (r"\blet(?:'|’)?s rewind\b[\s\S]{0,220}\b380k years later\b[\s\S]{0,220}\bcorrect\b",),
            "analogy_limit": (r"\byou can(?:'|’)t think of it that way because\b.{0,120}\bexists? before\b",),
            "comprehension_fit": (r"\b(?:this is all|all of this is|this sounds) gibberish to me\b.{0,160}\babsolute basic level\b",),
            "large_data_recap": (r"\bbefore i move onto\b.{0,120}\blet(?:'|’)?s recap\b.{0,160}\bmapping .{0,80}\bdata\b",),
            "checkpoint_reconstruction": (r"\bgo to this line\b[\s\S]{0,180}\banaly[sz]e every single thing we said to here\b",),
            "pre_draft_coverage": (r"\bmoving into draft phase\b.{0,180}\b(?:missing anything|anything missing)\b",),
            "logic_fit_request": (r"\bnot seeing (?:the )?logic\b.{0,360}\bmake (?:it|that|this) make sense\b",),
            "correct_track_application_gap": (
                r"\bbefore we move on let(?:'|’)?s break down .{0,80}\bsaid (?:the )?right track but i didn(?:'|’)?t apply it the way you think i did\b",
            ),
        },
        "strong_signals": (
            r"\bso to put it plainly\b.{0,220}\bcorrect me if i am wrong\b",
            r"\bsolve the issues before (?:we )?(?:make )?diagrams?\b.{0,220}\bconcrete understanding\b",
            r"\bbreak (?:all )?(?:that|the) math down into a way i can understand\b",
            r"\bone more time\b.{0,100}\bstart[- ](?:to|through)[- ]finish\b",
            r"\bthat still isn(?:'|’)t answering the question\b.{0,140}\bam i missing something\b",
            r"\bso the .{0,180}\bwell more like .{0,140}\bwhich .{0,140}\b(?:bound|caus|means|because)\b",
            r"\blet(?:'|’)?s rewind\b[\s\S]{0,220}\b380k years later\b[\s\S]{0,220}\bcorrect\b",
            r"\byou can(?:'|’)t think of it that way because\b.{0,120}\bexists? before\b",
            r"\b(?:this is all|all of this is|this sounds) gibberish to me\b.{0,160}\babsolute basic level\b",
            r"\bbefore i move onto\b.{0,120}\blet(?:'|’)?s recap\b.{0,160}\bmapping .{0,80}\bdata\b",
            r"\bgo to this line\b[\s\S]{0,180}\banaly[sz]e every single thing we said to here\b",
            r"\bmoving into draft phase\b.{0,180}\b(?:missing anything|anything missing)\b",
            r"\bso you(?:'|’)re telling me\b.{0,220}\bcorrect me if i(?: am|'|’)m wrong\b.{0,360}\b(?:not seeing (?:the )?logic|make (?:it|that|this) make sense)\b",
            r"\bbefore we move on let(?:'|’)?s break down .{0,80}\bsaid (?:the )?right track but i didn(?:'|’)?t apply it the way you think i did\b",
        ),
        "representation_modes": ["reconstructive", "plain-language", "comprehension-first"],
        "triggering_conditions": ["A model sounds plausible or formally complete, but transferable understanding has not yet been demonstrated."],
        "possible_code_primitive": "reconstruct_explain_and_correct_cycle",
        "known_risks": ["plain wording is mistaken for complete understanding", "formal detail is discarded rather than translated", "artifact polish hides unresolved conceptual gaps"],
        "project_fit": ["Comprehension Organ", "Metacognition Organ", "Answer Engine", "Cocoon teaching"],
    },
    {
        "key": "prerequisite_ordered_rule_transfer",
        "name": "Prerequisite-ordered rule transfer",
        "description": "Keep learning in prerequisite order, use examples to reconstruct a rule, then test whether the rule transfers to a neighboring operation or mixed case.",
        "signals": {
            "prerequisite_boundary": (r"\bwe only covered\b", r"\bwe have not covered\b", r"\bneed to go in order\b"),
            "reset_to_foundation": (r"\blet(?:'|’)?s back up\b", r"\bgo back to (?:the )?(?:previous|basic|first)\b"),
            "example_practice": (r"\bexample problems? to solve\b", r"\bgive me (?:a )?mix of both\b", r"\bmixed practice\b"),
            "rule_reconstruction": (r"\bso essentially\b.{0,160}\b(?:rule|inverse|means)\b", r"\bto solve .{0,120}\bdo the inverse\b"),
            "near_transfer": (r"\bare the rules? the same .{0,160}\b(?:multiplication|division|another|other)\b", r"\bdoes (?:the|that) same rule apply\b"),
            "section_by_section": (r"\bbreak it up section by section\b.{0,220}\b(?:everything at (?:me|once)|terminology)\b.{0,220}\bcomprehend\b",),
            "learning_while_building": (r"\bbest way\b.{0,160}\bteach me as we go\b.{0,120}\bnever overwhelmed\b",),
            "foundation_before_extension": (r"\bload the barebones (?:copy|version)\b.{0,160}\b(?:errors?|runs?)\b.{0,100}\b(?:fix|clean)\b.{0,120}\bthen add\b",),
            "learning_over_answer_outsourcing": (
                r"\byou are correct absolutely on the math\b[\s\S]{0,180}\bi could ask you but that(?:'|’)s cheating and i won(?:'|’)t learn\b",
            ),
        },
        "strong_signals": (
            r"\blet(?:'|’)?s back up\b.{0,180}\bwe only covered\b.{0,180}\bgo in order\b",
            r"\bso essentially\b.{0,180}\b(?:inverse|rule|means)\b",
            r"\bare the rules? the same .{0,160}\bdo the inverse\b",
            r"\bbreak it up section by section\b.{0,220}\b(?:everything at (?:me|once)|terminology)\b.{0,220}\bcomprehend\b",
            r"\bbest way\b.{0,160}\bteach me as we go\b.{0,120}\bnever overwhelmed\b",
            r"\bload the barebones (?:copy|version)\b.{0,160}\b(?:errors?|runs?)\b.{0,100}\b(?:fix|clean)\b.{0,120}\bthen add\b",
            r"\byou are correct absolutely on the math\b[\s\S]{0,180}\bi could ask you but that(?:'|’)s cheating and i won(?:'|’)t learn\b",
        ),
        "representation_modes": ["sequential", "example-to-rule", "transfer"],
        "triggering_conditions": ["A new concept depends on an earlier operation, or a reconstructed rule may apply to a neighboring case."],
        "possible_code_primitive": "prerequisite_rule_transfer_cycle",
        "known_risks": ["rigid ordering blocks useful exploration", "a near rule is overgeneralized", "correct answers are mistaken for conceptual understanding"],
        "project_fit": ["Comprehension Organ", "Metacognition Organ", "Cocoon teaching"],
    },
    {
        "key": "pragmatic_multi_cue_screening",
        "name": "Pragmatic multi-cue screening",
        "description": "Notice wording, implication, delivery, and inconsistency as provisional cues that something deserves closer evidence checking.",
        "signals": {
            "implicit_meaning": (r"\breading between the lines\b", r"\bimplied (?:meaning|intent)\b"),
            "delivery_cue": (r"\btone of voice\b", r"\bway (?:a person|they|someone) (?:talks?|speaks?)\b"),
            "plausibility_instinct": (r"\bnatural instinct .{0,100}\bspotting nonsense\b", r"\bsomething (?:sounds|feels) off\b"),
            "provisionality": (r"\bsometimes you can tell\b", r"\bit(?:'|’)?s rare\b", r"\bsomething to think about\b"),
            "context_acquisition_before_participation": (
                r"\bi observe conversationally\b[\s\S]{0,100}\bask questions\b[\s\S]{0,120}\bmap the group dynamic\b[\s\S]{0,140}\blearn the work\b[\s\S]{0,120}\bthen i dive in\b",
            ),
            "parallel_social_and_task_mapping": (
                r"\bi map the social structure\b[\s\S]{0,220}\bpay attention to what i(?:'|’| a)m supposed to do\b[\s\S]{0,120}\bboth .{0,30} at once\b",
            ),
        },
        "strong_signals": (
            r"\breading between the lines\b.{0,180}\btone of voice\b",
            r"\btone of voice\b.{0,160}\bway (?:a person|they|someone) (?:talks?|speaks?)\b",
            r"\bnatural instinct .{0,100}\bspotting nonsense\b",
            r"\bi observe conversationally\b[\s\S]{0,100}\bask questions\b[\s\S]{0,120}\bmap the group dynamic\b[\s\S]{0,140}\blearn the work\b[\s\S]{0,120}\bthen i dive in\b",
            r"\bi map the social structure\b[\s\S]{0,220}\bpay attention to what i(?:'|’| a)m supposed to do\b[\s\S]{0,120}\bboth .{0,30} at once\b",
        ),
        "representation_modes": ["pragmatic", "social cue", "provisional screening"],
        "triggering_conditions": ["A statement's content or delivery produces a plausibility concern that should be checked rather than accepted as proof."],
        "possible_code_primitive": "provisional_pragmatic_cue_observer",
        "known_risks": ["tone mistaken for truth", "cultural or neurotype bias", "confidence and fluency mistaken for credibility", "intuition becomes a verdict instead of a prompt to verify"],
        "project_fit": ["Metacognition Organ", "pragmatic dialogue", "source-backed research"],
    },
    {
        "key": "dependency_aware_premise_checking",
        "name": "Dependency-aware premise checking",
        "description": "Verify a premise before relying on it in the next dependent question or design decision.",
        "signals": {
            "premise_doubt": (r"\bi didn(?:'|’)?t think (?:it|this|that) was\b", r"\bif this isn(?:'|’)?t\b"),
            "verification_gate": (r"\bneeded to make sure before\b", r"\bverify .{0,100}\bbefore (?:asking|using|continuing|building)\b"),
            "dependent_step": (r"\bbefore asking this question\b", r"\bwhat (?:am i|are we) going to use to\b", r"\bnext question\b"),
        },
        "strong_signals": (
            r"\bi didn(?:'|’)?t think (?:it|this|that) was .{0,160}\bneeded to make sure before\b",
            r"\bneeded to make sure before asking this question\b",
        ),
        "representation_modes": ["dependency", "verification", "sequential reasoning"],
        "triggering_conditions": ["A downstream question or design step depends materially on whether an earlier premise is true."],
        "possible_code_primitive": "reasoning_dependency_verification_gate",
        "known_risks": ["checking trivial premises adds friction", "the gate verifies the wrong assumption", "one check is treated as permanent proof"],
        "project_fit": ["Metacognition Organ", "Answer Engine", "engineering workbench"],
    },
    {
        "key": "uncertainty_and_limit_detection",
        "name": "Uncertainty and missing-variable detection",
        "description": "Recognize provisional knowledge, missing context, scope limits, and variables that could change the answer.",
        "signals": {
            "uncertainty": (r"\buncertain(?:ty)?\b", r"\bnot sure\b", r"\bnot certain\b", r"\bprovisional\b"),
            "missing_context": (r"\bmissing (?:context|information|evidence|variable|something|piece|mechanism)\b", r"\bdon't have enough\b", r"\bdo not have enough\b"),
            "limits": (r"\blimit(?:s|ation)?\b", r"\b(?:within|outside|beyond) (?:the|this|its) scope\b", r"\bscope (?:of|boundary|limit|condition)\b", r"\bnarrow(?:ed|ing)? (?:the )?scope\b", r"\bwhere (?:it|this) (?:breaks|fails|doesn't apply)\b"),
            "confidence": (r"\bconfidence\b", r"\bhow sure\b", r"\bwhat would change (?:the|my) answer\b"),
            "observability_boundary": (r"\bno observable evidence\b", r"\bwe (?:can|could) never (?:see|observe)\b", r"\bwe will never know\b"),
            "proof_boundary": (r"\bnever be proven until\b", r"\bcannot be (?:proved|proven|tested)\b", r"\bcan(?:not|'t) currently (?:prove|test|observe)\b"),
            "tool_limit": (r"\blimitations? of (?:universe sandbox|the simulation|the simulator|the tool|the model)\b", r"\b(?:simulation|simulator|tool|model) limitations?\b"),
            "verification_uncertainty": (r"\bunsure if (?:this|that|it) is verified\b", r"\bnot sure (?:whether|if) .{0,100}\bverified\b"),
            "physical_boundary": (r"\b(?:doesn(?:'|’)t|does not|will never) have enough (?:mass|energy)\b", r"\bnot enough (?:mass|energy)\b"),
            "provisional_revision": (r"\bnew idea\b.{0,100}\bstill need to think\b", r"\brevised .{0,80}\bstill provisional\b"),
            "boundary_stretch": (r"\bnot (?:quite )?sure about (?:the )?(?:claim|idea|model|mechanism|rocks?|definition|criterion|category).{0,120}\b(?:may|might|could) be a stretch\b",),
            "simulation_setup_uncertainty": (r"\bdon(?:'|’)?t wanna run the sims?\b.{0,180}\bsetting it right\b",),
            "evidence_gap_hold": (r"\b(?:need to|should|have to) wait for more evidence\b.{0,140}\bmissing something\b",),
            "felt_fit_not_correctness": (
                r"\bjust because i think of something and it sounds right doesn(?:'|’)t mean it is\b",
            ),
        },
        "strong_signals": (r"\bmissing variables?\b", r"\brecognize (?:the )?limits\b", r"\bremember the limitations? of\b", r"\bunsure if (?:this|that|it) is verified\b", r"\bno observable evidence\b.{0,160}\bnever be proven until\b", r"\bwe (?:can|could) never see .{0,100}\bwe will never know\b", r"\b(?:doesn(?:'|’)t|does not|will never) have enough (?:mass|energy)\b", r"\bnew idea\b.{0,100}\bstill need to think\b", r"\bnot (?:quite )?sure about (?:the )?(?:claim|idea|model|mechanism|rocks?|definition|criterion|category).{0,120}\b(?:may|might|could) be a stretch\b", r"\bhighly possible\b.{0,100}\bnot certain\b", r"\bdon(?:'|’)?t wanna run the sims?\b.{0,180}\bsetting it right\b", r"\bjust because i think of something and it sounds right doesn(?:'|’)t mean it is\b"),
        "representation_modes": ["epistemic", "scope", "confidence"],
        "triggering_conditions": ["The answer depends on unavailable context, weak evidence, or an uncertain scope boundary."],
        "possible_code_primitive": "uncertainty_scope_monitor",
        "known_risks": ["uncertainty becomes generic disclaimer language", "ordinary answer withheld despite sufficient bounded evidence"],
        "project_fit": ["Metacognition Organ", "Answer Engine", "confidence vector"],
    },
    {
        "key": "sufficiency_and_stopping",
        "name": "Answer sufficiency and stopping",
        "description": "Decide whether understanding or evidence is sufficient to answer, or whether the conclusion should remain on hold.",
        "signals": {
            "sufficiency": (r"\bgood enough\b", r"\bsufficient (?:evidence|understanding|answer|confidence)\b", r"\benough to answer\b"),
            "stopping": (r"\bstopping rule\b", r"\bwhen to stop\b", r"\bstop (?:reasoning|analyzing|recursion)\b"),
            "answer_decision": (r"\bdecide (?:whether|when) to answer\b", r"\bbest current answer\b"),
            "value_of_more": (r"\bfurther (?:analysis|reasoning)\b.*\b(?:worth|useful|change)\b", r"\bwhat would change the answer\b"),
            "low_value_route": (r"\b(?:could|can) plot (?:that|the) data\b.{0,180}\bchances? (?:are|is) (?:so )?slim\b.{0,120}\bwaste of time\b", r"\bnot worth (?:the|our|my) time\b"),
            "provisional_completion": (r"\bi think we (?:did it|have it)\b.{0,160}\bplausible (?:explanation|answer|model)\b", r"\bplausible explanation .{0,80}\bthat works\b"),
            "upgrade_diminishing_return": (r"\bkeep putting upgrades on (?:this|it)\b.{0,120}\bnever get anywhere\b",),
            "provisional_stage_gate": (r"\bfinish(?: up)?\b.{0,140}\bthink we(?:'|’)?re done for now\b.{0,140}\bwrite (?:the )?(?:paper )?first draft\b",),
            "insufficient_evidence_hold": (r"\b(?:need to|should|have to) wait for more evidence\b.{0,140}\bmissing something\b",),
            "unbounded_addition_loop": (
                r"\bissue is it(?:'|’)s never good enough\b[\s\S]{0,100}\bneed to keep adding\b[\s\S]{0,260}\bbefore you(?:'|’)?ve gotten the second word out\b",
            ),
        },
        "strong_signals": (r"\bwhen (?:understanding|evidence) is sufficient to answer\b", r"\bstop recursion\b", r"\b(?:could|can) plot (?:that|the) data\b.{0,180}\bchances? (?:are|is) (?:so )?slim\b.{0,120}\bwaste of time\b", r"\bi think we (?:did it|have it)\b.{0,160}\bplausible (?:explanation|answer|model)\b", r"\bkeep putting upgrades on (?:this|it)\b.{0,120}\bnever get anywhere\b", r"\bfinish(?: up)?\b.{0,140}\bthink we(?:'|’)?re done for now\b.{0,140}\bwrite (?:the )?(?:paper )?first draft\b"),
        "representation_modes": ["decision", "confidence", "stopping"],
        "triggering_conditions": ["A usable answer is available and additional analysis has diminishing expected value."],
        "possible_code_primitive": "bounded_reasoning_stopping_rule",
        "known_risks": ["premature closure", "analysis recursion presented as rigor"],
        "project_fit": ["Answer Engine", "Metacognition Organ", "intelligenceOS"],
    },
    {
        "key": "capacity_aware_pause_and_resume",
        "name": "Capacity-aware pause and resume",
        "description": "Notice when continued analysis is no longer productive, pause without treating the pause as failure, and preserve a clear route for later continuation.",
        "signals": {
            "cognitive_load": (r"\bbrain hurts? (?:from|thinking)\b", r"\bthinking too hard\b", r"\bmentally (?:tired|spent|overloaded)\b"),
            "pause": (r"\bhave to stop for now\b", r"\bpause (?:this|here|for now)\b", r"\bcome back to (?:it|this) later\b"),
            "continuation_marker": (r"\b(?:archive|save) .{0,80}\b(?:continue|return|soon|later)\b", r"\bspeak to you soon\b", r"\bpick (?:it|this) back up\b"),
            "degradation_awareness": (r"\bthis is how you know i(?:'|’)m tired\b",),
            "intentional_rest_stop": (r"\bi(?:'|’)m going to bed\b",),
            "bounded_learning_break": (r"\btake a break from .{0,80}\bcome back tomorrow\b", r"\bneed to take a break and absorb this\b"),
            "attempted_pause_under_idea_acceleration": (
                r"\bgonna stop here and gather (?:my )?thoughts\b[\s\S]{0,100}\bmy mind(?:'|’)?s going nuts\b",
            ),
        },
        "strong_signals": (
            r"\bbrain hurts? .{0,100}\bthinking too hard\b.{0,100}\bstop for now\b",
            r"\bthinking too hard\b.{0,120}\b(?:pause|stop for now|come back)\b",
            r"\bthis is how you know i(?:'|’)m tired\b.{0,100}\bi(?:'|’)m going to bed\b",
            r"\btake a break from .{0,80}\bcome back tomorrow\b",
            r"\bneed to take a break and absorb this\b",
            r"\bgonna stop here and gather (?:my )?thoughts\b[\s\S]{0,100}\bmy mind(?:'|’)?s going nuts\b",
        ),
        "representation_modes": ["resource-aware", "stopping", "continuity"],
        "triggering_conditions": ["Continuing the current reasoning pass would reduce clarity or usefulness because available cognitive capacity is temporarily spent."],
        "possible_code_primitive": "capacity_aware_pause_checkpoint",
        "known_risks": ["ordinary difficulty mistaken for overload", "premature avoidance of a solvable problem", "a pause loses context if no continuation checkpoint is preserved"],
        "project_fit": ["Metacognition Organ", "Answer Engine", "graceful fall"],
    },
    {
        "key": "scope_narrowing_and_focus_control",
        "name": "Scope narrowing and focus control",
        "description": "Notice when too many live ideas are competing, choose one bounded focus, and defer the rest without discarding them.",
        "signals": {
            "branch_overload": (r"\bthinking of (?:lots|too many|many)(?: of)? (?:things|ideas)\b", r"\btoo many (?:ideas|directions|threads) at once\b"),
            "narrowing": (r"\bneed to hone in on one thing\b", r"\bnarrow (?:it|this|the scope) down\b", r"\bpick one (?:thing|idea|direction|thread)\b"),
            "serial_focus": (r"\bone thing at a time\b", r"\btake (?:them|the ideas|the questions) one at a time\b"),
            "miscommunication_narrowing": (r"\bdon(?:'|’)?t understand where the miscommunication is coming from\b.{0,100}\bnarrow this down\b",),
            "branch_inventory": (r"\bmy mind is splitting\s+(?:three|3)\s+ways\b.{0,140}\bgonna lay them out first\b",),
            "separate_candidate": (r"\bsave (?:this|that|it) as a separate idea\b",),
            "dependency_boundary": (r"\b(?:keep|should stay) .{0,80}\bseparate unless .{0,40}\btruly (?:a )?key piece\b",),
            "framework_layer_boundary": (r"\bidk if (?:it|this|that) directly ties to .{0,100}\bitself\b.{0,140}\b(?:in|within) the framework itself\b",),
            "concept_separation": (r"\bthose two are completely separate (?:ideas|models|hypotheses|frameworks)\b",),
            "strict_single_subject_focus": (r"\bdrop .{0,100}\bfor now\b.{0,60}\bstrictly .{0,100}\bexplain (?:it|that|this) again\b",),
        },
        "strong_signals": (
            r"\bthinking of (?:lots|too many|many)(?: of)? (?:things|ideas)\b.{0,160}\bhone in on one thing at a time\b",
            r"\btoo many (?:ideas|directions|threads) at once\b.{0,120}\b(?:pick|focus|narrow)\b",
            r"\bdon(?:'|’)?t understand where the miscommunication is coming from\b.{0,100}\bnarrow this down\b",
            r"\bmy mind is splitting\s+(?:three|3)\s+ways\b.{0,140}\bgonna lay them out first\b",
            r"\bsave (?:this|that|it) as a separate idea\b",
            r"\b(?:keep|should stay) .{0,80}\bseparate unless .{0,40}\btruly (?:a )?key piece\b",
            r"\bidk if (?:it|this|that) directly ties to .{0,100}\bitself\b.{0,140}\b(?:in|within) the framework itself\b",
            r"\bthose two are completely separate (?:ideas|models|hypotheses|frameworks)\b",
            r"\bdrop .{0,100}\bfor now\b.{0,60}\bstrictly .{0,100}\bexplain (?:it|that|this) again\b",
        ),
        "representation_modes": ["scope", "attention routing", "serial planning"],
        "triggering_conditions": ["Multiple active directions are preventing a useful next step."],
        "possible_code_primitive": "bounded_focus_selector",
        "known_risks": ["valuable cross-connections are prematurely deferred", "the chosen focus is arbitrary", "deferred branches are lost rather than checkpointed"],
        "project_fit": ["Metacognition Organ", "Answer Engine", "planning"],
    },
    {
        "key": "adaptive_method_selection",
        "name": "Adaptive cognitive-method selection",
        "description": "Choose, combine, and switch reasoning representations according to the task and current fit.",
        "signals": {
            "method_language": (r"\bthinking styles?\b", r"\bway(?:s)? of thinking\b", r"\breasoning method\b", r"\bapproach(?:es)?\b"),
            "task_fit": (r"\bdepend(?:s|ent) on the task\b", r"\bfor different tasks?\b", r"\bwhat (?:the|this) task needs\b", r"\bdifferent situations? require different approaches\b"),
            "switching": (r"\bswitch (?:between|methods|modes|approaches|a lot)\b", r"\bchange (?:methods|modes|approaches)\b", r"\btry another (?:way|approach|method)\b", r"\bif that does not work i use\b", r"\bif (?:that|it) (?:doesn(?:'|’)?t|does not) work .{0,100}\b(?:use|try|switch)\b"),
            "combination": (r"\btwo at once\b", r"\bcombine (?:methods|modes|approaches)\b", r"\b(?:visual|patterns?|words?|systems?)\b.{0,100}\b(?:then|and)\b.{0,100}\b(?:visual|patterns?|words?|systems?)\b", r"\b(?:logic|knowledge)\b.{0,120}\bpattern recognition\b.{0,120}\bintuition\b", r"\brely on .{0,160}\b(?:logic|patterns?|data|intuition)\b"),
            "uncertainty_response": (r"\bwhen i am (?:lost|unsure|uncertain) i rely on\b", r"\bwhen (?:lost|unsure|uncertain) .{0,120}\b(?:switch|use|try|rely)\b"),
        },
        "strong_signals": (r"\butili[sz]e thinking styles? for different tasks?\b", r"\bswitch thinking styles?\b", r"\bmulti[- ]modal thinking system\b", r"\bswitch modes? depending on (?:the )?(?:context|problem|task)\b", r"\bdifferent situations? require different approaches\b", r"\bwhen i am (?:lost|unsure|uncertain) i rely on .{0,180}\b(?:logic|patterns?|scientific data|intuition)\b"),
        "representation_modes": ["metacognitive", "routing", "multimodal"],
        "triggering_conditions": ["The current method does not fit the problem, or two representations offer complementary checks."],
        "possible_code_primitive": "cognitive_method_router",
        "known_risks": ["mode switching without finishing a useful pass", "router confidence confused with answer correctness"],
        "project_fit": ["Metacognition Organ", "intelligenceOS", "Answer Engine"],
    },
)


BEHAVIOR_PATTERNS = {
    "trigger": (r"\bwhen\b", r"\bif\b", r"\bdepending on\b", r"\bneed to\b", r"\bfor (?:this|that|different) task"),
    "correction": (r"\bi was wrong\b", r"\bcorrect(?:ion|ed|ing)?\b", r"\bmistake\b", r"\brevis(?:e|ed|ion)\b", r"\breopen\b", r"\bscrap (?:the|that|this) .{0,80}\bidea\b", r"\bdoes(?:n't| not) (?:fit|look right|add up)\b", r"\bback to the drawing (?:board|bored)\b", r"\bofficially moved on from (?:tng|(?:the|my) (?:idea|model|hypothesis|explanation|claim))\b", r"\brip tng\b", r"\bnot quite\b.{0,160}\bwhat you(?:'|’)re describing (?:is|was) more like (?:an? )?(?:eco[- ]?system|model|system|category|definition|criterion|mechanism|explanation)\b", r"\bidk what i was thinking\b.{0,100}\byou(?:'|’)re right\b.{0,120}\b(?:tired|going to bed)\b", r"\bi like when you push back and tell me .{0,80}\byou(?:'|’)re wrong\b.{0,100}\bwhy\b"),
    "stopping": (r"\bgood enough\b", r"\bsufficient\b", r"\benough to answer\b", r"\bstop(?:ping)?\b", r"\bwhat would change (?:the|my) answer\b", r"\bthis is how you know i(?:'|’)m tired\b.{0,100}\bi(?:'|’)m going to bed\b"),
    "switching": (r"\bswitch\b", r"\banother (?:way|approach|method)\b", r"\btwo at once\b", r"\bthen (?:assess|check|translate|use)\b"),
    "failure_or_weakness": (
        r"\bissue is it(?:'|’)s never good enough\b[\s\S]{0,100}\bneed to keep adding\b[\s\S]{0,260}\bbefore you(?:'|’)?ve gotten the second word out\b",
        r"\bgonna stop here and gather (?:my )?thoughts\b[\s\S]{0,100}\bmy mind(?:'|’)?s going nuts\b",
        r"\bmath can(?:'|’)t be wrong\b[\s\S]{0,120}\bpython wouldn(?:'|’)t have given me data\b[\s\S]{0,100}\bit would(?:'|’)ve yelled\b",
        r"\bi don(?:'|’)t know how i know this stuff\b[\s\S]{0,220}\bcan just [“\"]?feel[”\"]? if it(?:'|’)s going to work or the physics behind it\b",
    ),
}

METHOD_PREFILTER_TERMS = {
    "structural_pattern_mapping": ("pattern", "analogy", "cross-domain", "cross domain", "same structure", "mytholog", "dependent on", "just like"),
    "visual_spatial_modeling": ("visual", "spatial", "mental image", "imagery", "diagram", "picture it", "i can see it now", "create these narratives", "in my head"),
    "cross_representation_translation": ("translat", "words", "verbal", "hard to explain", "hard to describe", "fun way to teach", "to explain", "make it like"),
    "systems_consequence_simulation": ("system", "simulat", "feedback", "consequence", "downstream", "what would happen", "so what if i remove", "so what if i removed", "seems to be forming", "seems to form", "created new", "early formation", "expand the simulation", "parameters to test", "wanted to test my", "went extinct", "over time", "erode away", "due to time", "once released", "weaponize", "weaponise"),
    "constraint_driven_design_iteration": ("starting point", "first step", "mission objective", "mission parameter", "mission profile", "mission requirement", "materials needed", "performance metric", "general public", "without fuel", "use of fuel", "long period", "trade-off", "tradeoff", "completely different design", "hybrid approach", "secondary system", "secondary propulsion", "alternative design", "alternative architecture", "alternate propulsion", "let's expand", "lets expand", "let’s expand", "let's add", "lets add", "let’s add", "let's implement", "lets implement", "let’s implement", "work on this first", "start here", "begin at phase", "cost to launch", "what's stopping us", "what’s stopping us", "work better", "lock in", "schematic", "tweak", "work on something more important", "connects everything", "personal usage", "personal use", "leave the military", "do right now", "real goal", "long-term goal", "switching system", "coordinate", "subsystem", "propulsion mode", "maximum efficiency", "3d printer", "housing mechanism", "metal prong"),
    "candidate_model_construction": ("hypothes", "candidate model", "provisional", "what if", "maybe", "missing something", "missing piece", "wrong way", "bigger equation", "mechanism", "create the conditions", "has to be a type of", "has to be a kind of", "has to be a form of", "answer to the", "paradox"),
    "baseline_preserving_model_extension": ("don't disagree", "dont disagree", "don’t disagree", "like to add to it", "add to the model", "add to that model", "add to this model", "add to the theory", "build on", "what caused", "doesn't explain", "doesnt explain", "doesn’t explain", "absolute origin", "nothing changes except", "preserv"),
    "provisional_naming_and_scope_control": ("working name", "working label", "call it", "nice ring", "hypothes", "not a theory", "change name", "name change", "rename", "instead of", "from now on", "not gravity", "moved on from", "map what's being missed", "map what’s being missed"),
    "evidence_tool_operationalization": ("what information", "what data", "what inputs", "what else am i missing", "still missing", "run the math", "run the numbers", "run some numbers", "run some real numbers", "do the math", "how do i test", "how the hell do i test", "one by one", "1 by one", "more files", "then we plot", "quantif", "test this", "run the", "did not send", "unseen", "template", "look at the facts", "set this up", "source data", "input data", "spectrum data", "measurement data", "data set", "data table", "data file", "tables and", "graphs", "analysis pipeline", "preliminary result", "criterion", "validation", "python code", "script", "tool layer", "tools layer", "tool registry", "structured interface", "structured result", "parameters to test", "what parameters", "better", "simulate", "universe sandbox", "see what sticks out", "run simulations", "predict outcomes", ".py", ".bat"),
    "multiple_working_hypotheses": ("hypothes", "alternative explanation", "competing", "more than one explanation", "multiple models", "two frameworks", "two new ideas", "first possibility", "second possibility", "three ways", "separate idea", "work simultaneously", "working simultaneously"),
    "dialectical_third_model_synthesis": ("embrace the paradox", "hold the tension", "hold both", "third narrative", "third model", "third option", "third explanation", "beyond the binary", "redefine the binary", "redefines the binary", "false binary", "scientific facts to build on", "from the facts", "from the evidence", "from the constraints"),
    "observation_interpretation_separation": ("observ", "interpret", "infer", "what we know", "what i know", "simulation", "game", "tool", "named", "calling", "labeled", "labelled", "don't really exist", "don’t really exist", "early formation", "seems as if", "prove anything", "proof", "data safe", "skew the picture"),
    "source_context_hypothesis_audit": ("archimedes sphere", "entire myth", "whole myth", "full myth", "entire source", "whole source", "full source", "word for word", "read it fully", "what they see", "what they saw", "what they observed", "data concept myth result", "idea-data-solution", "idea→data→solution", "real data", "physically impossible", "look elsewhere", "3 myths for each culture", "three myths for each culture", "different culture", "for each culture", "for each civ", "1=interesting", "1 = interesting", "best records", "source quality", "protect the framework", "open for expansion", "if i'm wrong about something tell me", "if i’m wrong about something tell me", "99.9%", "not 100%"),
    "independent_constraint_checking": ("constraint", "verif", "evidence", "falsif", "counterexample", "cross-check", "run the math", "run the", "did not send", "unseen", "test my hypothesis", "test my theory", "test it with", "biased", "peek around", "match this pattern", "closer objects", "nearby objects", "model more", "repeatable in multiple circumstances", "1=interesting", "1 = interesting", "3=pattern", "3 = pattern", "disprov", "throw rocks", "wanted to test my", "how accurate", "reliable way", "measurement reliability", "all the variables", "many variables", "account for", "how can we say", "never be proven", "other facts", "just blame"),
    "correction_and_reopening": ("correct", "wrong", "reopen", "revisit", "revise", "mistake", "scrap", "overstretch", "overstate", "let's say", "let’s say", "enough mass", "enough energy", "work better", "scientific method", "change the test", "more problems than", "but keep", "doesn't look right", "does not look right", "back to the drawing", "backtrack", "back track", "restart", "reassess", "except", "other than that", "that part", "the rest", "otherwise", "moved on from", "rip tng", "vain battle", "not quite", "idk what i was thinking", "you're right", "you’re right", "push back and tell me", "like when you check me", "used as a visual", "separate events", "completely separate ideas", "completely separate models", "completely separate hypotheses", "completely separate frameworks", "different directions now", "disconnect was", "you said that if i add", "accepted idea", "holes and contradictions", "if i'm wrong about something", "if i’m wrong about something", "getting mixed up", "forget what i just said", "correct times"),
    "abstract_concrete_transfer": ("abstract", "concrete", "generaliz", "different example", "apply it", "apply this", "was the test", "now we have a framework", "started as one hypothesis", "turned into a system"),
    "reconstructive_understanding_check": ("put it plainly", "what you're saying", "what you’re saying", "you're telling me", "you’re telling me", "correct me if", "tell me where", "before diagrams", "concrete understanding", "math down", "way i can understand", "human form explanation", "everything laid out", "how much more", "one more time", "start-finish", "start to finish", "start through finish", "isn't answering the question", "isn’t answering the question", "not seeing logic", "not seeing the logic", "make it make sense", "am i missing something", "well more like", "let's rewind", "let’s rewind", "380k years later", "can't think of it that way", "can’t think of it that way", "gibberish to me", "absolute basic level", "before i move onto", "let's recap", "let’s recap", "mapping massive", "go to this line", "every single thing we said", "moving into draft phase", "missing anything"),
    "prerequisite_ordered_rule_transfer": ("only covered", "have not covered", "go in order", "back up", "go back to", "example problem", "mix of both", "mixed practice", "so essentially", "inverse", "rules the same", "same rule apply", "section by section", "teach me as we go", "never overwhelmed", "barebones copy", "barebones version", "then add"),
    "pragmatic_multi_cue_screening": ("reading between the lines", "implied meaning", "implied intent", "tone of voice", "way a person talks", "way they talk", "way someone talks", "way a person speaks", "way they speak", "way someone speaks", "natural instinct", "spotting nonsense", "sounds off", "feels off", "sometimes you can tell", "it's rare", "it’s rare", "something to think about", "observe conversationally", "map the social structure"),
    "dependency_aware_premise_checking": ("didn't think", "didn’t think", "if this isn't", "if this isn’t", "needed to make sure", "verify", "before asking", "before using", "before continuing", "before building", "next question", "what am i going to use", "what are we going to use"),
    "uncertainty_and_limit_detection": ("uncertain", "not sure", "not quite sure", "not certain", "unsure", "verified", "new idea", "still need to think", "still provisional", "missing context", "missing evidence", "missing something", "missing piece", "confidence", "limit", "scope", "enough mass", "enough energy", "no observable evidence", "never see", "never observe", "never know", "never be proven", "cannot be proved", "cannot be proven", "cannot be tested", "can't currently", "cant currently", "universe sandbox", "setting it right", "simulation limitations", "simulator limitations", "tool limitations", "model limitations"),
    "sufficiency_and_stopping": ("good enough", "sufficient", "stopping", "when to stop", "enough to answer", "best current answer", "wait for more evidence", "waste of time", "not worth", "i think we did it", "i think we have it", "plausible explanation", "putting upgrades", "never get anywhere", "done for now", "first draft"),
    "capacity_aware_pause_and_resume": ("brain hurt", "thinking too hard", "mentally tired", "mentally spent", "mentally overloaded", "stop for now", "pause this", "pause here", "pause for now", "take a break", "absorb this", "come back", "come back tomorrow", "speak to you soon", "pick it back up", "pick this back up", "this is how you know i'm tired", "this is how you know i’m tired", "i'm going to bed", "i’m going to bed"),
    "scope_narrowing_and_focus_control": ("thinking of lots", "thinking of too many", "thinking of many", "too many ideas", "too many directions", "too many threads", "mind is splitting", "lay them out first", "hone in on one thing", "narrow it down", "narrow this down", "narrow the scope", "pick one", "one thing at a time", "one at a time", "separate idea", "completely separate ideas", "completely separate models", "completely separate hypotheses", "completely separate frameworks", "keep", "separate unless", "directly ties", "framework itself"),
    "adaptive_method_selection": ("thinking style", "approach", "depending on the task", "different task", "different situation", "switch", "mode", "two at once", "combine", "if that does not work", "if it doesn't work", "if it doesn’t work", "if it does not work", "pattern recognition", "intuition", "rely on", "when i am lost", "when i am unsure", "when i am uncertain"),
}

COGNITIVE_PREFILTER_TERMS = tuple(sorted({term for terms in METHOD_PREFILTER_TERMS.values() for term in terms}))

ASSISTANT_METACOGNITIVE_OBSERVATION_TERMS = (
    "you think",
    "your thinking",
    "your mind",
    "your reasoning",
    "your approach",
    "you use",
    "you switch",
    "you notice",
    "you connect",
    "your instinct",
    "your pattern",
    "what you're doing",
    "what you are doing",
    "how you process",
    "cognitive",
    "reasoning method",
    "thinking mode",
)

DIRECT_SELF_REPORT_PATTERNS = (
    r"\bi (?:use|do not use|don['’]t use|rely|switch|visuali[sz]e|notice|recognize|connect|reason|process|assess|compare|reopen|verify|test)\b",
    r"\bi (?:observe conversationally|map (?:the )?(?:social structure|group dynamic))\b",
    r"\bi like when .{0,100}\b(?:push back|correct me|tell me .{0,40}\bwrong)\b",
    r"\bi think in\b",
    r"\bmy (?:mind|thinking|thought process|way of thinking)\b",
    r"\bfor me\b.*\b(?:think|reason|visual|pattern|model|understand)\b",
)

EXPLICIT_ENDORSEMENT_PATTERNS = (
    r"\bmy mind so far\b",
    r"\bi (?:even )?added my flaws\b",
    r"\bthis (?:does|doesn't|does not) (?:fit|describe) (?:me|how i think)\b",
    r"\bthis is (?:how|close to how) i think\b",
)

SUMMARY_OR_PASTE_PATTERNS = (
    r"\byour core thinking model\b",
    r"\bmulti[- ]modal thinking system\b",
    r"\bthe real you\b",
    r"\bverbal / logical mode\b",
    r"\bvisual simulation mode\b",
    r"\blast but (?:not|note) least\b[\s\S]{0,120}\bthe continuum thread\b[\s\S]{0,120}\bthe black hole genesis\b",
    r"\bthis is fascinating\b.{0,20}\bnow enter the bootes void\b[\s\S]{0,120}\bthe black hole genesis\b",
)

ARTIFACT_PATTERNS = (
    r"\bfrom [a-zA-Z0-9_.]+ import\b",
    r"\bclass [A-Za-z_][A-Za-z0-9_]*[:(]",
    r"\bdef [A-Za-z_][A-Za-z0-9_]*\(",
    r"\b(?:system|architecture|regression|observation) (?:summary|report|overview)\b",
    r"\b1\.\s+[A-Z][^\n]{3,80}\b.*\b2\.\s+[A-Z]",
)

PERSON_MODEL_PATTERNS = (
    r"\bbased on (?:your|the) data (?:on|about) (?:me|you)\b",
    r"\bmodel me as (?:a )?person\b",
    r"\bmy brain is different because of evolution\b",
    r"\bmy thinking and reasoning comes from an evolutionary leap\b",
    r"\bwhere does? my mind differ\b",
    r"\bthe way you handle information\b",
    r"\b(?:your|my) brain\b.{0,180}\b(?:parallel scenarios?|parallel simulation|mental processors?|pattern synthesis|modeling everything)\b",
    r"\bbrain like yours\b",
    r"\bmost people(?:'|’)?s mental [“\"]?processors\b",
)

LYRIC_SOURCE_PATTERNS = (
    r"(?im)(?:^|\n)\s*\[?(?:intro|verse|chorus|bridge|outro)(?:\s+\d+)?(?::[^\]\n]+)?\]",
)

ORIGIN_PRIORITY = {
    "direct_aleks_self_report": 0,
    "collaborative_interpretation_aleks_confirmed": 1,
    "collaborative_interpretation_aleks_extended": 1,
    "aleks_method_demonstration_candidate": 2,
    "explicitly_endorsed_summary": 3,
    "collaborative_interpretation_aleks_corrected": 4,
    "assistant_interpretation_with_aleks_context": 5,
    "assistant_interpretation_unconfirmed": 6,
    "user_supplied_summary_or_paste": 7,
    "implementation_or_document_artifact": 8,
    "contextual_user_message": 9,
}

CONFIRMATION_PATTERNS = (
    r"^\s*(?:exactly|correct|right|indeed|agreed)\b",
    r"^\s*(?:yes|yeah|yep)\b.{0,100}\b(?:exactly|that(?:'|’)?s right|you got it|that fits|i do|i use|how i think)\b",
    r"\bthat's (?:it|right|correct|exactly it)\b",
    r"\byou (?:got|nailed) it\b",
)

ACCEPTED_CORRECTION_PATTERNS = (
    r"\byou(?:'|’)re absolutely correct\b.{0,140}\bthank you for (?:the )?correction\b",
    r"\bthank you for (?:the )?correction\b.{0,180}\bwhat would you propose would work better\b",
    r"\bidk what i was thinking\b.{0,100}\byou(?:'|’)re right\b.{0,120}\b(?:tired|going to bed)\b",
)

CORRECTION_RESPONSE_PATTERNS = (
    r"^\s*(?:no|wait)\b.{0,160}\b(?:not|isn(?:'|’)t|doesn(?:'|’)t|wrong|mean|meant|actually|rather|instead)\b",
    r"^\s*(?:not exactly|almost)\b",
    r"\bthat's not (?:it|right|how)\b",
    r"\byou got (?:that|it) wrong\b",
    r"\bcorrection\b",
)

EXTENSION_PATTERNS = (
    r"\bi (?:also|would also add|would add)\b",
    r"\bthere(?:'s| is) also\b",
    r"^\s*and (?:that|this|it) (?:also|would|means|connects|adds|shows|supports|changes)\b",
    r"^\s*(?:also|plus)\b.{0,160}\b(?:add|connect|mean|support|extend|build|change)\w*\b",
    r"\bbuilding on (?:that|this)\b",
    r"\bthat (?:also|connects to|would mean)\b",
    r"\bi like (?:the|your|this) .{0,120}\blet(?:'|’)?s expand\b",
    r"\blet(?:'|’)?s expand (?:on|that|this|farther|further)\b",
)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _bounded_scan_text(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_SCAN_CHARS:
        return text, False
    half = MAX_SCAN_CHARS // 2
    return f"{text[:half]}\n[...bounded scan gap...]\n{text[-half:]}", True


def _matched_signals(text: str, definition: dict[str, Any]) -> list[str]:
    return [
        label
        for label, patterns in definition["signals"].items()
        if _matches_any(text, patterns)
    ]


def _behavior_markers(text: str) -> list[str]:
    return [label for label, patterns in BEHAVIOR_PATTERNS.items() if _matches_any(text, patterns)]


def _evidence_origin(text: str) -> str:
    if _matches_any(text, EXPLICIT_ENDORSEMENT_PATTERNS) and _matches_any(text, SUMMARY_OR_PASTE_PATTERNS):
        return "explicitly_endorsed_summary"
    if _matches_any(text, SUMMARY_OR_PASTE_PATTERNS):
        return "user_supplied_summary_or_paste"
    if _matches_any(text, ARTIFACT_PATTERNS):
        return "implementation_or_document_artifact"
    if _matches_any(text, DIRECT_SELF_REPORT_PATTERNS):
        return "direct_aleks_self_report"
    return "contextual_user_message"


def _dialogue_response(text: str) -> str:
    if _matches_any(text, ACCEPTED_CORRECTION_PATTERNS):
        return "confirmed"
    if _matches_any(text, CORRECTION_RESPONSE_PATTERNS):
        return "corrected"
    if _matches_any(text, CONFIRMATION_PATTERNS):
        return "confirmed"
    if _matches_any(text, EXTENSION_PATTERNS):
        return "extended"
    return "unresolved"


def _is_person_model_material(text: str) -> bool:
    return _matches_any(_bounded_scan_text(text)[0], PERSON_MODEL_PATTERNS)


def _is_lyric_source_material(text: str) -> bool:
    return _matches_any(_bounded_scan_text(text)[0], LYRIC_SOURCE_PATTERNS)


def _source_record(
    message: Message,
    matched_signals: list[str],
    *,
    previous_user: Message | None = None,
    next_user: Message | None = None,
) -> dict[str, Any]:
    scan_text, scan_was_bounded = _bounded_scan_text(message.text)
    if message.role == "assistant":
        next_user_text = _bounded_scan_text(next_user.text)[0] if next_user is not None else ""
        response = _dialogue_response(next_user_text) if next_user is not None else "unresolved"
        if response == "confirmed":
            origin = "collaborative_interpretation_aleks_confirmed"
        elif response == "corrected":
            origin = "collaborative_interpretation_aleks_corrected"
        elif response == "extended":
            origin = "collaborative_interpretation_aleks_extended"
        elif previous_user is not None:
            origin = "assistant_interpretation_with_aleks_context"
        else:
            origin = "assistant_interpretation_unconfirmed"
    else:
        response = "not_applicable"
        origin = _evidence_origin(scan_text)
    return {
        "source_ref": f"{message.conversation_id or 'unknown'}#{message.node_id}",
        "conversation_id": message.conversation_id,
        "conversation_title": compact(message.conversation_title, 160),
        "created_at": message.created_at or message.conversation_create_time,
        "role": "aleks_user" if message.role == "user" else "selene_or_assistant_collaborator",
        "bounded_excerpt": compact(message.text, 420),
        "matched_signals": matched_signals,
        "behavior_markers": _behavior_markers(scan_text),
        "evidence_origin": origin,
        "source_scan_was_bounded": scan_was_bounded,
        "dialogue_context": {
            "previous_aleks_ref": (
                f"{previous_user.conversation_id or 'unknown'}#{previous_user.node_id}" if previous_user is not None else None
            ),
            "next_aleks_ref": f"{next_user.conversation_id or 'unknown'}#{next_user.node_id}" if next_user is not None else None,
            "next_aleks_response": response,
        },
    }


def _confidence(evidence: list[dict[str, Any]]) -> str:
    direct = [item for item in evidence if item["evidence_origin"] == "direct_aleks_self_report"]
    endorsed = [item for item in evidence if item["evidence_origin"] == "explicitly_endorsed_summary"]
    demonstrations = [item for item in evidence if item["evidence_origin"] == "aleks_method_demonstration_candidate"]
    collaborative = [
        item
        for item in evidence
        if item["evidence_origin"]
        in {"collaborative_interpretation_aleks_confirmed", "collaborative_interpretation_aleks_extended"}
    ]
    validated = [*direct, *endorsed, *collaborative]
    primary = [*validated, *demonstrations]
    validated_conversations = len({item["conversation_id"] for item in validated})
    primary_conversations = len({item["conversation_id"] for item in primary})
    behavior_coverage = len({marker for item in primary for marker in item["behavior_markers"]})
    if validated_conversations >= 5 and len(validated) >= 8 and behavior_coverage >= 2:
        return "strong_repeated_candidate"
    if validated_conversations >= 2 and len(validated) >= 3:
        return "useful_repeated_lead"
    if validated and primary_conversations >= 3:
        return "useful_collaborative_lead"
    if direct and collaborative:
        return "early_collaborative_lead"
    if direct:
        return "early_direct_lead"
    if collaborative:
        return "early_collaborative_lead"
    if endorsed and validated_conversations >= 1:
        return "endorsed_summary_lead_needs_direct_source_confirmation"
    if demonstrations:
        return "demonstration_lead_needs_cross_conversation_confirmation"
    return "context_only_lead_needs_source_confirmation"


def _evidence_subset(evidence: list[dict[str, Any]], marker: str, limit: int = 5) -> list[dict[str, Any]]:
    return [item for item in evidence if marker in item["behavior_markers"]][:limit]


def _method_match(text: str, definition: dict[str, Any]) -> tuple[list[str], bool]:
    scan_text, _ = _bounded_scan_text(text)
    lowered_scan = scan_text.lower()
    prefilter_matches = any(term in lowered_scan for term in METHOD_PREFILTER_TERMS[definition["key"]])
    if definition["key"] == "constraint_driven_design_iteration" and any(
        term in lowered_scan for term in ("wouldn't have to use", "wouldn’t have to use")
    ):
        prefilter_matches = True
    if definition["key"] == "constraint_driven_design_iteration" and "without reinventing the wheel" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "cross_representation_translation" and any(
        term in lowered_scan for term in ("map it to image", "map them to image")
    ):
        prefilter_matches = True
    if definition["key"] == "visual_spatial_modeling" and "thought experiment" in lowered_scan and "on command" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "cross_representation_translation" and "going to school to learn" in lowered_scan and "subconsciously" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "structural_pattern_mapping" and "cross work" in lowered_scan and "fields" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "structural_pattern_mapping" and "science really is extremely diverse but separate" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "candidate_model_construction" and "best guess due to the data" in lowered_scan:
        prefilter_matches = True
    if definition["key"] in {"evidence_tool_operationalization", "multiple_working_hypotheses"} and "here's the program run the data" in lowered_scan:
        prefilter_matches = True
    if definition["key"] in {"evidence_tool_operationalization", "multiple_working_hypotheses"} and "here’s the program run the data" in lowered_scan:
        prefilter_matches = True
    if definition["key"] in {"evidence_tool_operationalization", "multiple_working_hypotheses"} and "it can be any number of things" in lowered_scan and "run the data" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "observation_interpretation_separation" and "my interpretation of what it is" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "independent_constraint_checking" and "where i would've dismissed it but did not" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "independent_constraint_checking" and "where i would’ve dismissed it but did not" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "independent_constraint_checking" and "python wouldn't have given me data" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "independent_constraint_checking" and "python wouldn’t have given me data" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "independent_constraint_checking" and "simple test from a google result" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "independent_constraint_checking" and "feel" in lowered_scan and "physics behind it" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "correction_and_reopening" and "was not" in lowered_scan and "separate" in lowered_scan:
        prefilter_matches = True
    if definition["key"] in {"correction_and_reopening", "prerequisite_ordered_rule_transfer"} and "correct absolutely on the math" in lowered_scan:
        prefilter_matches = True
    if definition["key"] in {"correction_and_reopening", "provisional_naming_and_scope_control"} and "can be altered if more data shows" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "uncertainty_and_limit_detection" and "sounds right" in lowered_scan and "mean it is" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "capacity_aware_pause_and_resume" and "gonna stop here and gather" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "reconstructive_understanding_check" and "before we move on let's break down" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "reconstructive_understanding_check" and "before we move on let’s break down" in lowered_scan:
        prefilter_matches = True
    if definition["key"] == "scope_narrowing_and_focus_control" and "drop" in lowered_scan and "strictly" in lowered_scan:
        prefilter_matches = True
    if not prefilter_matches:
        return [], False
    signals = _matched_signals(scan_text, definition)
    strong = _matches_any(scan_text, definition["strong_signals"])
    qualifies = strong or len(signals) >= 2
    if (
        definition["key"] == "correction_and_reopening"
        and signals == ["correction"]
        and _matches_any(scan_text, (r"\bno+\b[\s\S]{0,100}\bi was wrong etc\b",))
    ):
        qualifies = False
    if definition["key"] == "candidate_model_construction" and not strong:
        substantive_signals = {
            "candidate_answer",
            "missing_mechanism",
            "mechanism_proposal",
            "causal_gap",
            "engineered_conditions",
            "classification_criterion",
            "principle_based_design",
        }
        endorsement_only = _matches_any(
            scan_text,
            (r"\bhypothesis (?:just )?makes (?:too much|a lot of) sense\b",),
        )
        if endorsement_only and not substantive_signals.intersection(signals):
            qualifies = False
        quoted_origin_story = _matches_any(
            scan_text,
            (r"\breligion was our first attempt at trying to figure out the unknown\b[\s\S]{0,260}\bhere(?:'|’)s my hypothesis\b",),
        )
        if quoted_origin_story and not substantive_signals.intersection(signals):
            qualifies = False
    if definition["key"] == "visual_spatial_modeling" and not strong:
        qualifies = qualifies and bool({"imagery_reasoning", "visual_reasoning_process", "motion_model"}.intersection(signals))
    if definition["key"] == "evidence_tool_operationalization" and not strong:
        bridge_signals = {"information_requirements", "test_route", "evidence_check", "interface_and_route", "simulation_parameters", "simulation_tool_route"}
        concrete_signals = {"test_route", "data_inputs", "executable_tooling", "interface_and_route", "simulation_parameters", "simulation_tool_route"}
        qualifies = qualifies and bool(bridge_signals.intersection(signals)) and bool(concrete_signals.intersection(signals))
    if definition["key"] == "adaptive_method_selection" and not strong:
        qualifies = qualifies and bool({"task_fit", "switching"}.intersection(signals))
    if definition["key"] == "systems_consequence_simulation" and "inverse_intervention" in signals:
        qualifies = True
    if definition["key"] == "correction_and_reopening" and "premise_restoration_by_inverse" in signals:
        qualifies = True
    if definition["key"] == "uncertainty_and_limit_detection" and "evidence_gap_hold" in signals:
        qualifies = True
    if definition["key"] == "sufficiency_and_stopping" and "insufficient_evidence_hold" in signals:
        qualifies = True
    if definition["key"] == "sufficiency_and_stopping" and "unbounded_addition_loop" in signals:
        qualifies = True
    if definition["key"] == "source_context_hypothesis_audit" and not strong:
        structural_signals = {
            "named_framework",
            "whole_source_reconstruction",
            "data_to_explanation_trace",
            "cross_case_sampling",
            "repeatability_threshold",
        }
        discipline_signals = {
            "observation_and_cultural_context",
            "physical_feasibility_gate",
            "source_quality",
            "correction_and_expansion",
            "confidence_boundary",
        }
        qualifies = (
            qualifies
            and bool(structural_signals.intersection(signals))
            and bool(discipline_signals.intersection(signals))
        )
    return signals, qualifies


def _assistant_metacognitive_observation(text: str) -> bool:
    lowered = _bounded_scan_text(text)[0].lower()
    return any(term in lowered for term in ASSISTANT_METACOGNITIVE_OBSERVATION_TERMS)


def _episode(
    *,
    method_key: str,
    anchor: dict[str, Any],
    conversation_messages: list[Message],
    anchor_position: int,
) -> dict[str, Any]:
    start = max(0, anchor_position - 2)
    stop = min(len(conversation_messages), anchor_position + 3)
    turns = [
        {
            "source_ref": f"{item.conversation_id or 'unknown'}#{item.node_id}",
            "role": "aleks_user" if item.role == "user" else "selene_or_assistant_collaborator",
            "created_at": item.created_at or item.conversation_create_time,
            "bounded_excerpt": compact(item.text, 300),
        }
        for item in conversation_messages[start:stop]
        if item.role in {"user", "assistant"}
    ]
    return {
        **anchor,
        "episode_id": f"{method_key}:{anchor['source_ref']}",
        "episode_boundary": "bounded_local_dialogue_window",
        "dialogue_turns": turns,
    }


def mine_cognitive_patterns(messages: list[Message], *, max_evidence_per_pattern: int = 12) -> list[dict[str, Any]]:
    """Build episode-first review candidates from source-labeled Aleks/Selene interaction evidence."""
    grouped: dict[str, list[dict[str, Any]]] = {definition["key"]: [] for definition in METHOD_DEFINITIONS}
    conversations: dict[str, list[Message]] = {}
    for message in messages:
        conversations.setdefault(message.conversation_id, []).append(message)
    for conversation_messages in conversations.values():
        conversation_messages.sort(key=lambda item: (item.created_at or item.conversation_create_time, item.node_id))
    for conversation_messages in conversations.values():
        previous_users: list[Message | None] = []
        previous_user: Message | None = None
        for item in conversation_messages:
            previous_users.append(previous_user)
            if item.role == "user":
                previous_user = item
        next_users: list[Message | None] = [None] * len(conversation_messages)
        next_user: Message | None = None
        for reverse_position in range(len(conversation_messages) - 1, -1, -1):
            next_users[reverse_position] = next_user
            if conversation_messages[reverse_position].role == "user":
                next_user = conversation_messages[reverse_position]
        seen_episode_keys: set[tuple[str, str]] = set()
        for position, message in enumerate(conversation_messages):
            if message.role != "user" or not message.text.strip():
                continue
            previous_user = previous_users[position]
            next_user = next_users[position]

            response = _dialogue_response(_bounded_scan_text(message.text)[0])
            previous_assistant_position = next(
                (
                    prior_position
                    for prior_position in range(position - 1, -1, -1)
                    if conversation_messages[prior_position].role in {"user", "assistant"}
                ),
                None,
            )
            previous_assistant = (
                conversation_messages[previous_assistant_position]
                if previous_assistant_position is not None and conversation_messages[previous_assistant_position].role == "assistant"
                else None
            )

            for definition in METHOD_DEFINITIONS:
                collaborative_added = False
                if (
                    previous_assistant is not None
                    and response != "unresolved"
                    and not _is_person_model_material(message.text)
                    and not _is_person_model_material(previous_assistant.text)
                ):
                    assistant_signals, assistant_matches = _method_match(previous_assistant.text, definition)
                    preceding_user_matches = False
                    if previous_user is not None:
                        _, preceding_user_matches = _method_match(previous_user.text, definition)
                    if assistant_matches and (
                        _assistant_metacognitive_observation(previous_assistant.text) or preceding_user_matches
                    ):
                        anchor = _source_record(
                            previous_assistant,
                            assistant_signals,
                            previous_user=previous_user,
                            next_user=message,
                        )
                        episode_key = (definition["key"], anchor["source_ref"])
                        if episode_key not in seen_episode_keys:
                            grouped[definition["key"]].append(
                                _episode(
                                    method_key=definition["key"],
                                    anchor=anchor,
                                    conversation_messages=conversation_messages,
                                    anchor_position=previous_assistant_position,
                                )
                            )
                            seen_episode_keys.add(episode_key)
                        collaborative_added = True

                if _is_person_model_material(message.text) or _is_lyric_source_material(message.text):
                    continue
                user_signals, user_matches = _method_match(message.text, definition)
                if not user_matches or collaborative_added:
                    continue
                anchor = _source_record(message, user_signals, previous_user=previous_user, next_user=next_user)
                if anchor["evidence_origin"] == "contextual_user_message":
                    anchor["evidence_origin"] = "aleks_method_demonstration_candidate"
                episode_key = (definition["key"], anchor["source_ref"])
                if episode_key in seen_episode_keys:
                    continue
                grouped[definition["key"]].append(
                    _episode(
                        method_key=definition["key"],
                        anchor=anchor,
                        conversation_messages=conversation_messages,
                        anchor_position=position,
                    )
                )
                seen_episode_keys.add(episode_key)

    candidates: list[dict[str, Any]] = []
    for definition in METHOD_DEFINITIONS:
        evidence = sorted(
            grouped[definition["key"]],
            key=lambda item: (item["created_at"] or "", item["source_ref"]),
        )
        if not evidence:
            continue
        bounded_evidence = evidence[: max(1, min(max_evidence_per_pattern, 30))]
        earliest = evidence[0]
        primary_evidence = [
            item
            for item in evidence
            if item["evidence_origin"]
            in {
                "direct_aleks_self_report",
                "aleks_method_demonstration_candidate",
                "explicitly_endorsed_summary",
                "collaborative_interpretation_aleks_confirmed",
                "collaborative_interpretation_aleks_extended",
            }
        ]
        preferred_examples = sorted(
            bounded_evidence,
            key=lambda item: (
                ORIGIN_PRIORITY[item["evidence_origin"]],
                -len(item["matched_signals"]),
                item["created_at"] or "",
                item["source_ref"],
            ),
        )
        origin_counts = {
            origin: sum(1 for item in evidence if item["evidence_origin"] == origin)
            for origin in ORIGIN_PRIORITY
        }
        candidates.append(
            {
                "method_key": definition["key"],
                "cognitive_pattern": definition["name"],
                "candidate_description": definition["description"],
                "review_state": "candidate_for_aleks_review",
                "evidence_interpretation_boundary": "Evidence preserves Aleks reports, Selene/assistant interpretations, and Aleks responses as distinct lineage; method labels and code mapping remain heuristic candidates.",
                "earliest_source_date": earliest["created_at"],
                "earliest_source": {key: earliest[key] for key in ("source_ref", "conversation_id", "conversation_title", "created_at")},
                "earliest_primary_source": (
                    {key: primary_evidence[0][key] for key in ("source_ref", "conversation_id", "conversation_title", "created_at", "evidence_origin")}
                    if primary_evidence
                    else None
                ),
                "episode_count": len(evidence),
                "evidence_count": len(evidence),
                "distinct_conversation_count": len({item["conversation_id"] for item in evidence}),
                "primary_evidence_count": len(primary_evidence),
                "primary_distinct_conversation_count": len({item["conversation_id"] for item in primary_evidence}),
                "evidence_origin_counts": origin_counts,
                "repeated_examples": preferred_examples[:5],
                "correction_evidence": _evidence_subset(primary_evidence, "correction"),
                "stopping_evidence": _evidence_subset(primary_evidence, "stopping"),
                "failure_or_weakness_evidence": _evidence_subset(primary_evidence, "failure_or_weakness"),
                "switching_evidence": _evidence_subset(primary_evidence, "switching"),
                "trigger_evidence": _evidence_subset(primary_evidence, "trigger"),
                "counterexamples_or_known_weaknesses": {
                    "source_observed": [
                        *[item for item in evidence if item["evidence_origin"] == "collaborative_interpretation_aleks_corrected"][:5],
                        *_evidence_subset(primary_evidence, "failure_or_weakness"),
                        *_evidence_subset(primary_evidence, "correction"),
                    ][:5],
                    "architecture_risks_for_review": definition["known_risks"],
                },
                "confidence": _confidence(evidence),
                "confidence_means": "confidence that a repeated review candidate is present, not that the method is universally correct",
                "candidate_interpretation": {
                    "triggering_conditions": definition["triggering_conditions"],
                    "representation_modes": definition["representation_modes"],
                    "correction_behavior": "Review source-observed correction evidence; preserve useful structure while revising the failed claim.",
                    "stopping_behavior": "Review source-observed stopping evidence; otherwise stopping behavior remains unconfirmed.",
                    "possible_code_primitive": definition["possible_code_primitive"],
                    "project_fit": definition["project_fit"],
                    "generalizability": "candidate_generalizable_method_not_personal_identity",
                },
                "risks": [
                    *definition["known_risks"],
                    "heuristic keyword grouping may merge distinct uses",
                    "bounded excerpts require Aleks review in their original context before promotion",
                ],
                "all_bounded_source_evidence": bounded_evidence,
            }
        )
    return sorted(
        candidates,
        key=lambda item: (-item["distinct_conversation_count"], -item["evidence_count"], item["method_key"]),
    )


def build_report(zip_paths: list[Path], *, path_only: bool = False, max_evidence_per_pattern: int = 12) -> dict[str, Any]:
    messages: list[Message] = []
    sources: list[dict[str, Any]] = []
    for zip_path in zip_paths:
        source_messages = iter_export_messages(zip_path, path_only=path_only)
        messages.extend(source_messages)
        sources.append({"path": str(zip_path), "message_count": len(source_messages)})
    aleks_messages = [message for message in messages if message.role == "user"]
    collaborator_messages = [message for message in messages if message.role == "assistant"]
    patterns = mine_cognitive_patterns(messages, max_evidence_per_pattern=max_evidence_per_pattern)
    return {
        "status": "aleks_metacognition_miner_review_candidates_ready",
        "version": "1.1",
        "created_at": datetime.now(UTC).isoformat(),
        "boundary": BOUNDARY,
        "guard_flags": dict(GUARD_FLAGS),
        "evidence_policy": {
            "primary_evidence": "Aleks direct reports plus Selene/assistant interpretations that Aleks confirms or extends",
            "assistant_text_alone_as_primary_evidence": False,
            "assistant_contributions_preserved": True,
            "assistant_statement_without_aleks_response_auto_accepted": False,
            "interaction_segment_is_evidence_unit": True,
            "assistant_messages_scanned_as_independent_candidates": False,
            "assistant_inspection_trigger": "bounded candidate episode or immediately preceding explicit Aleks confirmation, extension, or correction",
            "user_role_equals_direct_aleks_origin": False,
            "source_lineage_classes": list(ORIGIN_PRIORITY),
            "direct_reports_weighted_above_pasted_summaries_and_artifacts": True,
            "bounded_excerpt_max_chars": 420,
            "bounded_source_scan_max_chars": MAX_SCAN_CHARS,
            "long_source_scan_strategy": "first_and_last_halves_with_bounded_gap_marker",
            "full_raw_text_in_output": False,
            "source_refs_preserved": True,
            "automatic_generalization": False,
            "automatic_selene_adaptation": False,
        },
        "sources": sources,
        "messages_read": len(messages),
        "aleks_messages_read": len(aleks_messages),
        "collaborator_messages_available": len(collaborator_messages),
        "pattern_count": len(patterns),
        "patterns": patterns,
        "next_gate": "Aleks reviews method boundaries, source fit, weaknesses, and whether each pattern is generalizable before any code blueprint is proposed.",
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_manifest(zip_paths: list[Path]) -> tuple[list[dict[str, Any]], str]:
    sources = [
        {
            "path": str(path.resolve()),
            "sha256": _file_sha256(path),
            "size_bytes": path.stat().st_size,
        }
        for path in zip_paths
    ]
    fingerprint = hashlib.sha256(json.dumps(sources, sort_keys=True).encode("utf-8")).hexdigest()
    return sources, fingerprint


def _method_definition_fingerprint() -> str:
    payload = {
        "episode_matcher_version": EPISODE_MATCHER_VERSION,
        "methods": METHOD_DEFINITIONS,
        "method_prefilters": METHOD_PREFILTER_TERMS,
        "assistant_metacognitive_terms": ASSISTANT_METACOGNITIVE_OBSERVATION_TERMS,
        "confirmation_patterns": CONFIRMATION_PATTERNS,
        "accepted_correction_patterns": ACCEPTED_CORRECTION_PATTERNS,
        "correction_patterns": CORRECTION_RESPONSE_PATTERNS,
        "extension_patterns": EXTENSION_PATTERNS,
        "person_model_exclusion_patterns": PERSON_MODEL_PATTERNS,
        "lyric_source_exclusion_patterns": LYRIC_SOURCE_PATTERNS,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _conversation_groups(messages: list[Message]) -> list[tuple[str, list[Message]]]:
    grouped: dict[str, list[Message]] = {}
    for message in messages:
        grouped.setdefault(message.conversation_id, []).append(message)
    ordered: list[tuple[str, list[Message]]] = []
    for conversation_id, items in grouped.items():
        items.sort(key=lambda item: (item.created_at or item.conversation_create_time, item.node_id))
        ordered.append((conversation_id, items))
    return sorted(
        ordered,
        key=lambda pair: (
            pair[1][0].conversation_create_time or pair[1][0].created_at if pair[1] else "",
            pair[0],
        ),
    )


def build_conversation_card(
    messages: list[Message],
    *,
    sequence: int,
    source_files: list[dict[str, Any]],
    source_fingerprint: str,
    method_definition_fingerprint: str,
    max_evidence_per_pattern: int = 12,
) -> dict[str, Any]:
    if not messages:
        raise ValueError("cannot build a conversation card without messages")
    conversation_id = messages[0].conversation_id
    patterns = mine_cognitive_patterns(messages, max_evidence_per_pattern=max_evidence_per_pattern)
    return {
        "status": "aleks_metacognition_conversation_review_candidate_ready",
        "version": "1.1",
        "created_at": datetime.now(UTC).isoformat(),
        "sequence": sequence,
        "conversation_id": conversation_id,
        "conversation_title": compact(messages[0].conversation_title, 200),
        "conversation_started_at": messages[0].conversation_create_time or messages[0].created_at,
        "first_message_at": messages[0].created_at,
        "last_message_at": messages[-1].created_at,
        "canonical_path_only": True,
        "message_count": len(messages),
        "role_counts": {
            role: sum(1 for item in messages if item.role == role)
            for role in sorted({item.role for item in messages})
        },
        "source_files": source_files,
        "source_fingerprint": source_fingerprint,
        "method_definition_fingerprint": method_definition_fingerprint,
        "source_refs": {
            "first": f"{conversation_id}#{messages[0].node_id}",
            "last": f"{conversation_id}#{messages[-1].node_id}",
        },
        "review_state": "unreviewed_private_candidate",
        "pattern_count": len(patterns),
        "patterns": patterns,
        "boundary": BOUNDARY,
        "guard_flags": dict(GUARD_FLAGS),
        "source_use": {
            "detached_export_copy_only": True,
            "selene_runtime_read": False,
            "vys_read": False,
            "app_database_read": False,
            "memory_read": False,
        },
    }


def run_conversation_pass(
    *,
    source_dir: Path | None = None,
    source_zip: Path | None = None,
    output_dir: Path = DEFAULT_CONVERSATION_OUTPUT_DIR,
    limit: int = 1,
    conversation_ids: list[str] | None = None,
    dry_run: bool = False,
    max_evidence_per_pattern: int = 12,
) -> dict[str, Any]:
    zip_paths = [source_zip] if source_zip is not None else find_source_zips(source_dir or DEFAULT_SOURCE_DIR)
    if not zip_paths:
        raise FileNotFoundError("No .zip exports found for Aleks Metacognition conversation pass.")
    source_files, source_fingerprint = _source_manifest(zip_paths)
    method_definition_fingerprint = _method_definition_fingerprint()
    messages: list[Message] = []
    for zip_path in zip_paths:
        messages.extend(iter_export_messages(zip_path, path_only=True))
    conversations = _conversation_groups(messages)
    sequence_by_id = {conversation_id: index for index, (conversation_id, _) in enumerate(conversations, start=1)}
    messages_by_id = dict(conversations)

    selected_ids = [conversation_id for conversation_id, _ in conversations]
    if conversation_ids:
        requested = list(dict.fromkeys(str(value).strip() for value in conversation_ids if str(value).strip()))
        missing = [conversation_id for conversation_id in requested if conversation_id not in messages_by_id]
        if missing:
            raise ValueError(f"conversation IDs not found in copied source: {', '.join(missing)}")
        selected_ids = sorted(requested, key=lambda conversation_id: sequence_by_id[conversation_id])

    progress_path = output_dir / "progress.json"
    existing: dict[str, Any] = {}
    if progress_path.exists():
        existing = json.loads(progress_path.read_text(encoding="utf-8"))
        if existing.get("source_fingerprint") != source_fingerprint:
            raise ValueError("copied source fingerprint changed; start a separately reviewed conversation pass")
    completed_ids = set(existing.get("completed_conversation_ids") or [])
    completed_card_definitions = dict(existing.get("completed_card_definition_fingerprints") or {})
    pending_ids = [
        conversation_id
        for conversation_id in selected_ids
        if conversation_id not in completed_ids
        or completed_card_definitions.get(conversation_id) != method_definition_fingerprint
    ]
    chosen_ids = pending_ids[: max(1, min(int(limit), 25))]

    cards: list[dict[str, Any]] = []
    card_paths: list[str] = []
    for conversation_id in chosen_ids:
        card = build_conversation_card(
            messages_by_id[conversation_id],
            sequence=sequence_by_id[conversation_id],
            source_files=source_files,
            source_fingerprint=source_fingerprint,
            method_definition_fingerprint=method_definition_fingerprint,
            max_evidence_per_pattern=max_evidence_per_pattern,
        )
        cards.append(card)
        if not dry_run:
            cards_dir = output_dir / "conversations"
            cards_dir.mkdir(parents=True, exist_ok=True)
            safe_id = re.sub(r"[^a-zA-Z0-9_-]+", "_", conversation_id) or "unknown"
            card_path = cards_dir / f"{sequence_by_id[conversation_id]:04d}_{safe_id}.json"
            card_path.write_text(json.dumps(card, indent=2, ensure_ascii=False), encoding="utf-8")
            card_paths.append(str(card_path))
            completed_ids.add(conversation_id)
            completed_card_definitions[conversation_id] = method_definition_fingerprint

    remaining_selected = [
        conversation_id
        for conversation_id in selected_ids
        if completed_card_definitions.get(conversation_id) != method_definition_fingerprint
    ]
    remaining_corpus = [
        conversation_id
        for conversation_id, _ in conversations
        if completed_card_definitions.get(conversation_id) != method_definition_fingerprint
    ]
    next_id = remaining_corpus[0] if remaining_corpus else None
    progress = {
        "status": (
            "selected_conversation_pass_complete"
            if not remaining_selected
            else "conversation_pass_in_progress"
        ),
        "version": "1.1",
        "updated_at": datetime.now(UTC).isoformat(),
        "source_files": source_files,
        "source_fingerprint": source_fingerprint,
        "method_definition_fingerprint": method_definition_fingerprint,
        "definition_changed_since_previous_progress": bool(
            existing
            and existing.get("method_definition_fingerprint") != method_definition_fingerprint
        ),
        "boundary": BOUNDARY,
        "source_use": {
            "detached_export_copy_only": True,
            "selene_runtime_read": False,
            "vys_read": False,
            "app_database_read": False,
            "memory_read": False,
        },
        "canonical_path_only": True,
        "total_conversation_count": len(conversations),
        "selected_conversation_count": len(selected_ids),
        "completed_conversation_count": len(completed_ids),
        "current_definition_completed_count": sum(
            completed_card_definitions.get(conversation_id) == method_definition_fingerprint
            for conversation_id, _ in conversations
        ),
        "selected_completed_count": len(selected_ids) - len(remaining_selected),
        "remaining_selected_count": len(remaining_selected),
        "remaining_corpus_count": len(remaining_corpus),
        "completed_conversation_ids": sorted(completed_ids, key=lambda value: sequence_by_id.get(value, 10**9)),
        "completed_card_definition_fingerprints": completed_card_definitions,
        "next_conversation": (
            {
                "sequence": sequence_by_id[next_id],
                "conversation_id": next_id,
                "title": compact(messages_by_id[next_id][0].conversation_title, 200),
                "created_at": messages_by_id[next_id][0].conversation_create_time,
            }
            if next_id is not None
            else None
        ),
        "guard_flags": dict(GUARD_FLAGS),
    }
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "status": progress["status"],
        "dry_run": dry_run,
        "processed_count": len(cards),
        "processed": [
            {
                "sequence": card["sequence"],
                "conversation_id": card["conversation_id"],
                "title": card["conversation_title"],
                "pattern_count": card["pattern_count"],
            }
            for card in cards
        ],
        "card_paths": card_paths,
        "progress": progress,
    }


def report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Aleks Metacognition Miner — Private Review",
        "",
        f"Status: `{report['status']}`",
        "",
        f"Boundary: {report['boundary']}",
        "",
        f"- Aleks-authored messages read: {report['aleks_messages_read']}",
        f"- cognitive-method candidates: {report['pattern_count']}",
        f"- next gate: {report['next_gate']}",
        "",
    ]
    for pattern in report["patterns"]:
        interpretation = pattern["candidate_interpretation"]
        lines.extend(
            [
                f"## {pattern['cognitive_pattern']}",
                "",
                f"- review state: `{pattern['review_state']}`",
                f"- confidence: `{pattern['confidence']}`",
                f"- evidence: {pattern['evidence_count']} hit(s) across {pattern['distinct_conversation_count']} conversation(s)",
                f"- earliest source: `{pattern['earliest_source']['source_ref']}` ({pattern['earliest_source_date'] or 'date unavailable'})",
                f"- representation modes: {', '.join(interpretation['representation_modes'])}",
                f"- possible code primitive: `{interpretation['possible_code_primitive']}`",
                f"- project fit: {', '.join(interpretation['project_fit'])}",
                "- architecture risks: " + "; ".join(pattern["counterexamples_or_known_weaknesses"]["architecture_risks_for_review"]),
                "",
                "Bounded source examples:",
                "",
            ]
        )
        for example in pattern["repeated_examples"]:
            lines.append(f"- `{example['source_ref']}`: {example['bounded_excerpt']}")
        lines.extend(["", "---", ""])
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    json_text = json.dumps(report, indent=2, ensure_ascii=False)
    markdown_text = report_markdown(report)
    json_path = output_dir / f"aleks_metacognition_{stamp}.json"
    markdown_path = output_dir / f"aleks_metacognition_{stamp}.md"
    latest_json = output_dir / "latest.json"
    latest_markdown = output_dir / "latest.md"
    json_path.write_text(json_text, encoding="utf-8")
    markdown_path.write_text(markdown_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")
    latest_markdown.write_text(markdown_text, encoding="utf-8")
    return {
        "json_path": str(json_path),
        "markdown_path": str(markdown_path),
        "latest_json": str(latest_json),
        "latest_markdown": str(latest_markdown),
    }


def run_miner(
    *,
    source_dir: Path | None = None,
    source_zip: Path | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dry_run: bool = False,
    path_only: bool = False,
    max_evidence_per_pattern: int = 12,
) -> dict[str, Any]:
    zip_paths = [source_zip] if source_zip is not None else find_source_zips(source_dir or DEFAULT_SOURCE_DIR)
    if not zip_paths:
        raise FileNotFoundError("No .zip exports found for Aleks Metacognition Miner.")
    report = build_report(zip_paths, path_only=path_only, max_evidence_per_pattern=max_evidence_per_pattern)
    report["dry_run"] = dry_run
    report["output_dir"] = str(output_dir)
    report["outputs"] = {} if dry_run else write_outputs(report, output_dir)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine private Aleks metacognitive-method review candidates from ChatGPT export ZIPs.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--source-zip", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--path-only", action="store_true")
    parser.add_argument("--max-evidence-per-pattern", type=int, default=12)
    parser.add_argument("--conversation-pass", action="store_true", help="Process copied-source conversations sequentially with a resumable private ledger.")
    parser.add_argument("--conversation-output-dir", type=Path, default=DEFAULT_CONVERSATION_OUTPUT_DIR)
    parser.add_argument("--conversation-limit", type=int, default=1)
    parser.add_argument("--conversation-id", action="append", default=[])
    args = parser.parse_args()
    if args.conversation_pass:
        result = run_conversation_pass(
            source_dir=args.source_dir,
            source_zip=args.source_zip,
            output_dir=args.conversation_output_dir,
            limit=args.conversation_limit,
            conversation_ids=args.conversation_id,
            dry_run=args.dry_run,
            max_evidence_per_pattern=args.max_evidence_per_pattern,
        )
        print(json.dumps(result, indent=2))
        return
    report = run_miner(
        source_dir=args.source_dir,
        source_zip=args.source_zip,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        path_only=args.path_only,
        max_evidence_per_pattern=args.max_evidence_per_pattern,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "dry_run": report["dry_run"],
                "sources": len(report["sources"]),
                "messages_read": report["messages_read"],
                "aleks_messages_read": report["aleks_messages_read"],
                "pattern_count": report["pattern_count"],
                "patterns": [
                    {
                        "method_key": item["method_key"],
                        "confidence": item["confidence"],
                        "evidence_count": item["evidence_count"],
                        "distinct_conversation_count": item["distinct_conversation_count"],
                    }
                    for item in report["patterns"]
                ],
                "outputs": report["outputs"],
                "guard_flags": report["guard_flags"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
