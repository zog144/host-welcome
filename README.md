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

# A simulated launcher plan (works without a browser):
host-welcome-kiosk --scenario pending --dry-run

# On an unprivileged Linux X11 or Wayland session with Firefox/Chromium installed:
host-welcome-kiosk --scenario pending --browser auto

# Generate Windows-friendly offline preview pages:
host-welcome-previews --output-dir welcome-previews
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


## Windows HTML previews (no development tools required)

Open the GitHub repository's **Actions** tab, select **host-welcome checks**, open a successful run on `unstable`, then download the **welcome-html-previews** artifact from **Artifacts**. Unzip it on Windows and double-click `index.html` to choose among five simulated scenarios. Each generated HTML file embeds Skiff animations and a static no-JavaScript SVG fallback. No Python, npm, local HTTP server, internet access or browser extension is needed on the laptop.

Artifact bundles are generated entirely on GitHub Actions. They are **review/demo fixtures only**; the readiness status is not a report from your Windows laptop or a live Zog host.

## Optional graphical kiosk

`host-welcome-kiosk` is an unprivileged Linux launcher. It prefers Firefox (including Firefox ESR), then Chromium. Use `--browser firefox` or `--browser chromium` to require a specific engine; `--browser auto` is the default. `--dry-run` validates the simulated snapshot and prints a command template without checking displays or browser installations.

A real launch requires an existing X11/Wayland session and installed browser, runs under the invoking non-root user, and uses a dedicated temporary browser profile. The browser receives a local `file://` URL, never a remote endpoint. The launcher waits for the browser to exit and removes temporary files afterward. It refuses root, unsupported platforms, missing displays and missing browsers rather than silently installing packages or disabling the browser sandbox. `host-welcome` console mode remains independently available.

The kiosk is **not a security boundary** or an installer/enrollment UI. A display manager and compositor/session supervisor would eventually own kiosk confinement and process lifecycle. The launcher currently renders simulation inputs only.
