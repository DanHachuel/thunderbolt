"""Canonical UI and video language catalog shared by Thunderbolt screens."""

from __future__ import annotations

from typing import Any


# The persisted value is always the short MoneyPrinterTurbo-compatible code.
LANGUAGE_CATALOG: tuple[dict[str, str], ...] = (
    {"code": "en", "name": "Inglês", "flag": "🇺🇸", "locale": "en-US"},
    {"code": "zh", "name": "Chinês Simplificado", "flag": "🇨🇳", "locale": "zh-CN"},
    {"code": "de", "name": "Alemão", "flag": "🇩🇪", "locale": "de-DE"},
    {"code": "vi", "name": "Vietnamita", "flag": "🇻🇳", "locale": "vi-VN"},
    {"code": "tr", "name": "Turco", "flag": "🇹🇷", "locale": "tr-TR"},
    {"code": "pt", "name": "Português", "flag": "🇧🇷", "locale": "pt-BR"},
    {"code": "ru", "name": "Russo", "flag": "🇷🇺", "locale": "ru-RU"},
    {"code": "es", "name": "Espanhol", "flag": "🇪🇸", "locale": "es-ES"},
    {"code": "id", "name": "Indonésio", "flag": "🇮🇩", "locale": "id-ID"},
    {"code": "it", "name": "Italiano", "flag": "🇮🇹", "locale": "it-IT"},
)

LANGUAGE_BY_CODE = {item["code"]: item for item in LANGUAGE_CATALOG}
LANGUAGE_CODES = tuple(item["code"] for item in LANGUAGE_CATALOG)

# Legacy labels used by existing channels, scripts and tests.  They remain
# readable while new UI selections persist only the canonical short code.
LEGACY_LANGUAGE_CODES = {
    "01 – inglês": "en",
    "01 - inglês": "en",
    "06 – alemão": "de",
    "06 - alemão": "de",
    "15 – italiano": "it",
    "15 - italiano": "it",
    "29 – turco": "tr",
    "29 - turco": "tr",
    "31 – russo": "ru",
    "31 - russo": "ru",
    "36 – português (brasil)": "pt",
    "36 - português (brasil)": "pt",
    "39 – mandarim": "zh",
    "39 - mandarim": "zh",
    "13 – espanhol (espanha)": "es",
    "41 - espanhol (latam)": "es",
    "42 – vietnamita": "vi",
    "42 - vietnamita": "vi",
    "44 – indonésio": "id",
    "44 - indonésio": "id",
    "13 – espanhol (espanha)": "es",
    "13 - espanhol (espanha)": "es",
    "37 – cantonês": "zh",
    "37 - cantonês": "zh",
    "english": "en",
    "inglês": "en",
    "inglés": "en",
    "zh": "zh",
    "chinês": "zh",
    "chinês simplificado": "zh",
    "deutsch": "de",
    "alemão": "de",
    "vietnamita": "vi",
    "turco": "tr",
    "português": "pt",
    "português (brasil)": "pt",
    "portuguese": "pt",
    "ru": "ru",
    "russo": "ru",
    "español": "es",
    "espanhol": "es",
    "indonésio": "id",
    "bahasa indonesia": "id",
    "italiano": "it",
}


def language_code(value: Any, default: str = "pt") -> str:
    """Normalize a canonical code or a legacy display label to a code."""
    raw = str(value or "").strip()
    if raw in LANGUAGE_BY_CODE:
        return raw
    lowered = raw.casefold()
    if lowered in LEGACY_LANGUAGE_CODES:
        return LEGACY_LANGUAGE_CODES[lowered]
    for item in LANGUAGE_CATALOG:
        if lowered in {item["name"].casefold(), item["locale"].casefold()}:
            return item["code"]
    return default if default in LANGUAGE_BY_CODE else "pt"


def language_label(value: Any, *, include_code: bool = True) -> str:
    """Return the visual label with the requested flag and optional code."""
    code = language_code(value)
    item = LANGUAGE_BY_CODE[code]
    suffix = f" ({item['code']})" if include_code else ""
    return f"{item['flag']} {item['name']}{suffix}"


def language_option_labels(*, include_code: bool = True) -> list[str]:
    return [language_label(item["code"], include_code=include_code) for item in LANGUAGE_CATALOG]


def language_option_codes() -> list[str]:
    return list(LANGUAGE_CODES)


UI_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "Início": "Home", "Niche Finder": "Niche Finder", "Pipeline": "Pipeline", "Pipeline TikTok": "TikTok Pipeline",
        "Automação": "Automation", "Edição": "Editing", "AI Influencers": "AI Influencers", "Configurações": "Settings",
        "Criação de Vídeos": "Video Creation", "Criação de Músicas": "Music Creation", "Roteiros": "Scripts", "Upload": "Upload",
        "Prompts Master": "Prompt Masters", "Contas TikTok": "TikTok Accounts", "Automação Youtube": "YouTube Automation",
        "Canais Youtube": "YouTube Channels", "Blueprints Youtube": "YouTube Blueprints", "Contas Google": "Google Accounts",
        "Configuração API": "API Configuration", "Notificações": "Notifications", "Niche Finder Kaggle": "Niche Finder Kaggle",
        "Niche Finder Apify": "Niche Finder Apify", "Limpador de Metadados": "Metadata Cleaner", "Cortes": "Cuts",
        "Editor Python": "Python Editor", "Download Mídia": "Media Download", "Personagens": "Characters", "Redes Sociais": "Social Networks",
        "Tutorial Meta": "Meta Tutorial", "Idioma da interface": "Interface language",
    },
    "zh": {
        "Início": "首页", "Pipeline": "视频流程", "Pipeline TikTok": "TikTok 流程", "Automação": "自动化", "Edição": "编辑", "Configurações": "设置",
        "Criação de Vídeos": "视频创作", "Criação de Músicas": "音乐创作", "Roteiros": "脚本", "Upload": "上传", "Contas Google": "Google 账户", "Notificações": "通知", "Idioma da interface": "界面语言",
    },
    "de": {
        "Início": "Startseite", "Pipeline": "Pipeline", "Pipeline TikTok": "TikTok-Pipeline", "Automação": "Automatisierung", "Edição": "Bearbeitung", "Configurações": "Einstellungen",
        "Criação de Vídeos": "Videoerstellung", "Criação de Músicas": "Musikerstellung", "Roteiros": "Skripte", "Upload": "Upload", "Contas Google": "Google-Konten", "Notificações": "Benachrichtigungen", "Idioma da interface": "Oberflächensprache",
    },
    "vi": {
        "Início": "Trang chủ", "Pipeline": "Quy trình", "Pipeline TikTok": "Quy trình TikTok", "Automação": "Tự động hóa", "Edição": "Chỉnh sửa", "Configurações": "Cài đặt",
        "Criação de Vídeos": "Tạo video", "Criação de Músicas": "Tạo nhạc", "Roteiros": "Kịch bản", "Upload": "Tải lên", "Contas Google": "Tài khoản Google", "Notificações": "Thông báo", "Idioma da interface": "Ngôn ngữ giao diện",
    },
    "tr": {
        "Início": "Ana sayfa", "Pipeline": "Akış", "Pipeline TikTok": "TikTok akışı", "Automação": "Otomasyon", "Edição": "Düzenleme", "Configurações": "Ayarlar",
        "Criação de Vídeos": "Video oluşturma", "Criação de Músicas": "Müzik oluşturma", "Roteiros": "Senaryolar", "Upload": "Yükleme", "Contas Google": "Google hesapları", "Notificações": "Bildirimler", "Idioma da interface": "Arayüz dili",
    },
    "ru": {
        "Início": "Главная", "Pipeline": "Конвейер", "Pipeline TikTok": "Конвейер TikTok", "Automação": "Автоматизация", "Edição": "Редактирование", "Configurações": "Настройки",
        "Criação de Vídeos": "Создание видео", "Criação de Músicas": "Создание музыки", "Roteiros": "Сценарии", "Upload": "Загрузка", "Contas Google": "Аккаунты Google", "Notificações": "Уведомления", "Idioma da interface": "Язык интерфейса",
    },
    "es": {
        "Início": "Inicio", "Pipeline": "Flujo", "Pipeline TikTok": "Flujo de TikTok", "Automação": "Automatización", "Edição": "Edición", "Configurações": "Configuración",
        "Criação de Vídeos": "Creación de vídeos", "Criação de Músicas": "Creación de música", "Roteiros": "Guiones", "Upload": "Carga", "Contas Google": "Cuentas de Google", "Notificações": "Notificaciones", "Idioma da interface": "Idioma de la interfaz",
    },
    "id": {
        "Início": "Beranda", "Pipeline": "Alur", "Pipeline TikTok": "Alur TikTok", "Automação": "Otomatisasi", "Edição": "Penyuntingan", "Configurações": "Pengaturan",
        "Criação de Vídeos": "Pembuatan video", "Criação de Músicas": "Pembuatan musik", "Roteiros": "Skrip", "Upload": "Unggah", "Contas Google": "Akun Google", "Notificações": "Notifikasi", "Idioma da interface": "Bahasa antarmuka",
    },
    "it": {
        "Início": "Home", "Pipeline": "Pipeline", "Pipeline TikTok": "Pipeline TikTok", "Automação": "Automazione", "Edição": "Modifica", "Configurações": "Impostazioni",
        "Criação de Vídeos": "Creazione video", "Criação de Músicas": "Creazione musicale", "Roteiros": "Script", "Upload": "Caricamento", "Contas Google": "Account Google", "Notificações": "Notifiche", "Idioma da interface": "Lingua dell'interfaccia",
    },
    "pt": {},
}


def ui_text(value: str, language: Any = "pt") -> str:
    code = language_code(language)
    return UI_TRANSLATIONS.get(code, {}).get(value, value)


def language_flag(value: Any) -> str:
    return LANGUAGE_BY_CODE[language_code(value)]["flag"]


def language_locale(value: Any) -> str:
    return LANGUAGE_BY_CODE[language_code(value)]["locale"]


def video_language_label(value: Any) -> str:
    """Format a video-language value while preserving all historical options."""
    raw = str(value or "").strip()
    if raw.casefold() in {
        "music",
        "00 – apenas música de fundo (sem falas)",
        "00 - apenas música de fundo (sem falas)",
    }:
        return "🎵 Apenas Música de Fundo (Sem Falas)"
    normalized = language_code(raw, default="")
    if normalized in LANGUAGE_BY_CODE and (raw.casefold() in LEGACY_LANGUAGE_CODES or raw in LANGUAGE_BY_CODE):
        return language_label(normalized)
    return raw


def video_language_options() -> list[str]:
    return ["music", *LANGUAGE_CODES]


__all__ = [
    "LANGUAGE_CATALOG",
    "LANGUAGE_BY_CODE",
    "LANGUAGE_CODES",
    "language_code",
    "language_flag",
    "language_label",
    "language_locale",
    "language_option_codes",
    "language_option_labels",
    "video_language_label",
    "video_language_options",
]
