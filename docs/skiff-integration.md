# Canonical Skiff 0.3 presenter integration

The source of truth is [zog144/pose-animate](https://github.com/zog144/pose-animate/tree/unstable), **pinned to** `ec5e8986be294a187e4d257df883dccfabea1034` (release candidate `0.3.0-rc.0`, unpublished). This consumes the [reviewed host-welcome integration handoff](https://github.com/zog144/pose-animate/blob/ec5e8986be294a187e4d257df883dccfabea1034/docs/HOST_WELCOME_INTEGRATION_HANDOFF_2026-10-16.md). Its identified implementation source is `4227ab2fe3ad0c417a4d47ce0d889f99c4c0d3d4`.

**License correction:** upstream now declares **BSD-3-Clause OR GPL-3.0-only**, NOT MIT. The generated runtime and SVG geometry are consumed under the BSD-3-Clause option. The exact upstream license text is shipped as `assets/pose-animate-BSD-3-Clause.txt`; upstream release remains subject to the documented copyright-holder/provenance gate. This change does not assert a formal published npm release.

Do not hand-edit generated `assets/pose_animate.js` or `assets/skiff-{ready,setup_pending,unknown,degraded,attention}.svg`. `scripts/sync-skiff.mjs` validates the exact upstream commit, compiles the canonical `dist/index.js` and `dist/presenter.js` modules, verifies that the presenter has only its expected relative import, and inlines the two modules into an offline-compatible script. The script records a combined SHA-256 digest. The five fallback SVGs come from the canonical pure renderer and retain eight six-square limbs.

The **application-facing runtime calls only `createSkiffPresenter`**, with `setState` and `destroy` on `pagehide`. It does not directly call low-level `createSkiff`, modify private squares or SVG IDs, or run timed demonstration sequences. Status selection remains the result of host-welcome's factual assessment. No `sequence-completed` event can ever establish application progress, host recovery or readiness.

| Assessed aggregate | Presenter semantic state | Expected appearance |
| --- | --- | --- |
| ready | ready | Greeting; happy |
| setup_pending | waiting | Listening; neutral |
| unknown | thinking | Ponder; focused |
| degraded | warning | Listening; concerned |
| attention | error | Still; concerned |

For future authenticated progress, `working`, `recovering`, `connection-interrupted` and other semantic states **must be selected only from producer-confirmed status**. The named demo sequence `connection-recovery` visually ends with `ready` and must NOT be used to imply actual recovery; independently verified `setState('ready')` is required. Presenter lifecycle events and completed visuals never authorize operations.

Reduced motion is handled by the upstream presenter/renderer at creation time. The text outside the SVG is the accessible status, the no-JavaScript fallback remains visible, and the HTML has no remote dependencies. The new presenter namespacing permits multiple Skiffs without ID collisions, but host-welcome's current page uses one. Browser and native session acceptance remain separate; no graphical or login-manager privileges are conferred.

Source-level tests confirm correct integration and snapshot generation; manual Windows/Firefox graphical evaluation and real authenticated progress integration are still independent gates.
