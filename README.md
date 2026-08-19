# Content-Hermes UI

> Consulte o [Manual completo de instalação](MANUAL-INSTALACAO.md) antes do primeiro teste local.

UI web local do Content-Hermes Fase 3, baseada no fluxo Streamlit do [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo). A aplicação organiza canais, blueprints, lotes de vídeos, filas, artefactos e upload em armazenamento local JSON.

## Estado actual

A primeira versão implementa a camada UI independente com:

| Área | Incluído |
|---|---|
| Dashboard | Resumo de canais, tarefas, backlog, execução e falhas |
| Pipeline | Filas por etapa |
| Blueprints | Leitura da pasta `storage/blueprints/`, upload/validação de JSON e criação a partir de link YouTube |
| Brandings | Subaba própria dentro de Blueprints, upload/listagem de Brandings e criação conjunta com Blueprint |
| Canais | Cadastro manual, importação via YouTube Data API quando configurada e edição de dados importados |
| Novo vídeo | Canal específico, lote no mesmo canal e lote geral |
| Vídeos | Filtro por estado e controlos iniciar/parar |
| Upload | Destinos YouTube/TikTok e diagnóstico do TikTok |
| Configurações | Caminhos locais, YouTube API key e credenciais TikTok |
| Launcher | Execução via `npx`, instalação assistida, diagnóstico e preparação para distribuição |

Os adaptadores de agentes Hermes, MoneyPrinterTurbo e publicação final em plataformas podem ser ligados pelas configurações locais e pelos pontos de integração em `integrations/`. A UI não inventa dados quando um serviço externo ou credencial não está disponível.

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

O pacote está publicado no npm como `@danhachuel/content-hermes-ui` e pode ser executado directamente via `npx`:

```bash
npx --yes @danhachuel/content-hermes-ui
```

Para instalar automaticamente o ambiente completo — Python 3.11+, ambiente virtual, dependências Python do Content-Hermes, dependências Python do MoneyPrinterTurbo, Streamlit e `imageio-ffmpeg` — execute:

```bash
npx --yes @danhachuel/content-hermes-ui install
```

Por defeito, o instalador cria automaticamente a pasta `~/Hermes-UI` — no Windows, `C:\Users\<utilizador>\Hermes-UI` —, clona o MoneyPrinterTurbo para `Hermes-UI/MoneyPrinterTurbo`, cria o ambiente em `Hermes-UI/.venv` e guarda o estado em `Hermes-UI/storage`. No Windows, se Python 3.11+ não estiver instalado, o instalador tenta instalá-lo automaticamente através do `winget`. A instalação é uma reinstalação limpa: apaga a pasta `Hermes-UI` e as instalações antigas conhecidas, incluindo `C:\Users\<utilizador>\AppData\Local\hermes`, sem migrar nem copiar ficheiros. O ambiente virtual, o MoneyPrinterTurbo, as dependências e o storage são recriados do zero. Para usar uma cópia existente do MoneyPrinterTurbo:

```bash
MONEYPRINTER_PATH=/caminho/MoneyPrinterTurbo npx --yes @danhachuel/content-hermes-ui install
```

Para instalar apenas a UI sem clonar o MoneyPrinterTurbo:

```bash
npx --yes @danhachuel/content-hermes-ui install --skip-moneyprinter
```

Para verificar o ambiente sem iniciar a aplicação:

```bash
npx --yes @danhachuel/content-hermes-ui doctor
```

Para executar apenas o diagnóstico do ambiente:

```bash
npx --yes --package=@danhachuel/content-hermes-ui content-hermes --check
```

Para instalar globalmente e disponibilizar o comando `content-hermes`:

```bash
npm install --global @danhachuel/content-hermes-ui
content-hermes
```

No Windows PowerShell, se `npx` for bloqueado por `npx.ps1`, use directamente `npx.cmd`:

```powershell
npx.cmd --yes @danhachuel/content-hermes-ui@0.2.5 install
npx.cmd --yes @danhachuel/content-hermes-ui@0.2.5 doctor
npx.cmd --yes @danhachuel/content-hermes-ui@0.2.5
```

Como alternativa, pode permitir scripts para o seu utilizador:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Ou apenas para a sessão actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Após `install`, o launcher usa o ambiente virtual instalado em `~/Hermes-UI/.venv` — no Windows, `C:\Users\<utilizador>\Hermes-UI\.venv` — e inicia a UI em `localhost:3030`. No Windows, a raiz é obtida por `USERPROFILE`, evitando a redirecção de `HOME` que pode ocorrer no MobaXterm. O instalador não instala drivers de GPU, Docker, chaves de API, modelos Whisper ou credenciais de plataformas; esses componentes continuam dependentes do sistema e da configuração do utilizador. Para desenvolvimento a partir do clone, continue a usar `node scripts/cli.mjs`.

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
│   └── settings.json
└── artifacts/        # ficheiros produzidos e caminhos referenciados
```

Para usar outro local, defina `HERMES_STORAGE_DIR`. O estado é escrito de forma atómica e ficheiros JSON inválidos são preservados com cópia `.corrupt-*` antes de serem recriados.

## Blueprints e Brandings

Coloque ficheiros `.json` em `storage/blueprints/canais`, `storage/blueprints/nichos` ou `storage/blueprints/importados`. A aba **Blueprints** relê a pasta e mostra o conteúdo estruturado. Também é possível importar através do carregador da própria interface.

A mesma aba possui a subaba **Brandings**. No formulário **Criar blueprint a partir de link**, cole um link de canal, handle ou vídeo do YouTube, informe o nicho e o idioma e escolha entre **Apenas Blueprint** ou **Blueprint + Branding completo**. O primeiro modo grava o blueprint forense local; o segundo grava também um ficheiro de Branding com identidade do canal, handle, descrição, hashtags, keywords, prompts de imagem de perfil e banner, direcção visual de thumbnails, assets e checklist de revisão.

O fluxo foi modelado a partir do blueprint de clonagem com Branding anexado, incluindo a distinção entre entrada de canal/vídeo, normalização do link, metadados de nicho/idioma, perfil do canal, estratégia de conteúdo, pesquisa, identidade visual e brand pack. Placeholders de serviços externos são tratados como configuração local; chaves presentes em workflows importados não devem ser commitadas.

## Canais YouTube

Sem chave, o cadastro manual continua disponível. Para importar nome, handle e estatísticas através da API oficial do YouTube Data API, configure `youtube_api_key` na aba **Configurações** ou em `YOUTUBE_API_KEY`.

## TikTok

A aba **Configurações** contém os campos da Content Posting API do TikTok: Client Key, Client Secret, Redirect URI e scopes. A publicação final depende da autorização OAuth e das permissões/aprovação da aplicação TikTok. O adaptador rejeita o upload quando faltam credenciais ou OAuth, em vez de indicar sucesso falso.

## Segurança

Não coloque chaves, cookies, tokens YouTube ou segredos TikTok no Git. Use a configuração local, variáveis de ambiente ou um ficheiro fora do repositório. O `.gitignore` exclui o storage de estado real, ambientes virtuais e ficheiros de segredo.
