from __future__ import annotations

from typing import Any

SUPPORTED_TUTORIAL_LANGUAGES = ("pt", "en", "zh", "de", "vi", "tr", "ru", "es", "id", "it")


_TUTORIALS: dict[str, dict[str, dict[str, str]]] = {
    "kaggle": {
        "pt": {
            "title": "Tutorial Kaggle",
            "caption": "Configure as credenciais Kaggle para o Niche Finder, com base no projecto Niche-Finder.",
            "body": """## O que este tutorial configura

O Niche Finder do Thunderbolt foi inspirado no projecto [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder). A referência usa o dataset público [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) para estudar vídeos, nichos, tendências e tags. No Thunderbolt, a análise Kaggle prepara e coloca em cache esse dataset antes de executar a análise.

> **Importante:** no fluxo actual do Thunderbolt, a análise é iniciada manualmente em **Niche Finder > Niche Finder Kaggle**. Não é necessário criar uma kernel Kaggle para esta operação.

## 1. Criar ou confirmar a conta Kaggle

Aceda a [kaggle.com](https://www.kaggle.com/) e entre na sua conta. Confirme o e-mail e, se o Kaggle solicitar, conclua as verificações da conta. O **username** é o identificador exibido no seu perfil; não inclua `@`, espaços ou a URL completa do perfil.

## 2. Obter a API Key

1. Abra [Kaggle Account API Tokens](https://www.kaggle.com/settings/api).
2. Na secção **API**, clique em **Generate New Token**. O Kaggle CLI actual também aceita este token através de `KAGGLE_API_TOKEN`.
3. Se precisar do formato legado usado por ferramentas antigas, abra **Legacy API Credentials** e clique em **Create Legacy API Key**. O download será um ficheiro `kaggle.json` com `username` e `key`.
4. Guarde o ficheiro ou o valor da chave fora do GitHub, de notebooks públicos e de mensagens. Se uma chave for exposta, revogue-a e gere outra imediatamente.

A documentação oficial confirma as duas vias: OAuth/CLI e criação de uma API key nas definições de tokens da conta [1] [2].

## 3. Preencher o cartão do Thunderbolt

Abra **Configuração API > API Keys > Niche Finder — Kaggle** e preencha **Kaggle Username** com o username sem `@` e **Kaggle API Key** com a chave. O campo **Slug da kernel** pode permanecer com o valor predefinido; ele é mantido para compatibilidade com configurações legadas e não é necessário para o download actual do dataset. Clique em **Testar chamada API**, confirme o resultado verde e depois clique em **Salvar**.

O teste faz apenas uma consulta autenticada de leitura ao perfil Kaggle. Ele não cria kernels, não executa notebooks e não publica nada.

## 4. Executar a análise de nichos

Entre em **Niche Finder > Niche Finder Kaggle**, escolha o intervalo de datas, país e filtros disponíveis e clique em **Analisar Nichos**. Na primeira execução, o Thunderbolt prepara o dataset e guarda uma cópia local validada. As execuções seguintes podem reutilizar o cache; se os dados estiverem incompletos ou forem removidos, repita a operação depois de confirmar as credenciais.

## Diagnóstico rápido

| Sintoma | Acção recomendada |
| --- | --- |
| `401` ou teste vermelho | Confirme o username exacto e gere uma nova chave em Kaggle > Settings > API. |
| Limite ou `429` | Aguarde alguns minutos e evite iniciar várias descargas consecutivas; o Kaggle aplica rate limits dinâmicos. |
| Dataset sem dados | Confirme a ligação do dataset de tendências e execute novamente a preparação automática. |
| Chave exposta | Revogue-a no Kaggle, crie outra e actualize somente o cartão local. |

## Referências

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "en": {
            "title": "Kaggle Tutorial",
            "caption": "Configure Kaggle credentials for Niche Finder, based on the Niche-Finder project.",
            "body": """## What this tutorial configures

Thunderbolt's Kaggle Niche Finder was inspired by [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder). That reference uses the public [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) to study videos, niches, trends, and tags. Thunderbolt prepares and caches that dataset before running the analysis.

> **Important:** the current Thunderbolt flow is started manually from **Niche Finder > Niche Finder Kaggle**. You do not need to create a Kaggle kernel for this operation.

## 1. Create or confirm your Kaggle account

Open [kaggle.com](https://www.kaggle.com/) and sign in. Confirm your email and complete any account verification requested by Kaggle. Your **username** is the identifier shown on your profile; do not include `@`, spaces, or the full profile URL.

## 2. Get the API key

1. Open [Kaggle Account API Tokens](https://www.kaggle.com/settings/api).
2. Under **API**, click **Generate New Token**. The current Kaggle CLI can also use this token through `KAGGLE_API_TOKEN`.
3. If an older tool requires the legacy format, open **Legacy API Credentials** and click **Create Legacy API Key**. Kaggle downloads a `kaggle.json` file containing `username` and `key`.
4. Keep the file or key out of GitHub, public notebooks, and messages. If it is exposed, revoke it and generate a replacement immediately.

The official documentation confirms both paths: OAuth/CLI and API-key creation in the account token settings [1] [2].

## 3. Fill in Thunderbolt

Open **API Configuration > API Keys > Niche Finder — Kaggle**. Enter your username without `@` in **Kaggle Username** and the secret value in **Kaggle API Key**. You may leave **Kernel slug** at its default; it is retained for legacy compatibility and is not required by the current dataset download. Click **Test API call**, confirm the green result, and then click **Save**.

The test performs only an authenticated, read-only profile lookup. It does not create kernels, run notebooks, or publish anything.

## 4. Run the niche analysis

Go to **Niche Finder > Niche Finder Kaggle**, choose the available date, country, and filter options, and click **Analyze Niches**. On the first run, Thunderbolt prepares the dataset and stores a validated local cache. Later runs may reuse it; if the cache is incomplete or removed, retry after checking the credentials.

## Quick troubleshooting

| Symptom | Recommended action |
| --- | --- |
| `401` or red test | Check the exact username and generate a new key at Kaggle > Settings > API. |
| Rate limit or `429` | Wait a few minutes and avoid repeated downloads; Kaggle uses dynamic rate limits. |
| Dataset has no rows | Check the trending dataset link and run the automatic preparation again. |
| Key exposed | Revoke it in Kaggle, create another one, and update only the local card. |

## References

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "zh": {
            "title": "Kaggle 教程",
            "caption": "根据 Niche-Finder 项目配置 Kaggle 凭据，用于 Niche Finder。",
            "body": """## 本教程配置什么

Thunderbolt 的 Kaggle 利基分析参考了 [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)。该项目使用公开的 [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) 分析视频、利基、趋势和标签。Thunderbolt 会在分析前准备并缓存该数据集。

> **重要：** 当前 Thunderbolt 流程在 **Niche Finder > Niche Finder Kaggle** 中手动启动。不需要创建 Kaggle kernel。

## 1. 创建或确认 Kaggle 账户

打开 [kaggle.com](https://www.kaggle.com/) 并登录，确认邮箱并完成 Kaggle 要求的账户验证。**username** 是个人资料中显示的标识；不要填写 `@`、空格或完整个人资料 URL。

## 2. 获取 API Key

1. 打开 [Kaggle API Tokens](https://www.kaggle.com/settings/api)。
2. 在 **API** 区域点击 **Generate New Token**。新版 Kaggle CLI 也可以通过 `KAGGLE_API_TOKEN` 使用该令牌。
3. 如果旧工具需要传统格式，请在 **Legacy API Credentials** 中点击 **Create Legacy API Key**，下载包含 `username` 和 `key` 的 `kaggle.json`。
4. 不要把文件或密钥放入 GitHub、公开 Notebook 或消息中。泄露后立即撤销并重新生成。

官方文档确认了 OAuth/CLI 和账户 Token 页面两种认证方式 [1] [2]。

## 3. 填写 Thunderbolt 卡片

进入 **API Configuration > API Keys > Niche Finder — Kaggle**。在 **Kaggle Username** 中填写不带 `@` 的用户名，在 **Kaggle API Key** 中填写密钥。**Kernel slug** 可以保持默认值；它用于兼容旧配置，当前数据集下载不需要它。点击 **Test API call**，确认绿色结果后点击 **Save**。

测试只会进行经过身份验证的只读个人资料查询，不会创建 kernel、运行 Notebook 或发布内容。

## 4. 运行利基分析

进入 **Niche Finder > Niche Finder Kaggle**，选择日期、国家和可用筛选条件，然后点击 **Analyze Niches**。第一次运行会准备数据集并保存经过验证的本地缓存；之后可以复用缓存。如果缓存不完整，请确认凭据后再次准备。

## 快速排查

| 现象 | 建议 |
| --- | --- |
| `401` 或红色测试 | 检查用户名，并在 Kaggle > Settings > API 重新生成密钥。 |
| `429` 或限流 | 等待几分钟，不要连续重复下载；Kaggle 使用动态限流。 |
| 数据集为空 | 检查趋势数据集链接并重新准备数据。 |
| 密钥泄露 | 在 Kaggle 撤销旧密钥，创建新密钥，只更新本地卡片。 |

## 参考

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "de": {
            "title": "Kaggle-Tutorial",
            "caption": "Kaggle-Zugangsdaten für den Niche Finder nach dem Projekt Niche-Finder konfigurieren.",
            "body": """## Was dieses Tutorial einrichtet

Der Kaggle-Nischenfinder von Thunderbolt ist von [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder) inspiriert. Die Referenz verwendet den öffentlichen [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code), um Videos, Nischen, Trends und Tags zu untersuchen. Thunderbolt bereitet den Datensatz vor und speichert einen lokalen Cache.

> **Wichtig:** Der aktuelle Thunderbolt-Ablauf wird manuell unter **Niche Finder > Niche Finder Kaggle** gestartet. Ein Kaggle-Kernel muss dafür nicht erstellt werden.

## 1. Kaggle-Konto erstellen oder bestätigen

Öffnen Sie [kaggle.com](https://www.kaggle.com/), melden Sie sich an, bestätigen Sie Ihre E-Mail und erledigen Sie eventuell verlangte Kontoprüfungen. Der **Benutzername** ist der Name in Ihrem Profil; verwenden Sie kein `@`, keine Leerzeichen und nicht die vollständige Profil-URL.

## 2. API-Key erhalten

1. Öffnen Sie [Kaggle API Tokens](https://www.kaggle.com/settings/api).
2. Klicken Sie im Bereich **API** auf **Generate New Token**. Die aktuelle Kaggle CLI kann diesen Token auch über `KAGGLE_API_TOKEN` verwenden.
3. Für ältere Werkzeuge öffnen Sie **Legacy API Credentials** und klicken Sie auf **Create Legacy API Key**. Kaggle lädt `kaggle.json` mit `username` und `key` herunter.
4. Bewahren Sie Datei und Key außerhalb von GitHub, öffentlichen Notebooks und Nachrichten auf. Bei einer Offenlegung sofort widerrufen und neu erzeugen.

Die offizielle Dokumentation bestätigt OAuth/CLI und die Erstellung eines API-Keys in den Kontoeinstellungen [1] [2].

## 3. Thunderbolt-Karte ausfüllen

Öffnen Sie **API-Konfiguration > API Keys > Niche Finder — Kaggle**. Tragen Sie den Benutzernamen ohne `@` und den Key ein. **Kernel slug** kann auf dem Standardwert bleiben; er dient der Kompatibilität und ist für den aktuellen Datensatz-Download nicht erforderlich. Klicken Sie auf **API-Aufruf testen**, prüfen Sie das grüne Ergebnis und klicken Sie danach auf **Speichern**.

Der Test führt nur eine authentifizierte, schreibgeschützte Profilabfrage aus. Er erstellt keine Kernel, startet keine Notebooks und veröffentlicht nichts.

## 4. Nischenanalyse ausführen

Gehen Sie zu **Niche Finder > Niche Finder Kaggle**, wählen Sie Datum, Land und Filter und klicken Sie auf **Analyze Niches**. Beim ersten Lauf wird der Datensatz vorbereitet und validiert lokal gespeichert. Bei einem unvollständigen Cache wiederholen Sie die Vorbereitung nach der Prüfung der Zugangsdaten.

## Schnelle Fehlerbehebung

| Symptom | Empfehlung |
| --- | --- |
| `401` oder roter Test | Benutzernamen prüfen und unter Kaggle > Settings > API einen neuen Key erzeugen. |
| `429` oder Limit | Einige Minuten warten und Downloads nicht wiederholt starten; Kaggle verwendet dynamische Limits. |
| Datensatz leer | Trend-Datensatz prüfen und die automatische Vorbereitung wiederholen. |
| Key offengelegt | In Kaggle widerrufen, neuen Key erstellen und nur die lokale Karte aktualisieren. |

## Quellen

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "vi": {
            "title": "Hướng dẫn Kaggle",
            "caption": "Cấu hình thông tin Kaggle cho Niche Finder dựa trên dự án Niche-Finder.",
            "body": """## Hướng dẫn này cấu hình gì

Niche Finder Kaggle của Thunderbolt được tham khảo từ [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder). Dự án dùng [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) để phân tích video, ngách, xu hướng và thẻ. Thunderbolt chuẩn bị và lưu bộ dữ liệu vào bộ nhớ đệm trước khi phân tích.

> **Quan trọng:** quy trình hiện tại được chạy thủ công tại **Niche Finder > Niche Finder Kaggle**. Không cần tạo Kaggle kernel.

## 1. Tạo hoặc xác nhận tài khoản Kaggle

Mở [kaggle.com](https://www.kaggle.com/), đăng nhập, xác nhận email và hoàn tất các bước xác minh nếu Kaggle yêu cầu. **Username** là tên trong hồ sơ; không nhập `@`, khoảng trắng hoặc URL đầy đủ.

## 2. Lấy API Key

1. Mở [Kaggle API Tokens](https://www.kaggle.com/settings/api).
2. Trong phần **API**, chọn **Generate New Token**. Kaggle CLI hiện tại cũng dùng token qua `KAGGLE_API_TOKEN`.
3. Với công cụ cũ, mở **Legacy API Credentials** và chọn **Create Legacy API Key** để tải `kaggle.json` gồm `username` và `key`.
4. Không lưu file hoặc key trong GitHub, notebook công khai hay tin nhắn. Nếu bị lộ, hãy thu hồi và tạo key mới.

Tài liệu chính thức xác nhận cả OAuth/CLI và việc tạo API key trong phần cài đặt tài khoản [1] [2].

## 3. Điền thẻ Thunderbolt

Mở **Cấu hình API > API Keys > Niche Finder — Kaggle**. Điền username không có `@` và API key. Có thể giữ **Kernel slug** mặc định; trường này chỉ duy trì tương thích và không cần cho việc tải dữ liệu hiện tại. Chọn **Kiểm tra lệnh gọi API**, xác nhận kết quả màu xanh rồi chọn **Lưu**.

Bài kiểm tra chỉ đọc hồ sơ qua một yêu cầu đã xác thực. Nó không tạo kernel, không chạy notebook và không xuất bản nội dung.

## 4. Chạy phân tích ngách

Vào **Niche Finder > Niche Finder Kaggle**, chọn ngày, quốc gia và bộ lọc rồi chọn **Analyze Niches**. Lần đầu Thunderbolt chuẩn bị bộ dữ liệu và lưu bản cache đã kiểm tra. Nếu cache không đầy đủ, hãy kiểm tra thông tin rồi chạy lại.

## Xử lý nhanh

| Hiện tượng | Cách xử lý |
| --- | --- |
| `401` hoặc kiểm tra đỏ | Kiểm tra username và tạo key mới tại Kaggle > Settings > API. |
| `429` hoặc giới hạn | Chờ vài phút và không tải lặp lại liên tục; Kaggle dùng giới hạn động. |
| Bộ dữ liệu trống | Kiểm tra liên kết bộ dữ liệu xu hướng và chuẩn bị lại. |
| Key bị lộ | Thu hồi trong Kaggle, tạo key mới và chỉ cập nhật thẻ cục bộ. |

## Tài liệu tham khảo

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "tr": {
            "title": "Kaggle Eğitimi",
            "caption": "Niche-Finder projesini temel alarak Niche Finder için Kaggle kimlik bilgilerini yapılandırın.",
            "body": """## Bu eğitim neyi yapılandırır

Thunderbolt Kaggle Niche Finder, [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder) projesinden uyarlanmıştır. Referans proje videoları, nişleri, trendleri ve etiketleri incelemek için herkese açık [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) verisini kullanır. Thunderbolt analizden önce bu veri setini hazırlar ve önbelleğe alır.

> **Önemli:** Güncel akış **Niche Finder > Niche Finder Kaggle** altında manuel başlatılır. Bu işlem için Kaggle kernel oluşturmanız gerekmez.

## 1. Kaggle hesabı

[kaggle.com](https://www.kaggle.com/) adresini açın, giriş yapın, e-postanızı doğrulayın ve istenen hesap kontrollerini tamamlayın. **Kullanıcı adı**, profilinizde görünen addır; `@`, boşluk veya tam profil URL'si eklemeyin.

## 2. API Key alma

1. [Kaggle API Tokens](https://www.kaggle.com/settings/api) sayfasını açın.
2. **API** bölümünde **Generate New Token** seçeneğine tıklayın. Güncel Kaggle CLI bu token'ı `KAGGLE_API_TOKEN` ile de kullanabilir.
3. Eski araçlar için **Legacy API Credentials** bölümünde **Create Legacy API Key** seçeneğini kullanarak `username` ve `key` içeren `kaggle.json` dosyasını indirin.
4. Dosyayı veya anahtarı GitHub'da, herkese açık notebooklarda ya da mesajlarda paylaşmayın. Açığa çıkarsa hemen iptal edip yenisini oluşturun.

Resmi belgeler OAuth/CLI ve hesap ayarlarındaki API key oluşturma yollarını açıklar [1] [2].

## 3. Thunderbolt kartı

**API Yapılandırması > API Keys > Niche Finder — Kaggle** yolunu açın. Kullanıcı adını ve API key'i girin. **Kernel slug** varsayılan kalabilir; eski ayar uyumluluğu içindir ve güncel veri indirme için gerekli değildir. **API çağrısını test et** düğmesine tıklayın, yeşil sonucu kontrol edin ve ardından **Kaydet** seçeneğini kullanın.

Test yalnızca kimlik doğrulamalı, salt okunur bir profil isteği yapar. Kernel oluşturmaz, notebook çalıştırmaz ve yayınlama yapmaz.

## 4. Niş analizini çalıştırma

**Niche Finder > Niche Finder Kaggle** sayfasına gidin, tarih, ülke ve filtreleri seçin ve **Analyze Niches** düğmesine tıklayın. İlk çalıştırmada veri seti hazırlanıp doğrulanmış yerel önbelleğe alınır.

## Hızlı sorun giderme

| Belirti | Önerilen işlem |
| --- | --- |
| `401` veya kırmızı test | Kullanıcı adını kontrol edin ve Kaggle > Settings > API'den yeni key oluşturun. |
| `429` veya limit | Birkaç dakika bekleyin; Kaggle dinamik limitler uygular. |
| Veri seti boş | Trend veri seti bağlantısını kontrol edip hazırlığı tekrarlayın. |
| Key açığa çıktı | Kaggle'da iptal edin, yeni key oluşturun ve yalnızca yerel kartı güncelleyin. |

## Kaynaklar

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "ru": {
            "title": "Руководство Kaggle",
            "caption": "Настройка данных Kaggle для Niche Finder на основе проекта Niche-Finder.",
            "body": """## Что настраивает руководство

Kaggle Niche Finder в Thunderbolt создан с учётом [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder). Проект использует открытый [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) для анализа видео, ниш, трендов и тегов. Thunderbolt подготавливает и кэширует этот набор перед анализом.

> **Важно:** текущий процесс запускается вручную в **Niche Finder > Niche Finder Kaggle**. Создавать Kaggle kernel не нужно.

## 1. Аккаунт Kaggle

Откройте [kaggle.com](https://www.kaggle.com/), войдите, подтвердите почту и завершите необходимые проверки аккаунта. **Username** — имя из профиля; не добавляйте `@`, пробелы или полный URL профиля.

## 2. Получение API Key

1. Откройте [Kaggle API Tokens](https://www.kaggle.com/settings/api).
2. В разделе **API** нажмите **Generate New Token**. Новый Kaggle CLI также принимает этот токен через `KAGGLE_API_TOKEN`.
3. Для старых инструментов откройте **Legacy API Credentials** и нажмите **Create Legacy API Key**, чтобы скачать `kaggle.json` с `username` и `key`.
4. Не помещайте файл или ключ в GitHub, открытые Notebook или сообщения. При утечке отзовите ключ и создайте новый.

Официальная документация описывает OAuth/CLI и создание API key в настройках аккаунта [1] [2].

## 3. Заполнение карточки Thunderbolt

Откройте **Настройка API > API Keys > Niche Finder — Kaggle** и заполните username и API key. **Kernel slug** можно оставить по умолчанию: он нужен для совместимости со старыми настройками и не требуется текущей загрузке данных. Нажмите **Проверить вызов API**, убедитесь в зелёном результате и нажмите **Сохранить**.

Проверка выполняет только аутентифицированный запрос профиля на чтение. Kernel и Notebook не создаются, публикация не выполняется.

## 4. Запуск анализа ниш

Перейдите в **Niche Finder > Niche Finder Kaggle**, выберите даты, страну и фильтры и нажмите **Analyze Niches**. При первом запуске набор данных подготавливается и сохраняется в проверенный локальный кэш.

## Быстрое решение проблем

| Симптом | Действие |
| --- | --- |
| `401` или красная проверка | Проверьте username и создайте новый ключ в Kaggle > Settings > API. |
| `429` или лимит | Подождите несколько минут; Kaggle использует динамические ограничения. |
| Нет данных | Проверьте ссылку на набор трендов и повторите подготовку. |
| Ключ раскрыт | Отзовите его в Kaggle, создайте новый и обновите только локальную карточку. |

## Источники

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "es": {
            "title": "Tutorial de Kaggle",
            "caption": "Configura las credenciales de Kaggle para Niche Finder basándote en el proyecto Niche-Finder.",
            "body": """## Qué configura este tutorial

El Niche Finder de Kaggle en Thunderbolt se inspira en [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder). La referencia usa el [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) para estudiar vídeos, nichos, tendencias y etiquetas. Thunderbolt prepara y guarda en caché ese conjunto antes del análisis.

> **Importante:** el flujo actual se inicia manualmente en **Niche Finder > Niche Finder Kaggle**. No es necesario crear un kernel de Kaggle.

## 1. Cuenta de Kaggle

Abre [kaggle.com](https://www.kaggle.com/), inicia sesión, confirma tu correo y completa las verificaciones que solicite Kaggle. El **username** es el identificador del perfil; no añadas `@`, espacios ni la URL completa.

## 2. Obtener la API Key

1. Abre [Kaggle API Tokens](https://www.kaggle.com/settings/api).
2. En **API**, pulsa **Generate New Token**. El Kaggle CLI actual también acepta el token mediante `KAGGLE_API_TOKEN`.
3. Para herramientas antiguas, abre **Legacy API Credentials** y pulsa **Create Legacy API Key** para descargar `kaggle.json` con `username` y `key`.
4. No guardes el archivo o la clave en GitHub, notebooks públicos ni mensajes. Si se expone, revócala y genera otra.

La documentación oficial confirma OAuth/CLI y la creación de claves en la configuración de tokens [1] [2].

## 3. Completar la tarjeta de Thunderbolt

Abre **Configuración de API > API Keys > Niche Finder — Kaggle**. Introduce el username sin `@` y la API key. **Kernel slug** puede quedarse con el valor predeterminado; se conserva por compatibilidad y no es necesario para la descarga actual. Pulsa **Probar llamada API**, confirma el resultado verde y después **Guardar**.

La prueba solo consulta el perfil de forma autenticada y de lectura. No crea kernels, no ejecuta notebooks y no publica nada.

## 4. Ejecutar el análisis

Ve a **Niche Finder > Niche Finder Kaggle**, selecciona fechas, país y filtros y pulsa **Analyze Niches**. En la primera ejecución se prepara el conjunto y se guarda una caché local validada.

## Solución rápida

| Síntoma | Acción |
| --- | --- |
| `401` o prueba roja | Comprueba el username y genera una clave nueva en Kaggle > Settings > API. |
| `429` o límite | Espera unos minutos; Kaggle aplica límites dinámicos. |
| Conjunto vacío | Comprueba el enlace del dataset y repite la preparación. |
| Clave expuesta | Revócala en Kaggle, crea otra y actualiza solo la tarjeta local. |

## Referencias

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "id": {
            "title": "Tutorial Kaggle",
            "caption": "Konfigurasikan kredensial Kaggle untuk Niche Finder berdasarkan proyek Niche-Finder.",
            "body": """## Apa yang dikonfigurasi

Niche Finder Kaggle di Thunderbolt terinspirasi oleh [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder). Referensi tersebut memakai [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) untuk menganalisis video, niche, tren, dan tag. Thunderbolt menyiapkan serta menyimpan cache dataset sebelum analisis.

> **Penting:** alur Thunderbolt saat ini dijalankan secara manual dari **Niche Finder > Niche Finder Kaggle**. Anda tidak perlu membuat kernel Kaggle.

## 1. Akun Kaggle

Buka [kaggle.com](https://www.kaggle.com/), masuk, konfirmasi email, dan selesaikan verifikasi yang diminta. **Username** adalah nama pada profil; jangan menambahkan `@`, spasi, atau URL lengkap.

## 2. Mendapatkan API Key

1. Buka [Kaggle API Tokens](https://www.kaggle.com/settings/api).
2. Pada bagian **API**, klik **Generate New Token**. Kaggle CLI terbaru juga dapat memakai token melalui `KAGGLE_API_TOKEN`.
3. Untuk alat lama, buka **Legacy API Credentials** dan klik **Create Legacy API Key** untuk mengunduh `kaggle.json` berisi `username` dan `key`.
4. Jangan menyimpan file atau key di GitHub, notebook publik, atau pesan. Jika bocor, cabut dan buat yang baru.

Dokumentasi resmi menjelaskan OAuth/CLI dan pembuatan API key di pengaturan akun [1] [2].

## 3. Mengisi kartu Thunderbolt

Buka **Konfigurasi API > API Keys > Niche Finder — Kaggle**. Masukkan username tanpa `@` dan API key. **Kernel slug** boleh memakai nilai bawaan; field ini dipertahankan untuk kompatibilitas dan tidak diperlukan untuk unduhan dataset saat ini. Klik **Uji panggilan API**, pastikan hasil hijau, lalu klik **Simpan**.

Pengujian hanya melakukan permintaan profil terautentikasi dan read-only. Tidak membuat kernel, menjalankan notebook, atau menerbitkan apa pun.

## 4. Menjalankan analisis

Buka **Niche Finder > Niche Finder Kaggle**, pilih tanggal, negara, dan filter, lalu klik **Analyze Niches**. Saat pertama dijalankan, dataset disiapkan dan disimpan sebagai cache lokal yang telah divalidasi.

## Pemecahan masalah

| Gejala | Tindakan |
| --- | --- |
| `401` atau tes merah | Periksa username dan buat key baru di Kaggle > Settings > API. |
| `429` atau batas | Tunggu beberapa menit; Kaggle menggunakan batas dinamis. |
| Dataset kosong | Periksa tautan dataset tren dan ulangi persiapan. |
| Key terbuka | Cabut di Kaggle, buat key baru, dan ubah hanya kartu lokal. |

## Referensi

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
        "it": {
            "title": "Tutorial Kaggle",
            "caption": "Configura le credenziali Kaggle per Niche Finder sulla base del progetto Niche-Finder.",
            "body": """## Cosa configura questo tutorial

Il Niche Finder Kaggle di Thunderbolt si ispira a [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder). Il progetto di riferimento usa il [Top Trending YouTube Videos Dataset](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries/code) per analizzare video, nicchie, tendenze e tag. Thunderbolt prepara e memorizza nella cache questo dataset prima dell'analisi.

> **Importante:** il flusso attuale viene avviato manualmente da **Niche Finder > Niche Finder Kaggle**. Non è necessario creare un kernel Kaggle.

## 1. Account Kaggle

Apri [kaggle.com](https://www.kaggle.com/), accedi, conferma l'e-mail e completa le verifiche richieste. Lo **username** è l'identificativo del profilo; non inserire `@`, spazi o l'URL completo.

## 2. Ottenere la API Key

1. Apri [Kaggle API Tokens](https://www.kaggle.com/settings/api).
2. Nella sezione **API**, fai clic su **Generate New Token**. Il Kaggle CLI attuale può usare il token anche tramite `KAGGLE_API_TOKEN`.
3. Per gli strumenti precedenti, apri **Legacy API Credentials** e fai clic su **Create Legacy API Key** per scaricare `kaggle.json` con `username` e `key`.
4. Non conservare file o chiave in GitHub, notebook pubblici o messaggi. Se viene esposta, revocala e creane una nuova.

La documentazione ufficiale descrive OAuth/CLI e la creazione della chiave nelle impostazioni dell'account [1] [2].

## 3. Compilare la scheda Thunderbolt

Apri **Configurazione API > API Keys > Niche Finder — Kaggle**. Inserisci username senza `@` e API key. **Kernel slug** può restare predefinito: è mantenuto per compatibilità e non serve per il download attuale. Fai clic su **Testa chiamata API**, verifica il risultato verde e poi fai clic su **Salva**.

Il test esegue solo una richiesta autenticata di lettura del profilo. Non crea kernel, non avvia notebook e non pubblica contenuti.

## 4. Eseguire l'analisi

Vai a **Niche Finder > Niche Finder Kaggle**, scegli date, paese e filtri e fai clic su **Analyze Niches**. Al primo avvio il dataset viene preparato e salvato in una cache locale validata.

## Risoluzione rapida

| Sintomo | Azione |
| --- | --- |
| `401` o test rosso | Controlla lo username e genera una nuova chiave in Kaggle > Settings > API. |
| `429` o limite | Attendi alcuni minuti; Kaggle usa limiti dinamici. |
| Dataset vuoto | Controlla il link del dataset e ripeti la preparazione. |
| Chiave esposta | Revocala in Kaggle, creane una nuova e aggiorna solo la scheda locale. |

## Riferimenti

[1] [Kaggle Public API](https://www.kaggle.com/docs/api) · [2] [Kaggle CLI — Authentication](https://github.com/Kaggle/kaggle-cli/blob/main/docs/README.md) · [3] [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder)
""",
        },
    },
    "apify": {
        "pt": {
            "title": "Tutorial Apify",
            "caption": "Configure a Apify para o Niche Finder e para a adaptação do workflow YTB Outlier Finder do n8n.",
            "body": """## O que este tutorial configura

A aba **Niche Finder Apify** é a alternativa remota ao fluxo baseado no dataset Kaggle. Ela foi baseada e adaptada do workflow n8n [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/), conhecido neste projecto como **YTB Outlier Finder**. O workflow de referência recupera palavras-chave, pesquisa vídeos no YouTube através de um actor Apify, aguarda o dataset, lê os resultados, resume os guiões e organiza a informação.

> **Diferença no Thunderbolt:** o fluxo é iniciado pelo botão **Pesquisar no Apify** e os resultados são tratados dentro da aplicação. Não é necessário configurar Airtable nem um gatilho semanal para fazer uma pesquisa manual.

## 1. Criar a conta Apify

Abra [Apify Console](https://console.apify.com/) e crie uma conta ou entre na sua conta existente. Aceda a **Settings > API & Integrations**. O Apify documenta esta área como o local para gerir tokens pessoais e integrações.

## 2. Criar e copiar a API Token

1. Em [Settings > API & Integrations](https://console.apify.com/settings/integrations), escolha a opção para criar um novo token.
2. Dê-lhe um nome reconhecível, por exemplo `thunderbolt-local`, e aplique o menor alcance disponível para a sua utilização, se a consola apresentar opções de permissões.
3. Copie o token apenas uma vez para um local seguro. Ele funciona como uma credencial de acesso; não o coloque em workflows públicos, screenshots, GitHub ou mensagens.
4. Se o token for exposto, elimine-o/revogá-lo na consola e crie outro.

A API oficial usa o cabeçalho `Authorization: Bearer YOUR_API_TOKEN`. O endpoint de diagnóstico documentado é `GET https://api.apify.com/v2/users/me` e deve responder `200` quando a credencial é válida [1].

## 3. Preencher o cartão do Thunderbolt

Abra **Configuração API > API Keys > Niche Finder — Apify**. Preencha **Apify API Token**. Mantenha **Actor ID** com o valor predefinido, salvo se souber que pretende utilizar outro actor compatível; não troque o actor apenas para testar a chave. Ajuste os tempos de polling apenas quando necessário.

Clique em **Testar chamada API**. O Thunderbolt faz uma consulta read-only a `users/me`: não inicia actor, não cria dataset e não consome uma execução de scraping. Depois do resultado verde, clique em **Salvar**.

## 4. Executar a pesquisa YTB Outlier Finder

Entre em **Niche Finder > Niche Finder Apify**, introduza as palavras-chave do nicho, país/idioma e os limites disponíveis e clique em **Pesquisar no Apify**. A aplicação inicia o actor configurado, aguarda a conclusão, lê o dataset devolvido e normaliza os vídeos para a análise local. Uma pesquisa pode demorar mais do que uma chamada de diagnóstico, porque o actor realmente consulta dados públicos do YouTube.

A lógica corresponde ao workflow n8n: **palavras-chave → pesquisa Apify → espera pelo dataset → leitura e normalização → análise de outliers**. O passo de Airtable do workflow original não é requisito do Thunderbolt.

## Diagnóstico rápido

| Sintoma | Acção recomendada |
| --- | --- |
| `401` no teste | Crie outro token em Settings > API & Integrations e substitua o valor no cartão. |
| `403` ou actor sem permissão | Confirme a conta, o alcance do token e o Actor ID configurado. |
| Actor não encontrado | Use um Actor ID completo e compatível com o input esperado pelo Thunderbolt. |
| Execução pendente | Consulte a execução na própria aba; não inicie várias pesquisas iguais em paralelo. |
| Limites ou cobrança | Reveja o consumo e as condições actuais na consola Apify antes de executar novas pesquisas. |

## Referências

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [Workflow YTB Outlier Finder no n8n](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [Vídeo associado](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "en": {
            "title": "Apify Tutorial",
            "caption": "Configure Apify for Niche Finder and the Thunderbolt adaptation of the n8n YTB Outlier Finder workflow.",
            "body": """## What this tutorial configures

The **Niche Finder Apify** page is the remote alternative to the Kaggle dataset flow. It was based on and adapted from the n8n workflow [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/), referred to in this project as **YTB Outlier Finder**. The reference workflow retrieves keywords, searches YouTube through an Apify Actor, waits for the dataset, reads the results, summarizes scripts, and organizes the information.

> **Thunderbolt difference:** the flow starts with **Search Apify** and processes results inside the app. Airtable and a weekly trigger are not required for a manual search.

## 1. Create an Apify account

Open [Apify Console](https://console.apify.com/) and sign up or sign in. Go to **Settings > API & Integrations**, the area Apify documents for managing personal tokens and integrations.

## 2. Create and copy the API token

1. Open [Settings > API & Integrations](https://console.apify.com/settings/integrations) and create a new token.
2. Give it a clear name, such as `thunderbolt-local`, and choose the smallest available permission scope if the console offers scopes.
3. Copy the token to a secure location. Never put it in public workflows, screenshots, GitHub, or messages.
4. If it is exposed, revoke/delete it in the console and create a replacement.

Apify's API uses `Authorization: Bearer YOUR_API_TOKEN`. The documented diagnostic endpoint is `GET https://api.apify.com/v2/users/me`, which should return `200` for a valid credential [1].

## 3. Fill in Thunderbolt

Open **API Configuration > API Keys > Niche Finder — Apify** and enter **Apify API Token**. Keep **Actor ID** at its default unless you know that another compatible Actor is required; do not change the Actor just to test the key. Adjust polling and timeout values only when necessary.

Click **Test API call**. Thunderbolt performs a read-only request to `users/me`: it does not start an Actor, create a dataset, or consume a scraping run. After the green result, click **Save**.

## 4. Run the YTB Outlier Finder search

Go to **Niche Finder > Niche Finder Apify**, enter niche keywords and the available language/country and result limits, and click **Search Apify**. The app starts the configured Actor, waits for completion, reads the returned dataset, and normalizes videos for local analysis. A real search can take longer than the credential test because the Actor retrieves public YouTube data.

The adapted logic is: **keywords → Apify search → wait for dataset → read and normalize → outlier analysis**. The Airtable step from the original workflow is not required in Thunderbolt.

## Quick troubleshooting

| Symptom | Recommended action |
| --- | --- |
| `401` in the test | Create another token in Settings > API & Integrations and replace it in the card. |
| `403` or Actor permission error | Check the account, token scope, and configured Actor ID. |
| Actor not found | Use a full Actor ID compatible with Thunderbolt's expected input. |
| Run remains pending | Monitor it in the page and do not launch identical searches in parallel. |
| Limits or charges | Review current usage and terms in the Apify console before starting more searches. |

## References

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [YTB Outlier Finder workflow on n8n](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [Associated video](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "zh": {
            "title": "Apify 教程",
            "caption": "为 Niche Finder 配置 Apify，并了解 Thunderbolt 对 n8n YTB Outlier Finder 流程的改编。",
            "body": """## 本教程配置什么

**Niche Finder Apify** 是基于 Kaggle 数据集流程的远程替代方案。它参考并改编了 n8n 工作流 [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/)，在本项目中称为 **YTB Outlier Finder**。原流程会取得关键词，通过 Apify Actor 搜索 YouTube，等待数据集，读取结果并整理信息。

> **Thunderbolt 的区别：** 点击 **Search Apify** 后在应用内部处理结果。手动搜索不需要 Airtable 或每周触发器。

## 1. 创建 Apify 账户

打开 [Apify Console](https://console.apify.com/) 并注册或登录，然后进入 **Settings > API & Integrations** 管理个人 Token。

## 2. 创建并复制 API Token

1. 在 [Settings > API & Integrations](https://console.apify.com/settings/integrations) 创建新 Token。
2. 使用清晰的名称，例如 `thunderbolt-local`；如果控制台提供权限范围，请选择满足用途的最小范围。
3. 将 Token 保存到安全位置，不要放入公开 workflow、截图、GitHub 或消息中。
4. 如果 Token 泄露，请在控制台撤销/删除并重新创建。

Apify API 使用 `Authorization: Bearer YOUR_API_TOKEN`。官方记录的诊断接口是 `GET https://api.apify.com/v2/users/me`，有效凭据应返回 `200` [1]。

## 3. 填写 Thunderbolt

进入 **API Configuration > API Keys > Niche Finder — Apify**，填写 **Apify API Token**。除非明确需要兼容 Actor，否则保持默认 **Actor ID**；不要为了测试密钥而更换 Actor。

点击 **Test API call**。Thunderbolt 只读取 `users/me`，不会启动 Actor、创建数据集或消耗抓取运行。看到绿色结果后点击 **Save**。

## 4. 运行 YTB Outlier Finder 搜索

进入 **Niche Finder > Niche Finder Apify**，填写利基关键词和可用的语言、国家及数量限制，然后点击 **Search Apify**。应用会启动配置的 Actor，等待完成，读取数据集并规范化视频。真实搜索比凭据测试耗时更长，因为 Actor 会检索公开的 YouTube 数据。

改编后的顺序是：**关键词 → Apify 搜索 → 等待数据集 → 读取与规范化 → 异常视频分析**。原工作流的 Airtable 步骤不是 Thunderbolt 的要求。

## 快速排查

| 现象 | 建议 |
| --- | --- |
| 测试返回 `401` | 在 Settings > API & Integrations 创建新 Token 并替换卡片内容。 |
| `403` 或 Actor 权限错误 | 检查账户、Token 权限和 Actor ID。 |
| 找不到 Actor | 使用完整且兼容的 Actor ID。 |
| 运行一直等待 | 在页面中查看状态，不要并行启动相同搜索。 |
| 限额或费用 | 开始更多搜索前，查看 Apify 控制台的当前用量和条款。 |

## 参考

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [n8n YTB Outlier Finder 工作流](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [关联视频](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "de": {
            "title": "Apify-Tutorial",
            "caption": "Apify für Niche Finder und die Thunderbolt-Anpassung des n8n-Workflows YTB Outlier Finder konfigurieren.",
            "body": """## Was dieses Tutorial einrichtet

**Niche Finder Apify** ist die entfernte Alternative zum Kaggle-Datensatz. Die Seite basiert auf dem n8n-Workflow [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/), der in diesem Projekt **YTB Outlier Finder** heißt. Die Referenz sammelt Keywords, sucht mit einem Apify Actor nach YouTube-Videos, wartet auf den Datensatz und verarbeitet die Ergebnisse.

> **Unterschied bei Thunderbolt:** Eine manuelle Suche startet über **Search Apify** und wird in der Anwendung verarbeitet. Airtable und ein wöchentlicher Trigger sind nicht erforderlich.

## 1. Apify-Konto

Öffnen Sie [Apify Console](https://console.apify.com/), registrieren Sie sich oder melden Sie sich an und öffnen Sie **Settings > API & Integrations**.

## 2. API-Token erstellen

1. Erstellen Sie unter [Settings > API & Integrations](https://console.apify.com/settings/integrations) einen neuen Token.
2. Verwenden Sie einen eindeutigen Namen wie `thunderbolt-local`. Falls Berechtigungsbereiche angeboten werden, wählen Sie den kleinsten passenden Umfang.
3. Speichern Sie den Token sicher und geben Sie ihn nicht in öffentlichen Workflows, Screenshots, GitHub oder Nachrichten weiter.
4. Bei Offenlegung Token in der Konsole widerrufen/löschen und ersetzen.

Die Apify API verwendet `Authorization: Bearer YOUR_API_TOKEN`. Der dokumentierte Prüf-Endpunkt ist `GET https://api.apify.com/v2/users/me`; bei gültigen Daten wird `200` erwartet [1].

## 3. Thunderbolt ausfüllen

Öffnen Sie **API-Konfiguration > API Keys > Niche Finder — Apify**, tragen Sie **Apify API Token** ein und lassen Sie **Actor ID** standardmäßig, sofern kein kompatibler anderer Actor benötigt wird. Klicken Sie auf **API-Aufruf testen**. Die Prüfung liest nur `users/me`; sie startet keinen Actor und erstellt keinen Datensatz. Danach **Speichern** wählen.

## 4. YTB-Outlier-Finder-Suche

Gehen Sie zu **Niche Finder > Niche Finder Apify**, geben Sie Keywords sowie die verfügbaren Sprach-, Länder- und Ergebnisgrenzen ein und klicken Sie auf **Search Apify**. Thunderbolt startet den Actor, wartet auf die Fertigstellung, liest den Datensatz und normalisiert Videos für die lokale Analyse.

Die Reihenfolge lautet: **Keywords → Apify-Suche → auf Datensatz warten → lesen und normalisieren → Outlier-Analyse**. Airtable aus dem ursprünglichen Workflow ist nicht erforderlich.

## Schnelle Fehlerbehebung

| Symptom | Empfehlung |
| --- | --- |
| `401` beim Test | Neuen Token in Settings > API & Integrations erzeugen und ersetzen. |
| `403` oder Actor-Fehler | Konto, Token-Berechtigung und Actor ID prüfen. |
| Actor nicht gefunden | Vollständige kompatible Actor ID verwenden. |
| Lauf wartet | Status in der Seite prüfen und gleiche Suchen nicht parallel starten. |
| Limits oder Kosten | Vor weiteren Suchen aktuelle Nutzung und Bedingungen in der Apify-Konsole prüfen. |

## Quellen

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [YTB Outlier Finder auf n8n](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [Zugehöriges Video](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "vi": {
            "title": "Hướng dẫn Apify",
            "caption": "Cấu hình Apify cho Niche Finder và phiên bản Thunderbolt của workflow YTB Outlier Finder trên n8n.",
            "body": """## Hướng dẫn này cấu hình gì

Trang **Niche Finder Apify** là lựa chọn từ xa thay cho luồng dữ liệu Kaggle. Trang này dựa trên và điều chỉnh workflow n8n [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/), được gọi là **YTB Outlier Finder** trong dự án. Workflow lấy từ khóa, tìm video YouTube bằng Apify Actor, chờ dataset và xử lý kết quả.

> **Khác biệt:** tìm kiếm thủ công bắt đầu bằng **Search Apify** và kết quả được xử lý trong ứng dụng. Không cần Airtable hoặc trigger hàng tuần.

## 1. Tạo tài khoản Apify

Mở [Apify Console](https://console.apify.com/), đăng ký hoặc đăng nhập và vào **Settings > API & Integrations**.

## 2. Tạo API token

1. Tạo token mới tại [Settings > API & Integrations](https://console.apify.com/settings/integrations).
2. Đặt tên rõ ràng như `thunderbolt-local`; nếu có phạm vi quyền, chọn phạm vi nhỏ nhất phù hợp.
3. Lưu token an toàn, không đưa vào workflow công khai, ảnh chụp, GitHub hoặc tin nhắn.
4. Nếu bị lộ, thu hồi/xóa token trong Console và tạo token mới.

API Apify dùng `Authorization: Bearer YOUR_API_TOKEN`. Endpoint kiểm tra chính thức là `GET https://api.apify.com/v2/users/me` và thông tin hợp lệ trả về `200` [1].

## 3. Điền Thunderbolt

Mở **Cấu hình API > API Keys > Niche Finder — Apify**, nhập **Apify API Token**. Giữ **Actor ID** mặc định trừ khi bạn cần Actor tương thích khác. Chọn **Kiểm tra lệnh gọi API**; Thunderbolt chỉ đọc `users/me`, không chạy Actor và không tạo dataset. Sau đó chọn **Lưu**.

## 4. Chạy tìm kiếm YTB Outlier Finder

Vào **Niche Finder > Niche Finder Apify**, nhập từ khóa ngách và các giới hạn ngôn ngữ, quốc gia, số kết quả rồi chọn **Search Apify**. Ứng dụng khởi chạy Actor, chờ hoàn tất, đọc dataset và chuẩn hóa video cho phân tích cục bộ.

Trình tự được điều chỉnh là: **từ khóa → tìm kiếm Apify → chờ dataset → đọc và chuẩn hóa → phân tích outlier**. Bước Airtable của workflow gốc không bắt buộc.

## Xử lý nhanh

| Hiện tượng | Cách xử lý |
| --- | --- |
| `401` | Tạo token mới trong Settings > API & Integrations và thay vào thẻ. |
| `403` hoặc lỗi quyền Actor | Kiểm tra tài khoản, quyền token và Actor ID. |
| Không tìm thấy Actor | Dùng Actor ID đầy đủ và tương thích. |
| Chạy đang chờ | Theo dõi ngay trong trang và không chạy trùng song song. |
| Giới hạn hoặc chi phí | Kiểm tra mức dùng và điều khoản hiện tại trong Console Apify. |

## Tài liệu tham khảo

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [Workflow YTB Outlier Finder trên n8n](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [Video liên quan](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "tr": {
            "title": "Apify Eğitimi",
            "caption": "Niche Finder için Apify'ı ve n8n YTB Outlier Finder iş akışının Thunderbolt uyarlamasını yapılandırın.",
            "body": """## Bu eğitim neyi yapılandırır

**Niche Finder Apify**, Kaggle veri seti akışının uzak alternatifidir. Bu sayfa, projede **YTB Outlier Finder** adı verilen n8n iş akışı [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) temel alınarak uyarlanmıştır. Referans; anahtar kelimeleri alır, Apify Actor ile YouTube araması yapar, veri setini bekler ve sonuçları işler.

> **Thunderbolt farkı:** Manuel arama **Search Apify** düğmesiyle başlar ve sonuçlar uygulama içinde işlenir. Airtable veya haftalık tetikleyici gerekli değildir.

## 1. Apify hesabı

[Apify Console](https://console.apify.com/) adresini açın, kayıt olun veya giriş yapın ve **Settings > API & Integrations** bölümüne gidin.

## 2. API token oluşturma

1. [Settings > API & Integrations](https://console.apify.com/settings/integrations) sayfasında yeni token oluşturun.
2. `thunderbolt-local` gibi anlaşılır bir ad verin; izin kapsamları sunuluyorsa gereken en küçük kapsamı seçin.
3. Token'ı güvenli yerde saklayın; herkese açık workflow, ekran görüntüsü, GitHub veya mesajlarda paylaşmayın.
4. Açığa çıkarsa Console'dan iptal/silme işlemi yapıp yeni token oluşturun.

Apify API `Authorization: Bearer YOUR_API_TOKEN` kullanır. Resmi doğrulama endpoint'i `GET https://api.apify.com/v2/users/me` adresidir ve geçerli kimlik bilgileri `200` döndürmelidir [1].

## 3. Thunderbolt ayarı

**API Yapılandırması > API Keys > Niche Finder — Apify** yolunu açın ve **Apify API Token** alanını doldurun. Uyumlu başka bir Actor gerekmiyorsa **Actor ID** varsayılan kalsın. **API çağrısını test et** düğmesi yalnızca `users/me` okur; Actor başlatmaz ve veri seti oluşturmaz. Yeşil sonuçtan sonra **Kaydet** seçeneğine tıklayın.

## 4. YTB Outlier Finder araması

**Niche Finder > Niche Finder Apify** sayfasında niş anahtar kelimelerini ve mevcut dil, ülke ve sonuç sınırlarını girip **Search Apify** düğmesine tıklayın. Uygulama Actor'ı başlatır, bitmesini bekler, veri setini okur ve videoları yerel analiz için normalleştirir.

Uyarlanan sıra: **anahtar kelimeler → Apify araması → veri setini bekle → oku ve normalleştir → outlier analizi**. Orijinal iş akışındaki Airtable adımı Thunderbolt için zorunlu değildir.

## Hızlı sorun giderme

| Belirti | Öneri |
| --- | --- |
| `401` | Settings > API & Integrations üzerinden yeni token oluşturup kartı güncelleyin. |
| `403` veya Actor yetki hatası | Hesabı, token izinlerini ve Actor ID'yi kontrol edin. |
| Actor bulunamadı | Tam ve uyumlu Actor ID kullanın. |
| Çalışma bekliyor | Sayfadan izleyin ve aynı aramaları paralel başlatmayın. |
| Limit veya ücret | Yeni aramalardan önce Apify Console'daki güncel kullanımı ve koşulları inceleyin. |

## Kaynaklar

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [n8n YTB Outlier Finder workflow](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [İlgili video](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "ru": {
            "title": "Руководство Apify",
            "caption": "Настройте Apify для Niche Finder и адаптации workflow YTB Outlier Finder из n8n.",
            "body": """## Что настраивает руководство

Страница **Niche Finder Apify** — удалённая альтернатива потоку Kaggle. Она основана на workflow n8n [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/), который в проекте называется **YTB Outlier Finder**. Исходный процесс получает ключевые слова, ищет видео YouTube через Apify Actor, ждёт набор данных и обрабатывает результаты.

> **Отличие Thunderbolt:** ручной поиск запускается кнопкой **Search Apify**, а результаты обрабатываются внутри приложения. Airtable и еженедельный trigger не требуются.

## 1. Аккаунт Apify

Откройте [Apify Console](https://console.apify.com/), зарегистрируйтесь или войдите и перейдите в **Settings > API & Integrations**.

## 2. Создание API token

1. Создайте новый token в [Settings > API & Integrations](https://console.apify.com/settings/integrations).
2. Назовите его, например `thunderbolt-local`; при наличии областей разрешений выберите минимально необходимую.
3. Сохраните token безопасно. Не помещайте его в публичные workflow, снимки экрана, GitHub или сообщения.
4. При утечке отзовите/удалите token в Console и создайте новый.

API Apify использует `Authorization: Bearer YOUR_API_TOKEN`. Официальная проверка выполняется через `GET https://api.apify.com/v2/users/me` и для действительных данных возвращает `200` [1].

## 3. Карточка Thunderbolt

Откройте **Настройка API > API Keys > Niche Finder — Apify**, заполните **Apify API Token** и оставьте **Actor ID** по умолчанию, если другой совместимый Actor не нужен. Нажмите **Проверить вызов API**: Thunderbolt только читает `users/me`, не запускает Actor и не создаёт dataset. После зелёного результата нажмите **Сохранить**.

## 4. Поиск YTB Outlier Finder

Перейдите в **Niche Finder > Niche Finder Apify**, введите ключевые слова ниши и доступные ограничения языка, страны и количества результатов, затем нажмите **Search Apify**. Приложение запускает Actor, ждёт завершения, читает dataset и нормализует видео для локального анализа.

Порядок адаптации: **ключевые слова → поиск Apify → ожидание dataset → чтение и нормализация → анализ outlier**. Шаг Airtable из исходного workflow не обязателен.

## Быстрое решение проблем

| Симптом | Действие |
| --- | --- |
| `401` | Создайте новый token в Settings > API & Integrations и замените его в карточке. |
| `403` или ошибка разрешений Actor | Проверьте аккаунт, разрешения token и Actor ID. |
| Actor не найден | Используйте полный совместимый Actor ID. |
| Запуск ожидает | Следите за ним на странице и не запускайте одинаковые поиски параллельно. |
| Лимиты или расходы | Перед новыми поисками проверьте текущее использование и условия в Console Apify. |

## Источники

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [Workflow YTB Outlier Finder в n8n](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [Связанное видео](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "es": {
            "title": "Tutorial de Apify",
            "caption": "Configura Apify para Niche Finder y la adaptación en Thunderbolt del workflow YTB Outlier Finder de n8n.",
            "body": """## Qué configura este tutorial

La página **Niche Finder Apify** es la alternativa remota al flujo de Kaggle. Se basa en el workflow de n8n [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/), llamado **YTB Outlier Finder** en este proyecto. El flujo de referencia obtiene palabras clave, busca vídeos de YouTube mediante un Actor de Apify, espera el dataset y procesa los resultados.

> **Diferencia en Thunderbolt:** la búsqueda manual empieza con **Search Apify** y los resultados se procesan dentro de la aplicación. No se necesita Airtable ni un disparador semanal.

## 1. Crear la cuenta Apify

Abre [Apify Console](https://console.apify.com/), regístrate o inicia sesión y entra en **Settings > API & Integrations**.

## 2. Crear y copiar el API token

1. Crea un token nuevo en [Settings > API & Integrations](https://console.apify.com/settings/integrations).
2. Usa un nombre claro, como `thunderbolt-local`, y el alcance mínimo disponible si la consola ofrece permisos.
3. Guarda el token de forma segura y no lo incluyas en workflows públicos, capturas, GitHub o mensajes.
4. Si se expone, revócalo/elíminalo en la consola y crea otro.

La API de Apify usa `Authorization: Bearer YOUR_API_TOKEN`. El endpoint oficial de verificación es `GET https://api.apify.com/v2/users/me` y debe devolver `200` con credenciales válidas [1].

## 3. Completar Thunderbolt

Abre **Configuración de API > API Keys > Niche Finder — Apify**, introduce **Apify API Token** y deja **Actor ID** por defecto salvo que necesites otro Actor compatible. Pulsa **Probar llamada API**: Thunderbolt solo lee `users/me`, no inicia un Actor ni crea un dataset. Después del resultado verde, pulsa **Guardar**.

## 4. Ejecutar la búsqueda YTB Outlier Finder

Ve a **Niche Finder > Niche Finder Apify**, introduce palabras clave del nicho y los límites disponibles de idioma, país y resultados y pulsa **Search Apify**. La aplicación inicia el Actor, espera, lee el dataset y normaliza los vídeos para el análisis local.

La secuencia adaptada es: **palabras clave → búsqueda Apify → esperar dataset → leer y normalizar → análisis de outliers**. El paso de Airtable del workflow original no es obligatorio.

## Solución rápida

| Síntoma | Acción |
| --- | --- |
| `401` | Crea otro token en Settings > API & Integrations y reemplázalo en la tarjeta. |
| `403` o error de permisos | Comprueba la cuenta, los permisos del token y el Actor ID. |
| Actor no encontrado | Usa un Actor ID completo y compatible. |
| Ejecución pendiente | Vigílala en la página y no ejecutes búsquedas iguales en paralelo. |
| Límites o costes | Revisa el uso y las condiciones actuales en Apify Console antes de iniciar más búsquedas. |

## Referencias

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [Workflow YTB Outlier Finder en n8n](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [Vídeo asociado](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "id": {
            "title": "Tutorial Apify",
            "caption": "Konfigurasikan Apify untuk Niche Finder dan adaptasi workflow YTB Outlier Finder n8n di Thunderbolt.",
            "body": """## Apa yang dikonfigurasi

Halaman **Niche Finder Apify** adalah alternatif jarak jauh untuk alur dataset Kaggle. Halaman ini diadaptasi dari workflow n8n [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/), yang disebut **YTB Outlier Finder** dalam proyek ini. Alurnya mengambil kata kunci, mencari video YouTube melalui Apify Actor, menunggu dataset, lalu memproses hasil.

> **Perbedaan Thunderbolt:** pencarian manual dimulai dengan **Search Apify** dan hasil diproses di dalam aplikasi. Airtable dan pemicu mingguan tidak diperlukan.

## 1. Membuat akun Apify

Buka [Apify Console](https://console.apify.com/), daftar atau masuk, lalu buka **Settings > API & Integrations**.

## 2. Membuat API token

1. Buat token baru di [Settings > API & Integrations](https://console.apify.com/settings/integrations).
2. Gunakan nama jelas seperti `thunderbolt-local`; jika tersedia pilihan izin, pilih cakupan paling kecil yang diperlukan.
3. Simpan token dengan aman dan jangan memasukkannya ke workflow publik, screenshot, GitHub, atau pesan.
4. Jika bocor, cabut/hapus token di Console dan buat yang baru.

API Apify memakai `Authorization: Bearer YOUR_API_TOKEN`. Endpoint pemeriksaan resmi adalah `GET https://api.apify.com/v2/users/me` dan kredensial valid mengembalikan `200` [1].

## 3. Mengisi Thunderbolt

Buka **Konfigurasi API > API Keys > Niche Finder — Apify**, isi **Apify API Token**, dan biarkan **Actor ID** pada nilai bawaan kecuali Anda memerlukan Actor kompatibel lain. Klik **Uji panggilan API**; Thunderbolt hanya membaca `users/me`, tidak menjalankan Actor atau membuat dataset. Setelah hasil hijau, klik **Simpan**.

## 4. Menjalankan pencarian YTB Outlier Finder

Buka **Niche Finder > Niche Finder Apify**, masukkan kata kunci niche serta batas bahasa, negara, dan jumlah hasil yang tersedia, lalu klik **Search Apify**. Aplikasi menjalankan Actor, menunggu selesai, membaca dataset, dan menormalkan video untuk analisis lokal.

Urutan adaptasinya: **kata kunci → pencarian Apify → tunggu dataset → baca dan normalisasi → analisis outlier**. Langkah Airtable dari workflow asli tidak wajib di Thunderbolt.

## Pemecahan masalah

| Gejala | Tindakan |
| --- | --- |
| `401` | Buat token lain di Settings > API & Integrations dan ganti pada kartu. |
| `403` atau izin Actor gagal | Periksa akun, izin token, dan Actor ID. |
| Actor tidak ditemukan | Gunakan Actor ID lengkap yang kompatibel. |
| Proses masih menunggu | Pantau dari halaman dan jangan menjalankan pencarian sama secara paralel. |
| Batas atau biaya | Tinjau penggunaan dan ketentuan terbaru di Apify Console sebelum pencarian berikutnya. |

## Referensi

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [Workflow YTB Outlier Finder di n8n](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [Video terkait](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
        "it": {
            "title": "Tutorial Apify",
            "caption": "Configura Apify per Niche Finder e l'adattamento Thunderbolt del workflow n8n YTB Outlier Finder.",
            "body": """## Cosa configura questo tutorial

La pagina **Niche Finder Apify** è l'alternativa remota al flusso del dataset Kaggle. È basata sul workflow n8n [Discover HIDDEN YouTube trends / outlier videos in your niche (Apify + Airtable)](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/), chiamato **YTB Outlier Finder** nel progetto. Il workflow di riferimento recupera parole chiave, cerca video su YouTube tramite un Actor Apify, attende il dataset e tratta i risultati.

> **Differenza Thunderbolt:** la ricerca manuale parte da **Search Apify** e i risultati vengono trattati nell'applicazione. Airtable e un trigger settimanale non sono necessari.

## 1. Account Apify

Apri [Apify Console](https://console.apify.com/), registrati o accedi e vai a **Settings > API & Integrations**.

## 2. Creare l'API token

1. Crea un nuovo token in [Settings > API & Integrations](https://console.apify.com/settings/integrations).
2. Usa un nome chiaro, per esempio `thunderbolt-local`; se sono disponibili permessi, scegli l'ambito minimo necessario.
3. Conserva il token in sicurezza e non inserirlo in workflow pubblici, screenshot, GitHub o messaggi.
4. Se viene esposto, revocalo/eliminalo nella Console e creane uno nuovo.

L'API Apify usa `Authorization: Bearer YOUR_API_TOKEN`. L'endpoint ufficiale di verifica è `GET https://api.apify.com/v2/users/me` e restituisce `200` con credenziali valide [1].

## 3. Compilare Thunderbolt

Apri **Configurazione API > API Keys > Niche Finder — Apify**, inserisci **Apify API Token** e lascia **Actor ID** predefinito salvo la necessità di un Actor compatibile diverso. Fai clic su **Testa chiamata API**: Thunderbolt legge solo `users/me`, non avvia Actor e non crea dataset. Dopo il risultato verde, fai clic su **Salva**.

## 4. Eseguire la ricerca YTB Outlier Finder

Vai a **Niche Finder > Niche Finder Apify**, inserisci parole chiave della nicchia e i limiti disponibili di lingua, paese e risultati, poi fai clic su **Search Apify**. L'app avvia l'Actor, attende il completamento, legge il dataset e normalizza i video per l'analisi locale.

La sequenza adattata è: **parole chiave → ricerca Apify → attesa dataset → lettura e normalizzazione → analisi outlier**. Il passaggio Airtable del workflow originale non è obbligatorio.

## Risoluzione rapida

| Sintomo | Azione |
| --- | --- |
| `401` | Crea un nuovo token in Settings > API & Integrations e sostituiscilo nella scheda. |
| `403` o errore di autorizzazione | Controlla account, permessi del token e Actor ID. |
| Actor non trovato | Usa un Actor ID completo e compatibile. |
| Esecuzione in attesa | Controllala nella pagina e non avviare ricerche identiche in parallelo. |
| Limiti o costi | Controlla uso e condizioni attuali nella Console Apify prima di altre ricerche. |

## Riferimenti

[1] [Apify API — Get started](https://docs.apify.com/api/v2/getting-started) · [2] [Apify Console — API & Integrations](https://console.apify.com/settings/integrations) · [3] [Workflow YTB Outlier Finder su n8n](https://n8n.io/workflows/4187-discover-hidden-youtube-trends-outlier-videos-in-your-niche-apify-airtable/) · [4] [Video associato](https://www.youtube.com/watch?v=pH2hVaij3FY)
""",
        },
    },
}


def tutorial_definition(kind: str, language: str) -> dict[str, str]:
    """Return a localized tutorial definition, falling back to Portuguese."""
    tutorials = _TUTORIALS.get(kind)
    if tutorials is None:
        raise KeyError(f"Unknown tutorial: {kind}")
    return tutorials.get(language, tutorials["pt"])


def tutorial_title(kind: str, language: str) -> str:
    return tutorial_definition(kind, language)["title"]


def tutorial_caption(kind: str, language: str) -> str:
    return tutorial_definition(kind, language)["caption"]


def tutorial_body(kind: str, language: str) -> str:
    return tutorial_definition(kind, language)["body"]


__all__ = [
    "SUPPORTED_TUTORIAL_LANGUAGES",
    "tutorial_body",
    "tutorial_caption",
    "tutorial_definition",
    "tutorial_title",
]
