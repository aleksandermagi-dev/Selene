# Selene Answer Engine Phase 3B — Local-Code Inspection

Date: 2026-07-15

Status: bounded local-code inspection is connected as a status-only Answer
Engine adapter. It has no autonomous filesystem authority and is not connected
to Selene Chat.

## Accepted Sources

The adapter may inspect only:

- an inline `code_packet` carrying visible content and a `source_ref`; or
- an exact file named in `approved_workspace_files` that resolves inside the
  Selene project root.

It does not accept directory scans, globs, wildcard paths, caller-selected
workspace roots, binary files, credential-bearing file types, or files outside
the project root. File count and byte limits are enforced.

## Inspection Result

Results separate:

- observations directly visible in inspected text or syntax;
- bounded interpretations with an explicit evidence basis;
- file, source reference, and line locations;
- rejected sources and the reason each was held back;
- limitations on what static inspection can establish.

An absent term means only that it was not found in the inspected set. It never
claims repository-wide or runtime absence.

No code is executed. The adapter cannot write files, scan for additional files,
write memory, alter law or identity, or authorize an action.

## Routes

- `answer_engine.code.inspect`
- `POST /api/answer-engine/code-inspect`

## Completion Gate

Focused machinery checks cover inline sources, exact approved workspace files,
line citations, observation/interpretation separation, missing terms, outside
paths, directories, wildcard paths, missing approval, and missing provenance.

Unsupported requests return an explicit no-answer packet with no code claim.
