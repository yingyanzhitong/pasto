"""Exercise release validation and real README/website rendering without network."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("sync_downloads", ROOT / "scripts/sync-release-downloads.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def published(version="9.8.7"):
    tag = "v" + version
    return {
        "tag_name": tag, "draft": False, "prerelease": False,
        "published_at": "2026-10-30T00:00:00Z",
        "html_url": f"{sync.BASE}/releases/tag/{tag}",
        "assets": [{"name": f"Pasto-{version}-macos-universal.dmg", "state": "uploaded", "size": 123,
                    "browser_download_url": f"{sync.BASE}/releases/download/{tag}/Pasto-{version}-macos-universal.dmg"}],
    }


class SyncReleaseDownloadsTests(unittest.TestCase):
    def test_future_release_updates_both_languages_and_both_installer_buttons(self):
        changes = sync.render(ROOT, published())
        self.assertEqual(set(changes), set(sync.FILES))
        url = published()["assets"][0]["browser_download_url"]
        for name in ("README.md", "README.en.md"):
            self.assertIn("**9.8.7**", changes[name])
            self.assertIn(url, changes[name])
            self.assertIn(f"{sync.BASE}/releases/latest", changes[name])
        self.assertEqual(changes["website/index.html"].count(url), 2)
        self.assertIn('data-release-version="9.8.7"', changes["website/index.html"])
        self.assertIn("Pasto 9.8.7 现已发布", changes["website/i18n.js"])
        self.assertIn("Pasto 9.8.7 is here", changes["website/i18n.js"])
        self.assertNotIn("package.json", changes)

    def test_sync_is_idempotent_and_does_not_change_other_readme_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in sync.FILES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text((ROOT / name).read_text())
            for name, text in sync.render(root, published()).items():
                (root / name).write_text(text)
            self.assertEqual(sync.render(root, published()), {})
            for name in ("README.md", "README.en.md"):
                original = (ROOT / name).read_text()
                updated = (root / name).read_text()
                self.assertEqual(original.split(sync.START)[0], updated.split(sync.START)[0])
                self.assertEqual(original.split(sync.END)[1], updated.split(sync.END)[1])

    def test_draft_prerelease_and_unpublished_releases_are_rejected(self):
        for field, value in [("draft", True), ("prerelease", True), ("published_at", None),
                             ("tag_name", "v9.8.7-dev.1"), ("tag_name", "v9.8.7/extra")]:
            with self.subTest(field=field, value=value):
                release = published()
                release[field] = value
                with self.assertRaises(ValueError):
                    sync.render(ROOT, release)

    def test_missing_incomplete_ambiguous_and_foreign_installers_are_rejected(self):
        good = published()
        variants = [[], good["assets"] * 2]
        for field, value in [("state", "new"), ("size", 0), ("name", "Pasto-intel.dmg"),
                             ("browser_download_url", "https://example.com/Pasto.dmg")]:
            assets = copy.deepcopy(good["assets"])
            assets[0][field] = value
            variants.append(assets)
        for assets in variants:
            with self.subTest(assets=assets):
                release = published()
                release["assets"] = assets
                with self.assertRaises(ValueError):
                    sync.render(ROOT, release)

    def test_missing_binding_aborts_render_without_writing_any_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = {}
            for name in sync.FILES:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                text = (ROOT / name).read_text()
                if name == "README.en.md":
                    text = text.replace(sync.END, "")
                target.write_text(text)
                before[name] = target.read_bytes()
            with self.assertRaises(ValueError):
                sync.render(root, published())
            for name, data in before.items():
                self.assertEqual((root / name).read_bytes(), data)

    def test_i18n_release_metadata_matches_the_shipped_html(self):
        html = (ROOT / "website/index.html").read_text()
        import re
        version = re.search(r'data-release-version="([^"]+)"', html)[1]
        catalog = (ROOT / "website/i18n.js").read_text()
        messages = json.loads(re.search(r"const messages = (\{[\s\S]*?\n\});", catalog)[1])
        for language in ("zh-CN", "en"):
            self.assertIn(version, messages[language]["hero.release"])
            self.assertTrue(messages[language]["download.meta"].startswith("v" + version + " ·"))

    def test_release_explicitly_dispatches_pages_after_publish_and_pages_saves_before_deploy(self):
        release = (ROOT / ".github/workflows/release.yml").read_text()
        pages = (ROOT / ".github/workflows/pages.yml").read_text()
        self.assertLess(release.index('release-ci.py publish'), release.index('gh workflow run pages.yml'))
        self.assertIn('actions: write', release)
        self.assertLess(pages.index('releases/latest'), pages.index('scripts/sync-release-downloads.py --release-json'))
        self.assertLess(pages.index('python3 scripts/check-website.py'), pages.index('git commit -m'))
        self.assertLess(pages.index('git push origin HEAD:main'), pages.index('actions/upload-pages-artifact'))
        self.assertIn('git add -- README.md README.en.md website/index.html website/i18n.js', pages)
        self.assertNotIn('git add .', pages)


if __name__ == "__main__":
    unittest.main()
