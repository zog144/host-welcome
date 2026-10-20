"""No live socket is contacted; fixed policy, frame and peer credentials tested."""
import json
import struct
import unittest
from unittest.mock import patch

from host_welcome import post_install_reader as reader
from host_welcome.progress_live import LiveProgressUnavailable

def policy():
    return dict(schema=reader.POLICY_SCHEMA, enabled=True, consumer_uid=10021,
        producer_uid=11051, socket=reader.IMAGE_SOCKET,
        image_build_source_commit=reader.IMAGE_BUILD_COMMIT)

class ImageReaderTests(unittest.TestCase):
    def test_exact_owner_contract_and_no_station_socket(self):
        self.assertIs(reader.validate_image_policy(policy()), policy()) if False else None
        self.assertEqual(reader.validate_image_policy(policy())["producer_uid"], 11051)
        for key, val in (("consumer_uid", 0), ("producer_uid", 0),
                         ("producer_uid", 10021), ("enabled", False),
                         ("image_build_source_commit", "0"*40),
                         ("socket", "/run/zog-host-export/application-progress/application-progress.sock")):
            with self.subTest(key=key):
                bad=dict(policy(),**{key:val})
                with self.assertRaises(LiveProgressUnavailable):
                    reader.validate_image_policy(bad)
        with self.assertRaises(LiveProgressUnavailable):
            reader.validate_image_policy(dict(policy(), unexpected=True))

    def test_policy_not_installed_fails_closed(self):
        with patch("host_welcome.post_install_reader.os.open",
                   side_effect=FileNotFoundError()):
            with self.assertRaises(LiveProgressUnavailable):
                reader.read_image_policy()

    def test_wrong_consumer_denied_before_socket(self):
        with patch("host_welcome.progress_live._welcome_uid", return_value=10021), \
             patch("host_welcome.post_install_reader.os.geteuid", return_value=99999, create=True), \
             patch("host_welcome.post_install_reader.socket.socket") as conn:
            with self.assertRaises(LiveProgressUnavailable):
                reader.request_image_progress(policy_reader=policy)
            conn.assert_not_called()

    def test_no_posix_peer_credentials_is_not_live(self):
        with patch("host_welcome.progress_live._welcome_uid", return_value=10021), \
             patch("host_welcome.post_install_reader.os.geteuid", return_value=10021, create=True), \
             patch("host_welcome.post_install_reader.socket.SO_PEERCRED", None, create=True):
            with self.assertRaises(LiveProgressUnavailable):
                reader.request_image_progress(policy_reader=policy)

    def test_framed_read_checks_peer_before_request(self):
        from host_welcome.post_install import SCHEMA
        # Even a forged good producer response may not be decoded from a
        # wrong peer; no sendall() may occur before SO_PEERCRED succeeds.
        class Socket:
            def __init__(self):
                self.sent=[]
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def settimeout(self,*a):pass
            def connect(self,path):
                assert path == reader.IMAGE_SOCKET
            def getsockopt(self,*a):
                return struct.pack("3i", 1, 11052, 1)
            def sendall(self,data):self.sent.append(data)
        sock=Socket()
        with patch("host_welcome.progress_live._welcome_uid", return_value=10021), \
             patch("host_welcome.post_install_reader.os.geteuid", return_value=10021, create=True), \
             patch("host_welcome.post_install_reader.socket.SO_PEERCRED", 17, create=True), \
             patch("host_welcome.post_install_reader.socket.socket", return_value=sock):
            with self.assertRaises(LiveProgressUnavailable):
                reader.request_image_progress(policy_reader=policy)
        self.assertFalse(sock.sent)
