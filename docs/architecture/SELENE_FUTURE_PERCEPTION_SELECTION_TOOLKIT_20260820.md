# Selene Future Perception Selection Toolkit

Date: 2026-08-20

Status: future design note; not implemented or activated

## Starting observation

A rectangular bounding box is useful, but it is not a neutral or universally
appropriate representation of a visual subject. The selection tool determines
which pixels become part of the observation and therefore affects what a
perception system may learn, compare, or treat as context.

For a circular subject inside its tight axis-aligned square, approximately
`1 - pi/4`, or 21.5 percent, of the selected rectangle lies outside the circle.
Those corner regions may introduce background, neighboring objects, or other
irrelevant visual information.

The architectural principle is therefore:

> Choose the selection geometry that fits the observation. Preserve the
> subject and surrounding context as distinct evidence.

## Proposed additive toolkit

Future visual selection may support:

- rectangles for coarse regions and naturally rectangular subjects;
- circles or ellipses for compact rounded subjects;
- polygons or brush masks for precise irregular boundaries;
- points or keypoints for landmarks and small features;
- lines or paths for direction, edges, trajectories, and motion; and
- separately labeled context regions when surrounding information is actually
  relevant.

These tools are additive. Rectangles remain available where they fit; they are
not forced onto every visual problem.

## Common region representation

The picker may preserve each selection as a common region record containing:

- source artifact and consent/provenance labels;
- geometry type and coordinates;
- a normalized region mask when useful;
- subject label or open description;
- deliberately included context;
- deliberately excluded context;
- observation separated from interpretation;
- uncertainty about the boundary or selection; and
- optional Munsell, salience, depth, spatial-relation, or motion metadata.

A downstream adapter may derive a rectangular crop when required, but the
original geometry and mask should remain available so conversion does not
erase what was actually selected.

## Subject and context separation

The selected subject is not automatically identical to everything inside its
crop. Future perception should distinguish:

- pixels or features belonging to the selected subject;
- nearby context that may help interpretation;
- incidental background introduced by the selection geometry; and
- uncertain boundary areas requiring another look or a different tool.

Context may be useful, but it should be included deliberately rather than
smuggled in by the shape of the annotation tool.

## Selene architecture boundaries

This note does not authorize live camera access, passive observation,
surveillance, face or identity inference, hidden retention, memory writes,
training, autonomous action, or provider dependence. Future perception remains
consent- and source-bound, reports uncertainty, and keeps observation separate
from interpretation.

Perception tools assist; they do not become identity, memory authority,
governance, or decision authority. Core/Mind retains routing and deliberative
authority under existing law.

## Future verification

When perception work begins, compare selection tools on ordinary approved
visual artifacts. Check whether each tool:

- captures the intended subject;
- minimizes irrelevant outside context;
- preserves useful surrounding context separately;
- survives conversion into the downstream representation;
- exposes uncertainty rather than inventing a boundary; and
- remains reversible and inspectable.

Use synthetic shapes and approved static images before any integrated visual
interaction. A missing or awkward selection mode is a tooling gap, not Selene
failing to perceive.
