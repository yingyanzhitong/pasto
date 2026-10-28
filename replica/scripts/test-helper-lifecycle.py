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


def lifecycle_time():
    # Explicitly use the same Darwin clock as the Swift fixture, not unrelated uptime APIs.
    return time.clock_gettime(time.CLOCK_MONOTONIC)


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
        # The production helper resolves its enclosing application by this exact name.
        app = root / "Pasto.app"
        helper = app / "Contents/Library/LoginItems/Lifecycle Helper.app"
        events = root / "launches.json"
        control = root / "quit"
        failure_event = root / "launch-failure.json"
        helper_events = root / "helper-events.json"
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
        clock_source = '''import Foundation
import Darwin
func regressionTime() -> Double {
    var value = timespec()
    precondition(clock_gettime(CLOCK_MONOTONIC, &value) == 0)
    return Double(value.tv_sec) + Double(value.tv_nsec) / 1_000_000_000
}
'''
        fixture_source.write_text(clock_source + '''import AppKit
import Foundation
@main struct Fixture {
    @MainActor static func main() {
        let info = Bundle.main.infoDictionary!
        let defaults = UserDefaults(suiteName: info["TestSuite"] as! String)!
        if CommandLine.arguments.contains("--mark") {
            defaults.set(true, forKey: "pasteIsRunning"); defaults.synchronize(); return
        }
        if CommandLine.arguments.contains("--clear") {
            defaults.removePersistentDomain(forName: info["TestSuite"] as! String)
            defaults.synchronize(); return
        }
        let app = NSApplication.shared
        app.setActivationPolicy(.prohibited)
        let events = URL(fileURLWithPath: info["TestEvents"] as! String)
        var records = (try? JSONSerialization.jsonObject(with: Data(contentsOf: events))) as? [[String: Any]] ?? []
        records.append(["pid": ProcessInfo.processInfo.processIdentifier, "time": regressionTime()])
        try! JSONSerialization.data(withJSONObject: records).write(to: events, options: .atomic)
        defaults.set(true, forKey: "pasteIsRunning"); defaults.synchronize()
        let timer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { _ in
            if FileManager.default.fileExists(atPath: info["TestQuit"] as! String) {
                defaults.set(false, forKey: "pasteIsRunning"); defaults.synchronize()
                app.terminate(nil)
            }
        }
        app.run(); withExtendedLifetime(timer) {}
    }
}
''')
        helper_source = root / "Helper.swift"
        source = (source_root / "Sources/PastoHelper/HelperMain.swift").read_text()
        for original, isolated in [("com.yingyanzhitong.paste-replica.session", suite),
                                   ("com.yingyanzhitong.paste-replica", identity)]:
            literal = json.dumps(original)
            assert source.count(literal) == 1, "Helper identity isolation needs review"
            source = source.replace(literal, json.dumps(isolated))
        # OSLog is not guaranteed to write stderr. Diagnostic-only taps in this
        # disposable copy distinguish KVO attempts from scheduled retry callbacks.
        failure_log = 'logger.error("Failed to launch Paste: \\(error.localizedDescription)")'
        assert source.count(failure_log) == 1, "Helper launch error observer needs review"
        source = source.replace(failure_log, failure_log + '\n' +
            '            regressionRecord("error")\n' +
            '            try! JSONSerialization.data(withJSONObject: ["time": regressionTime()])' +
            '.write(to: URL(fileURLWithPath: ' + json.dumps(str(failure_event)) + '), options: .atomic)')
        observations = {
            '_ = Task { @MainActor [weak self] in self?.checkRunning() }':
                '_ = Task { @MainActor [weak self] in regressionRecord("workspace-check"); self?.checkRunning() }',
            '        isLaunching = true':
                '        regressionRecord("attempt-start")\n        isLaunching = true',
            '        logger.info("Launching Paste at \\(url.path)")':
                '        regressionRecord("launch-call")\n        logger.info("Launching Paste at \\(url.path)")',
            '            logger.info("Paste launched successfully.")':
                '            regressionRecord("success")\n            logger.info("Paste launched successfully.")',
            '                try? await ContinuousClock().sleep(for: .seconds(retryDelay))':
                '                regressionRecord("retry-sleep-start")\n' +
                '                try? await ContinuousClock().sleep(for: .seconds(retryDelay))\n' +
                '                regressionRecord("retry-sleep-complete")',
        }
        for original, observed in observations.items():
            assert source.count(original) == 1, "Helper timing observer needs review"
            source = source.replace(original, observed)
        recorder = '''func regressionRecord(_ event: String) {
    let url = URL(fileURLWithPath: PATH)
    var records = (try? JSONSerialization.jsonObject(with: Data(contentsOf: url))) as? [[String: Any]] ?? []
    records.append(["event": event, "time": regressionTime(), "wallTime": Date().timeIntervalSince1970])
    try! JSONSerialization.data(withJSONObject: records).write(to: url, options: .atomic)
}
'''.replace('PATH', json.dumps(str(helper_events)))
        helper_source.write_text(clock_source + recorder + source)
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
        def observations():
            return json.loads(helper_events.read_text()) if helper_events.exists() else []
        try:
            with (root / "helper.log").open("wb") as log:
                helper_process = subprocess.Popen([str(helper_binary)], stdout=log, stderr=log)
                time.sleep(3.5)
                assert helper_process.poll() is None and not launches(), "False marker must prevent launch"
                # Restart the helper after marking, exercising its startup check as at login.
                helper_process.terminate(); helper_process.wait(timeout=5)
                subprocess.run([str(target), "--mark"], check=True, capture_output=True)
                marked_at = lifecycle_time()
                helper_process = subprocess.Popen([str(helper_binary)], stdout=log, stderr=log)
                first = wait_for(lambda: launches() or None)[0]
                active_pid = first["pid"]
                assert 2.8 <= first["time"] - marked_at <= 12, "Must wait the recovered three seconds"
                time.sleep(0.5)
                assert len(launches()) == 1, "Running target must not be opened again"
                crashed_at = lifecycle_time()
                os.kill(active_pid, signal.SIGKILL)
                second = wait_for(lambda: launches()[1] if len(launches()) >= 2 else None)
                active_pid = second["pid"]
                assert second["pid"] != first["pid"] and 2.8 <= second["time"] - crashed_at <= 12
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
                    def failed_attempt():
                        assert helper_process.poll() is None, "Helper exited during failure observation"
                        if failure_event.exists():
                            return json.loads(failure_event.read_text())
                        return None
                    failure = wait_for(failed_attempt)
                    failure_seen_at = failure["time"]
                    assert len(launches()) == 2, "Missing executable must fail without launching a target"
                finally:
                    unavailable.rename(target)
                third = wait_for(lambda: launches()[2] if len(launches()) >= 3 else None, timeout=20)
                active_pid = third["pid"]
                # isLaunching protects an attempt, not the cooldown. Other workspace
                # publications may start an earlier attempt; measure the retry Task
                # itself instead of imposing a global no-launch interval.
                sleep_end = wait_for(lambda: next((event for event in observations()
                    if event["event"] == "retry-sleep-complete"), None), timeout=20)
                timeline = observations()
                sleep_start = next(event for event in timeline if event["event"] == "retry-sleep-start")
                retry_sleep = sleep_end["time"] - sleep_start["time"]
                assert 9.8 <= retry_sleep <= 20, "Scheduled first retry must wait ten seconds"
                attempt_started = None
                launch_delays = []
                for event in timeline:
                    if event["event"] == "attempt-start":
                        attempt_started = event["time"]
                    elif event["event"] == "launch-call":
                        assert attempt_started is not None
                        delay = event["time"] - attempt_started
                        assert 2.8 <= delay <= 12, "Each actual launch must wait three seconds after its attempt"
                        launch_delays.append(delay)
                control.touch()
                wait_for(lambda: not process_exists(active_pid))
                active_pid = None
                result = {"passed": True, "launch_count": 3,
                          "timings_seconds": {"initial_launch": first["time"] - marked_at,
                                              "crash_relaunch": second["time"] - crashed_at,
                                              "error_to_next_launch": third["time"] - failure_seen_at,
                                              "retry_task_sleep": retry_sleep,
                                              "attempt_to_launch": launch_delays},
                          "helper_events": timeline,
                          "cooldown_kvo_note": "Other runningApplications publications may start an attempt while a retry Task sleeps; earliest success is not required to wait thirteen seconds.",
                          "checks": ["false shared marker prevents startup launch",
                                     "marked missing target opens after recovered three-second wait",
                                     "running target is not duplicated",
                                     "real SIGKILL triggers workspace observation and new target PID",
                                     "graceful exit clears marker and prevents relaunch",
                                     "real launch failure schedules a ten-second retry Task; actual attempts wait three seconds"],
                          "scope": "Real AppKit helper process and NSWorkspace runningApplications KVO. Temporary helper source copy replaces two identities and adds diagnostic-only timing writes; production delay/retry logic is unchanged. Disposable signed Pasto.app, isolated defaults suite; no service registration, production clipboard, or user data.",
                          "failure_observation": "actual NSWorkspace error catch timestamp, not OSLog stderr",
                          "isolated_bundle_id": identity, "isolated_defaults_suite": suite,
                          "limits": ["SMAppService registration is not exercised"]}
        except Exception as error:
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(json.dumps({"passed": False, "error": str(error),
                                                  "launches": launches(),
                                                  "helper_events": observations(),
                                                  "failure_observation": json.loads(failure_event.read_text()) if failure_event.exists() else None,
                                                  "helper_log": (root / "helper.log").read_text(errors="replace")}, indent=2) + "\n")
            raise
        finally:
            if helper_process and helper_process.poll() is None:
                helper_process.terminate(); helper_process.wait(timeout=5)
            owned_pids = {record["pid"] for record in launches()}
            if active_pid:
                owned_pids.add(active_pid)
            for pid in owned_pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            subprocess.run([str(target), "--clear"], check=False, capture_output=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    def exit_on_signal(number, frame):
        raise SystemExit(128 + number)
    signal.signal(signal.SIGTERM, exit_on_signal)
    main()
