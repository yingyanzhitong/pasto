import AppKit
import AudioToolbox
import Combine

/// Local sound feedback follows the history notifications, rather than capture creation.
/// Original Copy/Paste audio is not distributed; Pop remains a distinct fallback.
@MainActor
public final class OriginalSoundEffects {
    private static let resourceBundle: Bundle = {
        if let url = Bundle.main.resourceURL?.appendingPathComponent("PasteReplica_PasteReplicaCore.bundle"),
           let bundle = Bundle(url: url) { return bundle }
        return Bundle.module
    }()
    private let copySound: SystemSoundID?
    private let pasteSound: SystemSoundID?
    private var observations = Set<AnyCancellable>()

    public init(store: ClipboardStore, monitor: ClipboardMonitor?) {
        copySound = Self.loadSound(named: "Copy")
        pasteSound = Self.loadSound(named: "Paste")
        if let monitor {
            NotificationCenter.default.publisher(for: ClipboardMonitor.didCaptureItemNotification, object: monitor)
                .sink { [weak self, weak store] _ in
                    MainActor.assumeIsolated {
                        guard let self, store?.preferences.playSounds == true else { return }
                        self.play(self.copySound)
                    }
                }.store(in: &observations)
        }
        store.didRestoreItem.sink { [weak self, weak store] _ in
            MainActor.assumeIsolated {
                guard let self, store?.preferences.playSounds == true else { return }
                self.play(self.pasteSound)
            }
        }.store(in: &observations)
    }

    deinit {
        if let copySound { AudioServicesDisposeSystemSoundID(copySound) }
        if let pasteSound { AudioServicesDisposeSystemSoundID(pasteSound) }
    }

    public func stop() {
        observations.removeAll()
    }

    private static func loadSound(named name: String) -> SystemSoundID? {
        guard let url = Bundle.main.url(forResource: name, withExtension: "aiff")
            ?? resourceBundle.url(forResource: name, withExtension: "aiff") else { return nil }
        var sound: SystemSoundID = 0
        guard AudioServicesCreateSystemSoundID(url as CFURL, &sound) == noErr else { return nil }
        return sound
    }

    private func play(_ sound: SystemSoundID?) {
        if let sound { AudioServicesPlaySystemSound(sound) }
        else { NSSound(named: .init("Pop"))?.play() }
    }
}
