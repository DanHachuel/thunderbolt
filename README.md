# Thunderbolt UI

> Consulte o [Manual completo de instalação](MANUAL-INSTALACAO.md) antes do primeiro teste local.

Thunderbolt — UI web local da Fase 3, baseada no fluxo Streamlit do [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo). A aplicação organiza canais, blueprints, lotes de vídeos, filas, artefactos e upload em armazenamento local JSON.

## Estado actual

A primeira versão implementa a camada UI independente com:

| Área | Incluído |
|---|---|
| Início | Resumo de canais, tarefas, backlog, execução e falhas, com as filas do Pipeline inline |
| Pipeline | Menu expansível com Criação de Vídeos, Criação de Músicas, Roteiros e Upload |
| Blueprints Youtube | Leitura da pasta `storage/blueprints/`, upload/validação de JSON e criação a partir de link YouTube |
| Brandings | Subaba própria dentro de Blueprints, upload/listagem de Brandings e criação conjunta com Blueprint |
| Canais Youtube | Subabas de importação pública sem API Key, Canais em lote gmail por conta Google/YouTube via OAuth e cadastro manual independente; cartões com botão Editar, nicho/referências visível, Prompts do Canal/Blueprint, Narrador/voz e gestão dos últimos 10 vídeos |
| Criação de Vídeos / Criação de Músicas | Subabas Criar vídeo e Vídeos; idiomas históricos preservados e dez códigos MoneyPrinterTurbo com bandeiras; Pexels/Pixabay, full IA com Estilo IA e Apenas Música com agente musical; a segunda página reutiliza o mesmo fluxo com título próprio |
| Automação | Menu expansível com a subaba **Automação Youtube**, onde ficam os vídeos e canais, selectores editáveis de Blueprint/voz padrão, Automação ON, horário diário HH:MM e worker local baseado no relógio do computador |
| AI Influencers | Menu expansível com Personagens, Redes Sociais, Tutorial Meta e Tutorial Supabase; conteúdo interno localizado |
| Niche Finder | Menu expansível com duas alternativas independentes: Niche Finder Kaggle e Niche Finder Apify, com parâmetros, execução e resultados separados |
| Edição | Menu expansível abaixo de Automação com Limpador de Metadados, Clip Generator local em Cortes e Editor Python inspirado no PYEdit para vídeos e scripts locais |
| Upload | YouTube via `youtube-automation-agent` adaptado internamente, fallback ordenado API Oficial → Upload directo → Postiz, upload de MP4 para Postiz via API key/MCP configurável, TikTok, Instagram e Facebook Pages no front end |
| MCP | Catálogo local opcional de Short Video Maker, AutoVio, OpenMontage e OpenCut, com portas editáveis e activação |
| Configurações | **Contas Google**, **Configuração API** e **Notificações**; API Keys divididas entre **Serviços e modelos** e **Fontes de materiais**, com várias chaves independentes por fonte, além de contas Google/YouTube por cartão, `INNERTUBE_API_KEY` no documento da conta, providers, TTS, Nano Banana, Postiz, TikTok e Upload-Post |
| Launcher | Execução via `npx`, instalação assistida, diagnóstico e preparação para distribuição |

## Upload-Post — publicação para múltiplas plataformas

A página **Upload** contém quatro subabas: **Upload convencional**, **Upload directo**, **Postiz** e **Upload-Post**. A quarta alternativa usa a API oficial do [Upload-Post](https://docs.upload-post.com/) para enviar um vídeo local para uma ou mais plataformas ligadas ao perfil configurado. Seleccione as plataformas na própria subaba, confirme o título e a descrição e clique em **Enviar vídeo pelo Upload-Post**.

A API key, o username/perfil e a lista inicial de plataformas continuam em **Configuração API > API Keys > Serviços e modelos**, no expander **Publicação através do Upload-Post**. A subaba não pede novamente a credencial. O cliente envia `multipart/form-data` para `https://api.upload-post.com/api/upload`, repete `platform[]` para cada destino e guarda a resposta, o `request_id` e o resultado no histórico local de uploads. A opção **Processar em segundo plano** usa `async_upload=true` quando a API estiver configurada para processamento assíncrono.

O Upload-Post é independente do Postiz: Postiz continua a usar o seu fluxo próprio de asset + post, enquanto Upload-Post publica directamente nas plataformas ligadas ao username configurado. Uma publicação aceite pelo Upload-Post também é reconciliada no centro de **Notificações**.

## Upload directo — credenciais por conta e por canal

O Upload directo baseado no [YouTube-Video-Upload-Frontend-Api](https://github.com/Nojus10/YouTube-Video-Upload-Frontend-Api) usa um único documento JSON por conta Google. Em **Configurações > Contas Google > Contas Google/YouTube — canais em lote**, cada conta aparece como um cartão expansível identificado por **nome — e-mail**. Dentro do cartão existe o uploader **Subir documento de cookies/credenciais** e o único campo técnico permitido na UI, **sessionInfo token desta conta Google**. Cookies, `INNERTUBE_API_KEY`, `chunk_size` e `delegated_session_ids` continuam exclusivamente no documento.

O botão **Adicionar outra conta Gmail** fica abaixo de uma divisória, fora dos cartões existentes. Ao criar uma conta, o Thunderbolt cria imediatamente `credentials.json` com placeholders vazios. Um upload completo ou parcial é incorporado por merge: os cookies enviados actualizam apenas os cookies fornecidos e valores como `sessionInfo`, `INNERTUBE_API_KEY`, `chunk_size` e `delegated_session_ids` existentes não são apagados. O alerta **Documento incompleto: SID, SSID, HSID, APISID, SAPISID, sessionInfo, INNERTUBE_API_KEY** permanece visível por conta quando necessário.

O documento é guardado por Gmail em `storage/youtube_direct_accounts/<id-da-conta>/credentials.json`, com permissões locais restritas. Em **Canais > Canais cadastrados**, a UI apenas associa o canal à conta Google; essa associação continua permitida mesmo quando o documento está incompleto. O uploader procura o ID do canal dentro do mapa `delegated_session_ids` do documento e usa-o como `pageId`/`onBehalfOfUser`; só a operação de Upload directo é bloqueada quando faltarem os dados técnicos. Não existem campos separados de cookies, INNERTUBE_API_KEY, chunk_size ou DELEGATED_SESSION_ID na UI.

Os dados são segredos de sessão. Os valores não aparecem em tabelas ou logs, o ficheiro é escrito com permissões locais restritas e não é incluído no Git. O Thunderbolt não extrai cookies automaticamente do browser e não envia as credenciais para o GitHub. O método é não oficial e pode deixar de funcionar se o YouTube alterar os endpoints internos.


Os adaptadores do MoneyPrinterTurbo e de publicação nas plataformas são ligados pelas configurações locais e pelos pontos de integração em `integrations/`. A UI não inventa dados quando um serviço externo ou credencial não está disponível.

## Idiomas e selector rápido da UI

O Thunderbolt mantém os idiomas históricos da criação de vídeos e acrescenta as dez opções canónicas do MoneyPrinterTurbo: **Inglês (en) 🇺🇸**, **Chinês Simplificado (zh) 🇨🇳**, **Alemão (de) 🇩🇪**, **Vietnamita (vi) 🇻🇳**, **Turco (tr) 🇹🇷**, **Português (pt) 🇧🇷**, **Russo (ru) 🇷🇺**, **Espanhol (es) 🇪🇸**, **Indonésio (id) 🇮🇩** e **Italiano (it) 🇮🇹**. Os códigos curtos são os valores persistidos e sincronizados com `ui.video_language` no `config.toml`; a bandeira e o nome são apenas a apresentação visual.

No topo da área principal da aplicação existe o menu nativo de idioma no padrão do MoneyPrinterTurbo, sem sobrepor o toolbar do Streamlit. O selector mostra o rótulo visível **Language** acima do campo, cada opção aparece como **nome do idioma + código**, e a bandeira é uma imagem SVG local real, não um emoji ou sigla dependente da fonte do sistema. Ao escolher outra opção, a preferência é guardada em `storage/state/settings.json` como `ui_language`, e a navegação lateral e o dashboard inicial actualizam-se sem alterar o idioma seleccionado para os vídeos. O indicador de execução, o botão **Deploy** e o menu principal do Streamlit permanecem totalmente nativos e clicáveis.

## Temas claro e escuro

A UI suporta os temas **Dark** e **Light** através de um selector explícito dentro da aplicação. **Dark é sempre o padrão** quando ainda não existe preferência guardada; o utilizador pode seleccionar **Light** no selector e essa escolha fica persistida em `storage/state/settings.json` como `ui_theme`. A configuração distribuída em `.streamlit/config.toml` também define `base = "dark"`, seguindo o padrão de configuração do [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo). O CSS próprio do Thunderbolt usa cores semânticas, `currentColor` e `color-mix` para que a sidebar, cartões, estados, radio cards, expanders e o hero de Cortes acompanhem o tema seleccionado. As cores de identidade dos chips de plataformas e das bandeiras são intencionais e não são substituídas pelo tema.

## Navegação da UI 0.2.88

A barra lateral mantém os níveis principais, nesta ordem: **Início**, **Niche Finder**, **Pipeline**, **Pipeline TikTok**, **Automação**, **Edição**, **AI Influencers** e **Configurações**. **Pipeline** é expansível e contém **Criação de Vídeos**, **Criação de Músicas**, **Roteiros** e **Upload**. **Automação** também é expansível e contém **Automação Youtube**. **Edição** é expansível e contém **Limpador de Metadados**, **Cortes**, **Editor Python** e **Download Mídia**, nessa ordem. **AI Influencers** é expansível e contém **Personagens**, **Redes Sociais**, **Tutorial Meta** e **Tutorial Supabase**, nessa ordem. **Niche Finder** é expansível e contém **Niche Finder Kaggle** e **Niche Finder Apify**. **Configurações** é expansível e contém **Canais Youtube**, **Blueprints Youtube**, **MCP**, **Contas Google**, **Configuração API** e **Notificações**. O Início reúne o dashboard e as filas do Pipeline, sem botões de acções rápidas.

A subaba **Tutorial Supabase** apresenta o guia de criação das tabelas `plans` e `posts` e do bucket `instagram-images`, com ligação para a fonte original no GitHub. As duas frases promocionais da comunidade foram omitidas. Todas as subabas internas também são localizadas pelo helper nativo de tabs:

O conteúdo interno das páginas também é localizado, não apenas a navegação: títulos, subtítulos, descrições, labels de campos, placeholders, opções de selectores, botões, avisos, mensagens de sucesso/erro, estados vazios, métricas, expanderes e blocos Markdown/HTML são traduzidos no idioma seleccionado através da camada global de conteúdo. Valores técnicos, chaves de estado, IDs de formulários, nomes de ficheiros, URLs e dados introduzidos pelo utilizador permanecem inalterados.

Todas as subabas internas também são localizadas pelo helper nativo de tabs: **Blueprints/Brandings**, **Pesquisa pública/Cadastro manual/Contas cadastradas**, **Upload/Biblioteca**, **Importar do YouTube/Canais em lote gmail/Cadastro manual**, **Criar vídeo/Vídeos**, **Novo roteiro/letra/Histórico guardado**, as três abas de análise de clusters, as quatro abas de cortes, **Vídeos/Código Python**, as quatro opções de Upload, **API Keys/Teste de vozes**, **Serviços e modelos/Fontes de materiais** e **Client MCP/Servidor MCP/Skill**. As chaves técnicas e a ordem funcional permanecem inalteradas.

Dentro de **Configurações > Contas Google**, a UI contém os cartões expansíveis de contas Google/YouTube, `sessionInfo`, documentos de Upload directo, `INNERTUBE_API_KEY`, o formulário **Adicionar outra conta Gmail** e a configuração global do YouTube (OAuth Client ID, OAuth Client Secret e YouTube Data API Key). A página **Configuração API** contém as restantes credenciais, providers, modelos, serviços, Nano Banana, TikTok e Postiz.

Em **Configuração API > API Keys**, a subaba **Fontes de materiais** segue o padrão do MoneyPrinterTurbo: seleccione uma fonte — **Pexels**, **Pixabay**, **Coverr**, **WaveSpeed AI**, **LoomLoom**, **TwelveLabs** ou **Ficheiros locais** — e introduza as API keys dessa fonte. **Adicionar outra chave** cria outra linha para a mesma fonte; as listas são guardadas separadamente por fonte, deduplicadas e exportadas para o `config.toml` do motor como arrays para rotação. A subaba não expõe endpoint, proxy, qualidade, codec, FFmpeg, Whisper, directório ou filtros técnicos: esses valores permanecem internalizados e a fonte local não requer credencial.

A subaba **Serviços e modelos** mantém as credenciais de providers e serviços que não são fontes de materiais. A chave `gemini_image_api_key` da Nano Banana continua separada de `gemini_api_key` do LLM textual. `INNERTUBE_API_KEY` permanece exclusivamente em **Configurações > Contas Google**, dentro da configuração da conta, e não é duplicada em API Keys.

A página **AI Influencers > Tutorial Meta** apresenta o guia de configuração de uma conta Instagram profissional e das credenciais Meta para automações com n8n, distribuído localmente em `seed/references/guide-instagram.md` e com ligação para a [fonte original no GitHub](https://github.com/gyoridavid/ai_agents_az/blob/main/episode_8/guide-instagram.md). A página **Configurações > Notificações** mantém um histórico persistente de conclusões e falhas, reconcilia estados escritos por componentes locais e disponibiliza um checkbox independente para cada operação mapeada.

A página **Edição > Download Mídia** utiliza a API Python do [yt-dlp](https://github.com/yt-dlp/yt-dlp) para descarregar vídeos e áudio de URLs públicas, com qualidade, contentor, formato de áudio, legendas, metadados, playlists, progresso e histórico local em `storage/downloads/` e `storage/state/media_downloads.json`. Conversão e combinação de streams podem exigir FFmpeg.

## Canais Youtube — edição por cartão e vídeos recentes

A página **Canais Youtube** mantém o cadastro e a importação existentes, mas cada cartão agora tem o botão **Editar**. O editor permite alterar nome, URL, handle, idioma, estilo wide, **Canais de Referência / Nicho**, **Prompts do Canal** (Blueprint padrão), **Narrador** (voz padrão), conta Google do Upload directo, descrição e Automação ON/horário. O nicho aparece imediatamente abaixo do nome do canal no cartão; quando não existe, a UI mostra **SEM NICHO CONFIGURADO**.

Os blocos do cartão usam a nomenclatura solicitada: **Prompts do Canal**, **Canais de Referência** e **Narrador**. Os botões de acção abrem o mesmo editor persistente, sem criar um segundo canal nem perder as associações existentes.

Abaixo do cartão, a secção **Últimos 10 vídeos publicados** usa o feed público RSS do YouTube, sem Data API Key. O carregamento ocorre quando se clica em **Actualizar últimos 10 vídeos**, evitando chamadas automáticas ao abrir a página. Os vídeos ficam guardados em `storage/state/channel_videos.json` e podem ser apresentados em **Lista** ou **Kanban**, nos grupos Planejamento, Produção, Finalizado e Agendado/Publicado. Cada vídeo tem **Editar vídeo** para alterar localmente o título, estado, data, URL e notas. A fonte pública não substitui o vídeo nem publica alterações no YouTube; os campos editáveis são overrides locais de gestão.

## Criação de Vídeos — geração editorial por canal

A aba **Criação de Vídeos** permite escrever manualmente o **Tópico ou briefing** ou usar **Gerar tópico/briefing com IA**. A geração usa o provider LLM configurado localmente em **Configuração API > API Keys > Serviços e modelos**, incorpora o Blueprint, a descrição, o idioma e a voz do canal e só ocorre depois do clique do utilizador. Se não houver credenciais ou modelo, a UI mostra uma mensagem accionável e não inventa conteúdo.

Entre **Canal** e **Estilo wide**, a UI mostra o Blueprint padrão resolvido do canal e a voz associada. Quando não existe configuração, apresenta **SEM BLUEPRINT CONFIGURADO**. Depois do briefing, **Gerar títulos e thumbnails com IA** cria pelo menos 20 candidatos de título e 3–5 variantes de thumbnail. Os títulos seguem as fórmulas e regras de curiosidade, especificidade, emoção, keyword inicial e humanização fornecidas nas referências empacotadas; as thumbnails guardam conceito, overlay de até quatro palavras, composição, cores, prompt e sinergia com o título.

O pacote criativo é persistido na task. O título escolhido fica pré-preenchido no Upload e a thumbnail é usada quando existe um ficheiro em `artifacts.thumbnail`. Sem provider de imagem configurado, a aplicação conserva o prompt e apresenta **Prompt de thumbnail pronto — imagem pendente de provider de imagem**, sem criar um PNG falso.

No modo **Lote geral**, o Thunderbolt remove a selecção parcial e processa automaticamente todos os canais cadastrados. É criada exactamente uma tarefa por canal, com briefing, título, thumbnail, Blueprint, voz e contexto próprios; o mesmo tópico nunca é reutilizado para todos os canais. A Automação diária usa o mesmo serviço no horário local de cada canal e não cria o placeholder antigo quando o provider LLM não está configurado.

## OpenAI/ NVIDIA NIM — descoberta de modelos

Em **Configuração API > API Keys > Serviços e modelos > LLM — providers e modelos**, a área anteriormente chamada **OpenAI — API key, Base URL e modelo** passa a chamar-se **OpenAI/ NVIDIA NIM — API key, Base URL e modelo**. O campo de modelo manual usa o parâmetro `help` suportado pelas versões do Streamlit instaladas pelo Thunderbolt, evitando o erro de argumento `help_text`. O provider interno continua a ser `openai`, para preservar a compatibilidade com o MoneyPrinterTurbo e com os restantes endpoints OpenAI-compatible.

A Base URL predefinida para NVIDIA NIM é `https://integrate.api.nvidia.com/v1`. Depois de inserir a API key, clique em **Consultar/actualizar modelos NIM**. O Thunderbolt consulta a Base URL acrescentando `/models`, lê os identificadores do formato OpenAI (`data[].id`) e apresenta-os num selector. O modelo escolhido é guardado em `openai_model_name` e é sincronizado para o `config.toml` do motor.

A consulta só é executada quando o utilizador carrega no botão; a aplicação não envia a API key ao abrir a página. Se o endpoint estiver offline, recusar a credencial ou não disponibilizar `/models`, a UI mostra o erro sem expor a API key e mantém a opção **Escrever modelo manualmente**. Também é possível manter um endpoint local NIM ou outro servidor OpenAI-compatible substituindo a Base URL.

## Contas Google/YouTube e OAuth local

Para autorizar uma conta, use no Google Cloud um cliente OAuth do tipo **Desktop app**. O Thunderbolt usa o loopback local determinístico `http://127.0.0.1:8765/`, abre o browser e guarda o token por conta. Se estiver a usar um cliente do tipo Web application, adicione exactamente essa URI em **Google Cloud > APIs e serviços > Credenciais > URIs de redireccionamento autorizados**; a URI deve incluir a porta e a barra final. O erro `400: redirect_uri_mismatch` significa que a URI registada no cliente Google não coincide exactamente com a enviada pela aplicação.

A área **Contas Google/YouTube — canais em lote** permite manter várias contas em cartões expansíveis com nome e e-mail. Cada cartão tem OAuth Client ID, OAuth Client Secret, sessionInfo e documento de Upload directo; o formulário separado **Adicionar outra conta Gmail** cria o documento padrão automaticamente. Use **Apagar conta** para remover a conta, os tokens e os dados directos associados. O sessionInfo é sincronizado com o documento JSON da própria conta; cookies e os restantes parâmetros de Upload directo permanecem apenas nesse documento.

## Instalação

Recomenda-se Python 3.11 ou superior e Node.js 18 ou superior.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows PowerShell:

```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```

## Execução

A porta da aplicação é `3030`:

```bash
python -m streamlit run app/main.py --server.port 3030
```

Ou através do launcher Node:

```bash
node scripts/cli.mjs --check
node scripts/cli.mjs
```

O comando normal inicia a UI e o worker local de Automação. O worker verifica o relógio local do computador e coloca na fila os lotes de canais com **Automação ON** quando o horário `HH:MM` coincide. Para executar apenas o worker, sem abrir a UI:

```bash
node scripts/cli.mjs worker
```

O pacote está publicado no npm como `@danhachuel/thunderbolt` e pode ser executado directamente via `npx`:

```bash
npx --yes @danhachuel/thunderbolt
```

Para instalar automaticamente o ambiente completo — Python 3.11+, ambiente virtual, dependências Python do Thunderbolt, dependências Python do MoneyPrinterTurbo, Streamlit e `imageio-ffmpeg` — execute:

```bash
npx --yes @danhachuel/thunderbolt install
```

Por defeito, o instalador cria automaticamente a pasta `~/.thunderbolt` — no Windows, `%LOCALAPPDATA%\\THUNDERBOLT` —, clona o MoneyPrinterTurbo para `THUNDERBOLT/MoneyPrinterTurbo`, cria o ambiente em `THUNDERBOLT/.venv` e guarda o estado em `THUNDERBOLT/storage`. No Windows, se Python 3.11+ não estiver instalado, o instalador tenta instalá-lo automaticamente através do `winget`. A instalação normal é segura para actualizações: preserva `storage`, Blueprints, Brandings, configurações e artefactos, removendo apenas `.venv` e o clone técnico do MoneyPrinterTurbo para os recriar. A antiga pasta sem dados do utilizador em `C:\Users\<utilizador>\AppData\Local\hermes` pode ser removida. O caminho `AppData\Local\npm-cache\_npx` é apenas cache temporária do npm, não é a pasta de instalação final. Para apagar dados intencionalmente, use o parâmetro explícito `--purge-data`; nunca o use numa actualização normal. Para usar uma cópia existente do MoneyPrinterTurbo:

```bash
MONEYPRINTER_PATH=/caminho/MoneyPrinterTurbo npx --yes @danhachuel/thunderbolt install
```

Para instalar apenas a UI sem clonar o MoneyPrinterTurbo:

```bash
npx --yes @danhachuel/thunderbolt install --skip-moneyprinter
```

Para verificar o ambiente sem iniciar a aplicação:

```bash
npx --yes @danhachuel/thunderbolt doctor
```

Para executar apenas o diagnóstico do ambiente:

```bash
npx --yes --package=@danhachuel/thunderbolt thunderbolt --check
```

Para instalar globalmente e disponibilizar o comando `thunderbolt`:

```bash
npm install --global @danhachuel/thunderbolt
thunderbolt
```

No Windows PowerShell, se `npx` for bloqueado por `npx.ps1`, use directamente `npx.cmd`:

```powershell
npx.cmd --yes @danhachuel/thunderbolt@0.2.77 install
npx.cmd --yes @danhachuel/thunderbolt@0.2.77 doctor
npx.cmd --yes @danhachuel/thunderbolt@0.2.77
```

Como alternativa, pode permitir scripts para o seu utilizador:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Ou apenas para a sessão actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Após `install`, o launcher usa o ambiente virtual instalado em `~/.thunderbolt/.venv` — no Windows, `%LOCALAPPDATA%\\THUNDERBOLT\\.venv` — e inicia a UI em `localhost:3030`. No Windows, a raiz é `%LOCALAPPDATA%\\THUNDERBOLT`; no computador indicado, o caminho será `C:\\Users\\danha\\AppData\\Local\\THUNDERBOLT`. Isto evita a redirecção de `HOME` que pode ocorrer no MobaXterm.
 O instalador não instala drivers de GPU, Docker, chaves de API, modelos Whisper ou credenciais de plataformas; esses componentes continuam dependentes do sistema e da configuração do utilizador. Para desenvolvimento a partir do clone, continue a usar `node scripts/cli.mjs`.

## Niche Finder

O menu expansível **Niche Finder** contém duas alternativas independentes. **Niche Finder Kaggle** é a página actual de análise e integra a lógica do projecto open source [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder) directamente no processo Streamlit. O Thunderbolt não inicia Flask, não abre uma porta adicional e não copia templates HTML ou D3. Ao abrir a página, o Thunderbolt não descarrega dados, não prepara o dataset e não executa análises. A instalação das dependências continua automática, mas a operação é manual: o utilizador define os parâmetros dentro da própria aba e clica em **Analisar Nichos**. Só nesse momento o KaggleHub prepara ou reutiliza a cache local do dataset e a análise é executada.

A interface apresenta dentro da aba os parâmetros da busca: número de clusters entre 2 e 10, suporte mínimo entre 0,01 e 0,50, país, categoria de engagement, intervalo de datas e tags. A página permanece sem resultados até o primeiro clique em **Analisar Nichos**; depois, se os parâmetros forem alterados, mostra os resultados anteriores e pede novo clique para aplicar os filtros actuais. O núcleo aplica normalização, filtros, `log1p`, `StandardScaler`, K-Means e FP-Growth. Os resultados aparecem em DataFrames para clusters, itemsets frequentes, regras de associação e dados analisados, acompanhados por uma visualização Plotly nativa e pesquisa de palavras nos clusters.

**Niche Finder Apify** é a segunda alternativa e não usa o dataset, filtros, execução ou resultados Kaggle. Define três palavras-chave, período, limite de resultados, Shorts, duração, idioma de legendas e ordenação; depois de clicar em **Pesquisar no Apify**, inicia o actor `streamers~youtube-scraper`, acompanha o run, carrega o dataset, normaliza vídeos, limpa SRT, calcula VSC Ratio e tenta resumir as transcrições com o provider LLM configurado. Os resultados ficam na sessão própria `niche_apify_results`, o histórico pequeno fica em `storage/state/niche_apify_runs.json` e existem exportações JSON/CSV. Configure o **Apify API Token** em **Configuração API > API Keys > Serviços e modelos**. As dependências adicionais são instaladas pelo fluxo normal do pacote: `requests`, `pandas` e os componentes já existentes da análise. Em instalações existentes, execute novamente `npx.cmd --yes @danhachuel/thunderbolt@0.2.77 install`; o instalador detecta e reutiliza componentes já válidos.

## Editor Python baseado no PYEdit

O **Editor Python** combina o recorte seguro do [PYEdit](https://github.com/Congren/PYEdit) com o armazenamento local do Thunderbolt. Na subaba **Vídeos**, pode escolher um vídeo já gerado e registado nos artefactos da pipeline, indicar qualquer pasta local de vídeos ou fazer upload manual. A página não inicia nenhuma edição ao ser aberta.

As operações disponíveis são cortar trecho, remover áudio, extrair áudio, substituir áudio, alterar velocidade e redimensionar vídeo. Cada operação cria uma cópia em `storage/python_editor/outputs/`, preserva o original, regista um histórico separado em `storage/state/python_editor_edits.json` e permite descarregar o resultado e um manifesto JSON. As operações usam FFmpeg local, aproveitando a detecção interna e o fallback `imageio-ffmpeg`; a subaba de fontes não expõe caminhos técnicos.

Na subaba **Código Python**, pode criar e guardar scripts em `storage/python_editor/scripts/` ou carregar scripts existentes. Por segurança, a UI não executa código Python, não possui botão de execução e não executa scripts automaticamente.

## Armazenamento local

O sistema cria automaticamente:

```text
storage/
├── blueprints/       # blueprints JSON lidos pela aba Blueprints
├── state/
│   ├── channels.json
│   ├── tasks.json
│   ├── queues.json
│   ├── batches.json
│   ├── uploads.json
│   ├── metadata_edits.json
│   ├── mcp_integrations.json
│   └── settings.json
├── music/             # músicas locais para o modo Apenas Música
├── voice_previews/    # amostras isoladas do teste de vozes
├── data/
│   └── niches/        # dados automáticos cacheados para o Niche Finder
├── skills/            # skill MoneyPrinterTurbo guardada pelo utilizador
├── metadata_cleaner/
│   ├── originals/    # cópias dos vídeos terceiros enviados
│   └── outputs/      # versões com metadados limpos
└── artifacts/        # ficheiros produzidos e caminhos referenciados
```

Para usar outro local, defina `THUNDERBOLT_STORAGE_DIR`. O estado é escrito de forma atómica e ficheiros JSON inválidos são preservados com cópia `.corrupt-*` antes de serem recriados.

## Blueprints Youtube e Brandings

Coloque ficheiros `.json` em `storage/blueprints/canais`, `storage/blueprints/nichos` ou `storage/blueprints/importados`. A aba **Blueprints Youtube** relê a pasta e mostra o conteúdo estruturado. A instalação já inclui 13 Blueprints seed, copiados apenas quando o ficheiro ainda não existe; actualizações não substituem Blueprints locais. Também é possível importar através do carregador da própria interface.

A mesma aba possui a subaba **Brandings**. No formulário **Criar blueprint a partir de link**, cole um link de canal, informe o **Nome do Blueprint**, o nicho e o idioma e escolha entre **Apenas Blueprint** ou **Blueprint + Branding completo**. O nome é guardado no campo `name` do JSON e também é usado no nome do ficheiro. O primeiro modo grava o blueprint forense local; o segundo grava também um ficheiro de Branding com identidade do canal, handle, descrição, hashtags, keywords, prompts de imagem de perfil e banner, direcção visual de thumbnails, assets e checklist de revisão.

O fluxo foi modelado a partir do blueprint de clonagem com Branding anexado, incluindo a distinção entre entrada de canal/vídeo, normalização do link, metadados de nicho/idioma, perfil do canal, estratégia de conteúdo, pesquisa, identidade visual e brand pack. Placeholders de serviços externos são tratados como configuração local; chaves presentes em workflows importados não devem ser commitadas.

## Limpador de Metadados

A aba **Limpador de Metadados** foi adaptada do workflow `YTBMetadataGenerator.json`. Ela recebe apenas um vídeo externo já pronto, guarda uma cópia original separada, remove os metadados do contentor com FFmpeg e grava uma nova cópia com título, descrição, links, timestamps, tags e outros campos opcionais. O original nunca é alterado e os vídeos produzidos pelas páginas **Criação de Vídeos** e **Criação de Músicas** não aparecem nesta área.

A descrição segue a composição do workflow de referência: preview, secção de links e capítulos/timestamps. O resultado inclui um manifesto JSON para utilizar os metadados num fluxo posterior de upload. A versão local não usa o trigger RSS, o Apify ou a actualização automática de um vídeo YouTube; em vez disso, o utilizador fornece directamente o vídeo terceiro e controla a edição antes de publicar.

## Cortes — Clip Generator local

A aba **Cortes** é um Clip Generator local inspirado no fluxo do [OpenShorts](https://github.com/mutonby/openshorts). Permite fazer upload de um vídeo, descarregar uma URL directa de vídeo, seleccionar um vídeo gerado pela pipeline ou escolher uma pasta local. O original é preservado em `storage/cuts/inputs/`.

O formulário apresenta os formatos **9:16 — Shorts/Reels/TikTok**, **1:1 — Feed posts** e **16:9 — YouTube/landscape**, além de opções avançadas para modo automático por segmentos locais ou corte manual, número de clips, durações mínima/máxima e intervalo de início/fim. A execução só começa depois da confirmação explícita de direitos e do clique em **Gerar Clips**.

Os clips são gerados localmente com FFmpeg, redimensionados para o formato escolhido sem ampliar desnecessariamente a fonte e guardados em `storage/cuts/runs/<id>/`. A página apresenta estado de análise, preview dos resultados, download individual, download ZIP, manifesto JSON e histórico em `storage/state/cuts_runs.json`. A selecção automática de momentos virais por IA permanece um ponto de extensão: sem transcrição/provider configurado, o modo manual continua disponível e não são inventados resultados.

## Canais YouTube

A aba **Canais Youtube** está dividida em dois fluxos independentes. Em **Importar do YouTube**, o método padrão **Página pública — sem API Key** consulta a página pública do canal e preenche nome, ID, handle, URL, descrição e thumbnail quando esses dados estão disponíveis. A opção **YouTube Data API — API Key opcional** pode ser escolhida para métricas oficiais quando uma **YouTube Data API Key própria** estiver configurada em **Configurações** ou em `YOUTUBE_API_KEY`; essa chave é distinta do OAuth Client ID e Client Secret.

Em **Cadastro manual**, nenhum pedido ao YouTube é feito e não existe qualquer dependência de API Key. O utilizador pode preencher nome, URL, handle, descrição, métricas, thumbnail, idioma, estilo, Blueprint padrão, voz padrão, `DELEGATED_SESSION_ID` e configuração de Automação. A importação pública nunca grava automaticamente: os dados aparecem num formulário de revisão antes de guardar. A resolução pública aceita URLs `/channel/UC...`, handles e subpáginas; quando existe um ID mas o HTML não traz todos os dados, tenta o feed RSS público. Se o YouTube responder que o canal não existe ou não fornecer metadados, a UI mostra uma mensagem clara e não mantém o formulário de uma pesquisa anterior. Cada cartão de canal tem **Activo** e, logo abaixo, **Apagar canal**, com confirmação; tarefas e artefactos não são apagados.

## Upload YouTube e fallback Postiz

O Upload usa como caminho **principal** a lógica do `PublishingSchedulingAgent` do [youtube-automation-agent](https://github.com/darkzOGx/youtube-automation-agent), adaptada para Python e executada dentro do processo Streamlit do Thunderbolt. Não é necessário instalar ou iniciar um segundo servidor Node. O fluxo valida o MP4 real, constrói `snippet/status`, faz upload resumível e tenta enviar thumbnail e legendas.

Na aba **Upload**, configure primeiro apenas o **YouTube OAuth Client ID** e o **YouTube OAuth Client Secret** em **Configurações**. Em seguida, use **Autorizar agente YouTube**. O navegador local abrirá a autorização Google e o token será guardado apenas em `storage/state/youtube_agent_tokens.json`. Se a publicação principal falhar, o Thunderbolt tenta automaticamente o **OAuth directo de redundância**, usando o token local compatível; a Data API Key nunca é usada para autorizar ou publicar.

Use **Autorizar fallback OAuth** apenas se precisar de uma autorização separada para o caminho de redundância. Os resultados guardam no histórico local qual mecanismo foi utilizado e as tentativas realizadas, sem guardar segredos.

A subaba **Postiz**, dentro de **Upload**, permite carregar as integrações ligadas através de `GET /integrations`, enviar um MP4 para `POST /upload` e criar o post YouTube em `POST /posts`. A API key é enviada como valor bruto do cabeçalho `Authorization`; a base cloud é `https://api.postiz.com/public/v1` e pode ser substituída por uma instalação self-hosted. O modo MCP guarda também a URL Streamable HTTP configurável para uso futuro/alternativo.

O botão principal de YouTube usa a ordem **API Oficial → Upload directo → Postiz**. A API Oficial tem um contador local de cinco envios bem-sucedidos por dia por conta Gmail; quando a quota é atingida, ou o método falha, o Thunderbolt tenta o documento de sessão do Upload directo. Só depois de esse caminho falhar tenta o Postiz, desde que esteja activo, tenha API key e tenha um ID de integração configurado.

A subaba **Upload directo** adapta o [YouTube-Video-Upload-Frontend-Api](https://github.com/Nojus10/YouTube-Video-Upload-Frontend-Api). Ela usa cookies, `sessionInfo`, `INNERTUBE_API_KEY` e `DELEGATED_SESSION_ID` fornecidos manualmente pelo utilizador, cria o vídeo através do endpoint interno e envia o ficheiro em chunks de 256 KiB. Este caminho é experimental, não extrai cookies automaticamente e fica separado do agente YouTube principal.

## Pipeline: Criação de Vídeos, Criação de Músicas e Automação Youtube

Em **Criação de Vídeos**, o estilo visual `Pexels/Pixabay` é o modo de materiais, `full_ia` abre o selector **Estilo IA** com os 12 estilos solicitados e **Apenas Música** exige um áudio local, um upload musical ou um pedido ao endpoint Suno configurado. **Criação de Músicas** reutiliza o mesmo conteúdo e formulário com título próprio. Neste último modo, a task fica com `background_mode=none`: não são gerados fundos Pexels/Pixabay nem fundos IA.

A subaba **Roteiros**, entre **Criação de Músicas** e **Upload**, permite escolher um canal opcional, um Blueprint, o tipo **Roteiro de vídeo** ou **Letra de música**, idioma, briefing e notas de estrutura. O botão **Gerar com IA a partir do Blueprint** usa o provider LLM configurado, devolve um rascunho Markdown editável e só guarda o documento quando o utilizador confirmar. Os ficheiros ficam em `storage/scripts/` e o índice do histórico em `storage/state/scripts.json`; a própria página mostra o caminho absoluto correspondente ao storage local.

Na subaba **Vídeos** de **Criação de Vídeos**, a frase `Os vídeos são guardados em <storage>/videos` identifica a pasta real onde os artefactos de vídeo devem ser procurados.

O agente musical guarda os ficheiros em `storage/music/`, aceita formatos de áudio comuns e pode descarregar uma URL de áudio devolvida por um endpoint Suno compatível. Em **Canais Youtube**, abra **Definir Blueprint e voz padrão** no cartão do canal para guardar os defaults; em **Automação Youtube**, os mesmos dois selectores aparecem no cartão e são sincronizados. Esses valores são usados automaticamente em novas tarefas criadas para o canal. A aba **Automação Youtube** também guarda `Automação ON` e um horário diário `HH:MM` por canal e lista os vídeos cadastrados; por definição, esta entrega não executa workers de fundo.

## Teste de vozes

A área **Configurações > Configuração API > Teste de vozes** é isolada da pipeline.
 Permite escolher Edge/Azure Speech ou um provider HTTP configurado, seleccionar voz/ID, alterar a velocidade, sintetizar uma amostra, reproduzi-la e descarregá-la. O áudio é guardado em `storage/voice_previews/` e nunca altera vídeos ou tarefas. Se uma instalação antiga não tiver `edge-tts`, execute `npx.cmd --yes @danhachuel/thunderbolt install`; o instalador detecta a dependência em falta sem reinstalar componentes válidos.

## MCP e integrações externas opcionais

A aba **MCP** está organizada em três subabas independentes. **Client MCP** lista **Short Video Maker**, **AutoVio**, **OpenMontage** e **OpenCut** com links oficiais, protocolo/capacidade conhecida, porta local editável, detecção passiva e toggle **Activo**. Os repositórios externos não são clonados, instalados ou incluídos no pacote npm do Thunderbolt.

As portas iniciais são `3123` para Short Video Maker, `3001` para a API backend do AutoVio, `8000` como referência editável para OpenMontage — que não documenta uma porta HTTP padrão — e `8787` para a API do OpenCut, cujo frontend de desenvolvimento usa `5173`. A detecção do Client MCP apenas consulta `localhost` e nunca inicia processos externos.

**Servidor MCP** activa, mediante confirmação explícita na UI, um endpoint local em `http://127.0.0.1:3031/mcp`. O endpoint usa JSON-RPC sobre HTTP POST, disponibiliza ferramentas de leitura para estado da pipeline, canais, vídeos e Blueprints e exige um token quando o host é exposto fora do computador local. As ferramentas de escrita ficam desactivadas por padrão; quando o utilizador as activa, o agente pode criar lotes de vídeos através de uma ferramenta controlada. O endpoint `/health` serve apenas para verificação de disponibilidade.

**Skill** contém exclusivamente os botões para guardar localmente ou descarregar `moneyprinterturbo-video.md`. A skill é guardada em `storage/skills/` e não é misturada com o catálogo de clientes MCP.


## TikTok

A subaba **Vídeos**, dentro de **Criação de Vídeos** ou **Criação de Músicas**, mostra o backlog e permite iniciar/parar tarefas; deixou de existir como botão principal na barra lateral.

As credenciais do TikTok ficam em **Configuração API > API Keys > Serviços e modelos**, no expander próprio de TikTok.
 Para YouTube, o bloco principal pede o OAuth Client ID e Client Secret; a Data API Key, se usada, fica numa área opcional separada. Client ID + Client Secret não formam uma Data API Key nem um token OAuth.
 Redirect URI, scopes, autorização OAuth e tokens são geridos no TikTok for Developers Playground. O adaptador rejeita o upload quando faltam credenciais ou OAuth, em vez de indicar sucesso falso.

## Segurança

Não coloque chaves, cookies, tokens YouTube ou segredos TikTok no Git. Use a configuração local, variáveis de ambiente ou um ficheiro fora do repositório. O `.gitignore` exclui o storage de estado real, ambientes virtuais e ficheiros de segredo. O adaptador interno foi baseado na lógica publicada sob licença MIT do [youtube-automation-agent](https://github.com/darkzOGx/youtube-automation-agent).
