import Combine
import Foundation
import PastoCore
import ServiceManagement

@MainActor
enum BackgroundService {
    static let identifier = "com.yingyanzhitong.paste-replica.helper"
    static let sessionDefaults = UserDefaults(suiteName: "com.yingyanzhitong.paste-replica.session")
    private static let diagnostic = OriginalNamedDiagnostic.f_1000d4624(name: "PasteHelper")
    private static let enabledSubject = CurrentValueSubject<Bool, Never>(
        SMAppService.loginItem(identifier: identifier).status == .enabled)
    private static let enabledPublisher = enabledSubject.eraseToAnyPublisher()
    static var enabledChanges: AnyPublisher<Bool, Never> { enabledPublisher }
    static var isEnabled: Bool { enabledSubject.value }

    /// Paste 0x1000adc6c: publish requested state before attempting any service operation.
    static func setEnabled(_ enabled: Bool) {
        enabledSubject.send(enabled)
        let service = SMAppService.loginItem(identifier: identifier)
        do {
            if enabled {
                if service.status == .enabled {
                    // The original intentionally ignores failure of the preliminary removal.
                    try? SMAppService.loginItem(identifier: identifier).unregister()
                }
                try SMAppService.loginItem(identifier: identifier).register()
                diagnostic.f_1000d468c().f_1000d4dd4("Registered background helper")
            } else {
                try service.unregister()
                diagnostic.f_1000d468c().f_1000d4dd4("Unregistered background helper")
            }
        } catch {
            let operation = enabled ? "registering" : "unregistering"
            diagnostic.f_1000d468c().f_1000d4e0c("Error \(operation) background item: \(error.localizedDescription)")
        }
    }

    static func markRunning(_ running: Bool) {
        sessionDefaults?.set(running, forKey: "pasteIsRunning")
        sessionDefaults?.synchronize()
    }
}
