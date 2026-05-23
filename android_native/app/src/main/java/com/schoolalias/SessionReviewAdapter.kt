package com.schoolalias

import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.ArrayAdapter
import androidx.recyclerview.widget.RecyclerView
import com.schoolalias.databinding.ItemReviewedWordBinding

class SessionReviewAdapter(
    private val onStatusChanged: (String, WordStatus) -> Unit,
) : RecyclerView.Adapter<SessionReviewAdapter.WordViewHolder>() {
    private var items: List<ReviewedWord> = emptyList()

    fun submitList(words: List<ReviewedWord>) {
        items = words
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): WordViewHolder {
        val binding = ItemReviewedWordBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false,
        )
        return WordViewHolder(binding)
    }

    override fun getItemCount(): Int = items.size

    override fun onBindViewHolder(holder: WordViewHolder, position: Int) {
        holder.bind(items[position])
    }

    inner class WordViewHolder(
        private val binding: ItemReviewedWordBinding,
    ) : RecyclerView.ViewHolder(binding.root) {
        fun bind(item: ReviewedWord) {
            binding.reviewWord.text = item.word
            val labels = listOf("Угадано", "Пропуск")
            binding.reviewStatus.adapter = ArrayAdapter(
                binding.root.context,
                android.R.layout.simple_spinner_dropdown_item,
                labels,
            )
            binding.reviewStatus.setSelection(if (item.status == WordStatus.GUESSED) 0 else 1)
            binding.reviewStatus.setOnItemSelectedListener(object : android.widget.AdapterView.OnItemSelectedListener {
                override fun onItemSelected(
                    parent: android.widget.AdapterView<*>?,
                    view: android.view.View?,
                    position: Int,
                    id: Long,
                ) {
                    onStatusChanged(
                        item.word,
                        if (position == 0) WordStatus.GUESSED else WordStatus.SKIPPED,
                    )
                }

                override fun onNothingSelected(parent: android.widget.AdapterView<*>?) = Unit
            })
        }
    }
}
