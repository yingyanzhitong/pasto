#!/usr/bin/env python3
"""Check the public static site without accessing any clipboard or app data."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "website"


class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.targets = []
        self.downloads = set()
        self.release_version = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.release_version = attrs.get("data-release-version")
        if "id" in attrs:
            assert attrs["id"] not in self.ids, f"Duplicate id: {attrs['id']}"
            self.ids.add(attrs["id"])
        if tag == "img":
            assert "alt" in attrs, f"Image has no alt text: {attrs.get('src')}"
        for key in ("href", "src"):
            if key in attrs:
                self.targets.append(attrs[key])
                if attrs[key].endswith(".dmg"):
                    self.downloads.add(attrs[key])


def main():
    parser = SiteParser()
    parser.feed((SITE / "index.html").read_text())
    for target in parser.targets:
        url = urlsplit(target)
        if url.scheme or url.netloc:
            assert url.scheme == "https", f"Non-HTTPS external resource: {target}"
            continue
        if url.path:
            path = (SITE / unquote(url.path)).resolve()
            assert path.is_relative_to(SITE.resolve()), f"Resource outside website: {target}"
            assert path.is_file(), f"Missing resource: {target}"
        elif url.fragment:
            assert unquote(url.fragment) in parser.ids, f"Missing anchor: {target}"
    # Public download links may lag a package version while its release is still building.
    version = parser.release_version or json.loads((ROOT / "package.json").read_text())["version"]
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-dev\.[0-9]+)?", version), "Invalid public release version"
    expected = f"https://github.com/yingyanzhitong/pasto/releases/download/v{version}/Pasto-{version}-macos-universal.dmg"
    assert parser.downloads == {expected}, "Download does not match current universal release"
    allowed = {".html", ".css", ".js", ".png"}
    for path in SITE.rglob("*"):
        assert not path.is_symlink(), f"Unexpected symlink: {path}"
        if path.is_file():
            assert path.name == ".nojekyll" or path.suffix in allowed, f"Unexpected public file: {path}"
    print(json.dumps({"passed": True, "checked_links": len(parser.targets), "universal_download": version}, ensure_ascii=False))


if __name__ == "__main__":
    main()
