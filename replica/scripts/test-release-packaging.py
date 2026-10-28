#!/usr/bin/env python3
"""Check the one-DMG/two-architecture release contract without a macOS build."""
import importlib.util
import json
from pathlib import Path
import plistlib
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("release_ci", Path(__file__).with_name("release-ci.py"))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class UniversalReleaseTests(unittest.TestCase):
    def test_exactly_one_installer(self):
        self.assertEqual(release.asset_names("1.0.0"), [
            "Pasto-1.0.0-macos-universal.dmg", "SHA256SUMS.txt", "release-manifest.json"])

    def test_package_is_universal_and_records_both_architectures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            commands = []

            def run(args):
                commands.append(args)
                if args[1].endswith("build-dmg.sh"):
                    Path(args[3]).write_bytes(b"fixture-dmg")

            with patch.object(release, "ROOT", root), patch.object(release.platform, "system", return_value="Darwin"), \
                    patch.object(release, "run", side_effect=run), \
                    patch.object(release, "verify_app") as app_check, patch.object(release, "verify_dmg") as dmg_check:
                release.package("1.0.0", "v1.0.0", "fixture-commit")
                self.assertEqual(commands[0], ["bash", "replica/scripts/build-app.sh", "release", "universal"])
                self.assertEqual(len(commands), 2)
                self.assertEqual(commands[1][-1], "universal")
                self.assertEqual(app_check.call_args.args[2], ["arm64", "x86_64"])
                self.assertEqual(dmg_check.call_args.args[2], ["arm64", "x86_64"])
            output = root / "replica/dist/release"
            self.assertEqual(len(list(output.glob("*.dmg"))), 1)
            manifest = json.loads((output / "release-manifest.json").read_text())
            self.assertEqual(len(manifest["archives"]), 1)
            self.assertEqual(manifest["archives"][0]["architectures"], ["arm64", "x86_64"])

    def test_every_executable_must_include_both_architectures(self):
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "Pasto.app"
            (app / "Contents").mkdir(parents=True)
            (app / "Contents/Info.plist").write_bytes(plistlib.dumps({
                "CFBundleExecutable": "Pasto", "CFBundleDisplayName": "Pasto",
                "CFBundleShortVersionString": "1.0.0", "CFBundleVersion": "1.0.0", "PastoSourceVersion": "1.0.0"}))
            for thin_binary in [None, "Pasto", "pasto-mcp", "PastoHelper"]:
                with self.subTest(thin_binary=thin_binary):
                    def run(args, **kwargs):
                        thin = args[0] == "lipo" and Path(args[-1]).name == thin_binary
                        return SimpleNamespace(stdout="arm64" if thin else "arm64 x86_64")
                    with patch.object(release, "run", side_effect=run):
                        if thin_binary is None:
                            release.verify_app(app, "1.0.0", ["arm64", "x86_64"])
                        else:
                            with self.assertRaisesRegex(ValueError, "Unexpected executable architectures"):
                                release.verify_app(app, "1.0.0", ["arm64", "x86_64"])


if __name__ == "__main__":
    unittest.main()
