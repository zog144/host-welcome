# Application-installation progress — Handoff F / Phase 1

**Status:** simulation-first read-only console implementation; **NOT** a live application-progress observer, installer or production login session. This document describes host-welcome's own fixture format, not a new image-build/host-install producer protocol.

## Source boundaries

- `host-welcome.readiness/v1` remains unchanged and rejects untrusted `source_kind=host`. The existing approved HTML previews and Skiff presenter are unchanged in this milestone.
- `host-welcome-progress` is a separate command, with a separate `host-welcome.progress-fixture/v1` envelope. It reads in-memory `--scenario` examples or an untrusted `--input` *simulation fixture*; the only accepted `source_kind` is `fixture`. There is **no** socket connection, monitoring loop, HTTP request, controller mutation, GUI launch or startup dependency.
- The controller slice is a strict source-level validator of the current box-control `zog-application-progress-v1` **subset**: fixed `box-control` producer, max 4 build jobs plus max 4 runtimes, independent next cursors, null host/installation IDs and raw build application association. Controller success of an individual command does not prove verified publication. Persisted running states may report unknown. The upstream strict `ApplicationProgressClient` remains the responsible future authenticated transport.
- The `installation` section is a **host-welcome-only simulation projection** of separate host-install headless bootstrap outcome and optional graphical *request intent*. It is not accepted from the real `zog-host-install-bootstrap-readiness-v1` socket until a dedicated adapter verifies root peer UID, nonce, boot and producer schema.
- The `image_build` section has a deliberately named **`host-welcome.image-build-fixture/v1`**, which is NOT a contract implemented by image-build. Simulated operations map exact job IDs to an application/attempt and can carry distinct publication receipts. Real source integration needs a jointly reviewed read-only image-build adapter and independently authenticated publication selection.
- All supplied timestamps and optional boot IDs are checked. This simulated presentation uses the `reference_time` inside the fixture solely so an archived example remains deterministic; it **never** establishes the current system time, freshness or live host authority. The future live adapter MUST use a trusted runtime clock and current boot identity, not a user-supplied reference time.
- Input strings are enums or bounded identifiers. Raw path/argv/log/error strings, control codes, arbitrary messages, guessed percentages and ETA are not part of the model. No source field is interpolated into a shell command or browser script.

## Console use

```sh
host-welcome-progress --scenario building
host-welcome-progress --scenario blocked
host-welcome-progress --scenario uncertain
host-welcome-progress --scenario published
host-welcome-progress --scenario headless
host-welcome-progress --scenario unavailable
host-welcome-progress --scenario published --format json
```

Each output says **SIMULATED EXAMPLE** and distinguishes headless installation, explicit graphical request intent, command progress, separately evidenced publication and graphical/login readiness. The final one remains `not-verified` regardless of published software. The controller page never fabricates `not-requested` when empty. The welcome is non-interactive and leaves getty/login unaffected.

## Assessment examples

| Scenario | Honest claim |
| --- | --- |
| `building` | An image-build simulation says compiling; controller saved state cannot prove a running process; publication unknown |
| `blocked` | Source acquisition blocked; no automatic retry or download |
| `uncertain` | Job needs reconciliation; not success |
| `published` | Simulated independent software publication receipt and command success; graphical login still unverified |
| `headless` | Simulated verified headless installation, graphics explicitly not requested |
| `unavailable` | Controller and publication not observed; unknown, never green |

## Joining and fail-closed behavior

Data is grouped for **presentation**, not canonical lifecycle state. Controller pages are **not atomic** with image-build or installer observations, even when timestamps match. The current simulation never persists, silently combines or replaces old pages. Stale/future timestamp, unexpected boot, missing/pruned job association or conflicting command outcome blocks positive inferred progress. Verified publication requires a separate fixture publication receipt, software-view hash and producer-completed publication phase. Controller success alone can never synthesize it. A published application is still not an authenticated greetd/PAM/X11/Wayland session or usable browser.

## Remaining blocked gates

1. **host-install + box-control/root-control:** the current `0600` controller broker socket is authorized for the *station-access* UID. It must not be reused by the separate `host-welcome` account without a protected, explicitly reviewed observer identity/service/socket. The current host-install bootstrap socket is separately root-owned, nonce-bound and authorizes the `host-welcome` UID; don't collapse their trust boundaries.
2. **image-build:** produce a bounded, authenticated read-only attempt→stage→package→command→build-job mapping and selected immutable software-publication receipt tied to exact source/generation, with request intent handled by its real authority.
3. **host-deploy Work:** native systemd UID/socket/getty verification before production activation. No automatic refresh storm, no privileged greetd role or local seat before PAM/logind security design.

## Acceptance

Run `python -m unittest discover -s tests -v`. Progress-specific tests exercise all six simulation states; controller page bounds, malformed schemas, wrong IDs, future/stale timestamps, wrong boot, missing and contradictory jobs, phase-succeeded versus publication, explicitly not-requested vs empty pages, no fresh GUI claims, and untrusted `source_kind=host` refusal. CI on Python 3.11/3.12/3.13 remains the same; generated Skiff and Windows HTML preview acceptance are unchanged.
