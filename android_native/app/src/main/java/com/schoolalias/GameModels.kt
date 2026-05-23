package com.schoolalias

enum class WordStatus {
    GUESSED,
    SKIPPED,
}

data class ReviewedWord(
    val word: String,
    val status: WordStatus,
)

data class GameState(
    val subject: String = "",
    val difficulty: String = "",
    val timeLeftSeconds: Int = 60,
    val currentWord: String = "",
    val remainingWords: Int = 0,
    val isLastWordEnabled: Boolean = false,
    val isAwaitingLastWord: Boolean = false,
    val isFinished: Boolean = false,
    val reviewedWords: List<ReviewedWord> = emptyList(),
) {
    val score: Int
        get() = reviewedWords.count { it.status == WordStatus.GUESSED }
}

interface WordsRepository {
    fun wordsFor(subject: String, difficulty: String): List<String>
    fun subjects(): List<String>
    fun difficulties(subject: String): List<String>
}

class InMemoryWordsRepository(
    private val words: Map<String, Map<String, List<String>>>,
) : WordsRepository {
    override fun wordsFor(subject: String, difficulty: String): List<String> {
        return words[subject]?.get(difficulty).orEmpty()
    }

    override fun subjects(): List<String> = words.keys.toList()

    override fun difficulties(subject: String): List<String> {
        return words[subject]?.keys?.toList().orEmpty()
    }
}
