package com.schoolalias

import android.content.Context
import org.json.JSONObject

class AssetWordsRepository(context: Context) : WordsRepository {
    private val words: Map<String, Map<String, List<String>>> =
        parseWords(context.assets.open("words_db.json").bufferedReader().use { it.readText() })

    override fun wordsFor(subject: String, difficulty: String): List<String> {
        return words[subject]?.get(difficulty).orEmpty()
    }

    override fun subjects(): List<String> = words.keys.toList()

    override fun difficulties(subject: String): List<String> {
        return words[subject]?.keys?.toList().orEmpty()
    }

    private fun parseWords(json: String): Map<String, Map<String, List<String>>> {
        val root = JSONObject(json)
        return root.keys().asSequence().associateWith { subject ->
            val subjectObject = root.getJSONObject(subject)
            subjectObject.keys().asSequence().associateWith { difficulty ->
                val array = subjectObject.getJSONArray(difficulty)
                List(array.length()) { index -> array.getString(index) }
            }
        }
    }
}
