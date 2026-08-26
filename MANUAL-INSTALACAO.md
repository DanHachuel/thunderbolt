# Manual de Instalação — Thunderbolt UI

Este manual descreve a instalação local da UI Thunderbolt, baseada no MoneyPrinterTurbo, utilizando o pacote npm `@danhachuel/thunderbolt`. O fluxo recomendado instala automaticamente o ambiente Python, as dependências da aplicação, as dependências do MoneyPrinterTurbo, o Streamlit e o suporte FFmpeg através de `imageio-ffmpeg`.

> **Versão deste manual:** 0.3.39
> **Pacote npm:** `@danhachuel/thunderbolt`
> **Porta padrão da UI:** `localhost:3030`  
> **Repositório:** [github.com/DanHachuel/thunderbolt](https://github.com/DanHachuel/thunderbolt)

## 1. O que será instalado

A instalação assistida cria um ambiente local separado para evitar misturar as dependências do Thunderbolt com outros projectos Python.

| Componente | Local ou comportamento padrão |
|---|---|
| Python | Python 3.11 ou superior já instalado no sistema |
| Ambiente virtual | `~/.thunderbolt/.venv` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\\.venv`) |
| MoneyPrinterTurbo | `~/.thunderbolt/MoneyPrinterTurbo` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\\MoneyPrinterTurbo`) |
| Storage Thunderbolt | `~/.thunderbolt/storage` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\\storage`) |
| Dependências Thunderbolt | Instaladas a partir do `requirements.txt` incluído no pacote |
| Dependências MoneyPrinterTurbo | Instaladas a partir do `requirements.txt` do repositório oficial |
| Streamlit | Instalado como dependência Python |
| FFmpeg | Disponibilizado pelo pacote Python `imageio-ffmpeg` |
| Porta da aplicação | `3030`, configurável com `THUNDERBOLT_PORT` |

A aplicação não instala drivers de GPU, Docker, modelos Whisper ou credenciais externas. As chaves de API do MoneyPrinterTurbo são configuradas na aba **Configurações** e sincronizadas com o `config.toml` do clone local. O idioma da interface e o idioma dos vídeos são preferências independentes.

O MoneyPrinterTurbo declara Python 3.11 ou superior como requisito e documenta a instalação com `uv` ou com `venv + pip`. A aplicação segue o mesmo princípio e adiciona um instalador assistido próprio.[1]

## 2. Pré-requisitos

Instale os seguintes componentes antes de executar o instalador:

| Pré-requisito | Necessário | Observação |
|---|---:|---|
| Python 3.11+ | Sim | No Windows, o instalador tenta instalar automaticamente via winget; noutros sistemas deve estar instalado |
| npm | Sim | Normalmente vem incluído com Node.js |
| Node.js 18+ | Sim | Necessário para executar o pacote via `npx` |
| Git | Sim para instalação automática do MoneyPrinterTurbo | Pode ser evitado usando `--skip-moneyprinter` ou `MONEYPRINTER_PATH` |
| winget | Recomendado no Windows | Permite ao instalador instalar Python 3.11 automaticamente; vem normalmente com Windows 10/11 actualizado |
| Internet | Sim durante a instalação | Necessária para npm, GitHub e PyPI |
| Espaço em disco | Recomendado 5 GB ou mais | Dependências, caches, modelos e artefactos podem ocupar espaço adicional |

A instalação local do MoneyPrinterTurbo recomenda Windows 10+, macOS 11+ ou uma distribuição Linux corrente. Python 3.11 é a opção de referência do projecto base.[1]

### 2.1 Windows: PowerShell bloqueia npx.ps1

Em algumas instalações Windows, o PowerShell bloqueia o wrapper `npx.ps1` por causa da política de execução de scripts. Nesse caso, use `npx.cmd`, que executa o mesmo npm/npx sem depender do wrapper PowerShell:

```powershell
npx.cmd --yes @danhachuel/thunderbolt install
npx.cmd --yes @danhachuel/thunderbolt doctor
npx.cmd --yes @danhachuel/thunderbolt
```

Se preferir corrigir a política para o seu utilizador:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Para permitir apenas durante a sessão actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Não é necessário usar `Unrestricted`. Se estiver num terminal MobaXterm ou CMD, também pode executar:

```cmd
cmd /c npx.cmd --yes @danhachuel/thunderbolt install
```

### 2.2 Confirmar versões

Linux ou macOS:

```bash
node --version
npm --version
python3 --version
git --version
```

Windows PowerShell:

```powershell
node --version
npm --version
py --version
git --version
```

O Python deve apresentar a versão `3.11` ou superior. Se estiver no Windows sem Python, o instalador tenta executar automaticamente `winget install --exact --id Python.Python.3.11`. Se `winget` não estiver disponível, instale o App Installer/Microsoft Store ou Python a partir de [python.org](https://www.python.org/downloads/windows/) e repita a instalação. Em macOS/Linux, o instalador não assume permissões administrativas para instalar Python no sistema; instale-o pelo gestor de pacotes ou use `THUNDERBOLT_PYTHON`.

## 3. Instalação recomendada via npx

Execute:

Windows PowerShell ou MobaXterm:

```powershell
npx.cmd --yes @danhachuel/thunderbolt@0.3.39 install
```

Linux/macOS:

```bash
npx --yes @danhachuel/thunderbolt@0.3.39 install
```

A instalação normal é **segura para actualizações**: preserva `storage`, Blueprints, Brandings, configurações e artefactos do utilizador. Remove apenas `.venv`, o clone técnico do MoneyPrinterTurbo e dependências que serão recriadas. Uma pasta antiga sem dados do utilizador, como `C:\Users\<utilizador>\AppData\Local\hermes` da tentativa incompleta, pode ser removida; uma pasta antiga que contenha Blueprints, Brandings ou storage é preservada e apenas avisada no terminal. Feche processos Python, Node, Streamlit e MobaXterm que estejam a usar as pastas antes de executar.

Se quiser apagar absolutamente tudo de forma intencional, use o comando destrutivo separado:

```powershell
npx.cmd --yes --prefer-online @danhachuel/thunderbolt@VERSAO install --purge-data
```

O parâmetro `--purge-data` apaga Blueprints, Brandings, configurações, storage e artefactos locais. Não o use numa actualização normal.

No Windows, a instalação cria automaticamente `C:\\Users\\danha\\AppData\\Local\\THUNDERBOLT\\storage` quando executada pela conta `danha`; para outras contas, `%LOCALAPPDATA%\\THUNDERBOLT\\storage` aponta para a pasta equivalente do utilizador.

O instalador irá:

1. procurar Python 3.11 ou superior;
2. se estiver no Windows e Python não existir, instalar Python 3.11 automaticamente pelo `winget`;
3. criar o ambiente virtual `~/.thunderbolt/.venv` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\\.venv`);
4. clonar o repositório oficial MoneyPrinterTurbo para `~/.thunderbolt/MoneyPrinterTurbo` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\\MoneyPrinterTurbo`);
5. instalar as dependências do Thunderbolt;
6. instalar as dependências Python do MoneyPrinterTurbo;
7. instalar `imageio-ffmpeg` para disponibilizar FFmpeg no ambiente Python;
8. criar `~/.thunderbolt/storage/state/settings.json` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\storage\state\settings.json`);
9. registar o caminho local do MoneyPrinterTurbo;
10. deixar o ambiente pronto para o comando de arranque.

No Windows, o caminho padrão é construído a partir de `USERPROFILE`, `HOMEDRIVE/HOMEPATH` ou, em último recurso, `HOME`. O instalador remove o redireccionamento de MobaXterm (`AppData\Local\hermes` ou `AppData\Roaming\MobaXterm\home`) e usa `%LOCALAPPDATA%\\THUNDERBOLT`, salvo se `THUNDERBOLT_HOME` for definido explicitamente. A pasta `AppData\Local\npm-cache\_npx` é apenas cache temporária do npm e não é a pasta de instalação final. O fluxo normal preserva os dados; somente `--purge-data` activa a limpeza destrutiva.

A instalação pode demorar alguns minutos, especialmente durante a instalação de `faster-whisper` e de bibliotecas de processamento de vídeo. O caminho do pacote dentro de `AppData\Local\npm-cache\_npx` que aparece no log é temporário; o launcher usa esse pacote apenas para executar o instalador e os ficheiros finais ficam em `%LOCALAPPDATA%\\THUNDERBOLT`.

### 3.1 Usar o instalador com uma cópia existente do MoneyPrinterTurbo

Se já possui o MoneyPrinterTurbo clonado, indique o caminho.

Linux ou macOS:

```bash
MONEYPRINTER_PATH=/caminho/para/MoneyPrinterTurbo \
  npx --yes @danhachuel/thunderbolt install
```

Windows PowerShell:

```powershell
$env:MONEYPRINTER_PATH="C:\caminho\MoneyPrinterTurbo"
npx --yes @danhachuel/thunderbolt install
```

O instalador reutiliza a pasta existente e instala as suas dependências no ambiente virtual do Thunderbolt.

### 3.2 Instalar apenas a UI

Se pretende testar a interface sem clonar o MoneyPrinterTurbo:

```bash
npx --yes @danhachuel/thunderbolt install --skip-moneyprinter
```

Este modo instala o ambiente Python e as dependências da UI, mas não instala o conjunto de dependências do MoneyPrinterTurbo nem configura a integração local com ele.

### 3.3 Controlar os caminhos de instalação

É possível alterar o directório principal e o ambiente Python:

Linux ou macOS:

```bash
THUNDERBOLT_HOME=/caminho/thunderbolt \
MONEYPRINTER_PATH=/caminho/MoneyPrinterTurbo \
THUNDERBOLT_VENV=/caminho/thunderbolt/.venv \
npx --yes @danhachuel/thunderbolt install
```

Windows PowerShell:

```powershell
$env:THUNDERBOLT_HOME="C:\ContentHermes"
$env:MONEYPRINTER_PATH="C:\MoneyPrinterTurbo"
$env:THUNDERBOLT_VENV="C:\ContentHermes\.venv"
npx --yes @danhachuel/thunderbolt install
```

## Idiomas e selector de bandeira

O Thunderbolt inclui as dez opções de idioma usadas pelo fluxo MoneyPrinterTurbo: **Inglês (en) 🇺🇸**, **Chinês Simplificado (zh) 🇨🇳**, **Alemão (de) 🇩🇪**, **Vietnamita (vi) 🇻🇳**, **Turco (tr) 🇹🇷**, **Português (pt) 🇧🇷**, **Russo (ru) 🇷🇺**, **Espanhol (es) 🇪🇸**, **Indonésio (id) 🇮🇩** e **Italiano (it) 🇮🇹**. A criação de vídeos mantém ainda os rótulos históricos para não invalidar Blueprints e tarefas antigas.

No topo da área principal, o menu nativo de idioma segue o padrão do MoneyPrinterTurbo e mostra o rótulo **Language** acima do selector. Cada opção apresenta o nome e o código, acompanhados por uma imagem SVG local da bandeira; não depende de emojis nem de siglas da fonte do sistema. A escolha fica guardada como `ui_language` em `storage/state/settings.json` e, quando existe um caminho MoneyPrinterTurbo configurado, é sincronizada com `[ui].language` no `config.toml`. O dashboard inicial, o interior das páginas e as abas da barra lateral usam o mesmo idioma seleccionado. O toolbar do Streamlit não é manipulado: o indicador de execução, **Deploy** e o menu de três pontos permanecem nativos e clicáveis. Na Criação de Vídeos e em Roteiros, o selector **Script Language** mantém o catálogo de vídeo independente, mas guarda o código curto; essa escolha é sincronizada com `[ui].video_language`.

Todas as subabas internas e o conteúdo das páginas também são traduzidos nos dez idiomas. Isso inclui títulos, subtítulos, descrições, labels, placeholders, opções, botões, avisos, mensagens de sucesso/erro, estados vazios, métricas, expanderes e blocos Markdown/HTML. Valores técnicos, IDs, URLs, nomes de ficheiros e dados introduzidos pelo utilizador permanecem inalterados. As subabas internas traduzidas incluem: Blueprints/Brandings, Pesquisa pública/Cadastro manual/Contas cadastradas, Upload/Biblioteca, Importar do YouTube/Canais em lote gmail/Cadastro manual, Criar vídeo/Vídeos, Novo roteiro/letra/Histórico guardado, análise de clusters, edição de cortes, Vídeos/Código Python, as quatro opções de Upload, API Keys/Teste de vozes, Serviços e modelos/Fontes de materiais, Client MCP/Servidor MCP/Skill e Notificações Geral/Telegram. A ordem e as chaves internas dos widgets permanecem estáveis.

### Temas Light e Dark

A aplicação usa o mecanismo nativo de temas do Streamlit e é distribuída com `.streamlit/config.toml`, seguindo o padrão de configuração do [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo). O ficheiro disponibiliza as variantes nomeadas **Dark** e **Light**. A alternância entre elas fica exclusivamente no menu nativo de três pontos do Streamlit, no local original do toolbar; não existe um selector Theme dentro da página. Os componentes próprios da UI herdam as cores do tema activo através de `currentColor` e `color-mix`. O toolbar nativo, o indicador de execução, **Deploy** e o menu principal continuam sem sobreposições CSS.

## 4. Diagnóstico antes de iniciar

Depois da instalação, execute:

```bash
npx --yes @danhachuel/thunderbolt doctor
```

Também é possível usar:

```bash
npx --yes --package=@danhachuel/thunderbolt thunderbolt --check
```

Uma saída saudável apresenta versões de Python e Streamlit e um caminho de FFmpeg. Por exemplo:

```text
Ambiente OK. Python: 3.11.x; Streamlit: 1.x.x; FFmpeg: /.../ffmpeg
```

Se o diagnóstico indicar que FFmpeg não foi detectado, execute novamente a instalação ou verifique se `imageio-ffmpeg` está presente no ambiente virtual.

## 5. Iniciar a aplicação

Depois de instalar e diagnosticar:

```bash
npx --yes @danhachuel/thunderbolt
```

O comando normal inicia a UI e o worker local de Automação. O worker verifica o relógio local do computador e cria os lotes dos canais com **Automação ON** quando o horário `HH:MM` coincide. Para executar apenas o worker, sem abrir a UI:

```bash
npx --yes @danhachuel/thunderbolt worker
```

Abra no navegador:

```text
http://localhost:3030
```

O launcher usa o ambiente virtual em `~/.thunderbolt/.venv` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\\.venv`) quando ele existe. Se for necessário executar numa porta diferente:

Linux ou macOS:

```bash
THUNDERBOLT_PORT=3040 npx --yes @danhachuel/thunderbolt
```

Windows PowerShell:

```powershell
$env:THUNDERBOLT_PORT="3040"
npx --yes @danhachuel/thunderbolt
```

Para parar a aplicação, volte ao terminal e pressione `Ctrl+C`.

## 6. Instalação global via npm

Como alternativa ao `npx`, instale o comando globalmente:

```bash
npm install --global @danhachuel/thunderbolt
```

Depois execute:

```bash
thunderbolt
```

Diagnóstico:

```bash
thunderbolt doctor
```

Instalação assistida:

```bash
thunderbolt install
```

A instalação global controla apenas o launcher Node.js. O ambiente Python continua a ser criado em `~/.thunderbolt/.venv` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\\.venv`).

## 7. Instalação manual para desenvolvimento

Use esta opção quando quiser trabalhar directamente a partir do repositório GitHub.

```bash
git clone https://github.com/DanHachuel/thunderbolt.git
cd thunderbolt
```

### 7.1 Linux ou macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para instalar também o MoneyPrinterTurbo:

```bash
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
python -m pip install -r MoneyPrinterTurbo/requirements.txt
```

Inicie a UI:

```bash
python -m streamlit run app/main.py --server.port 3030
```

Ou use o launcher local:

```bash
node scripts/cli.mjs --check
node scripts/cli.mjs
```

### 7.2 Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Para instalar também o MoneyPrinterTurbo:

```powershell
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
python -m pip install -r MoneyPrinterTurbo\requirements.txt
```

Inicie a UI:

```powershell
python -m streamlit run app/main.py --server.port 3030
```

Se o PowerShell bloquear a activação do ambiente virtual, execute uma vez, com uma política adequada ao seu utilizador:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 8. Configuração inicial da UI

Na primeira execução, a barra lateral apresenta **Início**, **Niche Finder**, **Pipeline Vídeos**, **Pipeline Música**, **Automação**, **Edição**, **AI Influencers** e **Configurações**. O menu expansível **Pipeline Música** contém **Criação de Músicas** e **Upload Música**, cuja página tem as subabas **JewelMusic**, **Pushtunes** e **ytmusicapi**. O menu expansível **Pipeline Vídeos** contém **Criação de Vídeos**, **Backlog Vídeos**, **Roteiros**, **Thumbnails** e **Upload**. O menu expansível **Automação** contém a subaba **Automação Youtube**. O menu expansível **Edição** contém **Limpador de Metadados**, **Cortes** e **Editor Python**. O menu expansível **AI Influencers** contém **Personagens**, **Redes Sociais**, **Tutorial Meta** e **Tutorial Supabase**, nessa ordem. O **Tutorial Meta** apresenta o guia de configuração de Instagram e credenciais Meta para automações com n8n. O **Tutorial Supabase** apresenta o guia para criar as tabelas `plans` e `posts` e o bucket `instagram-images`, incluindo a ligação para a fonte original no GitHub; as duas frases promocionais da comunidade foram omitidas. O menu expansível **Niche Finder** contém **Niche Finder Kaggle** e **Niche Finder Apify**. A aba **Niche Finder Kaggle** mantém a análise do dataset Kaggle; **Niche Finder Apify** é uma segunda alternativa independente, com actor, dataset, parâmetros, credencial, execução e resultados próprios. O menu **Pipeline Vídeos** contém **Criação de Vídeos**, **Backlog Vídeos**, **Roteiros**, **Thumbnails** e **Upload**. O menu **Pipeline Música** contém **Criação de Músicas** e **Upload Música**. O menu **Configurações** contém **Canais Youtube**, **Blueprints Youtube**, **MCP**, **Contas Google**, **Configuração API** e **Notificações**. Abra **Configurações > Contas Google** para gerir contas Google/YouTube, cartões, documentos de Upload directo, `sessionInfo` por conta, a `INNERTUBE_API_KEY` global, contas adicionais e a configuração global do YouTube. Abra **Configurações > Configuração API** para configurar as restantes API Keys, providers, modelos, serviços e o **Teste de vozes**. A página **Configurações > Notificações** contém as subabas **Geral** e **Telegram**. A subaba Geral mantém o histórico e as preferências dos eventos locais; a subaba Telegram envia esses mesmos eventos para o Chat ID configurado. A página **Pipeline Música > Upload Música** contém as subabas **JewelMusic**, **Pushtunes** e **ytmusicapi**. Para YouTube, preencha primeiro o par **OAuth Client ID + OAuth Client Secret** em **Contas Google** se pretende autorizar uploads. A **YouTube Data API Key** é uma credencial Google Cloud diferente e fica em **Contas Google**, apenas para o método oficial de métricas; Client ID + Client Secret não formam uma API Key.

| Configuração | Finalidade |
|---|---|
| Porta Streamlit | Definir a porta local da UI |
| Pasta MoneyPrinterTurbo | Indicar o clone local que será sincronizado com `config.toml` |
| JewelMusic API Key/Base URL | Configurar o upload de tracks e os metadados de título, artista, álbum, ano e género |
| Pushtunes | Escolher fonte, destino, operação, perfil/CSV, browser.json, playlist e credenciais Spotify para sincronização de biblioteca |
| ytmusicapi browser.json | Autenticar uploads directos para YouTube Music através de uma sessão local de browser |
| YouTube Data API Key (opcional) | Em **Configurações > Contas Google**, permitir o método oficial Data API para métricas públicas; não é necessária para a página pública nem para OAuth |
| YouTube OAuth Client ID | Em **Configurações > Contas Google**, identificar a aplicação OAuth 2.0 do Google para autorizar operações autenticadas, como upload |
| YouTube OAuth Client Secret | Secret do mesmo cliente OAuth 2.0; não é uma Data API Key nem um token de acesso |
| OpenAI/ NVIDIA NIM API key | Credencial do OpenAI ou NVIDIA Build/NIM, guardada apenas no storage local |
| OpenAI/ NVIDIA NIM Base URL | Endpoint OpenAI-compatible; por padrão `https://integrate.api.nvidia.com/v1` |
| OpenAI/ NVIDIA NIM modelo | Selector carregado de `/models` ou campo manual de fallback; guardado como `openai_model_name` |
| YouTube upload principal | Lógica do `youtube-automation-agent` adaptada e executada dentro do Thunderbolt |
| OAuth directo de redundância | Caminho alternativo accionado automaticamente se o agente falhar |
| TikTok Client ID/Secret | Credenciais da aplicação; Redirect URI, scopes e autorização ficam no TikTok for Developers Playground |
| Kaggle Username | Nome da conta Kaggle usada para publicar e executar a kernel remota |
| Kaggle API Key | Chave da conta Kaggle, guardada mascarada apenas em `storage/state/settings.json` |
| Slug da kernel Kaggle | Identificador da kernel remota, por padrão `thunderbolt-niche-finder` |
| Apify API Token | Token pessoal da Apify, guardado mascarado no storage local e usado apenas pela alternativa Apify |
| Apify Actor ID | Actor usado pela alternativa Apify, por padrão `streamers~youtube-scraper` |
| Apify polling/timeout | Intervalo de consulta e limite máximo da execução do actor |
| Telegram Bot Token | Token criado pelo BotFather, guardado apenas no storage local |
| Telegram Chat ID | Utilizador, grupo ou canal que receberá as notificações |
| Telegram Proxy | Proxy HTTP/HTTPS/SOCKS opcional para ambientes sem acesso directo |
| Telegram timeout | Limite de espera de cada envio, entre 5 e 120 segundos |

### Execução do pipeline de vídeos e acompanhamento

Ao clicar em **Start** no **Backlog Vídeos**, a tarefa passa para `doing` e é processada pelo worker de pipeline iniciado pelo launcher normal. O worker grava o estado em `storage/state/pipeline_worker.json` e actualiza `updated_at`, a etapa e a percentagem em `storage/state/tasks.json`. O painel do Backlog consulta esse estado automaticamente a cada cinco segundos e mostra o worker, a etapa corrente, a percentagem, a idade da actualização e a mensagem de erro quando existe.

A percentagem representa o avanço conhecido do pipeline: tema, roteiro, título/keywords, thumbnail, vídeo e upload. Durante a chamada longa ao MoneyPrinterTurbo, a UI mantém um heartbeat a cada cinco segundos e avança apenas dentro da faixa reservada à geração do vídeo; não apresenta 100% antes de existir um MP4 válido. O worker passa explicitamente a **Pasta do motor de vídeo** configurada na UI ao helper, por isso o clone usado, os logs e o manifesto pertencem à instalação seleccionada pelo utilizador.

Uma execução da etapa Vídeo tem limite de 20 minutos. Se o processo externo terminar com erro, exceder o limite, devolver um resultado inválido ou ocorrer uma excepção inesperada, a tarefa é marcada como `failed`, com a etapa em `failed_stage`. As últimas linhas devolvidas pelo helper, sem as credenciais configuradas, são guardadas num artefacto `video-diagnostics` e as referências `video_log`/`video_result` ficam associadas à tarefa. Se o utilizador clicar em **Stop**, a tarefa passa para `blocked`, o subprocesso é terminado cooperativamente e o worker não substitui esse estado por `failed`.

Se o launcher ou o worker for encerrado abruptamente, uma tarefa `doing` sem actualização durante 25 minutos é recuperada e marcada como `failed`, evitando estados indefinidos eternos. Para processar novas tarefas, deixe a aplicação iniciada com o comando normal; o painel avisa quando não existe heartbeat recente do worker.

O **Backlog Vídeos** e a lista **Automação > Automação Youtube > Vídeos cadastrados** usam o mesmo catálogo completo de `storage/state/tasks.json`. Por isso, tarefas criadas manualmente e tarefas criadas pelo worker diário aparecem nos dois locais, sem filtragem implícita por origem. O filtro do Backlog mostra os estados conhecidos e inclui automaticamente estados adicionais encontrados nos dados.

Nos dois cards, o bloco de estado apresenta o valor técnico, o rótulo legível, a barra de progresso e a mensagem de erro quando existir. O bloco **Formato** resolve nesta ordem `format`, `style_wide`, `style` e, por fim, `wide`, mantendo a apresentação de formatos como `wide`, `shorts`, `music` ou `full_ia` mesmo em tarefas antigas.

### Upload Música — JewelMusic, Pushtunes e ytmusicapi

A área **Pipeline Música > Upload Música** separa três métodos com contratos diferentes. Em **JewelMusic**, active a integração, introduza a API Key fornecida pelo dashboard da JewelMusic e confirme a Base URL oficial `https://api.jewelmusic.com` e, se necessário, configure proxy e timeout. Carregue ou seleccione um ficheiro de música, indique artista e título e clique em **Enviar música para JewelMusic**. O teste de ligação consulta `/v1/ping`; o upload envia `multipart/form-data` para `/v1/tracks/upload` com os metadados preenchidos.

Em **Pushtunes**, active a integração e seleccione uma fonte, um destino e uma operação (`tracks`, `albums` ou `playlist`). Para uma fonte CSV, carregue o ficheiro na própria subaba; para YouTube Music, indique o `browser.json`; para Spotify, preencha Client ID, Client Secret e Redirect URI ou use a configuração que o Pushtunes espera; para playlists, preencha o nome. Perfis `.toml` podem fornecer parâmetros adicionais. O botão de validação não sincroniza nada. O botão de execução chama o CLI do Pushtunes sem shell, com argumentos separados, e grava o resultado no histórico local. Pushtunes é uma sincronização de biblioteca, não um upload de bytes de um MP3 isolado.

Em **ytmusicapi**, carregue um `browser.json` ou indique o caminho de um ficheiro existente, active a integração e seleccione uma música local. O teste consulta a biblioteca de uploads sem escrever; o envio usa `upload_song` e aceita MP3, M4A, WMA, FLAC e OGG com menos de 300 MB. O ficheiro de autenticação fica em `storage/ytmusicapi/browser.json` quando é carregado pela UI e não é enviado para o GitHub. Todas as operações ficam registadas em `uploads.json`, enquanto as credenciais permanecem apenas no storage local.

As dependências `ytmusicapi>=1.12,<2` e `pushtunes>=2.15,<3` são instaladas pelo procedimento normal. O adaptador JewelMusic usa directamente o contrato HTTP documentado porque o SDK Python upstream não estava publicado no PyPI no momento da implementação. Consulte `THIRD-PARTY-NOTICES.md`, sobretudo a licença AGPL do Pushtunes, antes de redistribuir o runtime.

### Telegram Gateway

Em **Configurações > Notificações > Telegram**, active **Activar notificações Telegram**, introduza o **Telegram Bot Token** criado pelo BotFather e o **Telegram Chat ID** de destino. O botão **Testar chamada API** executa apenas o método read-only `getMe` para validar o bot; não envia uma mensagem de teste. O proxy é opcional e o suporte SOCKS depende das dependências instaladas pelo `requirements.txt`.

Depois de guardar, cada nova notificação permitida pelas preferências da subaba **Geral** é enviada pela Bot API oficial do Telegram através de `sendMessage`. A notificação continua a ser persistida localmente mesmo que o Telegram esteja indisponível, o Chat ID esteja errado ou a API devolva um erro; a falha externa nunca interrompe a produção, os uploads ou a UI. A integração é apenas outbound: não recebe comandos, não faz polling e não expõe o Bot Token em logs, metadados ou no GitHub.

As credenciais devem ser inseridas apenas na configuração local. A Kaggle API Key pertence exclusivamente à alternativa Kaggle. O Apify API Token pertence exclusivamente à alternativa Apify e não é usado para Kaggle; os resultados e histórico Apify ficam separados em `niche_apify_runs.json`. A Data API Key, o OAuth Client ID e o OAuth Client Secret são valores diferentes; Client ID + Secret não geram uma API Key nem um token OAuth até a conta ser autorizada. Não coloque nenhum deles no GitHub, no `package.json`, em blueprints ou em ficheiros de estado versionados.

## OpenAI/ NVIDIA NIM — API key, Base URL e modelo

A secção **LLM — providers e modelos** mantém o provider técnico `openai`, mas a área visual passou a chamar-se **OpenAI/ NVIDIA NIM — API key, Base URL e modelo**. Isto permite usar a API oficial da OpenAI, a API pública NVIDIA NIM/NVIDIA Build ou qualquer servidor local OpenAI-compatible sem alterar o restante fluxo do MoneyPrinterTurbo. O campo de modelo manual utiliza o parâmetro `help` compatível com as versões de Streamlit instaladas pelo Thunderbolt; não utiliza `help_text`.

Para usar NVIDIA NIM, abra **Configurações > Configuração API**, mantenha ou preencha a Base URL `https://integrate.api.nvidia.com/v1` e introduza a API key do NVIDIA Build. Clique em **Consultar/actualizar modelos NIM**. O Thunderbolt executa a consulta apenas nesse momento, acrescentando `/models` à Base URL, envia a API key como `Authorization: Bearer ...` e interpreta a resposta OpenAI-compatible `data[].id`. Os IDs devolvidos aparecem num selector; ao escolher um, o valor é guardado em `openai_model_name` e continua a ser enviado para o `config.toml` do MoneyPrinterTurbo.

Se utilizar um NIM local, substitua a Base URL pelo endereço do serviço, por exemplo `http://127.0.0.1:8000/v1`. Se o serviço não tiver `/models`, estiver indisponível ou recusar a credencial, o erro aparece na própria UI sem mostrar a API key. Nesse caso, seleccione **Escrever modelo manualmente** ou utilize directamente o campo de modelo manual. A consulta não é executada automaticamente ao abrir Configuração API.

A API key não é gravada em logs, não é incluída no GitHub e não é enviada ao abrir a página. Os identificadores mostrados no selector são os IDs retornados pelo endpoint; para NVIDIA Build, normalmente não devem receber o prefixo interno `nvidia_nim/`, pois o endpoint OpenAI-compatible espera o ID original do modelo.

## 9. Testar as áreas principais

Após iniciar a aplicação, valide o seguinte percurso:

1. **Início:** confirme que a UI abre, mostra o estado local, as métricas e os cards das filas do Pipeline, sem botões de acções rápidas.
2. **Blueprints:** coloque um JSON em `~/.thunderbolt/storage/blueprints/importados/` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\storage\blueprints\importados\`) ou use o carregador da interface. No formulário **Criar blueprint a partir de link**, preencha também **Nome do Blueprint**; o campo é obrigatório e o valor fica no `name` do JSON e no nome do ficheiro criado.
3. **Brandings:** abra a subaba **Brandings** e confirme a listagem dos ficheiros JSON.
4. **Canais:** em **Importar do YouTube**, use o método **Página pública — sem API Key** com um URL `/channel/UC...`, um handle ou uma subpágina `/videos`; o parser resolve o ID, consulta a página pública e tenta o RSS quando necessário. Confirme que o resultado abre o formulário de revisão sem Data API Key. Se o canal não existir ou não fornecer metadados, confirme a mensagem clara e que o formulário de uma pesquisa anterior desaparece. A Data API é opcional e fica separada; em **Cadastro manual**, preencha os dados sem qualquer consulta externa.
5. **Niche Finder Kaggle:** abra o menu expansível **Niche Finder**, seleccione **Niche Finder Kaggle**, defina os parâmetros dentro do conteúdo principal e confirme que não há preparação automática. Antes do clique, não deve existir download de dataset nem análise. Clique em **Analisar Nichos** para iniciar a preparação dos dados e a análise; depois altere país, engagement, datas e tags e clique novamente para aplicar os novos parâmetros. Em seguida, abra a alternativa independente **Niche Finder Apify**, configure as palavras-chave e filtros na própria aba e confirme que nada é executado antes de clicar em **Pesquisar no Apify**.
6. **Pipeline > Criação de Vídeos:** teste primeiro o modo **Canal específico** e depois os modos de lote. O campo **Tópico ou briefing** pode ser escrito manualmente ou preenchido pelo botão **Gerar tópico/briefing com IA**; a geração só ocorre após o clique e usa o provider configurado em **Configuração API > API Keys > Serviços e modelos**.
7. **Criação de Vídeos:** depois de seleccionar o canal, confirme que o painel entre **Canal** e **Estilo wide** mostra o Blueprint e a voz, ou **SEM BLUEPRINT CONFIGURADO**. Clique em **Gerar títulos e thumbnails com IA**, confirme pelo menos 20 candidatos de título e 3–5 variantes de thumbnail, escolha uma variante e verifique o prompt guardado. Na subaba **Vídeos**, verifique o estado `to_do`, o título escolhido, o estado da thumbnail e os botões **Iniciar** e **Parar**. Confirme também que **Criação de Músicas** mostra o mesmo fluxo com título próprio.
8. **Lote geral:** confirme que não existe **Canais incluídos** nem selector parcial. A UI deve listar todos os canais cadastrados e criar exactamente uma tarefa por canal, com briefing, título, thumbnail e Blueprint próprios. Use **Gerar tópicos individuais para todos os canais** e **Gerar títulos e thumbnails para todos os canais** antes de criar o batch.
9. **Upload:** configure o OAuth Client ID e Secret, autorize primeiro o **youtube-automation-agent** na própria aba, confirme o estado **pronto para publicar**, preencha título/descrição/tags e publique um MP4 real. O botão **Autorizar fallback OAuth** existe apenas para redundância; a Data API Key, se configurada, é exclusivamente para consultas oficiais públicas e nunca substitui OAuth.
10. **Edição > Limpador de Metadados:** suba um vídeo de terceiro, preencha título, preview, links, timestamps e tags, aplique a limpeza e descarregue a cópia limpa e o manifesto JSON. O original fica preservado e vídeos das páginas de criação não são aceites nesta área.
11. **Configurações > Configuração API:** confirme que as credenciais ficam locais e não aparecem no Git. Em **API Keys > Fontes de materiais**, seleccione Pexels, Pixabay, Coverr, WaveSpeed AI, LoomLoom, TwelveLabs ou Ficheiros locais. Para uma fonte com API, preencha a primeira chave e use **Adicionar outra chave** para criar quantas linhas forem necessárias; clique em **Guardar fonte e chaves**. Cada fonte mantém a sua própria lista, com deduplicação e rotação interna. Não são pedidos endpoint, proxy, qualidade, codec, FFmpeg, Whisper, directório ou filtros nesta subaba. Na secção **Contas Google/YouTube — canais em lote**, adicione cada conta com o seu e-mail/Gmail, OAuth Client ID, OAuth Client Secret e `sessionInfo` próprios; use **Repetir campos para nova conta** para preparar contas adicionais e o ícone **Apagar conta** para eliminar individualmente a conta, tokens, documento JSON e associações de canais.
12. **OpenAI/ NVIDIA NIM:** em **API Keys > Serviços e modelos > LLM — providers e modelos**, seleccione `openai`, confirme a Base URL, introduza a API key e clique em **Consultar/actualizar modelos NIM**. Escolha um modelo da lista ou utilize o fallback manual e guarde as configurações. Confirme que a consulta só ocorre após o clique e que um erro de endpoint não interrompe a UI.
13. **Criação de Vídeos:** confirme que a fonte seleccionada em **API Keys > Fontes de materiais** é usada pela pipeline, que `Estilo IA` aparece apenas em `full_ia` e que `Apenas Música` exige áudio e guarda `background_mode=none`.
14. **Canais Youtube:** abra **Configurações > Canais Youtube**, clique em **Editar** num cartão, altere o nicho, Blueprint/Prompts do Canal, Narrador/Voz padrão e horário, guarde e confirme que o cartão é actualizado sem duplicar o canal. Clique em **Actualizar últimos 10 vídeos**, valide a vista Lista, mude para Kanban e abra **Editar vídeo** para testar título, estado, data, URL e notas.
15. **Automação Youtube:** no cartão de cada canal, escolha o **Blueprint padrão** e a **Voz padrão**, clique em `Guardar` e confirme que o resumo do cartão se actualiza. Configure também **Automação ON** e um horário `HH:MM`; confirme a lista de vídeos cadastrados. Os mesmos defaults aparecem em **Canais Youtube** e são usados em novas tarefas. Inicie o Thunderbolt pelo launcher, confirme o aviso verde **Worker activo** e verifique que o relógio apresentado corresponde ao computador. O worker cria no máximo um lote por canal por dia quando o horário local coincide.
16. **Configurações > Configuração API > Teste de vozes:** teste Edge/Azure ou provider configurado e confirme reprodução/download sem criação de tarefa.
17. **Upload directo:** em **Configurações > Contas Google**, cada cartão Gmail apresenta o uploader **Documento de credenciais desta conta Google** e o campo **sessionInfo token desta conta Google**. O sessionInfo é guardado por conta e sincronizado no documento JSON, que reúne `SID`, `SSID`, `HSID`, `APISID`, `chunk_size` e `delegated_session_ids` por canal; a `INNERTUBE_API_KEY` é guardada separadamente como configuração global para todas as contas e para todo o sistema. Use **Repetir campos para nova conta** para preencher o formulário seguinte e o ícone **Apagar conta** para remover a conta e os dados privados associados. Em **Canais Youtube > Canais cadastrados**, associe cada canal à conta Google do documento; a UI não mostra nem edita o `DELEGATED_SESSION_ID`. O documento é guardado em `storage/youtube_direct_accounts/<id-da-conta>/credentials.json`, e o uploader lê os valores directos exclusivamente desse documento. A `INNERTUBE_API_KEY` não é um campo técnico por conta nem pertence ao documento; existe apenas no bloco global da página. Não existem campos separados de cookies, `chunk_size` ou `DELEGATED_SESSION_ID` na parte inferior da UI e o método não extrai cookies automaticamente do navegador.
18. **Configurações > MCP > Client MCP:** confirme que Short Video Maker, AutoVio, OpenMontage e OpenCut aparecem com as portas padrão editáveis. O estado **Activo** é uma preferência local; a detecção deve indicar **Não detectado** quando os serviços externos não estiverem instalados ou iniciados.
19. **Configurações > MCP > Servidor MCP:** abra a subaba, mantenha o host `127.0.0.1`, active **Servidor MCP ON** e clique em **Guardar e iniciar Servidor MCP**. Confirme o endpoint `/mcp` e o health endpoint `/health`. Mantenha **Permitir ferramentas de escrita** desactivado até precisar que um agente crie lotes.
20. **Configurações > MCP > Skill:** clique em **Guardar skill localmente** e confirme o ficheiro em `storage/skills/moneyprinterturbo-video.md`; opcionalmente use **Descarregar skill .md** para obter a cópia através do navegador.

## Configuração API — fontes de materiais

A área **Configurações > Configuração API > API Keys** separa as credenciais de serviços da configuração de fontes. Abra a subaba **Fontes de materiais** e escolha a fonte que a pipeline deverá usar. Para **Pexels**, **Pixabay**, **Coverr**, **WaveSpeed AI**, **LoomLoom** ou **TwelveLabs**, cada linha **API Key** é mascarada. Clique em **Adicionar outra chave** para guardar várias credenciais da mesma fonte; por exemplo, duas chaves Pixabay e duas Pexels ficam em listas independentes.

Clique em **Guardar fonte e chaves** para persistir a fonte activa e as respectivas chaves no storage local. O Thunderbolt remove linhas vazias e duplicadas, mantém compatibilidade com instalações antigas que usavam campos separados e escreve arrays no `config.toml` do MoneyPrinterTurbo para permitir rotação interna. Ao seleccionar **Ficheiros locais**, nenhuma API key é necessária e os materiais são obtidos do storage local.

A subaba de fontes não é um painel de tuning: endpoints, proxy, qualidade, correspondência ao roteiro, directório, FFmpeg, codec, Whisper e outros parâmetros técnicos não são expostos ali. A subaba **Serviços e modelos** continua disponível para credenciais de LLM, TTS, Nano Banana, TikTok, Postiz e integrações que não são fontes de materiais. `INNERTUBE_API_KEY` não pertence a esta página; permanece no bloco de configuração global em **Configurações > Contas Google** e aplica-se a todas as contas.

## Gestão de Canais, edição e vídeos recentes

Na página **Configurações > Canais Youtube**, cada canal cadastrado aparece num cartão com o botão **Editar**. O editor permite alterar o nome, URL, handle, idioma, estilo wide, **Nicho**, **Blueprint Padrão**, **Narrador/Voz Padrão**, conta Google do Upload directo, descrição e Automação ON/horário. Guardar alterações actualiza o mesmo registo local; não é necessário apagar e criar o canal novamente.

O cartão mostra o nicho imediatamente abaixo do nome. Os quatro blocos compactos de gestão usam os rótulos **Blueprint Padrão**, **Nicho**, **Narrador/Voz Padrão** e **Idioma**, com os botões de edição correspondentes; o idioma é apenas apresentado a partir da configuração já guardada no canal.

A secção **Últimos 10 vídeos publicados** fica abaixo das configurações do canal, dentro de um expander fechado por defeito, e não dentro de Criação de Vídeos. Clique no expander e depois em **Actualizar últimos 10 vídeos** para consultar o feed RSS público do YouTube sem Data API Key. Os resultados são guardados em `storage/state/channel_videos.json`. A única vista disponível é **Lista**, que apresenta título, data, URL, estado e botão **Editar vídeo**. A edição local permite alterar título, estado, data, URL e notas. Essas alterações são overrides de gestão local e não publicam automaticamente no YouTube.

A página **Configurações > Logs** aparece no menu entre **Notificações** e **Configuração API**. Mostra uma projecção unificada das tarefas e notificações persistentes, com filtro livre por operação, filtros por operação e estado e as colunas mínimas **Operação**, **Estado**, **Data** e **Hora**. A tabela também mostra **Registo**, **Origem**, **Progresso** e **Detalhes**; estados como pendente, em execução, concluído, publicado, falha, cancelado e bloqueado são apresentados quando existirem no storage local.

## Canais em lote por conta Google/YouTube

A subaba **Canais em lote gmail**, dentro de **Canais Youtube**, não lê e-mails, mensagens, contactos ou a caixa Gmail. O nome identifica a conta Google/Gmail que gere os canais YouTube. Configure cada conta em **Configurações > Contas Google**, preenchendo e-mail, OAuth Client ID, OAuth Client Secret e o `sessionInfo token desta conta Google`.

Na subaba, seleccione a conta e clique em **Autorizar conta Google**. A autorização abre o browser do sistema e guarda um refresh token separado para essa conta. Use um cliente OAuth do tipo **Desktop app**; o Thunderbolt usa a URI loopback `http://127.0.0.1:8765/`. Se usar um cliente Web application, adicione exactamente essa URI em Google Cloud > APIs e serviços > Credenciais > URIs de redireccionamento autorizados, incluindo a porta e a barra final. Caso contrário, o Google devolve `Erro 400: redirect_uri_mismatch`. Depois clique em **Listar canais desta conta**. O Thunderbolt chama a YouTube Data API com `channels.list`, `mine=true`, `part=snippet,contentDetails,statistics`, suporta páginas sucessivas e apresenta os canais encontrados para selecção.

Escolha os canais e os defaults de Blueprint, voz, idioma e estilo wide, depois clique em **Cadastrar canais seleccionados**. A importação usa `youtube_channel_id` para não duplicar canais já cadastrados, preserva os registos existentes e identifica a origem como `youtube_data_api_oauth_mine`. A API Key global não substitui OAuth neste fluxo; permanece reservada para consultas públicas/métricas.

## Niche Finder Kaggle e Niche Finder Apify

A página **Niche Finder Kaggle** integra a lógica adaptada do projecto open source [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder), cujo projecto original usa K-Means e FP-Growth sobre o dataset público [Trending Youtube Video Statistics (113 Countries)](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries). No Thunderbolt não existe Flask, rota HTTP adicional, template HTML, JavaScript D3 ou segundo processo; toda a análise é síncrona no Streamlit.

Ao abrir a página, o Thunderbolt não prepara dados públicos, não descarrega o dataset e não inicia a análise. A instalação das dependências continua automática, mas a operação é manual: os parâmetros ficam dentro da própria aba e o utilizador deve clicar em **Analisar Nichos**. Só depois desse clique o KaggleHub prepara ou reutiliza a cache local; não há upload de CSV, botão de download manual ou selector de ficheiros.

Os parâmetros da UI são número de clusters entre 2 e 10, suporte mínimo entre 0,01 e 0,50, país, engagement, intervalo de datas e tags, todos dentro da área principal da aba. O núcleo normaliza os dados, calcula engagement, aplica filtros, faz transformação logarítmica e standardização, executa K-Means e calcula itemsets/regras com FP-Growth. Não são apresentados resultados até ao primeiro clique em **Analisar Nichos**; o mesmo botão aplica alterações posteriores aos filtros. Os resultados são DataFrames de clusters, itemsets frequentes, regras de associação e dados analisados; o gráfico de dispersão é criado nativamente com Plotly.

As dependências adicionais — `scikit-learn`, `mlxtend`, `plotly`, `seaborn`, `matplotlib` e `kagglehub` — são instaladas pelo procedimento normal de `npx`. Em instalações existentes, execute novamente `npx.cmd --yes @danhachuel/thunderbolt@0.3.39 install`; o instalador detecta e reutiliza o que já estiver válido.

### Niche Finder Apify

A alternativa Apify não usa o dataset, parâmetros, execução ou estado da alternativa Kaggle. Configure o **Apify API Token**, o **Apify Actor ID**, o intervalo de consulta e o limite da execução em **Configuração API > API Keys > Serviços e modelos**. Na aba, informe até três palavras-chave, período, máximo de resultados, Shorts, duração, idioma das legendas, ordenação e filtros de legendas. O botão **Pesquisar no Apify** inicia manualmente o actor `streamers~youtube-scraper`, consulta o estado do run, carrega o dataset, normaliza os vídeos, limpa SRT, calcula VSC Ratio, tenta resumir transcrições através do LLM configurado e disponibiliza resultados JSON/CSV. O histórico resumido é guardado em `storage/state/niche_apify_runs.json`; não há gravação automática no Airtable do workflow anexado.

## AI Influencers: Personagens, Redes Sociais, Tutorial Meta e Tutorial Supabase

O menu **AI Influencers** foi adicionado abaixo de **Edição**. As abas **Personagens**, **Redes Sociais**, **Tutorial Meta** e **Tutorial Supabase** aparecem nessa ordem. **Personagens** e **Redes Sociais** mostram apenas uma mensagem de reserva para desenvolvimento futuro; **Tutorial Meta** apresenta o guia local de configuração de Instagram e credenciais Meta para automações com n8n.

## Edição: Limpador de Metadados, Cortes, Editor Python e Download Mídia

A aba **Limpador de Metadados** continua funcional e foi movida para **Edição**. A aba **Cortes** é um Clip Generator local inspirado no [OpenShorts](https://github.com/mutonby/openshorts): permite upload de vídeo, URL directa, vídeos gerados ou pasta local, formatos 9:16/1:1/16:9, opções avançadas, modo manual ou automático por segmentos locais e confirmação de direitos antes da geração. Os clips são processados com FFmpeg, guardados em `storage/cuts/runs/<id>/`, apresentados com preview e downloads individual/ZIP, acompanhados de manifesto JSON e histórico. A aba **Editor Python** é funcional e permite escolher vídeos gerados, indicar uma pasta local ou fazer upload manual; as operações são manuais e criam cópias sem alterar os originais.

A aba **Download Mídia** usa a API Python do [yt-dlp](https://github.com/yt-dlp/yt-dlp) para descarregar vídeos ou áudio a partir de URLs públicas. Aceita uma URL por linha, permite escolher qualidade/contentor, formato de áudio, legendas, metadados e processamento de playlists, que fica desactivado por padrão. Os resultados são guardados em `storage/downloads/`, o histórico em `storage/state/media_downloads.json` e o progresso é apresentado durante a operação. A combinação de streams e a conversão de áudio podem exigir FFmpeg. A ferramenta não aceita cookies, tokens ou opções de linha de comandos introduzidas pelo utilizador.

## Editor Python baseado no PYEdit

O **Editor Python** adapta o recorte do [PYEdit](https://github.com/Congren/PYEdit) ao Thunderbolt. Na subaba **Vídeos**, pode seleccionar um vídeo já gerado e registado nos artefactos da pipeline, indicar uma pasta local de vídeos ou fazer upload manual. As operações disponíveis são cortar trecho, remover áudio, extrair áudio, substituir áudio, alterar velocidade e redimensionar vídeo.

Cada operação usa FFmpeg local, preserva o original, cria a saída em `storage/python_editor/outputs/`, guarda o histórico em `storage/state/python_editor_edits.json` e permite descarregar o resultado e um manifesto JSON. Na subaba **Código Python**, pode criar e guardar scripts em `storage/python_editor/scripts/` ou carregar scripts existentes. Por segurança, a UI não executa código Python e não executa scripts automaticamente.

No modo automático de **Cortes**, a aplicação não inventa uma selecção viral: sem transcrição ou provider de IA configurado, são gerados segmentos locais distribuídos pelo vídeo; o modo manual permite definir início e fim exactos. Abrir a página não inicia download, análise ou processamento.

## Criação de Vídeos — IA editorial e pacotes criativos

O formulário permite escrever manualmente o **Tópico ou briefing** ou clicar em **Gerar tópico/briefing com IA**. O botão usa o provider LLM, Base URL, API key e modelo guardados em **Configuração API > API Keys > Serviços e modelos**, incorpora a descrição, o nicho e o Blueprint do canal e coloca o resultado no campo para revisão. Abrir a página não inicia chamadas externas.

Depois do tópico, clique em **Gerar títulos e thumbnails com IA**. O Thunderbolt solicita pelo menos 20 títulos candidatos e 3–5 variantes de thumbnail, aplica as regras das referências empacotadas em `seed/references/` e guarda a variante escolhida na task. O título aparece pré-preenchido no Upload. A thumbnail guarda conceito, texto de até quatro palavras, composição, paleta, prompt e sinergia com o título; se não existir um provider de imagem configurado, fica com estado **Prompt de thumbnail pronto — imagem pendente de provider de imagem**, sem criar um ficheiro artificial.

No modo **Lote geral**, todos os canais cadastrados são incluídos automaticamente. Não existe selector **Canais incluídos**. O Thunderbolt cria exactamente uma task por canal e cada task recebe briefing, título, thumbnail, Blueprint, voz e contexto próprios. O mesmo tópico não é replicado entre canais.

## Pipeline: Criação de Vídeos, Criação de Músicas, Roteiros e Automação

O modo `Pexels/Pixabay` representa materiais de stock. Ao seleccionar `full_ia`, o selector `Estilo IA` apresenta os 12 estilos disponíveis. Ao seleccionar `Apenas Música`, a UI obriga a escolher uma música existente, carregar um ficheiro ou solicitar uma música a um endpoint Suno configurado. O vídeo recebe `background_mode=none`, sem fundo Pexels/Pixabay ou IA.

A aba **Roteiros**, colocada entre **Criação de Músicas** e **Upload**, permite seleccionar um canal opcional, um Blueprint, **Roteiro de vídeo** ou **Letra de música**, idioma, tema e estrutura. O botão **Gerar com IA a partir do Blueprint** usa o provider LLM configurado e devolve um rascunho Markdown editável; o utilizador deve rever e clicar em **Guardar documento no storage**. Os ficheiros são guardados em `storage/scripts/` e o índice em `storage/state/scripts.json`; o caminho absoluto aparece no topo da página. Na subaba **Vídeos** de **Criação de Vídeos**, a aplicação mostra a frase `Os vídeos são guardados em <storage>/videos`, que identifica a pasta local dos vídeos.

A aba **Automação Youtube**, dentro do menu expansível **Automação**, lista os canais e vídeos e apresenta nos cards os mesmos quatro elementos do cadastro: **Idioma Padrão**, **Blueprint Padrão**, **Nicho Padrão** e **Narrador/Voz Padrão**. Blueprint e Narrador/Voz continuam editáveis no card; Idioma e Nicho são mostrados a partir da configuração guardada no canal. A aba também guarda **Automação ON** e valida horários diários no formato `HH:MM`. Os valores ficam sincronizados com o editor existente no cartão da aba **Canais Youtube** e são copiados para novas tarefas. O launcher inicia o worker local, que consulta o relógio do computador, gera um briefing, título e pacote de thumbnail específicos com o provider LLM configurado, cria o lote agendado na fila e evita duplicar o mesmo canal no mesmo dia. Se a geração não puder ser executada, o erro fica registado e o placeholder antigo não é usado.

A área **Teste de vozes**, dentro de **Configurações > Configuração API**, é isolada da pipeline. O preview pode ser reproduzido e descarregado de `storage/voice_previews/`. Caminhos vazios, directórios, ficheiros vazios e previews sem permissões de leitura são ignorados com uma mensagem clara, sem traceback. Se uma instalação antiga mostrar que `edge-tts` está em falta, execute `npx.cmd --yes @danhachuel/thunderbolt install`; o detector reinstala apenas a dependência ausente.

## Upload, Postiz, Upload-Post e Upload directo

A subaba **Postiz**, dentro de **Upload**, permite carregar as integrações Postiz, seleccionar o canal ligado e enviar vídeos MP4 através da Public API. Configure **Activar Postiz como fallback final**, **Postiz API key**, **Postiz Public API Base URL**, **Postiz MCP URL** e, opcionalmente, o ID da integração padrão em **Configuração API > API Keys > Serviços e modelos**. A API key é enviada como valor bruto do cabeçalho `Authorization`; o upload usa `POST /upload` e a publicação usa `POST /posts`.

O botão de envio YouTube segue a ordem fixa **1. API Oficial, 2. Upload directo, 3. Postiz**. O **Upload-Post** é uma quarta subaba independente e não altera essa rota automática do YouTube. A API Oficial regista no storage local até cinco envios bem-sucedidos por dia por conta Gmail. Quando a quota é atingida ou o método falha, o Thunderbolt valida o `credentials.json` e tenta o Upload directo. Postiz só é tentado como último recurso e apenas quando está activo, com API key e integração válida.

Em **Configurações > Contas Google**, cada conta aparece como um expander identificado por nome e e-mail. Dentro dele existe o uploader **Subir documento de cookies/credenciais** e o input **sessionInfo token desta conta Google**. O documento JSON único contém cookies, `chunk_size` e o mapa de IDs delegados por canal; o sessionInfo preenchido na conta é sincronizado no mesmo ficheiro, guardado em `storage/youtube_direct_accounts/<id-da-conta>/credentials.json`. A `INNERTUBE_API_KEY` fica no bloco global da página, fora dos cartões, e é partilhada por todas as contas.

Em **Canais Youtube > Canais cadastrados**, a secção **Upload directo — documento da conta deste canal** mostra apenas a conta Google associada e confirma se o documento contém o ID delegado desse canal. O `DELEGATED_SESSION_ID` permanece exclusivamente no mapa do documento; o upload bloqueia a operação se faltar qualquer elemento técnico.

### Upload-Post

A subaba **Upload-Post** usa a API oficial do [Upload-Post](https://docs.upload-post.com/) para publicar vídeos prontos em uma ou mais plataformas ligadas ao perfil configurado. Em **Configuração API > API Keys > Serviços e modelos > Publicação através do Upload-Post**, active a integração, guarde a API key, o username/perfil e as plataformas padrão. Depois abra **Upload > Upload-Post**, confirme ou altere as plataformas, escreva o título e a descrição e clique em **Enviar vídeo pelo Upload-Post**.

A credencial não é duplicada na página de Upload. A integração envia o ficheiro local como `video` em `multipart/form-data`, usa `platform[]` repetido para cada destino e autentica com `Authorization: Apikey ...`. **Processar em segundo plano** envia `async_upload=true`; quando a API devolver `request_id`, este fica visível e é guardado em `uploads.json`. O histórico local também alimenta a notificação **Upload-Post concluído**. O Upload-Post é distinto do Postiz: não usa os endpoints nem a selecção de integrações do Postiz.

### Upload directo

A subaba **Upload directo** adapta o [YouTube-Video-Upload-Frontend-Api](https://github.com/Nojus10/YouTube-Video-Upload-Frontend-Api). Cada conta Google tem um único `credentials.json`, criado automaticamente ao adicionar a conta, com cookies, sessionInfo, `chunk_size` e `delegated_session_ids` por canal. A `INNERTUBE_API_KEY` é uma configuração global separada, usada por todas as contas. O uploader aceita um documento JSON completo ou parcial; o merge actualiza somente os valores presentes e preserva os restantes. O documento é guardado fora de `storage/state/`, com permissões locais restritas.

Associe cada canal à conta Google correcta em **Canais Youtube**; não introduza o ID delegado na UI. A associação do canal é permitida mesmo que o documento esteja incompleto. No momento do upload, o Thunderbolt lê a `INNERTUBE_API_KEY` global nas configurações, lê o documento da conta, encontra o `DELEGATED_SESSION_ID` pela chave do canal e bloqueia apenas a operação se faltar conta, documento válido, cookies, sessionInfo, chave global, ID delegado ou vídeo elegível. O tamanho de chunk é normalizado para múltiplos de 262144 bytes. O método é uma integração não oficial de sessão do YouTube; não extraia cookies automaticamente, não os coloque no repositório e não os partilhe.

## MCP e integrações externas

A subaba **Client MCP**, em **Configurações > MCP**, é um configurador local de quatro serviços opcionais. As portas iniciais são `3123` para Short Video Maker, `3001` para AutoVio, `8000` como referência editável para OpenMontage e `8787` para a API do OpenCut. A página consulta apenas `http://127.0.0.1:<porta>/` com timeout curto; não clona, instala ou inicia processos externos.

A subaba **Servidor MCP**, em **Configurações > MCP**, disponibiliza, após activação explícita, `http://127.0.0.1:3031/mcp` por JSON-RPC sobre HTTP POST. Para configurar um agente compatível, use esse URL como endpoint MCP. Se o host for alterado para uma interface externa, preencha primeiro um token e trate-o como segredo. O servidor disponibiliza ferramentas de leitura por padrão; a criação de lotes só é exposta quando **Permitir ferramentas de escrita** está activado.

A subaba **Skill**, em **Configurações > MCP**, contém as acções para guardar a skill anexada em `storage/skills/` ou descarregá-la como Markdown. Esta pasta fica fora dos estados JSON e é criada pelo instalador e pelo launcher. Os quatro repositórios continuam fora do pacote npm.

## 12. Limpador de Metadados

A aba **Limpador de Metadados** recebe somente vídeos externos já prontos. O ficheiro enviado é copiado para `storage/metadata_cleaner/originals/`; a aplicação não altera o original. Ao aplicar a operação, o FFmpeg remove os metadados existentes do contentor e cria uma nova versão em `storage/metadata_cleaner/outputs/` com o título, descrição, tags, idioma e outros campos preenchidos.

A descrição combina **Preview**, **Links** e **Timestamps**, seguindo a estrutura do workflow `YTBMetadataGenerator.json`. O preview recomendado tem entre 100 e 200 caracteres; os capítulos devem começar por `00:00`. O manifesto JSON descarregado contém os campos para um fluxo posterior de upload. Esta adaptação local não faz scraping automático via RSS/Apify nem publica directamente no YouTube.

Se a limpeza falhar, execute `doctor` para confirmar a disponibilidade do FFmpeg e valide a instalação de `imageio-ffmpeg`; o caminho técnico é detectado internamente e não é configurado na subaba de fontes. O processo usa `-map_metadata -1` para remover os metadados existentes e `-c copy` para evitar uma re-encodificação desnecessária sempre que o contentor permitir.

## 11. Problemas frequentes

### Python não encontrado

Mensagem típica:

```text
Python 3.11 ou superior não foi encontrado.
```

Instale Python 3.11+ e confirme:

```bash
python3 --version
```

Se houver várias versões instaladas, indique explicitamente:

```bash
THUNDERBOLT_PYTHON=/caminho/para/python3.11 npx --yes @danhachuel/thunderbolt install
```

No Windows PowerShell:

```powershell
$env:THUNDERBOLT_PYTHON="C:\Python311\python.exe"
npx --yes @danhachuel/thunderbolt install
```

### Git não encontrado

Instale Git a partir de [git-scm.com](https://git-scm.com/downloads), ou forneça uma cópia existente do MoneyPrinterTurbo através de `MONEYPRINTER_PATH`.

### Streamlit não está instalado

Execute:

```bash
npx --yes @danhachuel/thunderbolt install
npx --yes @danhachuel/thunderbolt doctor
```

Em instalação manual:

```bash
python -m pip install -r requirements.txt
```

### FFmpeg não detectado

Tente reinstalar o suporte Python:

```bash
python -m pip install --upgrade imageio-ffmpeg
```

Depois confirme:

```bash
npx --yes @danhachuel/thunderbolt doctor
```

O MoneyPrinterTurbo também permite indicar um caminho manual para FFmpeg na configuração local quando a detecção automática não funcionar.[1]

### A porta 3030 está ocupada

Use outra porta:

```bash
THUNDERBOLT_PORT=3040 npx --yes @danhachuel/thunderbolt
```

### O MoneyPrinterTurbo não aparece na UI

Confirme o caminho na aba **Configurações** ou execute:

```bash
MONEYPRINTER_PATH=/caminho/MoneyPrinterTurbo npx --yes @danhachuel/thunderbolt install --skip-python-deps
```

Depois reinicie a aplicação.

### Dependências Python falham durante a instalação

Actualize pip e tente novamente:

```bash
npx --yes @danhachuel/thunderbolt install
```

Se uma dependência específica falhar, guarde o log completo e verifique a compatibilidade da versão Python. Python 3.11 é a opção mais conservadora para o MoneyPrinterTurbo.

### Modelos Whisper não estão disponíveis

A instalação das dependências não baixa necessariamente todos os modelos grandes. O MoneyPrinterTurbo pode descarregar o modelo Whisper na primeira utilização, dependendo da configuração escolhida. Para ambientes sem acesso de rede, siga as instruções do projecto base para descarregar e colocar o modelo localmente.[1]

## 12. Desinstalação

Para remover o pacote global:

```bash
npm uninstall --global @danhachuel/thunderbolt
```

Para remover o ambiente e os dados locais:

Linux ou macOS:

```bash
rm -rf ~/.thunderbolt
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force "$HOME\\THUNDERBOLT"
```

> A remoção de `~/.thunderbolt` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT`) apaga estado JSON, blueprints, configurações e artefactos locais. Faça uma cópia de segurança antes de executar o comando.

## 13. Segurança

Nunca publique ou envie por chat:

- tokens npm;
- chaves YouTube, TikTok ou outros serviços;
- cookies e tokens OAuth;
- ficheiros de configuração com segredos;
- artefactos privados de canais.

Use secrets do GitHub Actions apenas para publicação do pacote. Para execução local, mantenha credenciais fora do repositório e use a área de configurações local ou variáveis de ambiente.

A publicação YouTube segue primeiro a lógica adaptada do `PublishingSchedulingAgent` do [youtube-automation-agent](https://github.com/darkzOGx/youtube-automation-agent), sob licença MIT. O código corre dentro do processo Streamlit; não é necessário iniciar o agente Node separadamente. O fallback OAuth directo só é chamado quando a tentativa primária falha.

## 14. Referências

[1]: https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README-en.md — MoneyPrinterTurbo: requisitos, instalação, dependências, Streamlit e FFmpeg.

[2]: https://www.npmjs.com/package/@danhachuel/thunderbolt — Pacote npm publicado.

[3]: https://github.com/DanHachuel/thunderbolt — Repositório GitHub do Thunderbolt UI.
