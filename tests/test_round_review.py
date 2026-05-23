import random
import unittest

from core.engine import GameEngine
from core.models import RoundConfig, WordReviewStatus
from core.session import GameSession


class FakeWordProvider:
    def get_words(self, subject, difficulty_id, language_code="ru"):
        self.last_request = (subject, difficulty_id, language_code)
        return ["дробь", "уравнение", "теорема"]


class RoundReviewTests(unittest.TestCase):
    def _session(self):
        return GameSession.create(
            config=RoundConfig(
                subject="Математика",
                difficulty_label="Легкий",
                difficulty_id="easy",
                time_total=60,
                penalty=1,
                team="Team A",
            ),
            word_provider=FakeWordProvider(),
            rng=random.Random(7),
        )

    def test_next_word_records_pending_review_item(self):
        session = self._session()

        word = session.next_word()

        self.assertEqual(session.state.reviewed_words[-1].word, word)
        self.assertEqual(session.state.reviewed_words[-1].status, WordReviewStatus.PENDING)

    def test_answer_updates_current_review_item(self):
        session = self._session()
        session.next_word()

        session.apply_answer(True)

        self.assertEqual(session.state.reviewed_words[-1].status, WordReviewStatus.CORRECT)

    def test_unanswered_last_word_is_ignored_by_score_recalculation(self):
        session = self._session()
        session.next_word()

        result = GameEngine().recalculate_from_reviews(session.state)

        self.assertEqual(result.score, 0)
        self.assertEqual(result.correct, 0)
        self.assertEqual(result.skipped, 0)

    def test_review_recalculation_supports_changed_statuses(self):
        session = self._session()
        session.next_word()
        session.apply_answer(False)
        session.next_word()
        session.apply_answer(True)

        session.state.reviewed_words[0].status = WordReviewStatus.CORRECT
        result = GameEngine().recalculate_from_reviews(session.state)

        self.assertEqual(result.score, 2)
        self.assertEqual(result.correct, 2)
        self.assertEqual(result.skipped, 0)


if __name__ == "__main__":
    unittest.main()
