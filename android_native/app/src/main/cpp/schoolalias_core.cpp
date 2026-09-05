#include <jni.h>

extern "C" JNIEXPORT jint JNICALL
Java_com_schoolalias_NativeGameCore_nativeNormalizeDuration(JNIEnv*, jobject, jint seconds) {
    if (seconds < 30) return 30;
    if (seconds > 180) return 180;
    return seconds;
}

extern "C" JNIEXPORT jint JNICALL
Java_com_schoolalias_NativeGameCore_nativeScoreForStatus(JNIEnv*, jobject, jint status, jint penalty) {
    if (status == 1) return 1;
    if (status == 2) return -penalty;
    return 0;
}
