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

The web renderer consumes **canonical `pose-animate` geometry and animation** instead of maintaining a separate Skiff drawing. The pinned upstream revision is `ec5e8986be294a187e4d257df883dccfabea1034` on `zog144/pose-animate`'s `unstable` branch. Its six-square-per-limb topology, joint curl, smaller square head and joined mouth are preserved. `host-welcome` selects the semantic state from assessed host readiness, through the upstream 0.3 presenter API, with a static pose snapshot as a no-JavaScript fallback. The original attached artwork remains the reference; visual approval of the renderer is still in progress. Upstream is an unpublished `0.3.0-rc.0` candidate, licensed **BSD-3-Clause OR GPL-3.0-only** (BSD license text supplied with the generated assets). See [provenance](docs/skiff-integration.md).

## Development

Use `unstable` for development. CI first compiles the pinned `pose-animate` source with TypeScript 5.8.3, refreshes generated browser assets, and runs standard-library tests on Python 3.11, 3.12 and 3.13. The asset build commits generated files back to `unstable` when repository token permissions permit; if not, run the sync locally (instructions below). These generated files are committed so consumers need **Python only**, not npm or a server, for ordinary rendering.

To refresh locally after an upstream review:

```sh
git clone --branch unstable https://github.com/zog144/pose-animate.git ../pose-animate
cd ../pose-animate
git checkout ec5e8986be294a187e4d257df883dccfabea1034
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

## Simulation-first application progress (Handoff F / Phase 1)

Use the separate dependency-free console tool to inspect representative post-install progress without launching builds or inspecting protected host state:

```sh
host-welcome-progress --scenario building
host-welcome-progress --scenario blocked
host-welcome-progress --scenario uncertain
host-welcome-progress --scenario published
host-welcome-progress --scenario headless
host-welcome-progress --scenario unavailable
host-welcome-progress --scenario building --format json
```

`host-welcome-progress --input /path/to/fixture.json` accepts **simulation fixtures only**, under `host-welcome.progress-fixture/v1`; no input file can gain live authority. The underlying controller section is the exact validated `zog-application-progress-v1` subset; image-build and installation sections are **local fixture formats, not upstream production schemas**. The console explicitly separates verified headless installation, optional application request intent, phase-limited build outcomes, separately evidenced publication and **unverified** graphical/login readiness. No invented progress percentages, ETA, automatic polling, requested-state inference from empty controller pages, or privilege escalation. See [application-progress contract and tests](docs/application-progress.md).

The production `host-welcome` UID does **not** currently have access to the station-access-only observer socket. The live adapter/authoritative image-build publication join, native systemd and getty acceptance, and greetd privileged PAM/local-seat role remain separate gates.


## Phase 2 protected live observation (one-shot, opt-in)

Run host-welcome-progress --live only as the dedicated non-root host-welcome account. The optional bootstrap reader calls the official zog.host_install.welcome_readiness.request_live() from the reviewed installed host-install package. That client authenticates a fixed root-owned AF_UNIX socket, root peer UID, response nonce, current boot and freshness. A caller-supplied JSON file never gains host authority.

The controller section requires a separate root-owned policy at /etc/zog/host-welcome-progress-observer.json and a dedicated /run/host-welcome/controller-progress.sock granting only the host-welcome numeric UID. It never reuses the station-access web listener. The reviewed box-control ApplicationProgressClient authenticates the pinned controller-owner UID and validates the bounded RPC. Missing configuration/package/socket/permission means controller unavailable, not build success. The root-only deployment must verify the actual UID identities, source package pin, service and socket ownership, and application view visibility before enabling the listener. The policy is never constructed from CLI input; --live --output is refused.

Image-build's authenticated attempt/application/publication projection is not deployed. Regardless of controller observation, optional app request intent and publication remain unknown/unobserved; graphical login is always not-verified. This command makes one bounded read and never automatically polls, builds, retries or mutates STATE. Tests use injected fakes only; a green source test is not native socket/getty acceptance.

**Dedicated observer contract adopted (2026-10-17):** host-install now stages a separately UID-authorized socket and reviewed installed wheel attestation; box-control's dedicated read-only broker is source-tested. Host-welcome pins the compatible controller source revision \u00608249715708c6ef8a1fd30a3fb529b4034ffffe25\u0060 in its protected policy, but this is metadata, never byte proof. Live activation still requires disposable-host systemd/UID/SELinux/getty acceptance. Simulation mode remains usable on Windows. See [Phase 2 adoption details](docs/application-progress-live.md).
