#import <Foundation/Foundation.h>
#include <stdint.h>

NS_ASSUME_NONNULL_BEGIN

int32_t PastoTranslateASCIIKeyLayoutData(void * _Nullable layoutData, uint16_t keyCode,
                                       uint16_t *characters, uint64_t capacity, uint64_t *length);

NS_ASSUME_NONNULL_END
