package com.schoolalias

import android.view.GestureDetector
import android.view.MotionEvent
import android.view.View

interface SwipeCallbacks {
    fun wordGuessed()
    fun wordSkipped()
    fun showSwipePreview(dx: Float, dy: Float, guessed: Boolean)
    fun resetSwipePreview()
}

class SwipeGestureListener(
    private val cardView: View,
    private val callbacks: SwipeCallbacks,
) : GestureDetector.SimpleOnGestureListener() {
    private val threshold = 110
    private val velocityThreshold = 140

    override fun onDown(e: MotionEvent): Boolean = true

    override fun onScroll(
        e1: MotionEvent?,
        e2: MotionEvent,
        distanceX: Float,
        distanceY: Float,
    ): Boolean {
        val dx = e2.x - (e1?.x ?: e2.x)
        val dy = e2.y - (e1?.y ?: e2.y)
        val guessed = dx > 0 || dy < 0
        cardView.translationX = dx * 0.35f
        cardView.translationY = dy * 0.22f
        callbacks.showSwipePreview(dx, dy, guessed)
        return true
    }

    override fun onFling(
        e1: MotionEvent?,
        e2: MotionEvent,
        velocityX: Float,
        velocityY: Float,
    ): Boolean {
        if (e1 == null) return false
        val dx = e2.x - e1.x
        val dy = e2.y - e1.y
        val isHorizontal = kotlin.math.abs(dx) >= kotlin.math.abs(dy)
        val hasDistance = kotlin.math.abs(dx) > threshold || kotlin.math.abs(dy) > threshold
        val hasVelocity = kotlin.math.abs(velocityX) > velocityThreshold ||
            kotlin.math.abs(velocityY) > velocityThreshold
        if (!hasDistance || !hasVelocity) return false

        cardView.animate().translationX(0f).translationY(0f).setDuration(120).start()
        if ((isHorizontal && dx > 0) || (!isHorizontal && dy < 0)) {
            callbacks.wordGuessed()
        } else {
            callbacks.wordSkipped()
        }
        return true
    }

    fun cancelPreview() {
        cardView.animate().translationX(0f).translationY(0f).setDuration(120).start()
        callbacks.resetSwipePreview()
    }
}
