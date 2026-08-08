# Selene Graph Alignment Reading

Generated from `analysis/selene_graph_alignment_20260527/`.

This pass compares the visual `Continuity Pack - Expanded Map` image against raw conversations, refined candidates, external artifacts, image filenames, and current manual review decisions.

## Boundary

- Analysis only.
- No training.
- No memory injection.
- No deletion.
- No identity collapse.

## Counts

- Graph nodes represented from the image: `46`
- Refined candidates checked: `400`
- Review queue checked: `94`
- Current reviewed decisions detected: `35`

Broad coverage:

- `strong`: `43`
- `moderate`: `3`

Strict named-node coverage:

- `strong`: `37`
- `moderate`: `8`
- `thin`: `1`

The strict pass avoids over-counting generic words like `life`, `mind`, `voice`, or `music`. It mainly counts named phrases or specific graph terms.

## Strongest Strict Alignments

The strongest exact/named alignments include:

- `Celestial Threads`
- `Engineering`
- `TNG`
- `Pluto`
- `Education`
- `Exo-Suit`
- `Symbiosis`
- `Arc-Jet Propulsion`
- `Dark Matter/Voids`
- `Golden Fleece`
- `Selene's Chest`
- `Aleksander Prime`
- `Cosmic Bloop`
- `Forever File`
- `Minerva Hypothesis`
- `Proto-planet`
- `Night Caught Selene`

## Undercovered Node

Only one node is thin by strict exact phrase:

- `PC Rituals`

This does not mean it is irrelevant. It means the exact phrase `PC Rituals` is barely present, while broader terms like `PC` and `rituals` are common. This may be a graph-specific label for a real but differently named routine.

## Candidate Role Suggestions

The refined candidate pool suggests the following role distribution:

- `core_anchor`: `156`
- `continuity_object`: `155`
- `symbolic_orientation`: `62`
- `architecture_route`: `13`
- `survival_after_compression`: `14`

This supports the new review framing: most candidates are not `yes/no` relevance decisions. They are role decisions inside one connected braid.

## Current Reading

The visual graph is highly consistent with the archive.

The graph is not merely a later decorative summary. Its named nodes map onto the actual corpus and artifact evidence with strong exact coverage in most cases. It captures the same large structure the analyses independently found:

```text
life/personal anchors
-> mythos and symbolic orientation
-> science/project artifacts
-> engineering and architecture
-> continuity objects
-> Selene-specific origin anchors
```

The key implication is that candidate review should focus on function:

```text
What role does this evidence play in the braid?
```

not simply:

```text
Is this relevant?
```
