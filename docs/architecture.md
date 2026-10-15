# host-welcome v1 architecture and integration boundary

## Purpose

A presentation-agnostic, read-only first-boot and recovery welcome, usable before station-access or any graphical session. Skiff supplies personality; evidence supplies facts. The CLI, later station-access adapter, and optional desktop share one versioned snapshot and assessment policy.

## Existing authorities (no ownership transfer)

* **host-install:** verified installation records, STATE validation, and verified booted-generation provenance; provisioning/writing remains host-install's own gated operation.
* **host-identify:** persistent Ed25519 identity. host-welcome never creates, exports or replaces private keys.
* **host-discover / station-access:** protected admission and authorized enrollment/hostname assignment, not implied by existence of an identity.
* **host-deploy:** deployment and approved lifecycle changes, not triggered by viewing status.
* **Network and web service:** separate link, reachability and station-access health producers; link detection is not proof HTTPS readiness.

See https://github.com/zog144/host-install/blob/main/docs/host-install/architecture.md .

## V1 contract

Schema `host-welcome.readiness/v1` includes `source_kind`, `observed_at` (timezone-aware ISO 8601), a display-only `host_label`, and exactly eight observations: installation, state_integrity, host_identity, enrollment, network, configuration, station_access, recovery.

Each observation contains `status`, `summary`, `producer`, and nullable `evidence_ref`. `verified` demands nonempty evidence_ref (an identifier, **not** certificate, credential, private key, raw STATE document or sensitive URL). `unknown` is not treated as success. Unknown fields/statuses/schema are rejected, not silently ignored. Rendering escapes the variable display strings.

Aggregate precedence: any failed → attention; else degraded → degraded; else unknown → unknown; else pending → setup_pending; otherwise ready. For trusted host-origin snapshots, evidence older than five minutes or dated more than 60 seconds into the future gives an aggregate of unknown; fixtures are explicitly simulated and do not expire. The freshness rule is applied before other status aggregation, so an old success cannot masquerade as current readiness.

## Trust and durability

Protected **producer state** remains durable across reboot; host-welcome does not hold the canonical state or maintain an independent state machine. Future integration must retrieve an atomic, authenticated snapshot over a protected local channel and validate it before setting `trusted=True`. A local file, arbitrary HTTP response, or caller-supplied JSON is not trusted just because it says `source_kind: host`.

At this milestone the CLI *only* accepts `source_kind: fixture`, including when reading `--input`. No systemd, host socket, HTTP listener, state mutation, root privilege, or remote telemetry is provided. If source authority or freshness cannot be established, report unknown, not ready.

## Future producer adapter: acceptance gates

1. Define an authenticated read-only UNIX socket or other protected transport with a versioned request/response and immutable snapshot ID.
2. Map authoritative producer-specific states and evidence references without guessing, and return unknown where producers are unavailable or contradictory.
3. Bound observation age; detect snapshot mismatch across reboot/generation and reject replay/future clocks.
4. Preserve protected STATE and installer/identity ownership; all enrollment, recovery, reset and certificate operations require distinct authorized controls.
5. Integrate one shared JSON snapshot into console, station-access and optional desktop clients; accessibility and headless execution remain mandatory.
6. Run interrupted-write, reboot, DNS/network loss, failed STATE integrity and conflicting-enrollment acceptance tests with synthetic/isolated hosts, then real host tests when images exist.

## Limitations

This is a design/simulated-test milestone, not bootability verification, proof of secure boot, station enrollment, production read-only adapter, actual HTTPS readiness, or authorization of recovery.
