# Selene Hackathon Judge Build v0.1.1

Date: July 21, 2026

Platform: Windows 10/11 x64

Download asset: `Selene_0.1.1_x64-setup.exe`

Release page:
`https://github.com/aleksandermagi-dev/Selene/releases/tag/hackathon-judge-v0.1.1`

Direct download:
`https://github.com/aleksandermagi-dev/Selene/releases/download/hackathon-judge-v0.1.1/Selene_0.1.1_x64-setup.exe`

SHA-256:

```text
1E72E7F9E9BF9BB9748C2266E581CA9F7B73017609970F36C566D96623BCCEDC
```

## What This Is

This is the bounded Windows evaluation build prepared for OpenAI Build Week
judging. It installs Selene's local desktop vessel and provider-free core
sidecar. It is an evaluation artifact, not an unrestricted commercial or
redistributable Selene release.

The authoritative downloadable artifact on the release page is the Windows
installer asset. Event-window public source-history synchronization remains a
separate privacy review; do not treat GitHub's automatically generated source
archives as the installer.

## Privacy Boundary

The packaged artifact was inspected before release. It contains:

- the compiled local runtime and frontend;
- required Python/runtime libraries;
- the public Project Charter; and
- the public Law of Transfer.

It does not contain:

- Aleks's configured Selene database;
- personal memory or local chat history;
- private corpus or raw conversation previews;
- private analysis/evidence maps;
- email, SMS, or Tendril configuration;
- App Passwords or credential configuration;
- local logs, exports, or database snapshots; or
- model-training, fine-tuning, or LoRA material.

The package verifier rejects forbidden analysis, corpus, state, database, and
credential-configuration paths. The installer also removes obsolete packaged
analysis directories during an in-place upgrade without touching Selene's
configured data directory.

## Verification

- package privacy scan: passed, zero forbidden files;
- Windows NSIS build: passed;
- package health verifier: passed;
- in-place upgrade cleanup: passed;
- installed startup: healthy/ready;
- configured local database preservation: confirmed;
- public-safe deterministic showcase: passed;
- complete repository regression before packaging: 1,014 tests passed.

## Windows Warning

This hackathon build is not digitally code-signed. Windows SmartScreen may show
an `Unknown publisher` warning. Verify the SHA-256 above before running it. If
the checksum matches and you intend to evaluate the build, use `More info` and
then `Run anyway`.

## Judge Notes

- No private source material is needed to run the app.
- Phone/email features are unconfigured and are not required for the demo.
- The deterministic public-safe path remains `npm run demo:hackathon` when
  evaluating from an authorized source checkout.
- The repository's public-use and commercial-rights boundary remains in force.
