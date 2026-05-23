package com.schoolalias

import android.os.Bundle
import android.os.CountDownTimer
import android.view.GestureDetector
import android.view.MotionEvent
import android.widget.AdapterView
import android.widget.ArrayAdapter
import androidx.activity.ComponentActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.ViewModelProvider
import androidx.recyclerview.widget.LinearLayoutManager
import com.schoolalias.databinding.FragmentGameBinding
import com.schoolalias.databinding.FragmentReviewBinding
import com.schoolalias.databinding.FragmentSetupBinding
import kotlin.random.Random

class MainActivity : ComponentActivity(), SwipeCallbacks {
    private lateinit var viewModel: GameViewModel
    private lateinit var repository: WordsRepository
    private var timer: CountDownTimer? = null
    private var gameBinding: FragmentGameBinding? = null
    private var swipeListener: SwipeGestureListener? = null
    private var gestureDetector: GestureDetector? = null
    private val teams = listOf("Команда A", "Команда B")

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        repository = AssetWordsRepository(this)
        viewModel = ViewModelProvider(
            this,
            GameViewModelFactory(repository),
        )[GameViewModel::class.java]
        showSetup()
    }

    override fun onDestroy() {
        timer?.cancel()
        super.onDestroy()
    }

    private fun showSetup() {
        timer?.cancel()
        val binding = FragmentSetupBinding.inflate(layoutInflater)
        setContentView(binding.root)
        val subjects = repository.subjects()
        val durations = listOf(30, 60, 90)
        var selectedSubject = subjects.firstOrNull().orEmpty()

        binding.subjectSpinner.adapter = simpleAdapter(subjects)
        binding.difficultySpinner.adapter = simpleAdapter(repository.difficulties(selectedSubject))
        binding.durationSpinner.adapter = simpleAdapter(durations.map { "$it секунд" })

        binding.subjectSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(
                parent: AdapterView<*>?,
                view: android.view.View?,
                position: Int,
                id: Long,
            ) {
                selectedSubject = subjects[position]
                binding.difficultySpinner.adapter = simpleAdapter(repository.difficulties(selectedSubject))
            }

            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
        }
        binding.randomizeTurnButton.setOnClickListener {
            binding.turnLabel.text = "Первой ходит: ${teams[Random.nextInt(teams.size)]}"
        }
        binding.startGameButton.setOnClickListener {
            val difficulty = binding.difficultySpinner.selectedItem?.toString().orEmpty()
            val duration = durations[binding.durationSpinner.selectedItemPosition.coerceAtLeast(0)]
            viewModel.startRound(
                subject = selectedSubject,
                difficulty = difficulty,
                durationSeconds = duration,
                isLastWordEnabled = binding.lastWordSwitch.isChecked,
            )
            showGame()
        }
    }

    private fun showGame() {
        val binding = FragmentGameBinding.inflate(layoutInflater)
        gameBinding = binding
        setContentView(binding.root)
        val listener = SwipeGestureListener(binding.wordCard, this)
        swipeListener = listener
        gestureDetector = GestureDetector(this, listener)
        binding.wordCard.setOnTouchListener { _, event ->
            val handled = gestureDetector?.onTouchEvent(event) == true
            if (event.action == MotionEvent.ACTION_UP || event.action == MotionEvent.ACTION_CANCEL) {
                swipeListener?.cancelPreview()
            }
            handled
        }
        binding.guessedButton.setOnClickListener { wordGuessed() }
        binding.skipButton.setOnClickListener { wordSkipped() }
        renderGame()
        startTimer(viewModel.state.timeLeftSeconds)
    }

    private fun startTimer(seconds: Int) {
        timer?.cancel()
        timer = object : CountDownTimer(seconds * 1000L, 1000L) {
            override fun onTick(millisUntilFinished: Long) {
                viewModel.tick((millisUntilFinished / 1000L).toInt() + 1)
                renderGame()
            }

            override fun onFinish() {
                viewModel.onTimerExpired()
                renderGame()
                if (viewModel.state.isFinished) showReview()
            }
        }.start()
    }

    override fun wordGuessed() {
        viewModel.wordGuessed()
        afterWordProcessed()
    }

    override fun wordSkipped() {
        viewModel.wordSkipped()
        afterWordProcessed()
    }

    override fun showSwipePreview(dx: Float, dy: Float, guessed: Boolean) {
        val color = if (guessed) R.color.school_green else R.color.school_red
        gameBinding?.wordCard?.setBackgroundColor(ContextCompat.getColor(this, color))
    }

    override fun resetSwipePreview() {
        gameBinding?.wordCard?.setBackgroundColor(ContextCompat.getColor(this, R.color.school_surface))
    }

    private fun afterWordProcessed() {
        resetSwipePreview()
        if (viewModel.state.isFinished) {
            timer?.cancel()
            showReview()
        } else {
            renderGame()
        }
    }

    private fun renderGame() {
        val state = viewModel.state
        val binding = gameBinding ?: return
        binding.wordText.text = state.currentWord.ifBlank { "Нет слов" }
        binding.timerText.text = state.timeLeftSeconds.toString()
        binding.scoreText.text = state.score.toString()
    }

    private fun showReview() {
        val binding = FragmentReviewBinding.inflate(layoutInflater)
        setContentView(binding.root)
        val adapter = SessionReviewAdapter { word, status ->
            viewModel.updateReviewStatus(word, status)
            binding.finalScoreText.text = "Итог: ${viewModel.state.score}"
        }
        binding.reviewList.layoutManager = LinearLayoutManager(this)
        binding.reviewList.adapter = adapter
        adapter.submitList(viewModel.state.reviewedWords)
        binding.finalScoreText.text = "Итог: ${viewModel.state.score}"
        binding.newRoundButton.setOnClickListener { showSetup() }
    }

    private fun simpleAdapter(values: List<String>): ArrayAdapter<String> {
        return ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, values)
    }
}
