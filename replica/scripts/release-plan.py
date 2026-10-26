#!/usr/bin/env python3
"""Select a versioned release without building or publishing anything."""
import json
import os
from pathlib import Path
import re
import subprocess

VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:-dev\.[0-9]+)?")


def select_plan(event, ref, version, previous_version=None):
    if not VERSION.fullmatch(version):
        raise ValueError("Unsupported package.json version: " + version)
    tag = "v" + version
    if ref.startswith("refs/tags/"):
        if ref != "refs/tags/" + tag:
            raise ValueError("Tag does not match package.json version")
        selected = event in {"push", "workflow_dispatch"}
    elif event == "workflow_dispatch":
        selected = True
    else:
        selected = event == "push" and ref == "refs/heads/main" and version != previous_version
    return {"release": str(selected).lower(), "version": version, "tag": tag}


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    version = json.loads(Path("package.json").read_text())["version"]
    previous = None
    before = event.get("before", "")
    if os.environ["GITHUB_EVENT_NAME"] == "push" and os.environ["GITHUB_REF"] == "refs/heads/main" and before.strip("0"):
        raw = subprocess.run(["git", "show", before + ":package.json"],
                             capture_output=True, check=True, text=True).stdout
        previous = json.loads(raw)["version"]
    result = select_plan(os.environ["GITHUB_EVENT_NAME"], os.environ["GITHUB_REF"], version, previous)
    result["commit"] = subprocess.run(["git", "rev-parse", "HEAD"],
                                      capture_output=True, check=True, text=True).stdout.strip()
    with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
        for key, value in result.items():
            output.write(key + "=" + value + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
