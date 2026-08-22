"""Canonical UI and video language catalog shared by Thunderbolt screens."""

from __future__ import annotations

import base64
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

# SVGs are embedded locally so flags render as images instead of relying on the
# host operating system's emoji font (which may show regional-letter siglas).
LANGUAGE_FLAG_SVGS: dict[str, str] = {
    "en": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><rect width="30" height="20" fill="#fff"/><path fill="#b22234" d="M0 0h30v2H0zm0 4h30v2H0zm0 4h30v2H0zm0 4h30v2H0zm0 4h30v2H0zm0 4h30v2H0z"/><rect width="13" height="10.8" fill="#3c3b6e"/><g fill="#fff"><circle cx="2" cy="2" r=".55"/><circle cx="5" cy="2" r=".55"/><circle cx="8" cy="2" r=".55"/><circle cx="11" cy="2" r=".55"/><circle cx="3.5" cy="4.2" r=".55"/><circle cx="6.5" cy="4.2" r=".55"/><circle cx="9.5" cy="4.2" r=".55"/><circle cx="2" cy="6.4" r=".55"/><circle cx="5" cy="6.4" r=".55"/><circle cx="8" cy="6.4" r=".55"/><circle cx="11" cy="6.4" r=".55"/><circle cx="3.5" cy="8.6" r=".55"/><circle cx="6.5" cy="8.6" r=".55"/><circle cx="9.5" cy="8.6" r=".55"/></g></svg>',
    "zh": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><rect width="30" height="20" fill="#de2910"/><path fill="#ffde00" d="m6 2 1 2.1 2.3.2-1.8 1.5.6 2.2L6 6.8 3.9 8l.6-2.2-1.8-1.5L5 4.1z"/></svg>',
    "de": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><path fill="#000" d="M0 0h30v6.67H0z"/><path fill="#d00" d="M0 6.67h30v6.66H0z"/><path fill="#ffce00" d="M0 13.33h30V20H0z"/></svg>',
    "vi": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><rect width="30" height="20" fill="#da251d"/><path fill="#ff0" d="m15 3 1.9 5.7h6l-4.9 3.5 1.9 5.8-4.9-3.6 1.9-5.8-4.9-3.5h6z"/></svg>',
    "tr": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><rect width="30" height="20" fill="#e30a17"/><circle cx="13" cy="10" r="5.2" fill="#fff"/><circle cx="15" cy="10" r="4.2" fill="#e30a17"/><path fill="#fff" d="m19 6.1 1.2 3.1 3.3.1-2.6 2 1 3.2-2.9-1.9-2.8 1.9 1-3.2-2.6-2 3.3-.1z"/></svg>',
    "pt": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><rect width="30" height="20" fill="#009c3b"/><path fill="#ffdf00" d="m15 1.2 13.2 8.8L15 18.8 1.8 10z"/><circle cx="15" cy="10" r="4.2" fill="#002776"/><path fill="#fff" d="M10.8 8.9c2.5-1.1 5.6-.5 8.4 1.5l-.4 1.1c-2.6-1.8-5.2-2.3-7.7-1.3z"/><g fill="#fff"><path d="m12.2 6.7.2.5.6.1-.4.4.1.5-.5-.3-.5.3.1-.5-.4-.4.6-.1z"/><path d="m17.7 7.2.2.5.6.1-.4.4.1.5-.5-.3-.5.3.1-.5-.4-.4.6-.1z"/><path d="m14.1 11.8.2.5.6.1-.4.4.1.5-.5-.3-.5.3.1-.5-.4-.4.6-.1z"/><path d="m17.9 12.7.2.5.6.1-.4.4.1.5-.5-.3-.5.3.1-.5-.4-.4.6-.1z"/></g></svg>',
    "ru": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><path fill="#fff" d="M0 0h30v6.67H0z"/><path fill="#22408c" d="M0 6.67h30v6.66H0z"/><path fill="#d52b1e" d="M0 13.33h30V20H0z"/></svg>',
    "es": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><path fill="#aa151b" d="M0 0h30v4H0zM0 16h30v4H0z"/><rect y="4" width="30" height="12" fill="#f1bf00"/><path fill="#ad1519" d="M7 7h2v6H7z"/></svg>',
    "id": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><path fill="#ce1126" d="M0 0h30v10H0z"/><path fill="#fff" d="M0 10h30v10H0z"/></svg>',
    "it": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 20"><path fill="#009246" d="M0 0h10v20H0z"/><path fill="#f1f2f1" d="M10 0h10v20H10z"/><path fill="#ce2b37" d="M20 0h10v20H20z"/></svg>',
}
LANGUAGE_FLAG_DATA_URIS = {
    code: "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
    for code, svg in LANGUAGE_FLAG_SVGS.items()
}

# Legacy labels used by existing channels, scripts and tests. They remain
# readable while new UI selections persist only the canonical short code.
LEGACY_LANGUAGE_CODES = {
    "01 – inglês": "en", "01 - inglês": "en", "06 – alemão": "de", "06 - alemão": "de",
    "15 – italiano": "it", "15 - italiano": "it", "29 – turco": "tr", "29 - turco": "tr",
    "31 – russo": "ru", "31 - russo": "ru", "36 – português (brasil)": "pt", "36 - português (brasil)": "pt",
    "39 – mandarim": "zh", "39 - mandarim": "zh", "13 – espanhol (espanha)": "es", "13 - espanhol (espanha)": "es",
    "41 - espanhol (latam)": "es", "42 – vietnamita": "vi", "42 - vietnamita": "vi",
    "44 – indonésio": "id", "44 - indonésio": "id", "37 – cantonês": "zh", "37 - cantonês": "zh",
    "english": "en", "inglês": "en", "inglés": "en", "zh": "zh", "chinês": "zh", "chinês simplificado": "zh",
    "deutsch": "de", "alemão": "de", "vietnamita": "vi", "turco": "tr", "português": "pt",
    "português (brasil)": "pt", "portuguese": "pt", "ru": "ru", "russo": "ru", "español": "es",
    "espanhol": "es", "indonésio": "id", "bahasa indonesia": "id", "italiano": "it",
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
    """Return a text label with the legacy emoji flag presentation."""
    code = language_code(value)
    item = LANGUAGE_BY_CODE[code]
    suffix = f" ({item['code']})" if include_code else ""
    return f"{item['name']}{suffix} {item['flag']}"


def ui_language_menu_label(value: Any, *, include_code: bool = True) -> str:
    """Return text-only UI label; the picker renders the flag as a real SVG icon."""
    code = language_code(value)
    item = LANGUAGE_BY_CODE[code]
    suffix = f" ({item['code']})" if include_code else ""
    return f"{item['name']}{suffix}"


def language_option_labels(*, include_code: bool = True) -> list[str]:
    return [language_label(item["code"], include_code=include_code) for item in LANGUAGE_CATALOG]


def language_option_codes() -> list[str]:
    return list(LANGUAGE_CODES)


_CORE_UI_TEXT_KEYS = (
    "Início", "Niche Finder", "Pipeline", "Pipeline TikTok", "Automação", "Edição", "AI Influencers", "Configurações",
    "Criação de Vídeos", "Criação de Músicas", "Roteiros", "Upload", "Prompts Master", "Contas TikTok", "Automação Youtube",
    "Niche Finder Kaggle", "Niche Finder Apify", "Limpador de Metadados", "Cortes", "Editor Python", "Download Mídia",
    "Personagens", "Redes Sociais", "Tutorial Meta", "Tutorial Supabase", "Canais Youtube", "Blueprints Youtube", "MCP", "Contas Google",
    "Configuração API", "Notificações", "Interface local para operação e automação de conteúdo faceless", "Canais", "activos",
    "Tarefas", "total registado", "A fazer", "na pipeline", "Em execução", "a decorrer", "Concluídos", "artefactos prontos",
    "Falhas", "requerem atenção", "Filas locais e dependências da cascata", "Niche", "Blueprints", "Brand", "Script", "Title",
    "Thumbnail", "Video", "Edit", "fila", "na biblioteca", "tarefa(s) na fila", "Language",
)


UI_TRANSLATIONS: dict[str, dict[str, str]] = {
    "pt": {key: key for key in _CORE_UI_TEXT_KEYS},
    "en": {
        "Início": "Home", "Niche Finder": "Niche Finder", "Pipeline": "Pipeline", "Pipeline TikTok": "TikTok Pipeline", "Automação": "Automation", "Edição": "Editing", "AI Influencers": "AI Influencers", "Configurações": "Settings", "Criação de Vídeos": "Video Creation", "Criação de Músicas": "Music Creation", "Roteiros": "Scripts", "Upload": "Upload", "Prompts Master": "Prompt Masters", "Contas TikTok": "TikTok Accounts", "Automação Youtube": "YouTube Automation", "Niche Finder Kaggle": "Niche Finder Kaggle", "Niche Finder Apify": "Niche Finder Apify", "Limpador de Metadados": "Metadata Cleaner", "Cortes": "Cuts", "Editor Python": "Python Editor", "Download Mídia": "Media Download", "Personagens": "Characters", "Redes Sociais": "Social Networks", "Tutorial Meta": "Meta Tutorial", "Canais Youtube": "YouTube Channels", "Blueprints Youtube": "YouTube Blueprints", "MCP": "MCP", "Contas Google": "Google Accounts", "Configuração API": "API Configuration", "Notificações": "Notifications", "Interface local para operação e automação de conteúdo faceless": "Local interface for faceless content operation and automation", "Canais": "Channels", "activos": "active", "Tarefas": "Tasks", "total registado": "total registered", "A fazer": "To do", "na pipeline": "in pipeline", "Em execução": "Running", "a decorrer": "in progress", "Concluídos": "Completed", "artefactos prontos": "ready artifacts", "Falhas": "Failures", "requerem atenção": "need attention", "Filas locais e dependências da cascata": "Local queues and cascade dependencies", "Niche": "Niche", "Blueprints": "Blueprints", "Brand": "Brand", "Script": "Script", "Title": "Title", "Thumbnail": "Thumbnail", "Video": "Video", "Edit": "Edit", "fila": "queue", "na biblioteca": "in library", "tarefa(s) na fila": "task(s) in queue", "Language": "Language",
    },
    "zh": {
        "Início": "首页", "Niche Finder": "利基搜索", "Pipeline": "视频流程", "Pipeline TikTok": "TikTok 流程", "Automação": "自动化", "Edição": "编辑", "AI Influencers": "AI 影响者", "Configurações": "设置", "Criação de Vídeos": "视频创作", "Criação de Músicas": "音乐创作", "Roteiros": "脚本", "Upload": "上传", "Prompts Master": "主提示词", "Contas TikTok": "TikTok 账户", "Automação Youtube": "YouTube 自动化", "Niche Finder Kaggle": "Kaggle 利基搜索", "Niche Finder Apify": "Apify 利基搜索", "Limpador de Metadados": "元数据清理器", "Cortes": "剪辑", "Editor Python": "Python 编辑器", "Download Mídia": "媒体下载", "Personagens": "角色", "Redes Sociais": "社交网络", "Tutorial Meta": "Meta 教程", "Canais Youtube": "YouTube 频道", "Blueprints Youtube": "YouTube 蓝图", "MCP": "MCP", "Contas Google": "Google 账户", "Configuração API": "API 配置", "Notificações": "通知", "Interface local para operação e automação de conteúdo faceless": "无脸内容运营与自动化本地界面", "Canais": "频道", "activos": "活跃", "Tarefas": "任务", "total registado": "已登记总数", "A fazer": "待处理", "na pipeline": "在流程中", "Em execução": "执行中", "a decorrer": "正在进行", "Concluídos": "已完成", "artefactos prontos": "成品已就绪", "Falhas": "失败", "requerem atenção": "需要关注", "Filas locais e dependências da cascata": "本地队列和级联依赖", "Niche": "利基", "Blueprints": "蓝图", "Brand": "品牌", "Script": "脚本", "Title": "标题", "Thumbnail": "缩略图", "Video": "视频", "Edit": "编辑", "fila": "队列", "na biblioteca": "在库中", "tarefa(s) na fila": "队列中的任务", "Language": "语言",
    },
    "de": {
        "Início": "Startseite", "Niche Finder": "Nischenfinder", "Pipeline": "Pipeline", "Pipeline TikTok": "TikTok-Pipeline", "Automação": "Automatisierung", "Edição": "Bearbeitung", "AI Influencers": "KI-Influencer", "Configurações": "Einstellungen", "Criação de Vídeos": "Videoerstellung", "Criação de Músicas": "Musikerstellung", "Roteiros": "Skripte", "Upload": "Upload", "Prompts Master": "Prompt Masters", "Contas TikTok": "TikTok-Konten", "Automação Youtube": "YouTube-Automatisierung", "Niche Finder Kaggle": "Kaggle-Nischenfinder", "Niche Finder Apify": "Apify-Nischenfinder", "Limpador de Metadados": "Metadatenbereinigung", "Cortes": "Schnitte", "Editor Python": "Python-Editor", "Download Mídia": "Mediendownload", "Personagens": "Figuren", "Redes Sociais": "Soziale Netzwerke", "Tutorial Meta": "Meta-Tutorial", "Canais Youtube": "YouTube-Kanäle", "Blueprints Youtube": "YouTube-Blueprints", "MCP": "MCP", "Contas Google": "Google-Konten", "Configuração API": "API-Konfiguration", "Notificações": "Benachrichtigungen", "Interface local para operação e automação de conteúdo faceless": "Lokale Oberfläche für den Betrieb und die Automatisierung von Faceless-Inhalten", "Canais": "Kanäle", "activos": "aktiv", "Tarefas": "Aufgaben", "total registado": "insgesamt registriert", "A fazer": "Offen", "na pipeline": "in der Pipeline", "Em execução": "In Ausführung", "a decorrer": "in Bearbeitung", "Concluídos": "Abgeschlossen", "artefactos prontos": "fertige Artefakte", "Falhas": "Fehler", "requerem atenção": "benötigen Aufmerksamkeit", "Filas locais e dependências da cascata": "Lokale Warteschlangen und Abhängigkeiten", "Niche": "Nische", "Blueprints": "Blueprints", "Brand": "Marke", "Script": "Skript", "Title": "Titel", "Thumbnail": "Thumbnail", "Video": "Video", "Edit": "Bearbeitung", "fila": "Warteschlange", "na biblioteca": "in der Bibliothek", "tarefa(s) na fila": "Aufgabe(n) in der Warteschlange", "Language": "Sprache",
    },
    "vi": {
        "Início": "Trang chủ", "Niche Finder": "Tìm ngách", "Pipeline": "Quy trình", "Pipeline TikTok": "Quy trình TikTok", "Automação": "Tự động hóa", "Edição": "Chỉnh sửa", "AI Influencers": "Người ảnh hưởng AI", "Configurações": "Cài đặt", "Criação de Vídeos": "Tạo video", "Criação de Músicas": "Tạo nhạc", "Roteiros": "Kịch bản", "Upload": "Tải lên", "Prompts Master": "Prompt Master", "Contas TikTok": "Tài khoản TikTok", "Automação Youtube": "Tự động hóa YouTube", "Niche Finder Kaggle": "Tìm ngách Kaggle", "Niche Finder Apify": "Tìm ngách Apify", "Limpador de Metadados": "Trình dọn siêu dữ liệu", "Cortes": "Cắt", "Editor Python": "Trình soạn thảo Python", "Download Mídia": "Tải phương tiện", "Personagens": "Nhân vật", "Redes Sociais": "Mạng xã hội", "Tutorial Meta": "Hướng dẫn Meta", "Canais Youtube": "Kênh YouTube", "Blueprints Youtube": "Blueprint YouTube", "MCP": "MCP", "Contas Google": "Tài khoản Google", "Configuração API": "Cấu hình API", "Notificações": "Thông báo", "Interface local para operação e automação de conteúdo faceless": "Giao diện cục bộ để vận hành và tự động hóa nội dung faceless", "Canais": "Kênh", "activos": "đang hoạt động", "Tarefas": "Tác vụ", "total registado": "tổng số đã đăng ký", "A fazer": "Cần làm", "na pipeline": "trong quy trình", "Em execução": "Đang chạy", "a decorrer": "đang diễn ra", "Concluídos": "Đã hoàn tất", "artefactos prontos": "sản phẩm đã sẵn sàng", "Falhas": "Lỗi", "requerem atenção": "cần chú ý", "Filas locais e dependências da cascata": "Hàng đợi cục bộ và các phụ thuộc", "Niche": "Ngách", "Blueprints": "Blueprint", "Brand": "Thương hiệu", "Script": "Kịch bản", "Title": "Tiêu đề", "Thumbnail": "Ảnh thu nhỏ", "Video": "Video", "Edit": "Chỉnh sửa", "fila": "hàng đợi", "na biblioteca": "trong thư viện", "tarefa(s) na fila": "tác vụ trong hàng đợi", "Language": "Ngôn ngữ",
    },
    "tr": {
        "Início": "Ana sayfa", "Niche Finder": "Niş Bulucu", "Pipeline": "Akış", "Pipeline TikTok": "TikTok Akışı", "Automação": "Otomasyon", "Edição": "Düzenleme", "AI Influencers": "Yapay Zekâ Etkileyicileri", "Configurações": "Ayarlar", "Criação de Vídeos": "Video Oluşturma", "Criação de Músicas": "Müzik Oluşturma", "Roteiros": "Senaryolar", "Upload": "Yükleme", "Prompts Master": "Prompt Master", "Contas TikTok": "TikTok Hesapları", "Automação Youtube": "YouTube Otomasyonu", "Niche Finder Kaggle": "Kaggle Niş Bulucu", "Niche Finder Apify": "Apify Niş Bulucu", "Limpador de Metadados": "Meta Veri Temizleyici", "Cortes": "Kesitler", "Editor Python": "Python Editörü", "Download Mídia": "Medya İndirme", "Personagens": "Karakterler", "Redes Sociais": "Sosyal Ağlar", "Tutorial Meta": "Meta Eğitimi", "Canais Youtube": "YouTube Kanalları", "Blueprints Youtube": "YouTube Blueprint'leri", "MCP": "MCP", "Contas Google": "Google Hesapları", "Configuração API": "API Yapılandırması", "Notificações": "Bildirimler", "Interface local para operação e automação de conteúdo faceless": "Faceless içerik operasyonu ve otomasyonu için yerel arayüz", "Canais": "Kanallar", "activos": "aktif", "Tarefas": "Görevler", "total registado": "kayıtlı toplam", "A fazer": "Yapılacak", "na pipeline": "akışta", "Em execução": "Çalışıyor", "a decorrer": "devam ediyor", "Concluídos": "Tamamlandı", "artefactos prontos": "hazır çıktılar", "Falhas": "Hatalar", "requerem atenção": "dikkat gerekiyor", "Filas locais e dependências da cascata": "Yerel kuyruklar ve bağımlılıklar", "Niche": "Niş", "Blueprints": "Blueprint", "Brand": "Marka", "Script": "Senaryo", "Title": "Başlık", "Thumbnail": "Küçük resim", "Video": "Video", "Edit": "Düzenle", "fila": "kuyruk", "na biblioteca": "kütüphanede", "tarefa(s) na fila": "kuyruktaki görev(ler)", "Language": "Dil",
    },
    "ru": {
        "Início": "Главная", "Niche Finder": "Поиск ниши", "Pipeline": "Конвейер", "Pipeline TikTok": "Конвейер TikTok", "Automação": "Автоматизация", "Edição": "Редактирование", "AI Influencers": "ИИ-инфлюенсеры", "Configurações": "Настройки", "Criação de Vídeos": "Создание видео", "Criação de Músicas": "Создание музыки", "Roteiros": "Сценарии", "Upload": "Загрузка", "Prompts Master": "Мастер-промпты", "Contas TikTok": "Аккаунты TikTok", "Automação Youtube": "Автоматизация YouTube", "Niche Finder Kaggle": "Поиск ниши Kaggle", "Niche Finder Apify": "Поиск ниши Apify", "Limpador de Metadados": "Очистка метаданных", "Cortes": "Нарезка", "Editor Python": "Редактор Python", "Download Mídia": "Загрузка медиа", "Personagens": "Персонажи", "Redes Sociais": "Социальные сети", "Tutorial Meta": "Руководство Meta", "Canais Youtube": "Каналы YouTube", "Blueprints Youtube": "Blueprint YouTube", "MCP": "MCP", "Contas Google": "Аккаунты Google", "Configuração API": "Настройка API", "Notificações": "Уведомления", "Interface local para operação e automação de conteúdo faceless": "Локальный интерфейс для работы и автоматизации faceless-контента", "Canais": "Каналы", "activos": "активны", "Tarefas": "Задачи", "total registado": "всего зарегистрировано", "A fazer": "К выполнению", "na pipeline": "в конвейере", "Em execução": "Выполняются", "a decorrer": "в процессе", "Concluídos": "Завершены", "artefactos prontos": "готовые материалы", "Falhas": "Ошибки", "requerem atenção": "требуют внимания", "Filas locais e dependências da cascata": "Локальные очереди и зависимости конвейера", "Niche": "Ниша", "Blueprints": "Blueprints", "Brand": "Бренд", "Script": "Сценарий", "Title": "Заголовок", "Thumbnail": "Миниатюра", "Video": "Видео", "Edit": "Монтаж", "fila": "очередь", "na biblioteca": "в библиотеке", "tarefa(s) na fila": "задач в очереди", "Language": "Язык",
    },
    "es": {
        "Início": "Inicio", "Niche Finder": "Buscador de nichos", "Pipeline": "Flujo", "Pipeline TikTok": "Flujo de TikTok", "Automação": "Automatización", "Edição": "Edición", "AI Influencers": "Influencers de IA", "Configurações": "Configuración", "Criação de Vídeos": "Creación de vídeos", "Criação de Músicas": "Creación de música", "Roteiros": "Guiones", "Upload": "Subir", "Prompts Master": "Prompts maestros", "Contas TikTok": "Cuentas de TikTok", "Automação Youtube": "Automatización de YouTube", "Niche Finder Kaggle": "Buscador de nichos Kaggle", "Niche Finder Apify": "Buscador de nichos Apify", "Limpador de Metadados": "Limpiador de metadatos", "Cortes": "Cortes", "Editor Python": "Editor de Python", "Download Mídia": "Descargar medios", "Personagens": "Personajes", "Redes Sociais": "Redes sociales", "Tutorial Meta": "Tutorial de Meta", "Canais Youtube": "Canales de YouTube", "Blueprints Youtube": "Blueprints de YouTube", "MCP": "MCP", "Contas Google": "Cuentas de Google", "Configuração API": "Configuración de API", "Notificações": "Notificaciones", "Interface local para operação e automação de conteúdo faceless": "Interfaz local para operar y automatizar contenido faceless", "Canais": "Canales", "activos": "activos", "Tarefas": "Tareas", "total registado": "total registrado", "A fazer": "Pendiente", "na pipeline": "en el flujo", "Em execução": "En ejecución", "a decorrer": "en curso", "Concluídos": "Completados", "artefactos prontos": "artefactos listos", "Falhas": "Fallos", "requerem atenção": "requieren atención", "Filas locais e dependências da cascata": "Colas locales y dependencias del flujo", "Niche": "Nicho", "Blueprints": "Blueprints", "Brand": "Marca", "Script": "Guion", "Title": "Título", "Thumbnail": "Miniatura", "Video": "Vídeo", "Edit": "Edición", "fila": "cola", "na biblioteca": "en la biblioteca", "tarefa(s) na fila": "tarea(s) en la cola", "Language": "Idioma",
    },
    "id": {
        "Início": "Beranda", "Niche Finder": "Pencari Niche", "Pipeline": "Alur", "Pipeline TikTok": "Alur TikTok", "Automação": "Otomatisasi", "Edição": "Penyuntingan", "AI Influencers": "Influencer AI", "Configurações": "Pengaturan", "Criação de Vídeos": "Pembuatan video", "Criação de Músicas": "Pembuatan musik", "Roteiros": "Skrip", "Upload": "Unggah", "Prompts Master": "Prompt Master", "Contas TikTok": "Akun TikTok", "Automação Youtube": "Otomatisasi YouTube", "Niche Finder Kaggle": "Pencari Niche Kaggle", "Niche Finder Apify": "Pencari Niche Apify", "Limpador de Metadados": "Pembersih metadata", "Cortes": "Potongan", "Editor Python": "Editor Python", "Download Mídia": "Unduh media", "Personagens": "Karakter", "Redes Sociais": "Jejaring sosial", "Tutorial Meta": "Tutorial Meta", "Canais Youtube": "Kanal YouTube", "Blueprints Youtube": "Blueprint YouTube", "MCP": "MCP", "Contas Google": "Akun Google", "Configuração API": "Konfigurasi API", "Notificações": "Notifikasi", "Interface local para operação e automação de conteúdo faceless": "Antarmuka lokal untuk operasi dan otomatisasi konten faceless", "Canais": "Kanal", "activos": "aktif", "Tarefas": "Tugas", "total registado": "total terdaftar", "A fazer": "Perlu dilakukan", "na pipeline": "dalam alur", "Em execução": "Berjalan", "a decorrer": "sedang berlangsung", "Concluídos": "Selesai", "artefactos prontos": "artefak siap", "Falhas": "Kegagalan", "requerem atenção": "perlu perhatian", "Filas locais e dependências da cascata": "Antrean lokal dan dependensi alur", "Niche": "Niche", "Blueprints": "Blueprint", "Brand": "Merek", "Script": "Skrip", "Title": "Judul", "Thumbnail": "Thumbnail", "Video": "Video", "Edit": "Edit", "fila": "antrean", "na biblioteca": "di pustaka", "tarefa(s) na fila": "tugas dalam antrean", "Language": "Bahasa",
    },
    "it": {
        "Início": "Home", "Niche Finder": "Trova nicchia", "Pipeline": "Pipeline", "Pipeline TikTok": "Pipeline TikTok", "Automação": "Automazione", "Edição": "Modifica", "AI Influencers": "Influencer AI", "Configurações": "Impostazioni", "Criação de Vídeos": "Creazione video", "Criação de Músicas": "Creazione musicale", "Roteiros": "Script", "Upload": "Caricamento", "Prompts Master": "Prompt Master", "Contas TikTok": "Account TikTok", "Automação Youtube": "Automazione YouTube", "Niche Finder Kaggle": "Trova nicchia Kaggle", "Niche Finder Apify": "Trova nicchia Apify", "Limpador de Metadados": "Pulizia metadati", "Cortes": "Tagli", "Editor Python": "Editor Python", "Download Mídia": "Download media", "Personagens": "Personaggi", "Redes Sociais": "Social network", "Tutorial Meta": "Tutorial Meta", "Canais Youtube": "Canali YouTube", "Blueprints Youtube": "Blueprint YouTube", "MCP": "MCP", "Contas Google": "Account Google", "Configuração API": "Configurazione API", "Notificações": "Notifiche", "Interface local para operação e automação de conteúdo faceless": "Interfaccia locale per la gestione e l'automazione di contenuti faceless", "Canais": "Canali", "activos": "attivi", "Tarefas": "Attività", "total registado": "totale registrato", "A fazer": "Da fare", "na pipeline": "nella pipeline", "Em execução": "In esecuzione", "a decorrer": "in corso", "Concluídos": "Completati", "artefactos prontos": "artefatti pronti", "Falhas": "Errori", "requerem atenção": "richiedono attenzione", "Filas locais e dependências da cascata": "Code locali e dipendenze della pipeline", "Niche": "Nicchia", "Blueprints": "Blueprint", "Brand": "Brand", "Script": "Script", "Title": "Titolo", "Thumbnail": "Miniatura", "Video": "Video", "Edit": "Modifica", "fila": "coda", "na biblioteca": "nella libreria", "tarefa(s) na fila": "attività in coda", "Language": "Lingua",
    },
}


_TAB_LABELS = (
    "Blueprints", "Brandings", "Pesquisa pública", "Cadastro manual", "Contas cadastradas", "Biblioteca",
    "Importar do YouTube", "Canais em lote gmail", "Criar vídeo", "Vídeos", "Novo roteiro/letra", "Histórico guardado",
    "Clusters encontrados", "Regras de associação", "Dados analisados", "Upload ficheiro", "URL de vídeo", "Vídeos gerados",
    "Pasta local", "Código Python", "Upload convencional", "Upload directo", "Postiz", "Upload-Post", "API Keys",
    "Teste de vozes", "Serviços e modelos", "Fontes de materiais", "Client MCP", "Servidor MCP", "Skill",
)

TAB_TRANSLATIONS: dict[str, dict[str, str]] = {
    "pt": {label: label for label in _TAB_LABELS},
    "en": {
        "Blueprints": "Blueprints", "Brandings": "Brandings", "Pesquisa pública": "Public search", "Cadastro manual": "Manual registration", "Contas cadastradas": "Registered accounts", "Biblioteca": "Library", "Importar do YouTube": "Import from YouTube", "Canais em lote gmail": "Bulk Gmail channels", "Criar vídeo": "Create video", "Vídeos": "Videos", "Novo roteiro/letra": "New script/lyrics", "Histórico guardado": "Saved history", "Clusters encontrados": "Found clusters", "Regras de associação": "Association rules", "Dados analisados": "Analyzed data", "Upload ficheiro": "Upload file", "URL de vídeo": "Video URL", "Vídeos gerados": "Generated videos", "Pasta local": "Local folder", "Código Python": "Python code", "Upload convencional": "Conventional upload", "Upload directo": "Direct upload", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "API Keys", "Teste de vozes": "Voice testing", "Serviços e modelos": "Services and models", "Fontes de materiais": "Media sources", "Client MCP": "MCP client", "Servidor MCP": "MCP server", "Skill": "Skill",
    },
    "zh": {
        "Blueprints": "蓝图", "Brandings": "品牌", "Pesquisa pública": "公开搜索", "Cadastro manual": "手动注册", "Contas cadastradas": "已注册账户", "Biblioteca": "库", "Importar do YouTube": "从 YouTube 导入", "Canais em lote gmail": "Gmail 批量频道", "Criar vídeo": "创建视频", "Vídeos": "视频", "Novo roteiro/letra": "新建脚本/歌词", "Histórico guardado": "已保存历史", "Clusters encontrados": "找到的聚类", "Regras de associação": "关联规则", "Dados analisados": "分析数据", "Upload ficheiro": "上传文件", "URL de vídeo": "视频 URL", "Vídeos gerados": "已生成视频", "Pasta local": "本地文件夹", "Código Python": "Python 代码", "Upload convencional": "常规上传", "Upload directo": "直接上传", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "API 密钥", "Teste de vozes": "语音测试", "Serviços e modelos": "服务与模型", "Fontes de materiais": "媒体来源", "Client MCP": "MCP 客户端", "Servidor MCP": "MCP 服务器", "Skill": "技能",
    },
    "de": {
        "Blueprints": "Blueprints", "Brandings": "Brandings", "Pesquisa pública": "Öffentliche Suche", "Cadastro manual": "Manuelle Registrierung", "Contas cadastradas": "Registrierte Konten", "Biblioteca": "Bibliothek", "Importar do YouTube": "Von YouTube importieren", "Canais em lote gmail": "Gmail-Kanäle im Stapel", "Criar vídeo": "Video erstellen", "Vídeos": "Videos", "Novo roteiro/letra": "Neues Skript/Liedtext", "Histórico guardado": "Gespeicherter Verlauf", "Clusters encontrados": "Gefundene Cluster", "Regras de associação": "Assoziationsregeln", "Dados analisados": "Analysierte Daten", "Upload ficheiro": "Datei hochladen", "URL de vídeo": "Video-URL", "Vídeos gerados": "Erstellte Videos", "Pasta local": "Lokaler Ordner", "Código Python": "Python-Code", "Upload convencional": "Herkömmlicher Upload", "Upload directo": "Direkter Upload", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "API-Schlüssel", "Teste de vozes": "Stimmtest", "Serviços e modelos": "Dienste und Modelle", "Fontes de materiais": "Medienquellen", "Client MCP": "MCP-Client", "Servidor MCP": "MCP-Server", "Skill": "Skill",
    },
    "vi": {
        "Blueprints": "Blueprint", "Brandings": "Thương hiệu", "Pesquisa pública": "Tìm kiếm công khai", "Cadastro manual": "Đăng ký thủ công", "Contas cadastradas": "Tài khoản đã đăng ký", "Biblioteca": "Thư viện", "Importar do YouTube": "Nhập từ YouTube", "Canais em lote gmail": "Kênh Gmail hàng loạt", "Criar vídeo": "Tạo video", "Vídeos": "Video", "Novo roteiro/letra": "Kịch bản/lời bài hát mới", "Histórico guardado": "Lịch sử đã lưu", "Clusters encontrados": "Cụm được tìm thấy", "Regras de associação": "Quy tắc liên kết", "Dados analisados": "Dữ liệu đã phân tích", "Upload ficheiro": "Tải tệp lên", "URL de vídeo": "URL video", "Vídeos gerados": "Video đã tạo", "Pasta local": "Thư mục cục bộ", "Código Python": "Mã Python", "Upload convencional": "Tải lên thông thường", "Upload directo": "Tải lên trực tiếp", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "Khóa API", "Teste de vozes": "Kiểm tra giọng nói", "Serviços e modelos": "Dịch vụ và mô hình", "Fontes de materiais": "Nguồn phương tiện", "Client MCP": "Máy khách MCP", "Servidor MCP": "Máy chủ MCP", "Skill": "Kỹ năng",
    },
    "tr": {
        "Blueprints": "Blueprint'ler", "Brandings": "Markalar", "Pesquisa pública": "Herkese açık arama", "Cadastro manual": "Manuel kayıt", "Contas cadastradas": "Kayıtlı hesaplar", "Biblioteca": "Kütüphane", "Importar do YouTube": "YouTube'dan içe aktar", "Canais em lote gmail": "Toplu Gmail kanalları", "Criar vídeo": "Video oluştur", "Vídeos": "Videolar", "Novo roteiro/letra": "Yeni senaryo/şarkı sözü", "Histórico guardado": "Kayıtlı geçmiş", "Clusters encontrados": "Bulunan kümeler", "Regras de associação": "Birliktelik kuralları", "Dados analisados": "Analiz edilen veriler", "Upload ficheiro": "Dosya yükle", "URL de vídeo": "Video URL'si", "Vídeos gerados": "Oluşturulan videolar", "Pasta local": "Yerel klasör", "Código Python": "Python kodu", "Upload convencional": "Geleneksel yükleme", "Upload directo": "Doğrudan yükleme", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "API anahtarları", "Teste de vozes": "Ses testi", "Serviços e modelos": "Hizmetler ve modeller", "Fontes de materiais": "Medya kaynakları", "Client MCP": "MCP istemcisi", "Servidor MCP": "MCP sunucusu", "Skill": "Beceri",
    },
    "ru": {
        "Blueprints": "Blueprints", "Brandings": "Брендинг", "Pesquisa pública": "Публичный поиск", "Cadastro manual": "Ручная регистрация", "Contas cadastradas": "Зарегистрированные аккаунты", "Biblioteca": "Библиотека", "Importar do YouTube": "Импорт из YouTube", "Canais em lote gmail": "Массовые каналы Gmail", "Criar vídeo": "Создать видео", "Vídeos": "Видео", "Novo roteiro/letra": "Новый сценарий/текст", "Histórico guardado": "Сохранённая история", "Clusters encontrados": "Найденные кластеры", "Regras de associação": "Правила ассоциаций", "Dados analisados": "Анализ данных", "Upload ficheiro": "Загрузить файл", "URL de vídeo": "URL видео", "Vídeos gerados": "Созданные видео", "Pasta local": "Локальная папка", "Código Python": "Код Python", "Upload convencional": "Обычная загрузка", "Upload directo": "Прямая загрузка", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "Ключи API", "Teste de vozes": "Тест голосов", "Serviços e modelos": "Сервисы и модели", "Fontes de materiais": "Источники материалов", "Client MCP": "Клиент MCP", "Servidor MCP": "Сервер MCP", "Skill": "Навык",
    },
    "es": {
        "Blueprints": "Blueprints", "Brandings": "Marcas", "Pesquisa pública": "Búsqueda pública", "Cadastro manual": "Registro manual", "Contas cadastradas": "Cuentas registradas", "Biblioteca": "Biblioteca", "Importar do YouTube": "Importar de YouTube", "Canais em lote gmail": "Canales Gmail por lotes", "Criar vídeo": "Crear vídeo", "Vídeos": "Vídeos", "Novo roteiro/letra": "Nuevo guion/letra", "Histórico guardado": "Historial guardado", "Clusters encontrados": "Clústeres encontrados", "Regras de associação": "Reglas de asociación", "Dados analisados": "Datos analizados", "Upload ficheiro": "Subir archivo", "URL de vídeo": "URL del vídeo", "Vídeos gerados": "Vídeos generados", "Pasta local": "Carpeta local", "Código Python": "Código Python", "Upload convencional": "Carga convencional", "Upload directo": "Carga directa", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "Claves API", "Teste de vozes": "Prueba de voces", "Serviços e modelos": "Servicios y modelos", "Fontes de materiais": "Fuentes de medios", "Client MCP": "Cliente MCP", "Servidor MCP": "Servidor MCP", "Skill": "Habilidad",
    },
    "id": {
        "Blueprints": "Blueprint", "Brandings": "Branding", "Pesquisa pública": "Pencarian publik", "Cadastro manual": "Pendaftaran manual", "Contas cadastradas": "Akun terdaftar", "Biblioteca": "Pustaka", "Importar do YouTube": "Impor dari YouTube", "Canais em lote gmail": "Kanal Gmail massal", "Criar vídeo": "Buat video", "Vídeos": "Video", "Novo roteiro/letra": "Skrip/lirik baru", "Histórico guardado": "Riwayat tersimpan", "Clusters encontrados": "Cluster ditemukan", "Regras de associação": "Aturan asosiasi", "Dados analisados": "Data yang dianalisis", "Upload ficheiro": "Unggah file", "URL de vídeo": "URL video", "Vídeos gerados": "Video yang dibuat", "Pasta local": "Folder lokal", "Código Python": "Kode Python", "Upload convencional": "Unggah konvensional", "Upload directo": "Unggah langsung", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "Kunci API", "Teste de vozes": "Uji suara", "Serviços e modelos": "Layanan dan model", "Fontes de materiais": "Sumber media", "Client MCP": "Klien MCP", "Servidor MCP": "Server MCP", "Skill": "Keahlian",
    },
    "it": {
        "Blueprints": "Blueprint", "Brandings": "Branding", "Pesquisa pública": "Ricerca pubblica", "Cadastro manual": "Registrazione manuale", "Contas cadastradas": "Account registrati", "Biblioteca": "Libreria", "Importar do YouTube": "Importa da YouTube", "Canais em lote gmail": "Canali Gmail in batch", "Criar vídeo": "Crea video", "Vídeos": "Video", "Novo roteiro/letra": "Nuovo copione/testo", "Histórico guardado": "Cronologia salvata", "Clusters encontrados": "Cluster trovati", "Regras de associação": "Regole di associazione", "Dados analisados": "Dati analizzati", "Upload ficheiro": "Carica file", "URL de vídeo": "URL video", "Vídeos gerados": "Video generati", "Pasta local": "Cartella locale", "Código Python": "Codice Python", "Upload convencional": "Caricamento convenzionale", "Upload directo": "Caricamento diretto", "Postiz": "Postiz", "Upload-Post": "Upload-Post", "API Keys": "Chiavi API", "Teste de vozes": "Test delle voci", "Serviços e modelos": "Servizi e modelli", "Fontes de materiais": "Fonti multimediali", "Client MCP": "Client MCP", "Servidor MCP": "Server MCP", "Skill": "Skill",
    },
}

for _language_code, _tab_translation in TAB_TRANSLATIONS.items():
    UI_TRANSLATIONS[_language_code].update(_tab_translation)


TUTORIAL_TRANSLATIONS: dict[str, dict[str, str]] = {
    "pt": {"Tutorial Supabase": "Tutorial Supabase", "Guia de configuração do Supabase para automações com n8n.": "Guia de configuração do Supabase para automações com n8n."},
    "en": {"Tutorial Supabase": "Supabase Tutorial", "Guia de configuração do Supabase para automações com n8n.": "Supabase setup guide for n8n automations."},
    "zh": {"Tutorial Supabase": "Supabase 教程", "Guia de configuração do Supabase para automações com n8n.": "用于 n8n 自动化的 Supabase 配置指南。"},
    "de": {"Tutorial Supabase": "Supabase-Tutorial", "Guia de configuração do Supabase para automações com n8n.": "Anleitung zur Supabase-Konfiguration für n8n-Automatisierungen."},
    "vi": {"Tutorial Supabase": "Hướng dẫn Supabase", "Guia de configuração do Supabase para automações com n8n.": "Hướng dẫn cấu hình Supabase cho tự động hóa n8n."},
    "tr": {"Tutorial Supabase": "Supabase Eğitimi", "Guia de configuração do Supabase para automações com n8n.": "n8n otomasyonları için Supabase yapılandırma rehberi."},
    "ru": {"Tutorial Supabase": "Руководство Supabase", "Guia de configuração do Supabase para automações com n8n.": "Руководство по настройке Supabase для автоматизации n8n."},
    "es": {"Tutorial Supabase": "Tutorial de Supabase", "Guia de configuração do Supabase para automações com n8n.": "Guía de configuración de Supabase para automatizaciones con n8n."},
    "id": {"Tutorial Supabase": "Tutorial Supabase", "Guia de configuração do Supabase para automações com n8n.": "Panduan konfigurasi Supabase untuk otomatisasi n8n."},
    "it": {"Tutorial Supabase": "Tutorial Supabase", "Guia de configuração do Supabase para automações com n8n.": "Guida alla configurazione di Supabase per le automazioni n8n."},
}

for _language_code, _tutorial_translation in TUTORIAL_TRANSLATIONS.items():
    UI_TRANSLATIONS[_language_code].update(_tutorial_translation)


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
    if raw.casefold() in {"music", "00 – apenas música de fundo (sem falas)", "00 - apenas música de fundo (sem falas)"}:
        return "🎵 Apenas Música de Fundo (Sem Falas)"
    normalized = language_code(raw, default="")
    if normalized in LANGUAGE_BY_CODE and (raw.casefold() in LEGACY_LANGUAGE_CODES or raw in LANGUAGE_BY_CODE):
        return language_label(normalized)
    return raw


def video_language_options() -> list[str]:
    return ["music", *LANGUAGE_CODES]


__all__ = [
    "LANGUAGE_CATALOG", "LANGUAGE_BY_CODE", "LANGUAGE_CODES", "LANGUAGE_FLAG_DATA_URIS", "language_code", "language_flag",
    "language_label", "ui_language_menu_label", "language_locale", "language_option_codes", "language_option_labels",
    "ui_text", "video_language_label", "video_language_options",
]
