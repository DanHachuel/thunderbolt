from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")


class AutomationCardsTests(unittest.TestCase):
    def test_automation_video_cards_have_start_and_stop_controls(self):
        self.assertIn('key=f"automation_start_{task[\'id\']}"', MAIN_SOURCE)
        self.assertIn('key=f"automation_stop_{task[\'id\']}"', MAIN_SOURCE)
        self.assertIn('key=f"automation_delete_{task[\'id\']}"', MAIN_SOURCE)
        self.assertIn('delete_task(task["id"])', MAIN_SOURCE)
        self.assertIn('st.button("Apagar"', MAIN_SOURCE)
        self.assertIn('retry_task_with_current_settings(task["id"])', MAIN_SOURCE)
        self.assertIn('transition_task(task["id"], "doing")', MAIN_SOURCE)
        self.assertIn('transition_task(task["id"], "blocked")', MAIN_SOURCE)
        self.assertIn("a nova tentativa lê as chaves, prioridades e configurações actualmente guardadas", MAIN_SOURCE)

    def test_automation_video_cards_do_not_render_channel_schedule(self):
        self.assertNotIn('st.caption("Horário do canal")', MAIN_SOURCE)
        self.assertIn('st.text_input("Horário (HH:MM)"', MAIN_SOURCE)


if __name__ == "__main__":
    unittest.main()
