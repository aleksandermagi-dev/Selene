# Selene Answer Engine Phase 3

Date: 2026-07-15

Status: a deterministic verified-math adapter is connected for bounded exact
arithmetic. Comparison/planning remains connected from Phase 2. Selene Chat
remains intentionally disconnected.

## Purpose

Phase 3 gives the Answer Engine a domain that can establish correctness through
a deterministic mechanism rather than sentence fluency or model confidence.
The first math boundary is deliberately small so that `verified` keeps a clear
meaning.

## Supported Math

The adapter accepts:

- integer and base-10 decimal literals;
- parentheses and standard arithmetic precedence;
- addition, subtraction, multiplication, and division;
- floor division and modulo;
- integer powers with absolute exponent no greater than 20;
- one equality check at a time.

Calculations use exact rational arithmetic. Terminating decimals remain exact,
and non-terminating rational results preserve their fraction alongside a
bounded decimal approximation.

## Explicitly Unsupported

The adapter does not guess at:

- symbolic algebra or variables;
- functions such as square root or trigonometry;
- units or conversions;
- natural-language percentage problems;
- inequalities;
- prose mixed with a partial numeric expression.

Unsupported or malformed requests return an honest no-answer packet. They are
not passed to a language model as if model confidence could verify arithmetic.

## Safety And Confidence

The evaluator parses a restricted Python abstract syntax tree. It never calls
Python `eval`, executes names or functions, uses an external provider, or
writes a record.

Successful results report:

- evidence confidence: `deterministic_exact_arithmetic`;
- answer confidence: `verified_exact`;
- expression confidence: `not_assessed`.

Unsupported results report `no_verified_result` and `unable_to_verify`.
Visible operation checks are calculation audit steps, not hidden reasoning.

The comparison/planning completion retry remains limited to one. Math does not
use a retry because repeating an unsupported or malformed calculation would
not add evidence.

## Routes

- `answer_engine.math.run`
- `POST /api/answer-engine/math-run`

The Phase 1 and Phase 2 Answer Engine status, preview, packet, and comparison
routes remain available.

## Still Deferred

- symbolic or advanced math;
- local-code inspection;
- source-backed research;
- approved-knowledge answer execution;
- ordinary-conversation answer execution;
- Acquire -> Integrate -> Express orchestration;
- Selene Chat, NLO, or Voice integration.

No activation, autonomy, model training, LoRA, memory write, raw corpus recall,
identity change, governance change, or personality change is introduced by
this phase.
