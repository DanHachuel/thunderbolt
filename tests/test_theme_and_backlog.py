from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
CONFIG_SOURCE = (ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8")


class ThemeAndBacklogTests(unittest.TestCase):
    def test_backlog_uses_canonical_title(self):
        self.assertIn('st.subheader("Backlog Vídeos")', MAIN_SOURCE)
        self.assertNotIn('st.subheader("Vídeos e backlog")', MAIN_SOURCE)

    def test_backlog_cards_match_automation_start_stop_controls(self):
        self.assertIn('key=f"automation_start_{task[\'id\']}"', MAIN_SOURCE)
        self.assertIn('key=f"automation_stop_{task[\'id\']}"', MAIN_SOURCE)
        self.assertIn('disabled=state not in {"to_do", "blocked", "failed"}', MAIN_SOURCE)
        self.assertIn('disabled=state != "doing"', MAIN_SOURCE)
        self.assertNotIn('key=f"start_{task[\'id\']}"', MAIN_SOURCE)
        self.assertNotIn('key=f"stop_{task[\'id\']}"', MAIN_SOURCE)

    def test_streamlit_exposes_switchable_light_and_dark_themes(self):
        self.assertIn("[theme.dark]", CONFIG_SOURCE)
        self.assertIn("[theme.light]", CONFIG_SOURCE)
        self.assertIn('[client]\ntoolbarMode = "auto"', CONFIG_SOURCE)
        theme_root = CONFIG_SOURCE.split("[theme.dark]", 1)[0]
        self.assertNotIn('base = "dark"', theme_root)
        self.assertNotIn('base = "light"', theme_root)

    def test_dashboard_cards_do_not_force_dark_palette(self):
        self.assertIn(".content-card {", MAIN_SOURCE)
        self.assertIn("background:color-mix(in srgb, currentColor 5%, transparent)", MAIN_SOURCE)
        self.assertNotIn("background:#121b26", MAIN_SOURCE)
        self.assertNotIn("color:#f4f8fb; font-size:1.8rem", MAIN_SOURCE)


if __name__ == "__main__":
    unittest.main()
