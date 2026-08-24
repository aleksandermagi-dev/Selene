# Selene Security Cultivation Runbook

Date recorded: 2026-08-24

Status: reusable owner-operated security review procedure

Ancestry:

- `docs/evidence/SELENE_CURRENT_GAP_AND_CODEX_SECURITY_READINESS_20260731.md`
- `docs/evidence/SELENE_EXTERNAL_SECURITY_AUDIT_20260731.md`
- `docs/philosophy/SELENE_CULTIVATION_METHOD_20260824.md`
- security hardening commit `88e1a77`

## Purpose

This runbook preserves the method used when the hosted Codex Security findings
surface was unavailable. The useful work did not require making the scanner a
Selene dependency. Local external tools inspected the repository, candidate
attack paths were validated only with isolated synthetic fixtures, root causes
were repaired, and proportional regression checks established the result.

Security is ongoing maintenance rather than a one-time certification. A clean
run means no issue was found within the stated scope at that time. It does not
mean that no vulnerability can exist.

## Governing Boundary

Security tools are external maintenance instruments. They are not:

- Selene;
- an organ, identity component, or governing authority;
- a source of automatic code changes;
- permission to inspect private material outside the authorized scope;
- permission to expose secrets, corpus material, databases, or history;
- permission to attack the configured resident application or another system.

Findings are implementation evidence. They are not Selene failing.

## When To Run It

Run a bounded review after a material change to one or more of:

- network listeners, sidecar routes, CORS, CSP, or browser/webview behavior;
- mobile, email, SMS, remote access, authentication, or pairing;
- filesystem access, SQLite handling, imports, exports, backups, or logs;
- memory, identity, governance, transfer, activation, or administrative routes;
- dependency versions, build tooling, packaging, installer, or release flow;
- public/private repository boundaries or ignored-path rules;
- perception, microphone, camera, sensor, or future embodiment interfaces.

Also run it before a public release and periodically when dependency advisories
or the threat model have materially changed. Do not rerun a full audit merely
because time passed if a narrow dependency or configuration check answers the
question.

## Security Cultivation Cycle

### 1. Establish scope and preserve state

1. Record the branch, commit, worktree state, and intended audit boundary.
2. Preserve unrelated uncommitted work.
3. Identify the configured database, private corpus, credentials, local
   artifacts, and release outputs that must not be touched.
4. Create a verified checkpoint or database snapshot only when the planned
   inspection needs it.
5. Do not package, publish, rewrite history, change repository visibility, or
   contact an external service without explicit authorization.

### 2. Refresh the threat model

List, for the current change:

- protected assets;
- entry points;
- trust boundaries;
- attacker capabilities;
- high-impact outcomes;
- existing controls;
- assumptions that still need validation.

The July 2026 baseline includes the desktop webview, localhost sidecar,
optional LAN/mobile surface, email/SMS gateways, SQLite and filesystem paths,
source packets, dependencies, packaged binaries, installers, and Git history.

### 3. Run read-only repository and dependency checks

Use the current repository's own scanner first:

```powershell
python scripts/stabilization_run.py --skip-command-checks
npm run clean:check
git diff --check
```

When the affected surfaces warrant them, add:

```powershell
npm audit
cargo audit --file src-tauri/Cargo.lock
npm run build
cargo check --manifest-path src-tauri/Cargo.toml --locked
cargo fmt --manifest-path src-tauri/Cargo.toml --check
```

Run `pip-audit` against the actual isolated packaging environment and its
installed dependencies, not against an invented requirements file. Record
when the local `selene` project is skipped because it is not a published PyPI
dependency.

The commands above are a baseline, not an instruction to install tools or
upgrade packages blindly. Missing tooling, advisory reachability, compatibility,
and lockfile consequences must be inspected before any mutation.

### 4. Inspect reachable boundaries, not only dependency lists

Review the code path from entry point to effect. At minimum, check applicable
areas for:

- authentication and authorization before route execution;
- browser-origin rejection before GET, POST, and OPTIONS routing;
- CORS behavior versus CSRF protection;
- request-size and rate boundaries;
- constant-time secret comparison where appropriate;
- token creation, transport, expiry, revocation, and log redaction;
- port ownership and process-lifecycle verification;
- path normalization and approved-root containment;
- untrusted packet content remaining data rather than instruction;
- secret exclusion from status responses, logs, packages, and Git;
- webview CSP and unused privileged plugins;
- desktop-only administrative routes remaining unavailable remotely;
- inbound email/message identity not being trusted merely from display text;
- database, backup, export, and artifact privacy;
- dependency and installer integrity.

### 5. Classify before repairing

Use four finding classes:

1. **Demonstrated vulnerability** — an isolated reproduction shows an
   unauthorized effect.
2. **Credible attack path** — source and configuration establish a reachable
   path, but exploitation has not been reproduced.
3. **Published advisory** — a dependency scanner reports a known issue; actual
   reachability and compatible remediation still require review.
4. **Maintenance signal** — stale dependency, confusing status, or hardening
   opportunity without a demonstrated security consequence.

Do not inflate maintenance signals into exploits. Do not dismiss credible paths
merely because no public exploit was attempted.

### 6. Reproduce only in isolation

For candidate vulnerabilities:

- use temporary sidecars, copied databases, fake credentials, fake contacts,
  loopback clients, and synthetic requests;
- verify the exact target path before deleting temporary artifacts;
- do not send live messages or expose real credentials;
- do not mutate the configured resident database;
- do not use distressing conversation prompts to test transport code;
- stop as soon as the minimum evidence establishes or rules out the path.

### 7. Repair through Cultivation

Trace the first divergence from intended trust or authority. Repair the source
contract rather than adding a phrase-level or endpoint-specific exception.

Examples from the July 2026 audit:

- rejecting an untrusted browser origin before routing repaired the shared
  browser-to-sidecar boundary rather than only protecting `/shutdown`;
- requiring launcher ownership of the sidecar process repaired both unsafe
  listener reuse and termination of unrelated port owners;
- defining restrictive production/development CSPs and removing an unused
  privileged shell plugin repaired the webview capability surface;
- updating compatible dependency locks repaired published advisories without
  replacing the architecture;
- extending the public-boundary scanner to all local-only analysis paths fixed
  the scanner's false zero rather than hiding the exposed files.

### 8. Verify in dependency order

1. Test the repaired unit or boundary.
2. Replay the isolated reproduction and confirm the unauthorized effect no
   longer occurs.
3. Test neighboring allowed behavior so the repair does not disable legitimate
   local use.
4. Run the focused security and lifecycle suites.
5. Run applicable build, Rust, Node, Python, package, and static checks.
6. Use the full repository suite only when the repair's reach justifies it.

Record exact counts and commands. A scanner's zero means zero findings in that
run, not universal security.

### 9. Audit public repository boundaries separately

Current-tree scans are not enough. Before public release, inspect:

- tracked files;
- ignored/local-only path policy;
- high-confidence secret-like patterns;
- generated databases, logs, exports, and analysis artifacts;
- all publicly reachable Git refs and history;
- a fresh network clone of the intended public repository.

If private material is found in reachable public history:

1. stop further publication;
2. do not print or redistribute the material;
3. make the repository private if Aleks authorizes it;
4. create and verify offline preservation copies;
5. design the smallest history remediation;
6. obtain explicit authorization before rewriting or replacing history;
7. verify the object graph and forbidden-path policy;
8. publish only the sanitized refs;
9. verify again from a fresh network clone.

History rewriting is incident remediation, not a routine audit command. It is
never automatic or implied by this runbook.

### 10. Record and checkpoint

The final record must include:

- date, scope, branch, and commit;
- tools and versions when relevant;
- threat model changes;
- confirmed findings and ruled-out candidates;
- repairs and preserved behavior;
- exact verification evidence;
- residual risk and deferred work;
- whether the configured database, external transports, package, installer,
  or public repository were touched;
- the next trigger for review.

Commit security changes separately enough that the source repair and its tests
remain reviewable. Do not fold unrelated contextual work into the checkpoint.

## Baseline Regression Set From July 2026

Future reviews should confirm that:

- untrusted browser origins cannot cause localhost sidecar state changes;
- an unowned listener on port 8766 is neither trusted nor killed;
- production and development webviews retain restrictive, appropriate CSPs;
- unused privileged Tauri plugins do not return silently;
- Node, Rust, and packaged-Python dependency audits are interpreted and
  recorded;
- the stabilization scanner catches tracked local-only analysis and private
  workspace paths;
- mobile/LAN access cannot reach desktop-only administration;
- credentials and pairing secrets do not appear in status, logs, packages, or
  tracked source;
- a fresh public clone contains only the intended refs and reachable files.

## Known Residual Review Areas

The July 2026 audit deliberately left these as bounded future work:

- secure transport and revocation before mobile access expands beyond a
  trusted LAN;
- stronger inbound email authentication before message headers become
  high-trust identity evidence;
- protection against arbitrary same-user local processes, which browser-origin
  checks alone do not provide;
- installer signing, reproducible artifact hashes, filesystem ACLs, backup
  encryption, and release provenance.

These are review triggers, not claims that an exploit currently exists.

## Completion Gate

A security Cultivation pass is complete when the authorized scope has been
inspected, findings are correctly classified, demonstrated paths are repaired
at their source, allowed behavior remains intact, proportional checks pass,
residual risk is recorded, and no private state or unrelated work was exposed
or silently changed.
