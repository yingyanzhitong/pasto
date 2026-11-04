#!/usr/bin/env python3
"""Sign the Universal DMG and appcast using the private key supplied by CI."""
import argparse
import base64
import datetime
import os
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SPARKLE = "http://www.andymatuschak.org/xml-namespaces/sparkle"
ET.register_namespace("sparkle", SPARKLE)


def make_feed(version, signature, size):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("The stable update feed requires a stable release version")
    if len(base64.b64decode(signature, validate=True)) != 64 or size <= 0:
        raise ValueError("Invalid archive signature or size")
    feed = ET.Element("rss", version="2.0")
    channel = ET.SubElement(feed, "channel")
    ET.SubElement(channel, "title").text = "Pasto Updates"
    ET.SubElement(channel, "link").text = "https://yingyanzhitong.github.io/pasto/"
    ET.SubElement(channel, "description").text = "Pasto stable macOS updates"
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = "Pasto " + version
    ET.SubElement(item, "link").text = "https://github.com/yingyanzhitong/pasto/releases/tag/v" + version
    ET.SubElement(item, "pubDate").text = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    ET.SubElement(item, "{" + SPARKLE + "}version").text = version
    ET.SubElement(item, "{" + SPARKLE + "}shortVersionString").text = version
    ET.SubElement(item, "{" + SPARKLE + "}minimumSystemVersion").text = "14.0"
    ET.SubElement(item, "enclosure", {
        "url": "https://github.com/yingyanzhitong/pasto/releases/download/v" + version
               + "/Pasto-" + version + "-macos-universal.dmg",
        "{" + SPARKLE + "}edSignature": signature,
        "length": str(size), "type": "application/octet-stream"})
    return ET.ElementTree(feed)


def create_feed(archive, version, sign_tool):
    private_key = os.environ.get("PASTO_UPDATE_PRIVATE_KEY", "").strip()
    if not private_key or len(base64.b64decode(private_key, validate=True)) != 32:
        raise ValueError("Configure the PASTO_UPDATE_PRIVATE_KEY Actions secret before publishing updates")
    # Keep the private seed off argv, disk, and the signer's environment.
    environment = {key: value for key, value in os.environ.items() if key != "PASTO_UPDATE_PRIVATE_KEY"}

    def sign(*arguments):
        return subprocess.run([str(sign_tool), "--ed-key-file", "-", *arguments],
                              input=private_key + "\n", text=True, capture_output=True,
                              check=True, env=environment).stdout.strip()

    signature = sign("-p", str(archive))
    subprocess.run(["swift", str(ROOT / "replica/scripts/verify-update-signature.swift"),
                    str(ROOT / "replica/Assets/UpdatePublicKey.txt"), signature, str(archive)],
                   check=True, env=environment)
    feed = archive.parent / "appcast.xml"
    make_feed(version, signature, archive.stat().st_size).write(feed, encoding="utf-8", xml_declaration=True)
    sign(str(feed))
    sign("--verify", str(feed))
    return feed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--sign-tool", type=Path)
    arguments = parser.parse_args()
    # Reject missing keys before fetching tools or writing any release asset.
    if not os.environ.get("PASTO_UPDATE_PRIVATE_KEY"):
        parser.error("PASTO_UPDATE_PRIVATE_KEY is required for signed in-app updates")
    tool = arguments.sign_tool or Path(subprocess.run(
        ["bash", str(ROOT / "replica/scripts/prepare-sparkle-tools.sh")],
        check=True, capture_output=True, text=True).stdout.strip())
    create_feed(arguments.archive, arguments.version, tool)


if __name__ == "__main__":
    main()
