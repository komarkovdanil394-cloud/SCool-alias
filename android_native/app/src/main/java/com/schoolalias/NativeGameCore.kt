package com.schoolalias

object NativeGameCore {
    private var nativeLoaded = false

    init {
        nativeLoaded = try {
            System.loadLibrary("schoolaliascore")
            true
        } catch (_: UnsatisfiedLinkError) {
            false
        }
    }

    private external fun nativeNormalizeDuration(seconds: Int): Int

    fun normalizeDuration(seconds: Int): Int {
        if (nativeLoaded) return nativeNormalizeDuration(seconds)
        return seconds.coerceIn(30, 180)
    }

    private external fun nativeScoreForStatus(status: Int, penalty: Int): Int

    fun scoreForStatus(status: Int, penalty: Int): Int {
        if (nativeLoaded) return nativeScoreForStatus(status, penalty)
        return when (status) {
            1 -> 1
            2 -> -penalty
            else -> 0
        }
    }
}
