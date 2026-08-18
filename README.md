# Content-Hermes UI

UI web local do Content-Hermes Fase 3, baseada no fluxo Streamlit do [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo). A aplicação organiza canais, blueprints, lotes de vídeos, filas, artefactos e upload em armazenamento local JSON.

## Estado actual

A primeira versão implementa a camada UI independente com:

| Área | Incluído |
|---|---|
| Dashboard | Resumo de canais, tarefas, backlog, execução e falhas |
| Pipeline | Filas por etapa |
| Blueprints | Leitura da pasta `storage/blueprints/`, upload e validação de JSON |
| Canais | Cadastro manual, importação via YouTube Data API quando configurada e edição de dados importados |
| Novo vídeo | Canal específico, lote no mesmo canal e lote geral |
| Vídeos | Filtro por estado e controlos iniciar/parar |
| Upload | Destinos YouTube/TikTok e diagnóstico do TikTok |
| Configurações | Caminhos locais, YouTube API key e credenciais TikTok |
| Launcher | Execução directa e preparação para futura distribuição via `npx` |

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

O launcher também está preparado para um futuro pacote npm:

```bash
npx --yes ./
```

A publicação no npm não faz parte desta fase.

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

## Blueprints

Coloque ficheiros `.json` em `storage/blueprints/canais`, `storage/blueprints/nichos` ou `storage/blueprints/importados`. A aba **Blueprints** relê a pasta e mostra o conteúdo estruturado. Também é possível importar através do carregador da própria interface.

## Canais YouTube

Sem chave, o cadastro manual continua disponível. Para importar nome, handle e estatísticas através da API oficial do YouTube Data API, configure `youtube_api_key` na aba **Configurações** ou em `YOUTUBE_API_KEY`.

## TikTok

A aba **Configurações** contém os campos da Content Posting API do TikTok: Client Key, Client Secret, Redirect URI e scopes. A publicação final depende da autorização OAuth e das permissões/aprovação da aplicação TikTok. O adaptador rejeita o upload quando faltam credenciais ou OAuth, em vez de indicar sucesso falso.

## Segurança

Não coloque chaves, cookies, tokens YouTube ou segredos TikTok no Git. Use a configuração local, variáveis de ambiente ou um ficheiro fora do repositório. O `.gitignore` exclui o storage de estado real, ambientes virtuais e ficheiros de segredo.
