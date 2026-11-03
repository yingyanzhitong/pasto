#import "PastoKeyTranslation.h"
#import <Carbon/Carbon.h>

int32_t PastoTranslateASCIIKeyLayoutData(void *layoutData, uint16_t keyCode,
                                       uint16_t *characters, uint64_t capacity, uint64_t *length) {
    const UCKeyboardLayout *layout = (const UCKeyboardLayout *)CFDataGetBytePtr((CFDataRef)layoutData);
    UInt32 deadKeyState = 0;
    UniCharCount actualLength = 0;
    OSStatus status = UCKeyTranslate(layout, keyCode, kUCKeyActionDisplay, 0, LMGetKbdType(), 0,
                                    &deadKeyState, (UniCharCount)capacity, &actualLength, characters);
    *length = (uint64_t)actualLength;
    return status;
}
