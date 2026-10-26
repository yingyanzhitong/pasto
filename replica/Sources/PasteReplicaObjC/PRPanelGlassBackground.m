#import "PRPanelGlassBackground.h"
#import <QuartzCore/QuartzCore.h>

@protocol PRPanelGlassConfiguration
@property(nonatomic) CGFloat cornerRadius;
@end

@implementation PRPanelGlassBackground {
    NSView *_effect;
}

- (instancetype)initWithFrame:(NSRect)frame {
    self = [super initWithFrame:frame];
    if (self) {
        if (@available(macOS 26.0, *)) {
            Class glassClass = NSClassFromString(@"NSGlassEffectView");
            if ([glassClass isSubclassOfClass:NSView.class]) {
                _effect = [[glassClass alloc] initWithFrame:self.bounds];
            }
        }
        if (!_effect) {
            NSVisualEffectView *visualEffect = [[NSVisualEffectView alloc] initWithFrame:self.bounds];
            visualEffect.material = NSVisualEffectMaterialHUDWindow;
            visualEffect.blendingMode = NSVisualEffectBlendingModeBehindWindow;
            visualEffect.state = NSVisualEffectStateActive;
            _effect = visualEffect;
        }
        _effect.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
        [self addSubview:_effect];
    }
    return self;
}

- (void)setCornerRadius:(CGFloat)cornerRadius {
    _cornerRadius = cornerRadius;
    if ([_effect respondsToSelector:@selector(setCornerRadius:)]) {
        ((id<PRPanelGlassConfiguration>)_effect).cornerRadius = cornerRadius;
    } else {
        _effect.wantsLayer = YES;
        _effect.layer.cornerRadius = cornerRadius;
        _effect.layer.masksToBounds = YES;
    }
}

- (NSView *)hitTest:(NSPoint)point {
    return nil;
}

@end
