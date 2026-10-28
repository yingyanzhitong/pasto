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
    self = [super initWithContentRect:contentRect styleMask:style backing:backingStoreType defer:flag];
    if (self) {
        // Resolve the public Tahoe class at runtime to support older build SDKs.
        Class glassClass = NSClassFromString(@"NSGlassEffectView");
        if ([glassClass isSubclassOfClass:NSView.class]) {
            NSView *content = [super contentView];
            _glassView = [[glassClass alloc] initWithFrame:contentRect];
            _glassView.cornerRadius = 26;
            [super setContentView:_glassView];
            _glassView.contentView = content;
        }
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
