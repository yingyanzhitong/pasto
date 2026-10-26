import AppKit
import QuartzCore

extension OriginalSearchField: NSMenuDelegate {
    @discardableResult
    public func f_1000457cc() -> Int {
        guard let layer = f_100045730().layer else { return 0 }
        let x = (0.5 - layer.anchorPoint.x) * layer.bounds.width
        let y = (0.5 - layer.anchorPoint.y) * layer.bounds.height
        let animation = CAKeyframeAnimation(keyPath: "transform")
        animation.values = [1.0, 1.16, 0.98, 1.0].map { scale in
            let translated = CATransform3DMakeTranslation(x, y, 0)
            let scaled = CATransform3DScale(translated, scale, scale, 1)
            return NSValue(caTransform3D: CATransform3DTranslate(scaled, -x, -y, 0))
        }
        animation.keyTimes = [0, 0.35, 0.7, 1]
        animation.calculationMode = .cubic
        animation.duration = 0.28
        layer.add(animation, forKey: "filtersBounce")
        return 0
    }

    // The existing filter menu supplies open/close events until the remaining
    // original FilterBrowserPopover and attachment coordinator are recovered.
    public func menuWillOpen(_ menu: NSMenu) { f_1000457cc() }
    public func menuDidClose(_ menu: NSMenu) { f_1000457cc() }
}
