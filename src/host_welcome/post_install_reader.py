"""Optional image-build AF_UNIX reader; fixed root-installed role, no user paths.

DRAFT consumer deployment policy: not activated by this repository.
Native socket/unit, producer source attestation and protected host-install
selection policy must be accepted independently before this transport is used.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import socket
import stat
import struct

from .post_install import WIRE, validate_image_snapshot
from .progress_live import LiveProgressUnavailable, _no_duplicates

IMAGE_POLICY = Path("/etc/zog/host-welcome-image-progress-observer.json")
IMAGE_SOCKET = "/run/host-welcome/image-progress.sock"
IMAGE_BUILD_COMMIT = "857bb454e64102afa51a93ce0b9f8cce5924b67c"
POLICY_SCHEMA = "zog-host-welcome-image-progress-observer-v1"
MAX_CONFIG = 2048
MAX_FRAME = 65536


def validate_image_policy(policy):
    """Exact proposed deployment contract, not a replacement for byte attestation."""
    if (type(policy) is not dict or set(policy) != {
            "schema", "enabled", "consumer_uid", "producer_uid", "socket",
            "image_build_source_commit"}
            or policy["schema"] != POLICY_SCHEMA
            or policy["enabled"] is not True
            or policy["socket"] != IMAGE_SOCKET
            or policy["image_build_source_commit"] != IMAGE_BUILD_COMMIT
            or type(policy["consumer_uid"]) is not int
            or type(policy["producer_uid"]) is not int
            or not 1 <= policy["consumer_uid"] < 2**31
            or not 1 <= policy["producer_uid"] < 2**31
            or policy["consumer_uid"] == policy["producer_uid"]):
        raise LiveProgressUnavailable("image-build observer policy invalid/unreviewed")
    return policy


def read_image_policy():
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise LiveProgressUnavailable("protected image-build policy unsupported")
    try:
        parent = os.open(str(IMAGE_POLICY.parent),
                         os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            st = os.fstat(parent)
            if (not stat.S_ISDIR(st.st_mode) or st.st_uid != 0
                    or stat.S_IMODE(st.st_mode) & 0o022):
                raise LiveProgressUnavailable("unsafe image-build policy directory")
            fd = os.open(IMAGE_POLICY.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
            try:
                st = os.fstat(fd)
                if (not stat.S_ISREG(st.st_mode) or st.st_uid != 0
                        or stat.S_IMODE(st.st_mode) & 0o022 or st.st_size < 1
                        or st.st_size > MAX_CONFIG):
                    raise LiveProgressUnavailable("unsafe image-build policy")
                raw = os.read(fd, MAX_CONFIG + 1)
            finally:
                os.close(fd)
        finally:
            os.close(parent)
        if len(raw) > MAX_CONFIG:
            raise LiveProgressUnavailable("image-build observer policy too large")
        return validate_image_policy(json.loads(raw, object_pairs_hook=_no_duplicates))
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        raise LiveProgressUnavailable("image-build observer policy missing or invalid") from exc


def _exact(conn, count):
    parts = []
    while count:
        chunk = conn.recv(count)
        if not chunk:
            raise LiveProgressUnavailable("truncated image-build progress reply")
        parts.append(chunk)
        count -= len(chunk)
    return b"".join(parts)


def request_image_progress(*, policy_reader=None):
    """One read from fixed reviewed broker; SO_PEERCRED before framing."""
    policy_reader = policy_reader or read_image_policy
    try:
        policy = validate_image_policy(policy_reader())
        from .progress_live import _welcome_uid
        if not hasattr(os, "geteuid") or not (os.geteuid() == _welcome_uid() == policy["consumer_uid"]):
            raise LiveProgressUnavailable("wrong dedicated image-progress consumer UID")
        if not hasattr(socket, "SO_PEERCRED"):
            raise LiveProgressUnavailable("kernel peer credentials unavailable")
        payload = json.dumps({
            "schema": WIRE, "operation": "snapshot", "after": None, "limit": 4,
        }, separators=(",", ":")).encode("ascii")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(12)
            conn.connect(IMAGE_SOCKET)
            creds = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED,
                                    struct.calcsize("3i"))
            _pid, uid, _gid = struct.unpack("3i", creds)
            if uid != policy["producer_uid"]:
                raise LiveProgressUnavailable("wrong image-build producer peer")
            conn.sendall(struct.pack("!I", len(payload)) + payload)
            count = struct.unpack("!I", _exact(conn, 4))[0]
            if not 0 < count <= MAX_FRAME:
                raise LiveProgressUnavailable("unbounded image-build reply")
            reply = json.loads(_exact(conn, count), object_pairs_hook=_no_duplicates)
        if (type(reply) is not dict or set(reply) != {"ok", "result"}
                or reply["ok"] is not True):
            raise LiveProgressUnavailable("image-build producer unavailable")
        return validate_image_snapshot(reply["result"])
    except Exception as exc:
        raise LiveProgressUnavailable("authenticated image-build progress unavailable") from exc
