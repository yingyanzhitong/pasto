import Foundation

public enum OriginalPreviewTitles {
    public static func f_100309008(rawType: Int, fileCount: Int? = nil) -> String {
        let resource: LocalizedStringResource
        switch rawType {
        case 1: resource = OriginalPreviewLocalization.f_1001c6f68()
        case 2: resource = OriginalPreviewLocalization.f_1001c6f44()
        case 3: resource = OriginalPreviewLocalization.f_1001e6c38(Int32(fileCount ?? 1))
        case 4: resource = OriginalPreviewLocalization.f_1001c6f8c()
        case 5: resource = OriginalPreviewLocalization.f_1001c7130()
        default: resource = OriginalPreviewLocalization.f_1001c7154()
        }
        return String(localized: resource)
    }

    public static func f_100308f88(_ title: String?, defaultTitle: String) -> String {
        if let title, !title.isEmpty { return title }
        return defaultTitle
    }
}
