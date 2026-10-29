#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN
@interface PRCloudKitEntitlements : NSObject
+ (NSDictionary<NSString *, id> *)currentProcess;
@end
NS_ASSUME_NONNULL_END
