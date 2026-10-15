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

Open `welcome.html` locally in a browser. The standalone HTML has no network or JavaScript dependencies and can be used as a desktop/web concept preview. You can also supply a simulation JSON file with `--input examples/pending.json`.

## Scope and trust

The versioned readiness model covers installation, protected STATE integrity, host identity, enrollment, network, configuration, station-access and recovery. All presentations call the same validator and assessment function. Status is `verified | pending | unknown | degraded | failed`; aggregate status is `ready | setup_pending | unknown | degraded | attention`.

A `verified` claim requires a producer and an evidence reference. Input marked `source_kind: host` is **rejected** by the public CLI until a protected, read-only host producer/adapter is implemented. The only CLI input accepted today is explicitly marked `source_kind: fixture`. A simulation banner is always shown. No persistent state is written by the application. Existing authoritative protected host state is owned by its producers, not host-welcome.

See [architecture and integration boundaries](docs/architecture.md).

## Skiff

`src/host_welcome/assets/skiff.svg` is a geometric SVG interpretation of the user-supplied blue pixel-octopus concept: **square head, no eyebrows, eight arms made of discrete outlined squares**. The original attached artwork remains the design reference, not a claim of a new trademark or separate license. Before redistributing the mascot independently, agree on the artwork's explicit licensing terms.

## Development

Use `unstable` for development. CI runs standard-library tests on Python 3.11, 3.12 and 3.13. Real host/installer integration and a station-access consumer are intentionally deferred until their read-only producer contracts are approved.
