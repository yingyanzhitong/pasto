#import "PRCloudKitEntitlements.h"
#import <Security/SecTask.h>

@implementation PRCloudKitEntitlements
+ (NSDictionary<NSString *, id> *)currentProcess {
    SecTaskRef task = SecTaskCreateFromSelf(kCFAllocatorDefault);
    if (!task) return @{};
    NSMutableDictionary *result = [NSMutableDictionary dictionary];
    for (NSString *key in @[@"com.apple.developer.icloud-container-identifiers",
                            @"com.apple.developer.icloud-services",
                            @"com.apple.developer.team-identifier",
                            @"com.apple.application-identifier",
                            @"com.apple.developer.icloud-container-environment"]) {
        CFTypeRef value = SecTaskCopyValueForEntitlement(task, (__bridge CFStringRef)key, NULL);
        if (value) result[key] = CFBridgingRelease(value);
    }
    CFRelease(task);
    return result;
}
@end
