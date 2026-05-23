package com.schoolalias

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class GameViewModelTest {
    private val words = mapOf(
        "История" to mapOf(
            "easy" to listOf("Рюрик", "Летопись"),
            "medium" to listOf("Опричнина"),
            "hard" to listOf("Смута"),
        ),
        "Обществознание" to mapOf(
            "easy" to listOf("Право"),
            "medium" to listOf("Институт"),
            "hard" to listOf("Легитимность"),
        ),
    )

    @Test
    fun startsRoundWithWordsSelectedBySubjectAndDifficultyOnly() {
        val viewModel = GameViewModel(InMemoryWordsRepository(words))

        viewModel.startRound(
            subject = "История",
            difficulty = "medium",
            durationSeconds = 60,
            isLastWordEnabled = false,
        )

        assertEquals("Опричнина", viewModel.state.currentWord)
        assertEquals(1, viewModel.state.remainingWords)
    }

    @Test
    fun supportsOnlyFixedTimerDurations() {
        val viewModel = GameViewModel(InMemoryWordsRepository(words))

        viewModel.startRound("История", "easy", durationSeconds = 45, isLastWordEnabled = false)

        assertEquals(60, viewModel.state.timeLeftSeconds)
    }

    @Test
    fun lastWordModeDelaysFinishUntilCurrentWordIsProcessed() {
        val viewModel = GameViewModel(InMemoryWordsRepository(words))
        viewModel.startRound("История", "easy", durationSeconds = 30, isLastWordEnabled = true)

        viewModel.onTimerExpired()

        assertFalse(viewModel.state.isFinished)
        assertTrue(viewModel.state.isAwaitingLastWord)

        viewModel.wordGuessed()

        assertTrue(viewModel.state.isFinished)
    }

    @Test
    fun logsEveryExposedWordForReviewAndCorrection() {
        val viewModel = GameViewModel(InMemoryWordsRepository(words))
        viewModel.startRound("История", "easy", durationSeconds = 30, isLastWordEnabled = false)

        val first = viewModel.state.currentWord
        viewModel.wordSkipped()
        val second = viewModel.state.currentWord
        viewModel.wordGuessed()
        viewModel.updateReviewStatus(first, WordStatus.GUESSED)

        assertEquals(
            listOf(
                ReviewedWord(first, WordStatus.GUESSED),
                ReviewedWord(second, WordStatus.GUESSED),
            ),
            viewModel.state.reviewedWords,
        )
    }
}
