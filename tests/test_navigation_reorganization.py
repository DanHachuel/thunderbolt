from pathlib import Path
import unittest

from hermes_ui.languages import ui_text


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
LANGUAGES_SOURCE = (ROOT / "hermes_ui" / "languages.py").read_text(encoding="utf-8")


class NavigationReorganizationTests(unittest.TestCase):
    def test_top_level_order_matches_requested_structure(self):
        expected_order = [
            '"Início"',
            '"Automação"',
            '"Niche Finder"',
            '"Pipeline Vídeos"',
            '"AI Influencers"',
            '"Arquivos Base"',
            '"Canais e Perfis de Vídeos"',
            '"Música"',
            '"Edição"',
            '"Growth"',
            '"Documentação"',
            '"Configurações"',
        ]
        top_block = MAIN_SOURCE.split("    top_pages = [", 1)[1].split("    ]", 1)[0]
        positions = [top_block.index(item) for item in expected_order]
        self.assertEqual(positions, sorted(positions))

    def test_requested_groups_and_children_are_present(self):
        required = (
            "Arquivos Base", "Blueprints Youtube", "Prompt Masters",
            "Canais e Perfis de Vídeos", "Canais YouTube", "Contas TikTok", "Facebook Pages",
            "Pipeline Vídeos", "Criação de Vídeos", "Backlog Vídeos", "Roteiros", "Upload",
            "AI Influencers", "Personagens", "Geração de Conteúdo IA", "Motion Control", "UGC Products", "Redes Sociais",
            "Música", "Criação de Músicas", "Upload Música",
            "Growth", "Analista Growth Youtube", "Analista Growth Tiktok", "Analista Growth Instagram",
            "Documentação", "Tutorial Meta", "Tutorial Supabase", "Tutorial Kaggle", "Tutorial Apify",
        )
        for label in required:
            self.assertIn(f'"{label}"', MAIN_SOURCE)

    def test_video_backlog_is_not_nested_inside_video_creation(self):
        self.assertIn('create_tab = render_localized_tabs(["Criar vídeo"])[0]', MAIN_SOURCE)
        self.assertNotIn("with videos_tab:", MAIN_SOURCE)
        self.assertIn('"Backlog Vídeos": render_videos', MAIN_SOURCE)

    def test_settings_order_keeps_notifications_before_api(self):
        settings_block = MAIN_SOURCE.split("    settings_items = [", 1)[1].split("    ]", 1)[0]
        self.assertLess(settings_block.index('"Notificações"'), settings_block.index('"Configuração API"'))

    def test_navigation_labels_have_translations_for_all_languages(self):
        languages = ("pt", "en", "zh", "de", "vi", "tr", "ru", "es", "id", "it")
        labels = (
            "Arquivos Base", "Pipeline Vídeos", "Canais e Perfis de Vídeos", "Canais YouTube",
            "Facebook Pages", "Prompt Masters", "Backlog Vídeos", "Música", "Upload Música",
            "Geração de Conteúdo IA", "Motion Control", "UGC Products", "Growth",
            "Analista Growth Youtube", "Analista Growth Tiktok", "Analista Growth Instagram",
            "Documentação", "Tutorial Kaggle", "Tutorial Apify", "Pipeline Músicas", "módulos disponíveis",
        )
        navigation_source = LANGUAGES_SOURCE.split("UI_NAV_TRANSLATIONS", 1)[1]
        for language in languages:
            language_block = navigation_source.split(f'    "{language}": {{', 1)[1].split("    },", 1)[0]
            for label in labels:
                self.assertIn(f'"{label}"', language_block, f"missing {label} source key for {language}")
                self.assertTrue(ui_text(label, language).strip(), f"empty translation for {label} in {language}")


if __name__ == "__main__":
    unittest.main()
