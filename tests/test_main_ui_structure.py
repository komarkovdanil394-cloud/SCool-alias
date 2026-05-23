import inspect
import unittest

from main import AliasNeonApp


class MainUiStructureTests(unittest.TestCase):
    def test_project_name_is_scool_alias(self):
        self.assertEqual(AliasNeonApp.APP_NAME, "SCool Alias")

    def test_final_screen_contains_round_review_controls(self):
        source = inspect.getsource(AliasNeonApp.show_final)

        self.assertIn("_build_reviewed_words_panel", source)
        self.assertIn("reviewed_words", source)

    def test_settings_screen_owns_round_duration_setting(self):
        source = inspect.getsource(AliasNeonApp.show_settings)

        self.assertIn("round_time_slider", source)

    def test_setup_screen_no_longer_owns_round_settings(self):
        source = inspect.getsource(AliasNeonApp.show_setup)

        self.assertNotIn("subject_dd", source)
        self.assertNotIn("difficulty_dd", source)
        self.assertNotIn("target_slider", source)
        self.assertNotIn("language_panel", source)

    def test_settings_screen_owns_round_settings(self):
        source = inspect.getsource(AliasNeonApp.show_settings)

        self.assertIn("subject_dd", source)
        self.assertIn("difficulty_dd", source)
        self.assertIn("target_slider", source)
        self.assertIn("_language_selector", source)

    def test_lobby_start_uses_saved_round_settings(self):
        source = inspect.getsource(AliasNeonApp.start_round_from_lobby)

        self.assertIn("selected_subject", source)
        self.assertIn("selected_difficulty", source)
        self.assertNotIn("subject_dd", source)
        self.assertNotIn("difficulty_dd", source)
        self.assertNotIn("target_slider", source)


if __name__ == "__main__":
    unittest.main()
