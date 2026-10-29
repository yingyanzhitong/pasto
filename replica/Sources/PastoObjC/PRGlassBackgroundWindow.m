#import "PRGlassBackgroundWindow.h"

@protocol PRModalGlassContent
@property(nonatomic, nullable, strong) NSView *contentView;
@property(nonatomic) CGFloat cornerRadius;
@end

@implementation PRGlassBackgroundWindow {
    NSView<PRModalGlassContent> *_glassView;
}

- (instancetype)initWithContentRect:(NSRect)contentRect
                         styleMask:(NSWindowStyleMask)style
                           backing:(NSBackingStoreType)backingStoreType
                             defer:(BOOL)flag {
    // Paste 0x10021dc14 creates the glass BEFORE NSWindow initialization:
    // NSWindow can already dispatch our contentView accessors during super init.
    Class glassClass = NSClassFromString(@"NSGlassEffectView");
    if ([glassClass isSubclassOfClass:NSView.class]) {
        _glassView = [[glassClass alloc] init];
    }
    self = [super initWithContentRect:contentRect styleMask:style backing:backingStoreType defer:flag];
    if (self && _glassView) {
        _glassView.cornerRadius = 26;
        [super setContentView:_glassView];
    }
    return self;
}

// Paste 0x10021dad0 / 0x10021db74: replace the glass content, not the surface.
- (NSView *)contentView {
    return _glassView ? _glassView.contentView : [super contentView];
}

- (void)setContentView:(NSView *)contentView {
    if (_glassView) {
        _glassView.contentView = contentView;
    } else {
        [super setContentView:contentView];
    }
}

@end
