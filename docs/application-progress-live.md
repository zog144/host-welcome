# Phase 2: authenticated one-shot progress adaptation

**2026-10-17 source implementation only. Native socket/getty acceptance not completed.**
Handoff F Phase 1 simulation fixtures remain isolated; no live producer can be
provided through --input and no fixture can receive host authority.

## Read-only path

host-welcome-progress --live is a one-shot console/JSON view with **no host-controlled
path options** and no writable output path. Its first producer is the installed
host-install official welcome_readiness.request_live() client, which already
verifies a dedicated non-login host-welcome UID, fixed root-owned
/run/host-install/welcome.sock, root peer via SO_PEERCRED, nonce, active boot,
response schema and freshness. If the package, socket or UID is unavailable,
the display honestly reports headless UNKNOWN, controller UNAVAILABLE and
publication UNOBSERVED.

After bootstrap acceptance it attempts an **independent** controller observation.
This is disabled until an installation owner stages a *separate* root-owned
/etc/zog/host-welcome-progress-observer.json policy and
/run/host-welcome/controller-progress.sock listener. The latter must use
SocketUser/Mode and kernel SO_PEERCRED to permit only the actual dedicated
host-welcome numeric UID, running its broker as the distinct non-root controller
project owner. The station-access socket at
/run/zog-host-export/application-progress/application-progress.sock is NEVER used
for this console role. Controller access is optional and independently fails
closed.

The fixed root-owned policy has exact schema zog-host-welcome-progress-observer-v1,
enabled=true, consumer_uid, controller_owner_uid, socket (must equal exact fixed
path), and box_control_source_commit (reviewed full lowercase Git SHA). It
rejects symlinked policy files, group/other-write permissions, unowned policy
and duplicate/missing/unknown JSON fields; source actual installed bytes must
be independently pinned by host-install or host-deploy before enabling. Policy
cannot elevate the host-welcome account or grant installation authority.
The source adapter imports the matching box-control strict
ApplicationProgressClient lazily; the peer UID, current boot ID, snapshot
fields, item enums and bounds are checked before console use.

This is a *consumer readiness implementation*, not confirmation that a
dedicated broker service, authenticated root policy or box-control client
software dependency has been deployed. Native systemd, UID/ACL/SELinux,
controller package source pin and getty acceptance are still required.

## Claims

Authenticated host-install headless status can be shown independently of
optional app downloads. The authenticated controller shows bounded raw
build-command and runtime rows, not names or publication for unassociated
build jobs. Image-build request intent is UNKNOWN and publication is
UNOBSERVED until its separate authenticated owner producer is agreed and
accepted. A running controller runtime does not prove browser rendering,
greetd authentication, or local X11/Wayland seat readiness.

No stale/previous-boot controller page, inconsistent schema, malformed ID,
unsupported operation or missing transport yields success; the tool displays
unavailability without exposing raw host paths or producer exception details.
There are no background refresh timers, auto retries, build submissions,
service commands, graphical handoffs, root operations or state writes.

## Next owner dependencies

1. host-install + box-control/root-control: supply dedicated numeric-UID
   console progress broker socket, root-owned policy, reviewed exact controller
   client dependency, protected state-independent boot order, native denial and
   reboot/getty acceptance.
2. image-build: deliver an authenticated read-only durable
   attempt/stage/package/command/job association plus separately verified
   artifact/view publication; see the new 2026-10-17 image-build handoff
   in know-file.
3. host-welcome: after both producers are accepted, add authoritative
   image-build publication and request intent joining, with source/revision
   conflict and stale observation tests, then safe bounded opt-in refresh
   separate from login/TTY control.
