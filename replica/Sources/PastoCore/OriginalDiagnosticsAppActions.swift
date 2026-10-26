import Darwin
import Foundation

public enum OriginalDiagnosticsAppActions {
    /// The original starts a delayed /usr/bin/open through /bin/sh, then exits
    /// immediately even when launching the shell fails.
    public static func f_10004e8ec() -> Never {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/sh")
        process.arguments = ["-c", "sleep 0.25 && open \"" + Bundle.main.bundleURL.path + "\""]
        try? process.run()
        _exit(0)
    }
}
