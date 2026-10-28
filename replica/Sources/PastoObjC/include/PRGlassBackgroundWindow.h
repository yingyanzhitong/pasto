#import <AppKit/AppKit.h>

NS_ASSUME_NONNULL_BEGIN

/// NSWindow content remains inside the native glass surface when replaced.
API_AVAILABLE(macos(26.0))
@interface PRGlassBackgroundWindow : NSWindow
@end

NS_ASSUME_NONNULL_END
