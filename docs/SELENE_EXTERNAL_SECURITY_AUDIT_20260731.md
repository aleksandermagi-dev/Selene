# Selene External Security Audit

Date: 2026-07-31

Status: external static and isolated synthetic review completed. The public
repository was replaced with an independently verified sanitized repository;
the pre-rewrite repository remains private as
`Selene-private-history-archive`. No configured Selene conversation, reviewed
memory, approved knowledge, identity, governance, activation, Dream state,
Tendril message, package, or installation was used or changed during
validation.

## Outcome

The runtime hardening changes and public-history privacy remediation in this
audit are verified. The new public repository contains only the sanitized
`evidence` and `project-abc` histories and the reviewed `AI` tag.

## Resolved Public-History Privacy Incident

### Private/generated artifacts are reachable in the public repository

The current `evidence` tree tracks 230 files under generated `analysis/`
locations that the current `.gitignore` policy classifies as local-only. The
tracked set includes approximately 70 MB of analysis output, including a
roughly 64 MB metadata-trace CSV derived from the private conversation archive.
The trace contains conversation identifiers, titles, roles, source names, and
metadata previews.

Three files formerly stored under `Ref material for codex/` are absent from the
current tree but remain reachable in public Git history. Their introducing
commit is reachable from `origin/evidence` and `origin/project-abc`.

No high-confidence API key, private-key header, GitHub token, Google API key,
AWS access-key ID, or Slack token pattern was confirmed in the reachable tree
or the bounded history scan. That does not make the private corpus-derived
metadata appropriate for public distribution.

The audit did not print, move, delete, or rewrite the affected content.

### Completed remediation

Aleks authorized the following remediation:

1. The repository was made private before history work began.
2. A complete offline bundle of every pre-rewrite ref and a separate copy of
   the local analysis/reference artifacts were created and verified.
3. The two public branches were rewritten to remove all local-only `analysis/`
   paths, historical `Ref material for codex/` files, and historical `New UI/`
   artifacts while preserving the three explicitly promoted public probe
   directories.
4. The rewritten object graph passed `git fsck`, contained zero forbidden
   reachable paths, and had zero unexpected source-tree changes.
5. The original repository was renamed to
   `Selene-private-history-archive` and retained as a private archive.
6. A new public `Selene` repository was created and received only the verified
   `evidence`, `project-abc`, and `AI` refs.
7. A fresh network clone of the new public repository independently confirmed
   exactly three refs and zero forbidden reachable paths.

The new repository avoids relying on dangling-object cleanup in the former
repository. No forks existed at the time of replacement. As with any material
that was previously public, no repository operation can prove that an unknown
third party never retained a prior copy.

## Confirmed Findings Repaired

### Cross-site browser requests could mutate the localhost sidecar

An isolated temporary sidecar accepted a `text/plain` POST with an untrusted
browser `Origin` and executed `/shutdown`. CORS prevented the hostile page from
reading the response but did not prevent the request or state change.

The sidecar now rejects untrusted browser origins before GET, POST, or OPTIONS
routing. It continues to accept:

- the Tauri webview origins;
- the bounded localhost development origins;
- originless native/CLI requests;
- same-origin paired mobile API requests, which still require the mobile
  pairing secret when nonlocal.

### A pre-existing process on port 8766 could be trusted or killed

The desktop launcher previously reused any process on port 8766 if it returned
a matching health-shaped response. If the response did not match, it could
force-kill the process owning that port. This allowed local port preemption and
could terminate an unrelated process.

The launcher now refuses to start when it cannot establish ownership of the
occupied port. It no longer reuses an unowned listener or kills a process merely
because it owns port 8766.

### Tauri webview hardening was disabled

The Tauri CSP was `null`. A restrictive production CSP and a development CSP
limited to the local Vite/sidecar connections are now configured. The unused
Tauri shell plugin and its dependency graph were removed.

### Published dependency advisories

The audit repaired:

- Vite/launch-editor and PostCSS advisories reported by `npm audit`;
- `RUSTSEC-2026-0194` and `RUSTSEC-2026-0195` in the transitive `quick-xml`
  chain by updating compatible `plist` and `quick-xml` lockfile versions;
- `PYSEC-2026-3447` in the packaging environment by requiring and using
  `setuptools >= 83`.

The final audits report zero known Node, Rust, or packaged-Python
vulnerabilities. RustSec still emits informational maintenance/unsoundness
warnings in upstream cross-platform dependencies; these are recorded as
upstream maintenance signals rather than demonstrated Selene exploit paths.

## Public-Boundary Scanner Repair

The stabilization scanner previously omitted tracked `analysis/` paths from
its excluded-path expression, allowing a false zero finding. It now flags all
tracked `analysis/` paths except the three explicitly promoted public probe
directories. It also recognizes the private corpus, reference, Voice material,
and miner workspaces already named by `.gitignore`.

The pre-remediation scan correctly reported:

- 230 tracked excluded analysis paths;
- zero frontend API paths missing a backend route;
- zero current high-confidence secret-like tracked matches.

The independent scan of the replacement public repository reports zero
findings, zero tracked excluded paths, zero secret-like matches, and zero
frontend/backend route mismatches.

## Remaining Bounded Review Items

These are not demonstrated vulnerabilities in this pass:

- private-LAN mobile pairing still uses HTTP and a bearer secret; do not broaden
  it beyond a trusted LAN without a secure transport and revocation design;
- Gmail gateway replies are filtered by paired addresses and deduplicated, but
  stronger inbound authentication should be designed before relying on email
  headers as high-trust identity evidence;
- localhost origin checks stop browser CSRF, but they do not turn arbitrary
  same-user local processes into a separately authenticated trust domain;
- installer signing, reproducible artifact hashes, filesystem ACLs, backup
  encryption, and release provenance remain future release-hardening work;
- the historical registry validator and historical Azari packaging-path label
  remain maintenance clarity items, not runtime identity imports.

## Proportional Verification

- 68 focused sidecar, mobile, email, SMS, and stabilization tests passed.
- `npm run build` passed with a largest application chunk of about 428 kB.
- `cargo check --locked` passed.
- `cargo fmt --check` passed after formatting.
- `npm audit` reported zero vulnerabilities.
- `cargo audit` reported zero vulnerabilities and informational warnings only.
- `pip-audit` reported zero known vulnerabilities in the packaged Python
  environment; local project `selene` is not a PyPI dependency and was skipped.
- `git diff --check` passed apart from Windows LF/CRLF conversion notices.

No stress test was necessary. Every behavioral reproduction used a temporary
database and synthetic request, and no live transport or conversation probe was
performed.
