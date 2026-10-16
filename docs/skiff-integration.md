# Canonical Skiff integration

The source of truth is [zog144/pose-animate](https://github.com/zog144/pose-animate/tree/unstable), **pinned to** `b7a6e3bdb15d0a15cc8b8cbc17e295dd472dc57a`. The package declares **MIT** in its package metadata; preserve this attribution and verify final license notices before any downstream distribution. The authored mascot design is still subject to visual sign-off.

**Do not manually edit generated** `assets/pose_animate.js` or `assets/skiff-{ready,setup_pending,unknown,degraded,attention}.svg`. They are outputs of `scripts/sync-skiff.mjs`, fed by the exactly pinned upstream `dist/index.js`. The build verifies the pinned source commit, checks that no runtime import remains, and emits a SHA-256 digest in the generated script header.

The Python renderer embeds the compiled JS module and one state-specific static fallback into a standalone HTML document. It calls the upstream `createSkiff` and `setState` API. Animated motion is disabled when reduced-motion is requested. No CDN or app-server access is required. If JavaScript is disabled, the fallback remains visible.

| Assessed aggregate | Upstream semantic state | Expected appearance |
| --- | --- | --- |
| ready | ready | Greeting; happy |
| setup_pending | waiting | Listening; neutral |
| unknown | thinking | Ponder; focused |
| degraded | warning | Listening; concerned |
| attention | error | Still; concerned |

Upstream `pose-animate` owns visual geometry, timing, semantic expression precedence, colors and transition implementations. `host-welcome` owns the translation from authenticated readiness to Skiff state, user-visible text, console and headless functionality. UI must never use animation as the only indicator of failures. Do not promote `unstable` to `main` without acceptance of the updated canonical mascot.
