import Foundation

private final class OriginalResourceBundleFinder: NSObject { }

/// Paste 0x1002fa3d4 searches app resources, the module's bundle, then the app root.
enum OriginalResourceBundle {
    static let bundle: Bundle = {
        let directories = [Bundle.main.resourceURL,
                           Bundle(for: OriginalResourceBundleFinder.self).resourceURL,
                           Bundle.main.bundleURL].compactMap { $0 }
        for directory in directories {
            if let bundle = Bundle(url: directory.appendingPathComponent("Pasto_PastoCore.bundle")) {
                return bundle
            }
        }
        return Bundle.module
    }()
}
