# host-welcome

Skiff's first-boot welcome for Zog, designed to work **before station-access** and on **headless hosts**.

This first milestone is a **simulation-only, read-only reference implementation**. It does not inspect the running host, install software, enroll a machine, modify STATE, or authorize recovery. A fixture is never presented as a verified live host.

## Try it

Requires Python 3.11+; no runtime dependencies.

```sh
python -m pip install -e .
host-welcome --scenario pending
host-welcome --scenario pending --format html --output welcome.html
host-welcome --scenario recovery --format html --output recovery.html
host-welcome --scenario ready --format json
python -m unittest discover -s tests -v
```

Open `welcome.html` locally in a browser. The standalone HTML has **no network dependencies**: it embeds the pinned pose-animate JavaScript and an SVG fallback for JavaScript-disabled/reduced-motion users. JavaScript is used only for optional character animation, never for status assessment. You can also supply a simulation JSON file with `--input examples/pending.json`.

## Scope and trust

The versioned readiness model covers installation, protected STATE integrity, host identity, enrollment, network, configuration, station-access and recovery. All presentations call the same validator and assessment function. Status is `verified | pending | unknown | degraded | failed`; aggregate status is `ready | setup_pending | unknown | degraded | attention`.

A `verified` claim requires a producer and an evidence reference. Input marked `source_kind: host` is **rejected** by the public CLI until a protected, read-only host producer/adapter is implemented. The only CLI input accepted today is explicitly marked `source_kind: fixture`. A simulation banner is always shown. No persistent state is written by the application. Existing authoritative protected host state is owned by its producers, not host-welcome.

See [architecture and integration boundaries](docs/architecture.md).

## Skiff

The web renderer consumes **canonical `pose-animate` geometry and animation** instead of maintaining a separate Skiff drawing. The pinned upstream revision is `b7a6e3bdb15d0a15cc8b8cbc17e295dd472dc57a` on `zog144/pose-animate`'s `unstable` branch. Its six-square-per-limb topology, joint curl, smaller square head and joined mouth are preserved. `host-welcome` selects the semantic state from assessed host readiness, with a static pose snapshot as a no-JavaScript fallback. The original attached artwork remains the reference; visual approval of the renderer is still in progress. See [provenance](docs/skiff-integration.md).

## Development

Use `unstable` for development. CI first compiles the pinned `pose-animate` source with TypeScript 5.8.3, refreshes generated browser assets, and runs standard-library tests on Python 3.11, 3.12 and 3.13. The asset build commits generated files back to `unstable` when repository token permissions permit; if not, run the sync locally (instructions below). These generated files are committed so consumers need **Python only**, not npm or a server, for ordinary rendering.

To refresh locally after an upstream review:

```sh
git clone --branch unstable https://github.com/zog144/pose-animate.git ../pose-animate
cd ../pose-animate
git checkout b7a6e3bdb15d0a15cc8b8cbc17e295dd472dc57a
npm install --no-save --no-package-lock typescript@5.8.3
npm run build
cd ../host-welcome
node scripts/sync-skiff.mjs ../pose-animate
python -m unittest discover -s tests -v
```

 Real host/installer integration and a station-access consumer are intentionally deferred until their read-only producer contracts are approved.
