# Thunderbolt UI

> Consulte o [Manual completo de instalação](MANUAL-INSTALACAO.md) antes do primeiro teste local.

Thunderbolt — UI web local da Fase 3, baseada no fluxo Streamlit do [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo). A aplicação organiza canais, blueprints, lotes de vídeos, filas, artefactos e upload em armazenamento local JSON.

## Estado actual

A primeira versão implementa a camada UI independente com:

| Área | Incluído |
|---|---|
| Dashboard | Resumo de canais, tarefas, backlog, execução e falhas |
| Pipeline | Filas por etapa |
| Blueprints | Leitura da pasta `storage/blueprints/`, upload/validação de JSON e criação a partir de link YouTube |
| Brandings | Subaba própria dentro de Blueprints, upload/listagem de Brandings e criação conjunta com Blueprint |
| Canais | Subabas de importação pública sem API Key, Data API opcional e cadastro manual independente |
| Novo vídeo | Subabas Criar vídeo e Vídeos; lotes; 51 rótulos de idioma; Pexels/Pixabay, full IA com Estilo IA e Apenas Música com agente musical |
| Automação | Lista de vídeos e canais, selectores editáveis de Blueprint/voz padrão, Automação ON e horário diário HH:MM; UI configurável sem worker em segundo plano |
| Upload | YouTube via `youtube-automation-agent` adaptado internamente, OAuth directo de redundância, Upload directo experimental, TikTok, Instagram e Facebook Pages no front end |
| MCP | Catálogo local opcional de Short Video Maker, AutoVio, OpenMontage e OpenCut, com portas editáveis e activação |
| Limpador de metadado | Upload isolado de vídeos terceiros, limpeza FFmpeg, edição de título/descrição/tags e manifesto JSON |
| Configurações | Provedores LLM, TTS/voz, preview de vozes, Suno, materiais, Whisper, FFmpeg, OAuth YouTube, Data API Key opcional, Upload directo, TikTok Client ID/Secret e Upload-Post |
| Launcher | Execução via `npx`, instalação assistida, diagnóstico e preparação para distribuição |

Os adaptadores do MoneyPrinterTurbo e de publicação nas plataformas são ligados pelas configurações locais e pelos pontos de integração em `integrations/`. A UI não inventa dados quando um serviço externo ou credencial não está disponível.

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
npx.cmd --yes @danhachuel/thunderbolt@0.2.25 install
npx.cmd --yes @danhachuel/thunderbolt@0.2.25 doctor
npx.cmd --yes @danhachuel/thunderbolt@0.2.25
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
├── skills/            # skill MoneyPrinterTurbo guardada pelo utilizador
├── metadata_cleaner/
│   ├── originals/    # cópias dos vídeos terceiros enviados
│   └── outputs/      # versões com metadados limpos
└── artifacts/        # ficheiros produzidos e caminhos referenciados
```

Para usar outro local, defina `THUNDERBOLT_STORAGE_DIR`. O estado é escrito de forma atómica e ficheiros JSON inválidos são preservados com cópia `.corrupt-*` antes de serem recriados.

## Blueprints e Brandings

Coloque ficheiros `.json` em `storage/blueprints/canais`, `storage/blueprints/nichos` ou `storage/blueprints/importados`. A aba **Blueprints** relê a pasta e mostra o conteúdo estruturado. A instalação já inclui 13 Blueprints seed, copiados apenas quando o ficheiro ainda não existe; actualizações não substituem Blueprints locais. Também é possível importar através do carregador da própria interface.

A mesma aba possui a subaba **Brandings**. No formulário **Criar blueprint a partir de link**, cole um link de canal, handle ou vídeo do YouTube, informe o nicho e o idioma e escolha entre **Apenas Blueprint** ou **Blueprint + Branding completo**. O primeiro modo grava o blueprint forense local; o segundo grava também um ficheiro de Branding com identidade do canal, handle, descrição, hashtags, keywords, prompts de imagem de perfil e banner, direcção visual de thumbnails, assets e checklist de revisão.

O fluxo foi modelado a partir do blueprint de clonagem com Branding anexado, incluindo a distinção entre entrada de canal/vídeo, normalização do link, metadados de nicho/idioma, perfil do canal, estratégia de conteúdo, pesquisa, identidade visual e brand pack. Placeholders de serviços externos são tratados como configuração local; chaves presentes em workflows importados não devem ser commitadas.

## Limpador de metadado

A aba **Limpador de metadado** foi adaptada do workflow `YTBMetadataGenerator.json`. Ela recebe apenas um vídeo externo já pronto, guarda uma cópia original separada, remove os metadados do contentor com FFmpeg e grava uma nova cópia com título, descrição, links, timestamps, tags e outros campos opcionais. O original nunca é alterado e os vídeos produzidos pela aba **Novo vídeo** não aparecem nesta área.

A descrição segue a composição do workflow de referência: preview, secção de links e capítulos/timestamps. O resultado inclui um manifesto JSON para utilizar os metadados num fluxo posterior de upload. A versão local não usa o trigger RSS, o Apify ou a actualização automática de um vídeo YouTube; em vez disso, o utilizador fornece directamente o vídeo terceiro e controla a edição antes de publicar.

## Canais YouTube

A aba **Canais** está dividida em dois fluxos independentes. Em **Importar do YouTube**, o método padrão **Página pública — sem API Key** consulta a página pública do canal e preenche nome, ID, handle, URL, descrição e thumbnail quando esses dados estão disponíveis. A opção **YouTube Data API — API Key opcional** pode ser escolhida para métricas oficiais quando uma **YouTube Data API Key própria** estiver configurada em **Configurações** ou em `YOUTUBE_API_KEY`; essa chave é distinta do OAuth Client ID e Client Secret.

Em **Cadastro manual**, nenhum pedido ao YouTube é feito e não existe qualquer dependência de API Key. O utilizador pode preencher nome, URL, handle, descrição, métricas, thumbnail, idioma, estilo, Blueprint padrão, voz padrão, `DELEGATED_SESSION_ID` e configuração de Automação. A importação pública nunca grava automaticamente: os dados aparecem num formulário de revisão antes de guardar. A resolução pública aceita URLs `/channel/UC...`, handles e subpáginas; quando existe um ID mas o HTML não traz todos os dados, tenta o feed RSS público. Se o YouTube responder que o canal não existe ou não fornecer metadados, a UI mostra uma mensagem clara e não mantém o formulário de uma pesquisa anterior. Cada cartão de canal tem **Activo** e, logo abaixo, **Apagar canal**, com confirmação; tarefas e artefactos não são apagados.

## Upload YouTube

O Upload usa como caminho **principal** a lógica do `PublishingSchedulingAgent` do [youtube-automation-agent](https://github.com/darkzOGx/youtube-automation-agent), adaptada para Python e executada dentro do processo Streamlit do Thunderbolt. Não é necessário instalar ou iniciar um segundo servidor Node. O fluxo valida o MP4 real, constrói `snippet/status`, faz upload resumível e tenta enviar thumbnail e legendas.

Na aba **Upload**, configure primeiro apenas o **YouTube OAuth Client ID** e o **YouTube OAuth Client Secret** em **Configurações**. Em seguida, use **Autorizar agente YouTube**. O navegador local abrirá a autorização Google e o token será guardado apenas em `storage/state/youtube_agent_tokens.json`. Se a publicação principal falhar, o Thunderbolt tenta automaticamente o **OAuth directo de redundância**, usando o token local compatível; a Data API Key nunca é usada para autorizar ou publicar.

Use **Autorizar fallback OAuth** apenas se precisar de uma autorização separada para o caminho de redundância. Os resultados guardam no histórico local qual mecanismo foi utilizado e as tentativas realizadas, sem guardar segredos.

A subaba **Upload directo** adapta o [YouTube-Video-Upload-Frontend-Api](https://github.com/Nojus10/YouTube-Video-Upload-Frontend-Api). Ela usa cookies, `sessionInfo`, `INNERTUBE_API_KEY` e `DELEGATED_SESSION_ID` fornecidos manualmente pelo utilizador, cria o vídeo através do endpoint interno e envia o ficheiro em chunks de 256 KiB. Este caminho é experimental, não extrai cookies automaticamente e fica separado do agente YouTube principal.

## Novo vídeo, Automação e música

Em **Novo vídeo**, o estilo visual `Pexels/Pixabay` é o modo de materiais, `full_ia` abre o selector **Estilo IA** com os 12 estilos solicitados e **Apenas Música** exige um áudio local, um upload musical ou um pedido ao endpoint Suno configurado. Neste último modo, a task fica com `background_mode=none`: não são gerados fundos Pexels/Pixabay nem fundos IA.

O agente musical guarda os ficheiros em `storage/music/`, aceita formatos de áudio comuns e pode descarregar uma URL de áudio devolvida por um endpoint Suno compatível. Em **Canais**, abra **Definir Blueprint e voz padrão** no cartão do canal para guardar os defaults; em **Automação**, os mesmos dois selectores aparecem no cartão e são sincronizados. Esses valores são usados automaticamente em novas tarefas criadas para o canal. A aba **Automação** também guarda `Automação ON` e um horário diário `HH:MM` por canal e lista os vídeos cadastrados; por definição, esta entrega não executa workers de fundo.

## Teste de vozes

A área **Configurações > Teste de vozes** é isolada da pipeline. Permite escolher Edge/Azure Speech ou um provider HTTP configurado, seleccionar voz/ID, alterar a velocidade, sintetizar uma amostra, reproduzi-la e descarregá-la. O áudio é guardado em `storage/voice_previews/` e nunca altera vídeos ou tarefas.

## MCP e integrações externas opcionais

A aba **MCP** funciona como um catálogo local de clientes externos. Ela lista **Short Video Maker**, **AutoVio**, **OpenMontage** e **OpenCut** com os respectivos links oficiais, protocolo/capacidade conhecida, porta local editável e toggle **Activo**. Os repositórios não são clonados, instalados ou incluídos no pacote npm do Thunderbolt.

As portas iniciais são `3123` para Short Video Maker, `3001` para a API backend do AutoVio, `8000` como referência editável para OpenMontage — que não documenta uma porta HTTP padrão — e `8787` para a API do OpenCut, cujo frontend de desenvolvimento usa `5173`. A detecção é passiva: apenas consulta `localhost` e nunca inicia processos externos. Activar uma integração guarda a preferência local; não substitui a instalação/configuração do serviço externo.

A mesma aba permite **Guardar skill localmente**, copiando `moneyprinterturbo-video.md` para `storage/skills/`, e **Descarregar skill .md** através do navegador. A skill é um recurso separado dos quatro repositórios externos.

## TikTok

A subaba **Vídeos**, dentro de **Novo vídeo**, mostra o backlog e permite iniciar/parar tarefas; deixou de existir como botão principal na barra lateral.

A aba **Configurações** contém apenas o TikTok Client ID e o TikTok Client Secret para TikTok. Para YouTube, o bloco principal pede o OAuth Client ID e Client Secret; a Data API Key, se usada, fica numa área opcional separada. Client ID + Client Secret não formam uma Data API Key nem um token OAuth.
 Redirect URI, scopes, autorização OAuth e tokens são geridos no TikTok for Developers Playground. O adaptador rejeita o upload quando faltam credenciais ou OAuth, em vez de indicar sucesso falso.

## Segurança

Não coloque chaves, cookies, tokens YouTube ou segredos TikTok no Git. Use a configuração local, variáveis de ambiente ou um ficheiro fora do repositório. O `.gitignore` exclui o storage de estado real, ambientes virtuais e ficheiros de segredo. O adaptador interno foi baseado na lógica publicada sob licença MIT do [youtube-automation-agent](https://github.com/darkzOGx/youtube-automation-agent).
