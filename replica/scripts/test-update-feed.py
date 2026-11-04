#!/usr/bin/env python3
"""Test the signed update-feed contract without building or accessing GitHub."""
import base64
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location("update_feed", Path(__file__).with_name("create-update-feed.py"))
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)


class UpdateFeedTests(unittest.TestCase):
    def test_stable_universal_archive_and_system_requirement(self):
        signature = base64.b64encode(bytes(64)).decode()
        result = feed.make_feed("1.0.6", signature, 1234)
        item = result.find("channel/item")
        self.assertEqual(item.find("{" + feed.SPARKLE + "}version").text, "1.0.6")
        self.assertEqual(item.find("{" + feed.SPARKLE + "}minimumSystemVersion").text, "14.0")
        enclosure = item.find("enclosure")
        self.assertEqual(enclosure.get("url"),
            "https://github.com/yingyanzhitong/pasto/releases/download/v1.0.6/Pasto-1.0.6-macos-universal.dmg")
        self.assertEqual(enclosure.get("{" + feed.SPARKLE + "}edSignature"), signature)
        self.assertEqual(enclosure.get("length"), "1234")
        ET.fromstring(ET.tostring(result.getroot()))

    def test_invalid_versions_and_signatures(self):
        valid = base64.b64encode(bytes(64)).decode()
        for version in ["1.0", "1.0.6-dev.1", "v1.0.6", "1.0.6/evil", "1.0.6\n"]:
            with self.subTest(version=version), self.assertRaises(ValueError):
                feed.make_feed(version, valid, 1234)
        for signature, size in [("invalid", 1234), ("", 1234), (valid, 0), (valid, -1)]:
            with self.subTest(signature=signature, size=size), self.assertRaises(ValueError):
                feed.make_feed("1.0.6", signature, size)

    def test_missing_private_key_fails_before_signing(self):
        with patch.dict(feed.os.environ, {}, clear=True), patch.object(feed.subprocess, "run") as run:
            with self.assertRaises(ValueError):
                feed.create_feed(Path("missing.dmg"), "1.0.6", Path("sign_update"))
            run.assert_not_called()

    def test_private_key_uses_stdin_and_feed_is_signed_and_verified(self):
        secret = base64.b64encode(bytes(range(32))).decode()
        signature = base64.b64encode(bytes(64)).decode()
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "Pasto-1.0.6-macos-universal.dmg"
            archive.write_bytes(b"fixture")
            with patch.dict(feed.os.environ, {"PASTO_UPDATE_PRIVATE_KEY": secret}), \
                    patch.object(feed.subprocess, "run") as run:
                run.return_value.stdout = signature
                result = feed.create_feed(archive, "1.0.6", Path("sign_update"))
                self.assertEqual(result.name, "appcast.xml")
                self.assertEqual(len(run.call_args_list), 4)
                for call in run.call_args_list:
                    self.assertNotIn(secret, " ".join(map(str, call.args[0])))
                    self.assertNotIn("PASTO_UPDATE_PRIVATE_KEY", call.kwargs["env"])
                self.assertEqual(run.call_args_list[0].kwargs["input"], secret + "\n")
                self.assertIn("verify-update-signature.swift", run.call_args_list[1].args[0][1])
                self.assertEqual(run.call_args_list[2].args[0][-1], str(result))
                self.assertIn("--verify", run.call_args_list[3].args[0])


if __name__ == "__main__":
    unittest.main()
