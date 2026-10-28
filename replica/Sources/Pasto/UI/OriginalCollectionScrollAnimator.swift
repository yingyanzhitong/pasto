import AppKit
import CoreVideo
import QuartzCore

/// The six polynomial coefficients stored by the original cubic timing function.
struct OriginalCollectionCubicTimingCurve {
    let ax: Double
    let bx: Double
    let cx: Double
    let ay: Double
    let by: Double
    let cy: Double

    // f1f8a84: return the parameter, without applying the Y polynomial.
    func parameter(x: Double, epsilon: Double) -> Double {
        func sample(_ t: Double) -> Double { t * (cx + t * (t * ax + bx)) }
        var t = x
        var error = sample(t) - x
        if abs(error) < epsilon { return t }
        let a3 = ax * 3
        let b2 = bx + bx
        func derivative(_ t: Double) -> Double { cx + t * (t * a3 + b2) }
        for _ in 0..<7 {
            let slope = derivative(t)
            guard abs(slope) >= 0.000001 else { break }
            t -= error / slope
            error = sample(t) - x
            if abs(error) < epsilon { return t }
        }
        if !(x >= 0) { return 0 }
        if !(x <= 1) { return 1 }
        var lower = 0.0
        var upper = 1.0
        t = x
        repeat {
            let value = sample(t)
            if abs(value - x) < epsilon { return t }
            if x <= value { upper = t } else { lower = t }
            t = lower + (upper - lower) * 0.5
        } while lower < upper
        return t
    }

    // f1f8858: solve X, then apply the stored Y polynomial.
    func value(at x: Double, epsilon: Double) -> Double {
        let t = parameter(x: x, epsilon: epsilon)
        return t * (cy + t * (t * ay + by))
    }
}

/// CGPoint specialization of the original keyed animator, used by collection scrolling.
@MainActor
final class OriginalCollectionScrollAnimator {
    @MainActor
    private struct Animation {
        let from: CGPoint
        let to: CGPoint
        let duration: Double
        let startTime: Double
        let update: (CGPoint) -> Void
        let completion: ((Bool) -> Void)?

        // f1f42bc / f1f4414: clamp before easing, then interpolate the point.
        func tick(_ timestamp: Double) {
            let progress = (timestamp - startTime) / duration
            var bounded = progress <= 1 ? progress : 1
            if bounded < 0 { bounded = 0 }
            let eased = OriginalCollectionScrollAnimator.timing(bounded, duration: duration)
            let point: CGPoint
            if eased <= 0 {
                point = from
            } else if eased < 1 {
                point = CGPoint(x: from.x + (to.x - from.x) * eased,
                    y: from.y + (to.y - from.y) * eased)
            } else {
                point = to
            }
            update(point)
        }
    }

    private var animations: [String: Animation] = [:]
    private var clock: OriginalCollectionDisplayClock?
    private var lastScrollTimestamp: Double = 0

    // f229d4c: matching and immediate offsets do not cancel an existing animation.
    func setContentOffset(_ target: CGPoint, in clip: NSClipView, animated: Bool,
        completion: ((Bool) -> Void)? = nil) {
        if clip.bounds.origin == target {
            completion?(true)
            return
        }
        guard animated else {
            var bounds = clip.bounds
            bounds.origin = target
            clip.bounds = bounds
            completion?(true)
            return
        }
        let now = CACurrentMediaTime()
        let elapsed = fmin(now - lastScrollTimestamp, 0.25)
        lastScrollTimestamp = now
        let from = clip.bounds.origin
        let duration = elapsed > 0.1 ? elapsed : 0
        let animation = Animation(from: from, to: target, duration: duration,
            startTime: CACurrentMediaTime(), update: { [weak clip] point in
                guard let clip else { return }
                var bounds = clip.bounds
                bounds.origin = point
                clip.bounds = bounds
            }, completion: completion)
        // f20b948 / f1f4a1c: remove before cancellation; callbacks may reenter.
        let key = "contentOffset"
        animations.removeValue(forKey: key)?.completion?(false)
        animations[key] = animation
        start()
    }

    private func start() {
        guard !animations.isEmpty else { return }
        if clock == nil {
            clock = OriginalCollectionDisplayClock { [weak self] timestamp in self?.tick(timestamp) }
        }
        clock?.start()
    }

    // f1f5144: retain a value snapshot, complete before removing its original key.
    private func tick(_ timestamp: Double) {
        let snapshot = animations
        for (key, animation) in snapshot {
            animation.tick(timestamp)
            if animation.startTime + animation.duration <= timestamp {
                animation.completion?(true)
                animations.removeValue(forKey: key)
            }
        }
        if animations.isEmpty { clock?.stop() }
    }

    // f1f6900: the actual scroll consumer supplies f229d4c's stored coefficients.
    private static func timing(_ x: Double, duration: Double) -> Double {
        let epsilon = fmax(duration * 0.005, 0.0001)
        let curve = OriginalCollectionCubicTimingCurve(ax: 1, bx: -0.75, cx: 0.75,
            ay: -1.7000000000000004, by: 2.4000000000000004, cy: 0.30000000000000004)
        return curve.value(at: x, epsilon: epsilon)
    }
}

/// f1f72d8 / f1f7444 / f1f7600: capture media time on the display thread,
/// then deliver it on MainActor while the clock is still alive.
private final class OriginalCollectionDisplayClock {
    private let link: CVDisplayLink
    private let onTick: @MainActor @Sendable (Double) -> Void

    init?(onTick: @escaping @MainActor @Sendable (Double) -> Void) {
        var created: CVDisplayLink?
        CVDisplayLinkCreateWithActiveCGDisplays(&created)
        guard let created else { return nil }
        link = created
        self.onTick = onTick
        CVDisplayLinkSetOutputHandler(created) { [weak self] _, _, _, _, _ in
            let timestamp = CACurrentMediaTime()
            Task { @MainActor [weak self] in self?.onTick(timestamp) }
            return kCVReturnSuccess
        }
        CVDisplayLinkSetCurrentCGDisplay(created, CGMainDisplayID())
    }

    func start() {
        if !CVDisplayLinkIsRunning(link) { CVDisplayLinkStart(link) }
    }

    func stop() {
        if CVDisplayLinkIsRunning(link) { CVDisplayLinkStop(link) }
    }

    deinit {
        if CVDisplayLinkIsRunning(link) { CVDisplayLinkStop(link) }
    }
}
