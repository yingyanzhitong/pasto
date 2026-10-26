import AppKit
import QuartzCore

@MainActor
public enum OriginalViewAnimation {
    public static func f_10021ccd4() -> CAMediaTimingFunction {
        CAMediaTimingFunction(name: .easeOut)
    }

    public static func f_10021cd10(_ context: NSAnimationContext, duration: TimeInterval?,
                                  timingFunction: CAMediaTimingFunction?, animations: () -> Void) {
        if let duration { context.duration = duration }
        context.timingFunction = timingFunction
        context.allowsImplicitAnimation = true
        animations()
    }

    public static func f_10021ce98(_ completion: (() -> Void)?) { completion?() }

    public static func f_10021cadc(duration: TimeInterval?, timingFunction: CAMediaTimingFunction?,
                                  animated: Bool, animations: () -> Void,
                                  completion: (() -> Void)? = nil) {
        if !animated {
            animations()
            completion?()
            return
        }
        NSAnimationContext.runAnimationGroup { context in
            f_10021cd10(context, duration: duration, timingFunction: timingFunction, animations: animations)
        } completionHandler: {
            f_10021ce98(completion)
        }
    }
}
