import AppKit

@MainActor
public enum OriginalSearchSuggestionAnchor {
    public static func f_100046e28(_ manager: NSTextLayoutManager, range: NSRange) -> CGRect {
        guard let content = manager.textContentManager,
              let location = content.location(content.documentRange.location, offsetBy: range.location),
              let fragment = manager.textLayoutFragment(for: location) else { return .zero }
        let offset = UInt(bitPattern: range.location)
        let matchingLine = fragment.textLineFragments.first { line in
            let characterRange = line.characterRange
            let start = UInt(bitPattern: characterRange.location)
            return offset >= start && offset - start < UInt(bitPattern: characterRange.length)
        }
        guard let line = matchingLine ?? fragment.textLineFragments.first else { return .zero }
        let nonnegativeIndex = max(0, range.location - line.characterRange.location)
        let index = min(nonnegativeIndex, line.characterRange.length)
        let characterX: CGFloat
        if index < line.characterRange.length {
            characterX = line.locationForCharacter(at: index).x
        } else {
            characterX = line.typographicBounds.width
        }
        let x = characterX + line.glyphOrigin.x
        let y = fragment.layoutFragmentFrame.minY + line.glyphOrigin.y
        return CGRect(x: x, y: y, width: line.typographicBounds.width,
                      height: line.typographicBounds.height)
    }
}
