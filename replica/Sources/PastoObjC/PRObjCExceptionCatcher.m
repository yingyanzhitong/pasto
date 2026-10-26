#import "PRObjCExceptionCatcher.h"

@implementation PRObjCExceptionCatcher
+ (NSException *)catchExceptionIn:(void (NS_NOESCAPE ^)(void))operation {
    @try {
        operation();
        return nil;
    } @catch (NSException *exception) {
        return exception;
    }
}
@end
