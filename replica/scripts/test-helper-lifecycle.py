#!/usr/bin/env python3
"""Run the helper's real workspace/relaunch path with disposable app identities."""
import argparse
import json
import os
import pathlib
import plistlib
import signal
import subprocess
import tempfile
import time
import uuid


def wait_for(check, timeout=12):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError("Isolated helper lifecycle did not reach expected state")


def process_exists(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=pathlib.Path)
    args = parser.parse_args()
    source_root = pathlib.Path(__file__).resolve().parents[1]
    identity = "com.pastereplica.lifecycle." + uuid.uuid4().hex
    suite = identity + ".session"
    active_pid = None
    helper_process = None
    with tempfile.TemporaryDirectory(prefix="paste-helper-lifecycle-") as temporary:
        root = pathlib.Path(temporary)
        app = root / "Lifecycle Fixture.app"
        helper = app / "Contents/Library/LoginItems/Lifecycle Helper.app"
        events = root / "launches.json"
        control = root / "quit"
        for bundle, executable, bundle_id in [(app, "LifecycleFixture", identity),
                                               (helper, "LifecycleHelper", identity + ".helper")]:
            (bundle / "Contents/MacOS").mkdir(parents=True)
            (bundle / "Contents/Info.plist").write_bytes(plistlib.dumps({
                "CFBundleIdentifier": bundle_id, "CFBundleName": bundle.stem,
                "CFBundleExecutable": executable, "CFBundlePackageType": "APPL",
                "LSUIElement": True, "NSPrincipalClass": "NSApplication",
                "TestSuite": suite, "TestEvents": str(events), "TestQuit": str(control),
            }))
        fixture_source = root / "Fixture.swift"
        fixture_source.write_text('''import AppKit
import Foundation
@main struct Fixture {
    @MainActor static func main() {
        let info = Bundle.main.infoDictionary!
        let defaults = UserDefaults(suiteName: info["TestSuite"] as! String)!
        if CommandLine.arguments.contains("--mark") {
            defaults.set(true, forKey: "isRunning"); defaults.synchronize(); return
        }
        if CommandLine.arguments.contains("--clear") {
            defaults.removePersistentDomain(forName: info["TestSuite"] as! String)
            defaults.synchronize(); return
        }
        let app = NSApplication.shared
        app.setActivationPolicy(.prohibited)
        let events = URL(fileURLWithPath: info["TestEvents"] as! String)
        var records = (try? JSONSerialization.jsonObject(with: Data(contentsOf: events))) as? [[String: Any]] ?? []
        records.append(["pid": ProcessInfo.processInfo.processIdentifier, "time": Date().timeIntervalSince1970])
        try! JSONSerialization.data(withJSONObject: records).write(to: events, options: .atomic)
        defaults.set(true, forKey: "isRunning"); defaults.synchronize()
        let timer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            if FileManager.default.fileExists(atPath: info["TestQuit"] as! String) {
                defaults.set(false, forKey: "isRunning"); defaults.synchronize()
                app.terminate(nil)
            }
        }
        app.run(); withExtendedLifetime(timer) {}
    }
}
''')
        helper_source = root / "Helper.swift"
        source = (source_root / "Sources/PastoHelper/HelperMain.swift").read_text()
        source = source.replace('"com.yingyanzhitong.paste-replica.session"', json.dumps(suite))
        source = source.replace('"com.yingyanzhitong.paste-replica"', json.dumps(identity))
        helper_source.write_text(source)
        target = app / "Contents/MacOS/LifecycleFixture"
        helper_binary = helper / "Contents/MacOS/LifecycleHelper"
        for source, output in [(fixture_source, target), (helper_source, helper_binary)]:
            subprocess.run(["xcrun", "swiftc", "-parse-as-library", "-swift-version", "5",
                            str(source), "-o", str(output)], check=True, capture_output=True)
        for bundle in [helper, app]:
            subprocess.run(["codesign", "--force", "--sign", "-", str(bundle)], check=True, capture_output=True)
        def launches():
            try:
                return json.loads(events.read_text())
            except FileNotFoundError:
                return []
        try:
            with (root / "helper.log").open("wb") as log:
                helper_process = subprocess.Popen([str(helper_binary)], stdout=log, stderr=log)
                time.sleep(3.5)
                assert helper_process.poll() is None and not launches(), "False marker must prevent launch"
                # Restart the helper after marking, exercising its startup check as at login.
                helper_process.terminate(); helper_process.wait(timeout=5)
                subprocess.run([str(target), "--mark"], check=True, capture_output=True)
                marked_at = time.time()
                helper_process = subprocess.Popen([str(helper_binary)], stdout=log, stderr=log)
                first = wait_for(lambda: launches() or None)[0]
                active_pid = first["pid"]
                assert first["time"] - marked_at >= 2.8, "Must wait the recovered three seconds"
                time.sleep(0.5)
                assert len(launches()) == 1, "Running target must not be opened again"
                crashed_at = time.time()
                os.kill(active_pid, signal.SIGKILL)
                second = wait_for(lambda: launches()[1] if len(launches()) >= 2 else None)
                active_pid = second["pid"]
                assert second["pid"] != first["pid"] and second["time"] - crashed_at >= 2.8
                control.touch()
                wait_for(lambda: not process_exists(active_pid))
                time.sleep(4.5)
                assert len(launches()) == 2, "Graceful exit must not be restarted"
                assert helper_process.poll() is None
                active_pid = None
                # Force an actual launch error without touching the installed app.
                helper_process.terminate(); helper_process.wait(timeout=5)
                control.unlink()
                subprocess.run([str(target), "--mark"], check=True, capture_output=True)
                unavailable = target.with_suffix(".unavailable")
                target.rename(unavailable)
                try:
                    helper_process = subprocess.Popen([str(helper_binary)], stdout=log, stderr=log)
                    wait_for(lambda: "background launch failed" in (root / "helper.log").read_text(errors="replace"))
                    failure_seen_at = time.time()
                finally:
                    unavailable.rename(target)
                third = wait_for(lambda: launches()[2] if len(launches()) >= 3 else None, timeout=20)
                active_pid = third["pid"]
                assert third["time"] - failure_seen_at >= 12.6, "First failed attempt waits ten seconds, then three before retry"
                control.touch()
                wait_for(lambda: not process_exists(active_pid))
                active_pid = None
                result = {"passed": True, "launch_count": 3,
                          "checks": ["false shared marker prevents startup launch",
                                     "marked missing target opens after recovered three-second wait",
                                     "running target is not duplicated",
                                     "real SIGKILL triggers workspace observation and new target PID",
                                     "graceful exit clears marker and prevents relaunch",
                                     "real missing-executable launch error retries after ten plus three seconds"],
                          "scope": "Real AppKit helper process and NSWorkspace runningApplications KVO; only the two identity literals are replaced in a temporary helper source copy. Disposable signed target app, isolated defaults suite; no service registration, production clipboard, or user data.",
                          "limits": ["SMAppService registration is not exercised"]}
        except Exception as error:
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(json.dumps({"passed": False, "error": str(error),
                                                  "launches": launches(),
                                                  "helper_log": (root / "helper.log").read_text(errors="replace")}, indent=2) + "\n")
            raise
        finally:
            if helper_process and helper_process.poll() is None:
                helper_process.terminate(); helper_process.wait(timeout=5)
            if active_pid:
                try:
                    os.kill(active_pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            subprocess.run([str(target), "--clear"], check=False, capture_output=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
