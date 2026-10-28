#!/usr/bin/env python3
"""Build/verify a macOS archive or publish already verified assets; never run the app."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
RELEASE_ARCHITECTURES = ["arm64", "x86_64"]


def bundle_version(version):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-dev\.[0-9]+)?", version):
        raise ValueError("Unsupported release version")
    pieces = version.split("-dev.")
    build = pieces[0] if len(pieces) == 1 else ".".join(pieces[0].split(".")[:2] + [pieces[1]])
    return pieces[0], build


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
    bundle_version(version)
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
    return ["Pasto-" + version + "-macos-" + arch + ".dmg" for arch in RELEASE_ARCHITECTURES] + ["SHA256SUMS.txt", "release-manifest.json"]


def changelog_entry(version):
    lines = (ROOT / "CHANGELOG.md").read_text().splitlines()
    entry = None
    for line in lines:
        if line.startswith("## "):
            if entry is not None:
                break
            if line.startswith("## " + version + " - "):
                entry = []
        elif entry is not None:
            entry.append(line)
    if entry is None or not "\n".join(entry).strip():
        raise ValueError("Release version has no changelog entry")
    return "\n".join(entry).strip()


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


def verify_app(app, version, architectures):
    info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    short_version, expected_build = bundle_version(version)
    if (info.get("CFBundleExecutable") != "Pasto" or info.get("CFBundleDisplayName") != "Pasto"
            or info.get("CFBundleShortVersionString") != short_version
            or info.get("CFBundleVersion") != expected_build or info.get("PastoSourceVersion") != version):
        raise ValueError("Application bundle version/name mismatch")
    run(["codesign", "--verify", "--deep", "--strict", str(app)])
    executables = [app / "Contents/MacOS/Pasto", app / "Contents/MacOS/pasto-mcp",
                   app / "Contents/Library/LoginItems/Pasto Helper.app/Contents/MacOS/PastoHelper"]
    for executable in executables:
        actual = run(["lipo", "-archs", str(executable)], capture_output=True, text=True).stdout.split()
        if len(actual) != len(architectures) or set(actual) != set(architectures):
            raise ValueError("Unexpected executable architectures: " + str(executable) + " " + str(actual))


def verify_intel(version):
    if platform.system() != "Darwin" or platform.machine() != "x86_64":
        raise ValueError("Intel verification requires a native macOS x86_64 runner")
    verify_app(ROOT / "replica/dist/Pasto.app", version, ["x86_64"])


def verify_dmg(archive, version, architecture):
    with tempfile.TemporaryDirectory(prefix="pasto-release-mount-") as temporary:
        mount = Path(temporary)
        run(["hdiutil", "attach", "-readonly", "-nobrowse", "-mountpoint", str(mount), str(archive)])
        try:
            verify_app(mount / "Pasto.app", version, [architecture])
            applications = mount / "Applications"
            if not applications.is_symlink() or os.readlink(applications) != "/Applications":
                raise ValueError("Disk image is missing the Applications shortcut")
        finally:
            run(["hdiutil", "detach", str(mount)])


def package(version, tag, commit):
    if platform.system() != "Darwin":
        raise ValueError("Release requires a macOS runner")
    app = ROOT / "replica/dist/Pasto.app"
    output = ROOT / "replica/dist/release"
    output.mkdir(parents=True, exist_ok=False)
    archives = []
    for architecture, name in zip(RELEASE_ARCHITECTURES, asset_names(version)[:2]):
        run(["bash", "replica/scripts/build-app.sh", "release", architecture])
        verify_app(app, version, [architecture])
        archive = output / name
        run(["bash", "replica/scripts/build-dmg.sh", str(app), str(archive), architecture])
        verify_dmg(archive, version, architecture)
        archives.append({"archive": name, "architectures": [architecture], "sha256": sha(archive)})
    manifest = {"version": version, "tag": tag, "commit": commit, "archives": archives, "container": "dmg",
                "codesign_verified": True, "notarized": False,
                "functional_tests_executed": False, "application_executed": False}
    (output / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "SHA256SUMS.txt").write_text("".join(
        sha(output / name) + "  " + name + "\n" for name in asset_names(version)[:2] + ["release-manifest.json"]))


def publish(repo, version, tag, commit):
    ref, existing = check_existing(repo, version, tag, commit)
    if existing:
        return
    output = ROOT / "replica/dist/release"
    names = asset_names(version)
    manifest = json.loads((output / "release-manifest.json").read_text())
    expected_archives = [{"archive": name, "architectures": [architecture], "sha256": sha(output / name)}
                         for architecture, name in zip(RELEASE_ARCHITECTURES, names[:2])]
    expected_sums = "".join(sha(output / name) + "  " + name + "\n"
                            for name in names[:2] + ["release-manifest.json"])
    if (manifest.get("commit") != commit or manifest.get("version") != version or manifest.get("tag") != tag
            or manifest.get("container") != "dmg" or manifest.get("archives") != expected_archives
            or manifest.get("codesign_verified") is not True
            or (output / "SHA256SUMS.txt").read_text() != expected_sums):
        raise ValueError("Unverified or stale local release assets")
    for architecture, name in zip(RELEASE_ARCHITECTURES, names[:2]):
        verify_dmg(output / name, version, architecture)
    if not ref:
        api("repos/" + repo + "/git/refs", "--method", "POST", "-f", "ref=refs/tags/" + tag, "-f", "sha=" + commit)
    remote_state(repo, tag, commit)
    notes = output / "notes.md"
    download = "https://github.com/" + repo + "/releases/download/" + tag + "/"
    notes.write_text("[下载 Apple Silicon 版（arm64）](" + download + names[0] + ")\n\n"
                     "[下载 Intel 版（x86_64）](" + download + names[1] + ")\n\n"
                     "Pasto " + version + " · macOS 14+。请选择与芯片对应的独立 DMG。\n\n"
                     "## 更新内容\n\n" + changelog_entry(version) + "\n\n"
                     "## 安装与验证\n\n"
                     "将 Pasto.app 拖入 Applications 即可安装；同时提供 SHA256SUMS.txt 与构建来源清单。\n"
                     "应用采用临时签名，未经 Apple 公证。\n"
                     "本次 Actions 发布任务验证编译、架构、版本、签名及安装镜像，没有在构建节点执行应用或功能回归；本机定向验证范围见上方变更日志。\n"
                     "本流程仅上传两个 DMG、校验文件及清单；页面中的 Source code (zip/tar.gz) 链接由 GitHub 自动生成，没有主动上传源码包。\n\n"
                     "Commit: " + commit + "\n")
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
    edit_args = ["gh", "release", "edit", tag, "--repo", repo, "--draft=false", "--verify-tag"]
    if "-dev." not in version:
        edit_args.append("--latest")
    run(edit_args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["check", "verify-intel", "package", "publish"])
    parser.add_argument("--version")
    parser.add_argument("--tag")
    parser.add_argument("--commit")
    args = parser.parse_args()
    if args.mode == "package":
        args.version = args.version or json.loads((ROOT / "package.json").read_text())["version"]
        args.tag = args.tag or "v" + args.version
        args.commit = args.commit or run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    elif not all([args.version, args.tag, args.commit]):
        parser.error("--version, --tag and --commit are required for this mode")
    validate_identity(args.version, args.tag, args.commit)
    if args.mode == "verify-intel":
        verify_intel(args.version)
        return
    if args.mode == "check":
        repo = os.environ["GITHUB_REPOSITORY"]
        _, release = check_existing(repo, args.version, args.tag, args.commit)
        with Path(os.environ["GITHUB_OUTPUT"]).open("a") as output:
            output.write("exists=" + str(bool(release)).lower() + "\n")
    elif args.mode == "package":
        package(args.version, args.tag, args.commit)
    else:
        publish(os.environ["GITHUB_REPOSITORY"], args.version, args.tag, args.commit)


if __name__ == "__main__":
    main()
