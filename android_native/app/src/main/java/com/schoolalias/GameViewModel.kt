package com.schoolalias

import androidx.lifecycle.ViewModel

private val ALLOWED_DURATIONS = setOf(30, 60, 90)

class GameViewModel(
    private val wordsRepository: WordsRepository,
) : ViewModel() {
    var state: GameState = GameState()
        private set

    private var wordQueue: MutableList<String> = mutableListOf()
    private var timerExpired: Boolean = false

    fun startRound(
        subject: String,
        difficulty: String,
        durationSeconds: Int,
        isLastWordEnabled: Boolean,
    ) {
        val normalizedDuration = if (durationSeconds in ALLOWED_DURATIONS) durationSeconds else 60
        wordQueue = wordsRepository.wordsFor(subject, difficulty).toMutableList()
        timerExpired = false
        val firstWord = nextWord()
        state = GameState(
            subject = subject,
            difficulty = difficulty,
            timeLeftSeconds = normalizedDuration,
            currentWord = firstWord,
            remainingWords = wordQueue.size + if (firstWord.isNotBlank()) 1 else 0,
            isLastWordEnabled = isLastWordEnabled,
        )
    }

    fun tick(secondsLeft: Int) {
        state = state.copy(timeLeftSeconds = secondsLeft.coerceIn(0, 90))
    }

    fun onTimerExpired() {
        timerExpired = true
        state = if (state.isLastWordEnabled && state.currentWord.isNotBlank()) {
            state.copy(timeLeftSeconds = 0, isAwaitingLastWord = true)
        } else {
            state.copy(timeLeftSeconds = 0, isFinished = true)
        }
    }

    fun wordGuessed() {
        processCurrentWord(WordStatus.GUESSED)
    }

    fun wordSkipped() {
        processCurrentWord(WordStatus.SKIPPED)
    }

    fun updateReviewStatus(word: String, status: WordStatus) {
        state = state.copy(
            reviewedWords = state.reviewedWords.map {
                if (it.word == word) it.copy(status = status) else it
            },
        )
    }

    private fun processCurrentWord(status: WordStatus) {
        if (state.currentWord.isBlank() || state.isFinished) return

        val updatedReview = state.reviewedWords + ReviewedWord(state.currentWord, status)
        if (timerExpired && state.isLastWordEnabled) {
            state = state.copy(
                reviewedWords = updatedReview,
                isAwaitingLastWord = false,
                isFinished = true,
                remainingWords = wordQueue.size,
            )
            return
        }

        val newWord = nextWord()
        state = state.copy(
            currentWord = newWord,
            reviewedWords = updatedReview,
            remainingWords = wordQueue.size + if (newWord.isNotBlank()) 1 else 0,
            isFinished = newWord.isBlank(),
        )
    }

    private fun nextWord(): String {
        if (wordQueue.isEmpty()) return ""
        return wordQueue.removeAt(0)
    }
}
