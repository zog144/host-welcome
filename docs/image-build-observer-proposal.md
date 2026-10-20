# Draft image-build observer transport — source-only

The image-build source projection `image-build-post-install-progress-v2` is implemented and reviewed in code at `fcc12f3db959afe395b1adfb5b0b4dc1f16a3258`. The consumer can validate and join an authenticated producer page with the controller's independently peer-checked progress. Native observer staging and authority remain **unapproved**; the fixed path and root-owned policy below are a **proposal for host-install and image-build review**, not a deployed or finalized protocol.

- Proposed dedicated AF_UNIX socket: `/run/host-welcome/image-progress.sock` served by an independently non-root image-build producer UID.
- Proposed root-owned policy: `/etc/zog/host-welcome-image-progress-observer.json` with exact schema `zog-host-welcome-image-progress-observer-v1`, `enabled`, distinct numeric `consumer_uid` and `producer_uid`, fixed `socket`, and pinned `image_build_source_commit`.
- Consumer requires the actual dedicated `host-welcome` numeric UID, authenticates `SO_PEERCRED` before sending a framed bounded `snapshot` request, and accepts only exact bounded response schemas. A source-commit value in a root policy is metadata, **not** a substitute for installed byte attestation.
- If policy or socket is unavailable or failed authentication, image-build publication is UNOBSERVED; headless console and authenticated host-install/bootstrap/controller observations remain available. No raw paths, source directories, logs, credentials, transport selectors or mutation operations can be supplied through the CLI.

The producer implementation requires systemd-activated one-socket AF_UNIX and permits only a fixed allowlist. It should also be reviewed against the consumer's exact socket path, protected parent directory, UID peer enforcement and native SELinux/LSM requirements. No unit, privilege grant or policy is installed by host-welcome. **This is not production activation authorization.**
