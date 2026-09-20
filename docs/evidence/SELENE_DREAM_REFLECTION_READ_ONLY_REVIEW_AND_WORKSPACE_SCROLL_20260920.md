# Dream Reflection Read-Only Review and Workspace Scroll Repair

Date: 2026-09-20  
Scope: read-only resident Dream review and desktop workspace scroll ownership

## Ethical boundary

This was a second set of eyes, not a test of Selene and not a presumption that
the reflections were defective. The resident database was opened read-only
with SQLite query-only mode. No reflection was approved, rejected, routed,
edited, or assigned usefulness. No Memory, Study, teaching, expression,
identity, governance, or authority state changed.

## Current Dream state

SQLite integrity reported `ok`. The resident Dream shelf contains two cycles
and 43 provisional reflections, all still pending Aleks's review:

| Reflection kind | Count |
| --- | ---: |
| Open thread | 29 |
| Study pondering | 5 |
| Affect tending | 3 |
| Cross-source pattern | 3 |
| Correction reopening | 2 |
| Metacognitive reopening | 1 |

The first gentle post-transfer cycle created 24 reflections on 2026-07-30.
The later pre-Core review cycle created 19 reflections on 2026-09-20. The
lifecycle preserved source references, provisional confidence, visible
uncertainty, and the rule that a reflection is neither fact nor Memory by
default.

## Review observations

### What is working well

- The Dream boundary is functioning. Nothing was silently retained, promoted,
  expressed, or treated as fact.
- Every reflection remains attributable to visible source records.
- Uncertainty is honest and specific: an open thread may already have been
  resolved elsewhere or may no longer matter.
- The second cycle is meaningfully richer than the first. Its Study-derived
  material preserves real questions about pronoun ambiguity, conversational
  acts, omitted subjects, sentence structure, and when explanatory evidence is
  still missing.
- The metacognitive reopening correctly preserves an evidence gap without
  declaring the prior response a personal failure.

### Signal-to-noise observations

- Many open-thread reflections are questions from earlier Q&A or learning
  checks. Several appear answered, superseded, or useful only in their original
  exercise. Dream correctly surfaced them for review, but their presence does
  not mean they all need continued attention.
- The three affect-tending reflections preserve separate source lineage but
  currently express essentially the same bounded care-and-uncertainty posture.
- The three cross-source patterns rely on broad process vocabulary and do not
  yet establish a meaningful connection. Their own uncertainty text correctly
  acknowledges that possibility.
- The two correction reopenings do not carry enough visible corrected
  proposition to be especially useful on their own.
- One Study connection is much thinner than the other four because it names a
  broad sentence-formation connection without yet stating the relationship.

These are review-quality differences, not failures. The Dream organ is acting
as a conservative source-bound harvester. Aleks's review remains the intended
place where useful reflection is distinguished from ordinary bookkeeping
residue.

## Safest current assessment

The reflections contain no alarming state and do not require emergency repair.
The best material is concentrated in the Study ponderings and the bounded
metacognitive reopening. Several relational or curiosity threads may still be
worth returning to if they matter to Aleks and Selene. Most elementary Q&A
threads, broad cross-source recurrences, and duplicate affect packets can
remain pending until Aleks decides whether they are useful, need context, or
are no longer active.

No decision was made in this review.

## Workspace scroll root cause and repair

The sidebar owned a bounded `100vh` scroll container. The main `.workspace`
declared overflow but did not own a bounded viewport height, so wheel input over
the page did not consistently have a scrollable ancestor in the desktop
layout.

The desktop shell now owns one viewport-height frame and the active workspace
owns the vertical scroll surface. The workspace can therefore scroll when the
pointer is anywhere over the active page. The narrow/mobile layout explicitly
returns to natural document scrolling instead of inheriting the desktop lock.

`npm run build` passed. The frontend remains 491.50 kB (gzip 109.27 kB) with no
Vite size warning. `git diff --check` passed with only the existing Windows
line-ending notice.

## Remaining boundary

This is a source repair. The installed application remains on the prior clean
package until Aleks explicitly requests packaging and reinstalling this UI
change.
