import unittest

from data.word_provider import StaticWordProvider, UserWordProvider, parse_user_words


class CustomWordsTests(unittest.TestCase):
    def test_parse_user_words_accepts_lines_commas_and_deduplicates(self):
        words = parse_user_words(" школа, урок\nКласс; школа \n\nдоска")

        self.assertEqual(words, ["школа", "урок", "Класс", "доска"])

    def test_user_provider_exposes_custom_subject_when_words_exist(self):
        base = StaticWordProvider(
            base_catalog={"Обычная тема": {"easy": ["слово"]}},
            localized_catalogs={},
        )
        provider = UserWordProvider(base)

        provider.set_user_words(["парта", "звонок"])

        self.assertEqual(provider.get_subjects("ru")[0], "Свои слова")
        self.assertEqual(provider.get_words("Свои слова", "hard", "ru"), ["парта", "звонок"])

    def test_user_provider_falls_back_to_base_when_custom_words_are_empty(self):
        base = StaticWordProvider(
            base_catalog={"Обычная тема": {"easy": ["слово"]}},
            localized_catalogs={},
        )
        provider = UserWordProvider(base)

        provider.set_user_words([])

        self.assertEqual(provider.get_subjects("ru"), ["Обычная тема"])
        self.assertEqual(provider.get_words("Обычная тема", "easy", "ru"), ["слово"])


if __name__ == "__main__":
    unittest.main()
