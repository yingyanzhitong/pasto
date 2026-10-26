#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface PRObjCExceptionCatcher : NSObject
+ (nullable NSException *)catchExceptionIn:(void (NS_NOESCAPE ^)(void))operation
    NS_SWIFT_NAME(catchException(in:));
@end

NS_ASSUME_NONNULL_END
