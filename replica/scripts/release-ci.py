#!/usr/bin/env python3
"""Build/verify a macOS archive or publish already verified assets; never run the app."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def run(args, **kwargs):
    return subprocess.run(args, cwd=ROOT, check=True, **kwargs)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def api(endpoint, *options, optional=False):
    result = subprocess.run(["gh", "api", endpoint, *options], cwd=ROOT, capture_output=True, text=True)
    if optional and result.returncode and "HTTP 404" in result.stderr:
        return None
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def validate_identity(version, tag, commit):
    if json.loads((ROOT / "package.json").read_text())["version"] != version or tag != "v" + version:
        raise ValueError("Release identity does not match checked-out package.json")
    actual = run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if actual != commit:
        raise ValueError("Release commit does not match checkout")


def remote_state(repo, tag, commit):
    ref = api("repos/" + repo + "/git/ref/tags/" + tag, optional=True)
    if ref:
        obj = ref["object"]
        for _ in range(8):
            if obj["type"] == "commit":
                break
            if obj["type"] != "tag":
                raise ValueError("Unexpected tag object type")
            obj = api("repos/" + repo + "/git/tags/" + obj["sha"])["object"]
        if obj["type"] != "commit" or obj["sha"] != commit:
            raise ValueError("Existing version tag points to another commit; refusing overwrite")
    release = api("repos/" + repo + "/releases/tags/" + tag, optional=True)
    if release and not ref:
        raise ValueError("Existing release has no matching remote tag")
    return ref, release


def asset_names(version):
    return ["Pasto-" + version + "-macos-arm64.zip", "SHA256SUMS.txt", "release-manifest.json"]


def check_existing(repo, version, tag, commit):
    ref, release = remote_state(repo, tag, commit)
    if release:
        if release["draft"]:
            raise ValueError("Existing draft needs review; refusing to overwrite assets or publish a failed attempt")
        names = {asset["name"] for asset in release["assets"]}
        if not set(asset_names(version)).issubset(names):
            raise ValueError("Existing published release is incomplete; refusing overwrite")
        print("Release already published for this commit: " + release["html_url"])
    return ref, release


def package(version, tag, commit):
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError("Release requires a native macOS arm64 runner")
    run(["bash", "replica/scripts/build-app.sh", "release"])
    app = ROOT / "replica/dist/Pasto.app"
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    pieces = version.split("-dev.")
    expected_build = pieces[0] if len(pieces) == 1 else ".".join(pieces[0].split(".")[:2] + [pieces[1]])
    if (info.get("CFBundleExecutable") != "Pasto" or info.get("CFBundleDisplayName") != "Pasto"
            or info.get("CFBundleShortVersionString") != pieces[0]
            or info.get("CFBundleVersion") != expected_build or info.get("PastoSourceVersion") != version):
        raise ValueError("Application bundle version/name mismatch")
    run(["codesign", "--verify", "--deep", "--strict", str(app)])
    executables = [app / "Contents/MacOS/Pasto", app / "Contents/MacOS/pasto-mcp",
                   app / "Contents/Library/LoginItems/Pasto Helper.app/Contents/MacOS/PastoHelper"]
    for executable in executables:
        if run(["lipo", "-archs", str(executable)], capture_output=True, text=True).stdout.strip() != "arm64":
            raise ValueError("Unexpected executable architecture")
    output = ROOT / "replica/dist/release"
    output.mkdir(exist_ok=False)
    archive = output / asset_names(version)[0]
    run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app), str(archive)])
    with tempfile.TemporaryDirectory() as temporary:
        run(["ditto", "-x", "-k", str(archive), temporary])
        run(["codesign", "--verify", "--deep", "--strict", str(Path(temporary) / "Pasto.app")])
    manifest = {"version": version, "tag": tag, "commit": commit, "architecture": "arm64",
                "archive": archive.name, "archive_sha256": sha(archive),
                "codesign_verified": True, "notarized": False,
                "functional_tests_executed": False, "application_executed": False}
    (output / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "SHA256SUMS.txt").write_text("".join(
        sha(output / name) + "  " + name + "\n" for name in [archive.name, "release-manifest.json"]))


def publish(repo, version, tag, commit):
    ref, existing = check_existing(repo, version, tag, commit)
    if existing:
        return
    output = ROOT / "replica/dist/release"
    names = asset_names(version)
    manifest = json.loads((output / "release-manifest.json").read_text())
    if manifest["commit"] != commit or manifest["version"] != version or manifest["archive_sha256"] != sha(output / names[0]):
        raise ValueError("Unverified or stale local release assets")
    if not ref:
        api("repos/" + repo + "/git/refs", "--method", "POST", "-f", "ref=refs/tags/" + tag, "-f", "sha=" + commit)
    remote_state(repo, tag, commit)
    notes = output / "notes.md"
    notes.write_text("Pasto " + version + "\n\nmacOS 14+ · Apple Silicon（arm64）。\n\n"
                     "提供 ZIP、SHA256SUMS.txt 与构建来源清单。应用采用临时签名，未经 Apple 公证。\n"
                     "此发布只验证编译、架构、版本与签名，没有执行应用或功能回归。\n\nCommit: " + commit + "\n")
    args = ["gh", "release", "create", tag, *[str(output / name) for name in names],
            "--repo", repo, "--draft", "--verify-tag", "--target", commit,
            "--title", "Pasto " + version, "--notes-file", str(notes)]
    if "-dev." in version:
        args += ["--prerelease", "--latest=false"]
    run(args)
    # Verify uploaded bytes before switching the draft to published. Never clobber assets.
    with tempfile.TemporaryDirectory() as temporary:
        run(["gh", "release", "download", tag, "--repo", repo, "--dir", temporary])
        for name in names:
            if sha(Path(temporary) / name) != sha(output / name):
                raise ValueError("Uploaded asset mismatch; release remains a draft")
    remote_state(repo, tag, commit)
    run(["gh", "release", "edit", tag, "--repo", repo, "--draft=false", "--verify-tag"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["check", "package", "publish"])
    parser.add_argument("--version", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    validate_identity(args.version, args.tag, args.commit)
    repo = os.environ["GITHUB_REPOSITORY"]
    if args.mode == "check":
        _, release = check_existing(repo, args.version, args.tag, args.commit)
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
            output.write("exists=" + str(bool(release)).lower() + "\n")
    elif args.mode == "package":
        package(args.version, args.tag, args.commit)
    else:
        publish(repo, args.version, args.tag, args.commit)


if __name__ == "__main__":
    main()
