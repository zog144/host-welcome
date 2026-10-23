"""Authenticated response-credential consumer (no privileged host required).

Linux tests also exercise an actual AF_UNIX socketpair and SCM_CREDENTIALS.
These tests never stage host-install units or grant the production observer.
"""
import json
import os
import socket
import struct
import sys
import threading
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from host_welcome import post_install_reader as reader
from host_welcome import post_install
from host_welcome.progress_live import LiveProgressUnavailable


LINUX_CREDS = (
    sys.platform.startswith("linux")
    and all(hasattr(socket, name) for name in
            ("SCM_CREDENTIALS", "SO_PASSCRED", "CMSG_SPACE", "MSG_CTRUNC"))
    and hasattr(socket.socket, "recvmsg")
)
OLD_PIN = "7348ec730a3181f1a8ecc62a6e4d633ce191674a"
OLDER_PIN = "fcc12f3db959afe395b1adfb5b0b4dc1f16a3258"
NEW_PIN = "7b653e8be3f89730a52688d71df28513456f9cf3"


def policy(consumer_uid=10021, producer_uid=11051):
    return dict(schema=reader.POLICY_SCHEMA, enabled=True,
                consumer_uid=consumer_uid, producer_uid=producer_uid,
                socket=reader.IMAGE_SOCKET,
                image_build_source_commit=reader.IMAGE_BUILD_COMMIT)


def example_snapshot():
    return dict(
        schema=post_install.SCHEMA,
        snapshot_id="e" * 32,
        observed_at=datetime.now(timezone.utc).isoformat(),
        producer="image-build",
        producer_source={
            "contract": post_install.PRODUCER_SOURCE,
            "repository": "zog144/image-build",
            "revision": NEW_PIN,
        },
        boot_id="11111111-1111-4111-8111-111111111111",
        selection_owner="host-install",
        items=[],
        page={"has_more": False, "next_after": None},
    )


class ImagePolicyTests(unittest.TestCase):
    def test_exact_reviewed_source_and_fixed_role(self):
        self.assertEqual(reader.IMAGE_BUILD_COMMIT, NEW_PIN)
        self.assertEqual(post_install.PRODUCER_PIN, NEW_PIN)
        self.assertEqual(post_install.WIRE, "image-build-post-install-progress-rpc-v2")
        self.assertEqual(reader.TRANSPORT_AUTH,
                         "image-build-post-install-progress-linux-credentials-v1")
        self.assertNotEqual(reader.IMAGE_SOCKET,
                            "/run/zog-host-export/application-progress/application-progress.sock")
        self.assertEqual(reader.validate_image_policy(policy())["producer_uid"], 11051)
        for name, value in (("consumer_uid", 0), ("producer_uid", 0),
                            ("producer_uid", 10021), ("enabled", False),
                            ("image_build_source_commit", OLD_PIN),
                            ("image_build_source_commit", OLDER_PIN),
                            ("image_build_source_commit", "0" * 40),
                            ("socket", "/run/zog-host-export/application-progress/application-progress.sock")):
            with self.subTest(name=name, value=value):
                with self.assertRaises(LiveProgressUnavailable):
                    reader.validate_image_policy(dict(policy(), **{name: value}))
        with self.assertRaises(LiveProgressUnavailable):
            reader.validate_image_policy(dict(policy(), extra=True))

    def test_policy_not_installed_fails_closed(self):
        with patch("host_welcome.post_install_reader.os.open", side_effect=FileNotFoundError()):
            with self.assertRaises(LiveProgressUnavailable):
                reader.read_image_policy()

    def test_wrong_consumer_is_denied_before_socket_creation(self):
        with patch("host_welcome.progress_live._welcome_uid", return_value=10021), \
             patch("host_welcome.post_install_reader.os.geteuid", return_value=99999, create=True), \
             patch("host_welcome.post_install_reader.socket.socket") as create:
            with self.assertRaises(LiveProgressUnavailable):
                reader.request_image_progress(policy_reader=policy)
            create.assert_not_called()

    def test_unavailable_kernel_credential_api_denied(self):
        with patch("host_welcome.progress_live._welcome_uid", return_value=10021), \
             patch("host_welcome.post_install_reader.os.geteuid", return_value=10021, create=True), \
             patch("host_welcome.post_install_reader.socket.SCM_CREDENTIALS",
                   None, create=True), \
             patch("host_welcome.post_install_reader.socket.socket") as create:
            # Patching to None still satisfies hasattr, but must not produce
            # a successful verified response or an actual host claim.
            with self.assertRaises(LiveProgressUnavailable):
                reader.request_image_progress(policy_reader=policy)
        # Remove the attribute altogether to verify the feature check itself.
        if LINUX_CREDS:
            with patch("host_welcome.progress_live._welcome_uid", return_value=10021), \
                 patch("host_welcome.post_install_reader.os.geteuid",
                       return_value=10021, create=True), \
                 patch("host_welcome.post_install_reader.socket.socket") as create:
                original = socket.SCM_CREDENTIALS
                try:
                    del socket.SCM_CREDENTIALS
                    with self.assertRaises(LiveProgressUnavailable):
                        reader.request_image_progress(policy_reader=policy)
                    create.assert_not_called()
                finally:
                    socket.SCM_CREDENTIALS = original


@unittest.skipUnless(LINUX_CREDS, "Linux SCM_CREDENTIALS required")
class KernelCredentialTests(unittest.TestCase):
    def good_record(self, uid=11051, pid=52):
        return (socket.SOL_SOCKET, socket.SCM_CREDENTIALS,
                struct.pack("3i", pid, uid, 3030))

    class Fake:
        def __init__(self, response):
            self.response = response
            self.tail = b"\x00\x00\x06"  # completes a first-byte length
            self.sent = []
            self.opt = []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def settimeout(self, *_):
            pass

        def setsockopt(self, *args):
            self.opt.append(args)

        def connect(self, path):
            assert path == reader.IMAGE_SOCKET

        def getsockopt(self, *_):
            raise AssertionError("listener SO_PEERCRED is not responder authentication")

        def sendall(self, data):
            self.sent.append(data)

        def recvmsg(self, maxsize, ancsize):
            assert maxsize == 4
            assert ancsize >= socket.CMSG_SPACE(struct.calcsize("3i"))
            return self.response

        def recv(self, count):
            result = self.tail[:count]
            self.tail = self.tail[count:]
            return result

    def call_fake(self, response):
        fake = self.Fake(response)
        with patch("host_welcome.progress_live._welcome_uid", return_value=10021), \
             patch("host_welcome.post_install_reader.os.geteuid",
                   return_value=10021, create=True), \
             patch("host_welcome.post_install_reader.socket.socket", return_value=fake), \
             patch("host_welcome.post_install_reader.json.loads",
                   side_effect=AssertionError("must reject before JSON")) as decode:
            with self.assertRaises(LiveProgressUnavailable):
                reader.request_image_progress(policy_reader=policy)
            decode.assert_not_called()
        self.assertEqual(fake.opt, [(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)])
        self.assertEqual(len(fake.sent), 1)

    def test_missing_duplicate_wrong_or_truncated_credentials_rejected_pre_json(self):
        good = self.good_record()
        cases = (
            (b"\0", [], 0, None),  # absent
            (b"\0", [good, good], 0, None),  # duplicate
            (b"\0", [self.good_record(uid=0)], 0, None),
            (b"\0", [self.good_record(uid=11052)], 0, None),
            (b"\0", [self.good_record(pid=0)], 0, None),
            (b"\0", [(socket.SOL_SOCKET, socket.SCM_CREDENTIALS, good[2][:8])], 0, None),
            (b"\0", [(socket.SOL_SOCKET, 888, good[2])], 0, None),
            (b"\0", [(888, socket.SCM_CREDENTIALS, good[2])], 0, None),
            (b"\0", [good], socket.MSG_CTRUNC, None),
            (b"", [good], 0, None),
        )
        for response in cases:
            with self.subTest(case=str(response)[:100]):
                self.call_fake(response)

    def test_header_fragmentation_missing_bytes_fails_closed(self):
        fake = self.Fake((b"\0", [self.good_record()], 0, None))
        fake.tail = b""  # server disconnected after authenticated first byte
        with self.assertRaises(LiveProgressUnavailable):
            reader._credentialed_header(fake, 11051)


@unittest.skipUnless(LINUX_CREDS and os.geteuid() != 0,
                     "actual unprivileged Linux AF_UNIX credentials required")
class RealLinuxSocketTests(unittest.TestCase):
    def test_kernel_credentials_authenticate_sender_not_listener_creator(self):
        """The kernel supplies responder UID on the explicit first-byte sendmsg."""
        producer_uid = os.geteuid()
        consumer_uid = producer_uid + 101
        left, right = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        errors = []
        received_requests = []

        class ConnectedClient:
            """Already-connected socket; pretend listener SO_PEERCRED is root."""
            def __init__(self, underlying):
                self.underlying = underlying
                self.setopts = []

            def __enter__(self):
                return self

            def __exit__(self, *_):
                self.underlying.close()

            def settimeout(self, seconds):
                self.underlying.settimeout(seconds)

            def setsockopt(self, *args):
                self.setopts.append(args)
                return self.underlying.setsockopt(*args)

            def connect(self, path):
                self.path = path

            def getsockopt(self, *args):
                raise AssertionError("do not inspect listener's root credentials")

            def sendall(self, data):
                return self.underlying.sendall(data)

            def recvmsg(self, *args):
                return self.underlying.recvmsg(*args)

            def recv(self, *args):
                return self.underlying.recv(*args)

        def exact(sock, count):
            parts = []
            while count:
                chunk = sock.recv(count)
                if not chunk:
                    raise OSError("request truncated")
                parts.append(chunk)
                count -= len(chunk)
            return b"".join(parts)

        def serve():
            try:
                with right:
                    right.settimeout(5)
                    size = struct.unpack("!I", exact(right, 4))[0]
                    req = json.loads(exact(right, size))
                    received_requests.append(req)
                    reply = json.dumps({"ok": True, "result": example_snapshot()},
                                       separators=(",", ":")).encode()
                    framed = struct.pack("!I", len(reply)) + reply
                    cmsg = [(socket.SOL_SOCKET, socket.SCM_CREDENTIALS,
                             struct.pack("3i", os.getpid(), producer_uid, os.getegid()))]
                    self.assertEqual(right.sendmsg([framed[:1]], cmsg), 1)
                    right.sendall(framed[1:])
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=serve)
        thread.start()
        client = ConnectedClient(left)
        modified_policy = policy(consumer_uid=consumer_uid, producer_uid=producer_uid)
        with patch("host_welcome.progress_live._welcome_uid",
                   return_value=consumer_uid), \
             patch("host_welcome.post_install_reader.os.geteuid",
                   return_value=consumer_uid, create=True), \
             patch("host_welcome.post_install_reader.socket.socket", return_value=client):
            result = reader.request_image_progress(
                policy_reader=lambda: modified_policy)
        thread.join(timeout=7)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result["schema"], post_install.SCHEMA)
        self.assertEqual(result["items"], [])
        self.assertEqual(client.path, reader.IMAGE_SOCKET)
        self.assertIn((socket.SOL_SOCKET, socket.SO_PASSCRED, 1), client.setopts)
        self.assertEqual(received_requests, [{
            "schema": post_install.WIRE, "operation": "snapshot",
            "after": None, "limit": 4,
        }])
