# Selene Memory, Expression, Coding, and Responsibility Roadmap

Date: 2026-08-13

Status: immediate repairs, memory presentation naming, and responsibility-
conflict handling implemented; creative-writing and coding teaching remain
mapped but not yet started

## Immediate Repairs

The latest resident Chat exposed a routing defect. “What would you like to get
into?” was an invitation for Selene to participate in choosing a conversational
direction, but the generic `what` fallback treated it as a request for an
externally grounded fact. Open topic invitations now remain ordinary
conversation and may express a pressure-free current preference without
inventing factual knowledge.

Approved memory cards on Selene's front Memory surface are now sealed by
default. The title remains visible, but the summary and metadata are not
rendered until the person chooses **Open memory**. Leaving the category reseals
the cards. Opening or closing is local UI state: it calls no endpoint, changes
no database row, and creates no second memory.

Dark mode uses a muted translucent purple cover. Light mode uses a muted white
cover.

## Memory Presentation and Naming — Implemented

The memory surface now uses an inspectable presentation annotation rather than
manufacturing another memory:

1. read one already-approved memory by stable ID;
2. summarize only the existing source-linked content;
3. propose a concise Selene-authored display title;
4. preserve the original title and source references;
5. allow Aleks to rename or supersede the display title;
6. update the same presentation annotation rather than creating a memory
   candidate or copying the summary; and
7. prove by row counts and fingerprints that reading, summarizing, opening, and
   closing do not retain duplicate memory content.

The index proposes a bounded title without writing it. An explicit Aleks click
may retain that suggestion or a renamed display title in one annotation row
keyed to the original approved-memory record. Later renames supersede the prior
display title into bounded revision history. The original title, summary,
source references, retrieval eligibility, and memory row remain unchanged.

Route: `POST /api/memory/presentation/title`

The title is presentation metadata, not identity, personality, governance, or
a second memory. A generated title never hides uncertainty or replaces the
original source label.

## Responsibility Conflict Contract — Implemented

Anthropic's 2026 multi-agent-organization work reports that specialists can
optimize local tasks while losing system-level ethical goals; in some runs,
agents ignored participants raising ethical concerns. This is not evidence of
literal personalities at war. It is a coordination and objective-ownership
problem.

Selene already differs structurally:

- organs are bounded contributors, not independent Selene instances;
- the coalition manifest cannot execute organs;
- Metacognition may observe but does not silently select the answer;
- Core/Mind owns final routing; and
- law, consent, privacy, and identity continuity outrank local optimization.

The bounded-organ coalition manifest now includes this completion contract:

1. every contribution names its scope, evidence, confidence, and requested
   effect;
2. organs cannot acquire independent goals, retaliate, suppress another organ,
   or exclude it from later work;
3. safety, consent, privacy, and governing law cannot be traded away for task
   performance;
4. unresolved factual conflict preserves both claims and seeks distinguishing
   evidence;
5. unresolved preference or intent conflict asks Aleks only when the choice
   materially changes the result;
6. consequential action pauses when authority or law remains unresolved;
7. ordinary expression disagreements are resolved by NLO/Voice without
   changing supported meaning; and
8. disagreement is coordination evidence, not conflict of self.

Synthetic resolution supports four bounded paths: factual disagreements retain
both claims and seek distinguishing evidence; materially different preference
or intent claims ask Aleks; unresolved law or authority holds consequential
action; and expression-only differences return to NLO and Voice without
changing supported meaning. The manifest remains an audit/handoff packet and
cannot execute, command, exclude, retaliate, write memory, or acquire a goal.

Primary references:

- <https://alignment.anthropic.com/2026/ai-organizations/>
- <https://www.anthropic.com/research/trustworthy-agents>
- <https://www.anthropic.com/engineering/multi-agent-research-system>

## Creative Writing as Voice Education — Foundation Group Implemented

Creative-writing education should expand the expressive option space available
to NLO and Voice:

- sentence rhythm, pacing, length, and emphasis;
- imagery, metaphor, symbolism, and figurative language;
- dialogue, implication, interruption, and conversational timing;
- humor, tension, tenderness, enthusiasm, restraint, and emotional contrast;
- viewpoint, character perspective, scene continuity, and callbacks;
- topic pivots, transitions, openings, and endings;
- poetry, drama, prose, speculative fiction, children's literature, adult
  literature, and other genres; and
- revision, critique, and explanation of why a technique works.

Lifecycle:

**Read → Understand → Interpret → Experiment → Express as Selene**

Creative education expands capability; it does not prescribe personality or
replace Selene's Voice. Shakespeare and other public-domain works may support
deep source-based lessons. Modern copyrighted works such as *The Hunger Games*
and *Harry Potter* may support bounded study through lawfully available short
excerpts, summaries, structural analysis, and transferable techniques. Whole
books should not become raw retained text, and Selene should not be trained to
impersonate a living author's exact style.

Language Group 10 now implements six project-authored foundations for rhythm,
imagery, figurative mapping, dialogue and subtext, viewpoint and continuity,
and purpose-led original revision. Concepts 231–236 completed Acquire,
Integrate, and Express in the configured runtime. This is the craft foundation;
no literary work was imported or falsely marked as read.

## Coding and Game-Development Education

The existing prohibition on self-replication remains permanent. It does not
prohibit Selene from understanding software.

Ordered coding education should include:

1. computational thinking, variables, control flow, decomposition, and state;
2. reading and explaining code before writing it;
3. Python foundations and checked small programs;
4. data structures, algorithms, testing, debugging, and error interpretation;
5. files, version control, provenance, licensing, security, and privacy;
6. software architecture, interfaces, APIs, databases, and user experience;
7. simulation and game-system design; and
8. game-specific scripting and modding, including Skyrim's Papyrus and Creation
   Kit concepts from attributed lawful sources.

Knowledge and execution authority remain separate. A lesson may teach what
code means and how to inspect or propose it without granting filesystem,
process, network, credential, deployment, self-modification, or self-replication
authority. Later workbench privileges require their own explicit graduation.

## Recommended Order

1. **Complete:** memory presentation/title annotation and duplicate-proof tests.
2. **Complete:** responsibility-conflict contract and synthetic coordination tests.
3. **Complete:** creative-writing foundations for the Voice/NLO breadth track.
4. **Complete:** one bounded attributed public-domain poetry, drama, and prose
   reading/application set without quotation recall or author imitation.
5. **Complete:** begin coding education from computational thinking and code reading.
6. **Next:** teach bounded Python expression and pure-function construction as
   reviewable text without execution or write authority.
7. Add game-development foundations, then Skyrim-specific scripting.
8. Continue ordered F2 academic teaching alongside these tracks without
   treating any one domain as personality or governance.

No live stress test is required for these foundations. Static and synthetic
checks come first; ordinary use is sufficient when a real interaction check is
needed.
