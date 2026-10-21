# Adopted image-build SCM_CREDENTIALS consumer protocol — source acceptance

The image-build source projection `image-build-post-install-progress-v2` is implemented and reviewed in code at `7348ec730a3181f1a8ecc62a6e4d633ce191674a`. The consumer can validate and join an authenticated producer page with the controller's independently peer-checked progress. The producer transport is reviewed as `image-build-post-install-progress-linux-credentials-v1`; host-install owns protected installation and native attestation. Source implementation is not authorization to enable this observer on an unaccepted production host.

- Dedicated AF_UNIX socket: `/run/host-welcome/image-progress.sock` served by an independently non-root image-build producer UID.
- Protected root-owned policy: `/etc/zog/host-welcome-image-progress-observer.json` with exact schema `zog-host-welcome-image-progress-observer-v1`, `enabled`, distinct numeric `consumer_uid` and `producer_uid`, fixed `socket`, and pinned `image_build_source_commit`.
- Consumer requires the actual dedicated `host-welcome` numeric UID and kernel `SO_PASSCRED` / `SCM_CREDENTIALS` support. The fixed, secret-free read-only `snapshot` request precedes producer authentication. The image-build broker sends the first response byte using `sendmsg` with Linux `SCM_CREDENTIALS`. The consumer receives the initial header via `recvmsg`, rejects missing/ambiguous/truncated records or wrong PID/UID before decoding JSON, completes the 4-byte header, checks reply bounds and the exact image-build v2 snapshot/source/boot/freshness. Under systemd socket activation **connected `SO_PEERCRED` refers to PID 1/root**, and is never trusted as the non-root responder. The producer source pin embedded in protected policy is metadata, **not** a substitute for installed byte attestation.
- If policy or socket is unavailable or failed authentication, image-build publication is UNOBSERVED; headless console and authenticated host-install/bootstrap/controller observations remain available. No raw paths, source directories, logs, credentials, transport selectors or mutation operations can be supplied through the CLI.

The producer implementation requires systemd-activated one-socket AF_UNIX and permits only a fixed allowlist. It should also be reviewed against the consumer's exact socket path, protected parent directory, UID peer enforcement and native SELinux/LSM requirements. No unit, privilege grant or policy is installed by host-welcome. **This is not production activation authorization.**

## Versioned source adoption (October 21, 2026)

- Reviewed runtime/projection source: `7348ec730a3181f1a8ecc62a6e4d633ce191674a`.
- Deployment reference: `10d5c89f9ad865f3f58094ba2b5a629c211d918d`.
- Broker blob: `e7ba6eab10e70e91fc5921bba1eec26f31ace1db`.
- JSON/RPC remains `image-build-post-install-progress-rpc-v2`; no v3 or policy schema change.
- Transport v1 authenticates **the first reply byte** with a kernel credential record. Subsequent stream bytes belong to this bounded single-response exchange; native Work tests must verify actual systemd/AF_UNIX response behavior. This consumer does not claim to authenticate a separately delegated writer for every subsequent byte.
- The producer also handles a disconnected authorized consumer per connection; source and native testing are separate gates.
- [host-welcome issue #1](https://github.com/zog144/host-welcome/issues/1) tracks consumer acceptance. [host-install issue #1](https://github.com/zog144/host-install/issues/1) tracks actual UID derivation, aggregate wheel source-byte attestation, staged systemd units and fresh native rerun. Existing console/getty fallback remains independent.
