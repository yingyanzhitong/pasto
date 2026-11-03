#!/usr/bin/env python3
"""Sync public download links from an already published stable GitHub release."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
REPO = "yingyanzhitong/pasto"
BASE = "https://github.com/" + REPO
FILES = ("README.md", "README.en.md", "website/index.html", "website/i18n.js")
START = "<!-- pasto-download:start -->"
END = "<!-- pasto-download:end -->"


def release_info(release):
    tag = release.get("tag_name", "")
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Expected a stable vMAJOR.MINOR.PATCH release")
    if release.get("draft") is not False or release.get("prerelease") is not False or not release.get("published_at"):
        raise ValueError("Download links require a published, non-prerelease release")
    version = tag[1:]
    name = f"Pasto-{version}-macos-universal.dmg"
    assets = [asset for asset in release.get("assets", []) if asset.get("name", "").endswith(".dmg")]
    if len(assets) != 1 or assets[0].get("name") != name:
        raise ValueError("Expected exactly one versioned Universal DMG")
    asset = assets[0]
    url = f"{BASE}/releases/download/{tag}/{name}"
    if asset.get("browser_download_url") != url or asset.get("state") != "uploaded" or asset.get("size", 0) <= 0:
        raise ValueError("The Universal DMG is missing, incomplete, or belongs to another repository")
    if release.get("html_url") != f"{BASE}/releases/tag/{tag}":
        raise ValueError("Unexpected release URL")
    return version, url


def replace_one(pattern, replacement, source):
    result, count = re.subn(pattern, replacement, source)
    if count != 1:
        raise ValueError(f"Expected exactly one binding for {pattern!r}; found {count}")
    return result


def render(root, release):
    version, url = release_info(release)
    originals = {name: (root / name).read_text() for name in FILES}
    updated = dict(originals)
    for name, lead, label in [
        ("README.md", f"当前正式版 **{version}**，一个安装包兼容 Intel 与 Apple 芯片：", "下载"),
        ("README.en.md", f"Current stable version: **{version}**. One installer supports Intel and Apple silicon:", "Download"),
    ]:
        block = f"{START}\n{lead}\n\n[{label} Pasto-{version}-macos-universal.dmg]({url})\n{END}"
        updated[name] = replace_one(re.escape(START) + r"[\s\S]*?" + re.escape(END), lambda _: block, originals[name])

    html = replace_one(r'data-release-version="[^"]+"', lambda _: f'data-release-version="{version}"', originals["website/index.html"])
    html = replace_one(r'(class="release-pill" href=")[^"]+(")', lambda m: m[1] + f"{BASE}/releases/tag/v{version}" + m[2], html)
    html, count = re.subn(re.escape(BASE) + r'/releases/download/[^/"\s]+/Pasto-[^"\s]+\.dmg', lambda _: url, html)
    if count != 2:
        raise ValueError("Expected both website installer buttons")
    html = replace_one(r'(data-i18n="hero.release">)[^<]+', lambda m: m[1] + f"Pasto {version} 现已发布", html)
    html = replace_one(r'(data-i18n="download.meta">)[^<]+', lambda m: m[1] + f"v{version} · macOS 14+ · Intel / Apple 芯片", html)
    updated["website/index.html"] = html

    catalog = originals["website/i18n.js"]
    for key in ("hero.release", "download.meta"):
        def translate(match):
            value = json.loads(match[2])
            value, count = re.subn(r"(?<![0-9])[0-9]+\.[0-9]+\.[0-9]+(?:-dev\.[0-9]+)?", lambda _: version, value)
            if count != 1:
                raise ValueError("Translation must contain one release version: " + key)
            return match[1] + json.dumps(value, ensure_ascii=False)
        catalog, count = re.subn(r'("' + re.escape(key) + r'":\s*)("(?:\\.|[^"\\])*")', translate, catalog)
        if count != 2:
            raise ValueError("Expected Chinese and English release translations: " + key)
    updated["website/i18n.js"] = catalog
    return {name: text for name, text in updated.items() if text != originals[name]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-json", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    release = json.loads(args.release_json.read_text())
    changes = render(ROOT, release)  # Validate all bindings before writing any file.
    if args.check and changes:
        raise SystemExit("Stale download bindings: " + ", ".join(changes))
    for name, text in changes.items():
        (ROOT / name).write_text(text)
    print(json.dumps({"release": release["tag_name"], "changed": list(changes)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
