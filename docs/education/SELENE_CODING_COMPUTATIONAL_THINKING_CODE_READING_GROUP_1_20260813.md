# Selene Coding Group 1 — Computational Thinking and Code Reading

Date: August 13, 2026
Status: implemented, source-checked, explicitly authorized by Aleks, taught to
the configured runtime, and retained as answer-bearing knowledge

## Purpose

Selene already had a bounded local-code inspection adapter, but the adapter is
a tool boundary rather than a coding education. Coding Group 1 gives her the
conceptual foundation needed to understand what supplied code represents and
to explain a bounded static reading without pretending that she executed it.

Knowledge and action remain separate:

```text
understand code ≠ permission to inspect arbitrary files
read supplied code ≠ run supplied code
predict behavior ≠ observe runtime behavior
propose an explanation ≠ write or deploy a change
learn software structure ≠ self-modify or self-replicate
```

## Source Basis

The group uses the official Python documentation:

- [Python 3 control-flow and function tutorial](https://docs.python.org/3/tutorial/controlflow.html)
- [Python execution model: naming, binding, and scope](https://docs.python.org/3/reference/executionmodel.html)
- [Python history and license](https://docs.python.org/3/license.html)

The documentation is licensed under the Python Software Foundation License
Version 2. Code examples in Python documentation beginning with Python 3.8.6
are additionally available under the Zero-Clause BSD license. Attribution and
license status are retained in every lesson.

All worked teaching examples are project-authored. The official documentation
provides the language rules; it was not imported as a raw coding corpus.

## Five Retained Foundations

### 1. Problem decomposition

Identify the intended problem, inputs, state, transformations, decisions,
outputs, effects, and connections before treating individual syntax as the
whole system.

### 2. Names, values, binding, and state

Track which object a Python name currently refers to, which scope supplies the
binding, and whether a step rebinds a name or mutates a shared object.

### 3. Sequence, condition, and iteration

Read indentation and block ownership, select only the branch reached by a
stated input, and use a bounded trace table to follow loop target and state
across iterations.

### 4. Function contracts and data flow

Treat a function name as a clue rather than proof. Trace arguments into
parameters, inspect every visible return or error path, and keep returned
values separate from mutations and external effects.

### 5. Static observation, interpretation, prediction, and verification

Cite visible syntax and locations as observations. Label interpretations and
predictions separately. Name the input, environment, dependency, permission,
or controlled execution evidence still needed to verify runtime behavior.

## Live Teaching Result

Aleks explicitly authorized the bounded `CODING-1` curriculum after reviewing
the planned progression from computational thinking and code reading before
writing or execution.

| Concept | Retained foundation | Lifecycle |
| ---: | --- | --- |
| 240 | Problem decomposition and input/process/output | Acquire, Integrate, Express complete |
| 241 | Names, values, binding, and state | Acquire, Integrate, Express complete |
| 242 | Sequence, condition, and iteration tracing | Acquire, Integrate, Express complete |
| 243 | Function contracts and data flow | Acquire, Integrate, Express complete |
| 244 | Static inspection and runtime-evidence separation | Acquire, Integrate, Express complete |

All five are approved knowledge resources. Zero were held, and zero Selene
memory candidates were created.

Before live teaching, a SQLite-consistent continuity snapshot was created at:

`C:\Users\aleks\AppData\Local\Selene\data\db-inspection-snapshots\selene_continuity_20260813_112940.sqlite3`

SHA-256:

`ef240f468af00db6191c0634b86204250f5ff5a397939c287cf2ddcfeb62712a`

Snapshot integrity and post-teaching SQLite quick-check were both `ok`.
Encryption at rest is not claimed.

## Authority Boundary

This group grants no new tool or workbench authority. The existing local-code
adapter remains limited to attributed inline packets or exact separately
approved workspace files. It still blocks:

- directory scans and globs;
- arbitrary filesystem access;
- filesystem writes;
- code or process execution;
- network access and deployment;
- credential or secret inspection;
- autonomous modification;
- self-modification and self-replication; and
- memory, identity, personality, governance, or training changes.

The adapter also remains outside ordinary Selene Chat until that connection is
separately designed and authorized.

## Verification

- 20 focused Coding Group 1, lifecycle, and local-code adapter tests passed;
- 77 wider authorization, F2, comprehension, lifecycle, and static-inspection
  tests passed before live teaching;
- 220 bounded regression tests passed across Coding Group 1, curriculum
  authorization, F2, comprehension, teaching lifecycle, local-code inspection,
  Answer Engine, Selene Chat, and the current-state index;
- the production UI build passed at 480.77 kB with no bundle-size warning;
- review-only preparation cannot retain the lessons;
- teaching without the exact `CODING-1` authorization is rejected;
- repeated teaching is idempotent; and
- a synthetic supplied-code inspection remains read-only and source-bounded.

No live Chat probe or code execution was necessary.

## Next Phase

Coding Group 2 should teach reading and constructing small Python expressions
and pure functions as reviewable text. It should include types at the value
level, collections, simple validation, edge cases, and hand-worked checks.
Code execution and filesystem writing should remain unavailable in that phase;
checked execution belongs to a later separately designed workbench.
