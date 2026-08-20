# Manual de Instalação — Thunderbolt UI

Este manual descreve a instalação local da UI Thunderbolt, baseada no MoneyPrinterTurbo, utilizando o pacote npm `@danhachuel/thunderbolt`. O fluxo recomendado instala automaticamente o ambiente Python, as dependências da aplicação, as dependências do MoneyPrinterTurbo, o Streamlit e o suporte FFmpeg através de `imageio-ffmpeg`.

> **Versão deste manual:** 0.2.35
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

A aplicação não instala drivers de GPU, Docker, modelos Whisper ou credenciais externas. As chaves de API do MoneyPrinterTurbo são configuradas na aba **Configurações** e sincronizadas com o `config.toml` do clone local.

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
npx.cmd --yes @danhachuel/thunderbolt@0.2.35 install
```

Linux/macOS:

```bash
npx --yes @danhachuel/thunderbolt@0.2.35 install
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

Na primeira execução, a barra lateral apresenta **Início**, **Pipeline**, **Automação**, **Niche Finder** e **Configurações**. O menu expansível **Niche Finder** contém **Niche Finder Kaggle** e **Niche Finder Apify**. A aba **Niche Finder Kaggle** mantém a análise actual; **Niche Finder Apify** é uma área vazia reservada para desenvolvimento futuro. Abra **Configurações > Configurações Técnicas** e reveja. O menu **Pipeline** contém **Criação de Vídeos**, **Criação de Músicas**, **Upload** e **Limpador de Metadados**. O menu **Configurações** contém **Canais**, **Blueprints**, **MCP** e **Configurações Técnicas**. Para YouTube, preencha primeiro o par **OAuth Client ID + OAuth Client Secret** se pretende autorizar uploads. A **YouTube Data API Key** é uma credencial Google Cloud diferente e fica numa área opcional, apenas para o método oficial de métricas; Client ID + Client Secret não formam uma API Key.

| Configuração | Finalidade |
|---|---|
| Porta Streamlit | Definir a porta local da UI |
| Pasta MoneyPrinterTurbo | Indicar o clone local que será sincronizado com `config.toml` |
| YouTube Data API Key (opcional) | Permitir o método oficial Data API para métricas públicas; não é necessária para a página pública nem para OAuth |
| YouTube OAuth Client ID | Identificar a aplicação OAuth 2.0 do Google para autorizar operações autenticadas, como upload |
| YouTube OAuth Client Secret | Secret do mesmo cliente OAuth 2.0; não é uma Data API Key nem um token de acesso |
| YouTube upload principal | Lógica do `youtube-automation-agent` adaptada e executada dentro do Thunderbolt |
| OAuth directo de redundância | Caminho alternativo accionado automaticamente se o agente falhar |
| TikTok Client ID/Secret | Credenciais da aplicação; Redirect URI, scopes e autorização ficam no TikTok for Developers Playground |
| Kaggle Username | Nome da conta Kaggle usada para publicar e executar a kernel remota |
| Kaggle API Key | Chave da conta Kaggle, guardada mascarada apenas em `storage/state/settings.json` |
| Slug da kernel Kaggle | Identificador da kernel remota, por padrão `thunderbolt-niche-finder` |

As credenciais devem ser inseridas apenas na configuração local. A Kaggle API Key é usada somente pelo executor remoto para publicar a kernel, consultar o estado e obter os resultados pequenos; o dataset não é descarregado para `storage/data/niches`. A Data API Key, o OAuth Client ID e o OAuth Client Secret são valores diferentes; Client ID + Secret não geram uma API Key nem um token OAuth até a conta ser autorizada. Não coloque nenhum deles no GitHub, no `package.json`, em blueprints ou em ficheiros de estado versionados.

## 9. Testar as áreas principais

Após iniciar a aplicação, valide o seguinte percurso:

1. **Início:** confirme que a UI abre, mostra o estado local, as métricas e os cards das filas do Pipeline, sem botões de acções rápidas.
2. **Blueprints:** coloque um JSON em `~/.thunderbolt/storage/blueprints/importados/` (Windows: `%LOCALAPPDATA%\\THUNDERBOLT\storage\blueprints\importados\`) ou use o carregador da interface.
3. **Brandings:** abra a subaba **Brandings** e confirme a listagem dos ficheiros JSON.
4. **Canais:** em **Importar do YouTube**, use o método **Página pública — sem API Key** com um URL `/channel/UC...`, um handle ou uma subpágina `/videos`; o parser resolve o ID, consulta a página pública e tenta o RSS quando necessário. Confirme que o resultado abre o formulário de revisão sem Data API Key. Se o canal não existir ou não fornecer metadados, confirme a mensagem clara e que o formulário de uma pesquisa anterior desaparece. A Data API é opcional e fica separada; em **Cadastro manual**, preencha os dados sem qualquer consulta externa.
5. **Niche Finder Kaggle:** abra o menu expansível **Niche Finder**, seleccione **Niche Finder Kaggle**, defina os parâmetros dentro do conteúdo principal e confirme que não há preparação automática. Antes do clique, não deve existir download de dataset nem análise. Clique em **Analisar Nichos** para iniciar a preparação dos dados e a análise; depois altere país, engagement, datas e tags e clique novamente para aplicar os novos parâmetros. Abra também **Niche Finder Apify** e confirme que a página está vazia, informativa e sem operações.
6. **Pipeline > Criação de Vídeos:** teste primeiro o modo **Canal específico** e depois os modos de lote.
7. **Criação de Vídeos > Vídeos:** verifique o estado `to_do` e os botões **Iniciar** e **Parar** dentro da subaba. Confirme também que **Criação de Músicas** mostra o mesmo fluxo com título próprio.
8. **Upload:** configure o OAuth Client ID e Secret, autorize primeiro o **youtube-automation-agent** na própria aba, confirme o estado **pronto para publicar**, preencha título/descrição/tags e publique um MP4 real. O botão **Autorizar fallback OAuth** existe apenas para redundância; a Data API Key, se configurada, é exclusivamente para consultas oficiais públicas e nunca substitui OAuth.
9. **Pipeline > Limpador de Metadados:** suba um vídeo de terceiro, preencha título, preview, links, timestamps e tags, aplique a limpeza e descarregue a cópia limpa e o manifesto JSON. O original fica preservado e vídeos das páginas de criação não são aceites nesta área.
10. **Configurações > Configurações Técnicas:** confirme que os caminhos e credenciais estão locais e não aparecem no Git.
11. **Criação de Vídeos:** confirme que `Pexels/Pixabay` substitui o label antigo, que `Estilo IA` aparece apenas em `full_ia` e que `Apenas Música` exige áudio e guarda `background_mode=none`.
12. **Automação:** no cartão de cada canal, escolha o **Blueprint padrão** e a **Voz padrão**, clique em `Guardar` e confirme que o resumo do cartão se actualiza. Configure também **Automação ON** e um horário `HH:MM`; confirme a lista de vídeos cadastrados. Os mesmos defaults aparecem em **Canais** e são usados em novas tarefas. Inicie o Thunderbolt pelo launcher, confirme o aviso verde **Worker activo** e verifique que o relógio apresentado corresponde ao computador. O worker cria no máximo um lote por canal por dia quando o horário local coincide.
13. **Configurações > Configurações Técnicas > Teste de vozes:** teste Edge/Azure ou provider configurado e confirme reprodução/download sem criação de tarefa.
14. **Upload directo:** configure manualmente cookies, sessionInfo e INNERTUBE_API_KEY, atribua o `DELEGATED_SESSION_ID` no canal e teste apenas com um vídeo de validação. O método envia chunks de 256 KiB e não extrai cookies do navegador.
15. **Configurações > MCP > Client MCP:** confirme que Short Video Maker, AutoVio, OpenMontage e OpenCut aparecem com as portas padrão editáveis. O estado **Activo** é uma preferência local; a detecção deve indicar **Não detectado** quando os serviços externos não estiverem instalados ou iniciados.
16. **Configurações > MCP > Servidor MCP:** abra a subaba, mantenha o host `127.0.0.1`, active **Servidor MCP ON** e clique em **Guardar e iniciar Servidor MCP**. Confirme o endpoint `/mcp` e o health endpoint `/health`. Mantenha **Permitir ferramentas de escrita** desactivado até precisar que um agente crie lotes.
17. **Configurações > MCP > Skill:** clique em **Guardar skill localmente** e confirme o ficheiro em `storage/skills/moneyprinterturbo-video.md`; opcionalmente use **Descarregar skill .md** para obter a cópia através do navegador.

## Niche Finder

A página **Niche Finder Kaggle** integra a lógica adaptada do projecto open source [johanfortus/Niche-Finder](https://github.com/johanfortus/Niche-Finder), cujo projecto original usa K-Means e FP-Growth sobre o dataset público [Trending Youtube Video Statistics (113 Countries)](https://www.kaggle.com/datasets/asaniczka/trending-youtube-videos-113-countries). No Thunderbolt não existe Flask, rota HTTP adicional, template HTML, JavaScript D3 ou segundo processo; toda a análise é síncrona no Streamlit.

Ao abrir a página, o Thunderbolt não prepara dados públicos, não descarrega o dataset e não inicia a análise. A instalação das dependências continua automática, mas a operação é manual: os parâmetros ficam dentro da própria aba e o utilizador deve clicar em **Analisar Nichos**. Só depois desse clique o KaggleHub prepara ou reutiliza a cache local; não há upload de CSV, botão de download manual ou selector de ficheiros.

Os parâmetros da UI são número de clusters entre 2 e 10, suporte mínimo entre 0,01 e 0,50, país, engagement, intervalo de datas e tags, todos dentro da área principal da aba. O núcleo normaliza os dados, calcula engagement, aplica filtros, faz transformação logarítmica e standardização, executa K-Means e calcula itemsets/regras com FP-Growth. Não são apresentados resultados até ao primeiro clique em **Analisar Nichos**; o mesmo botão aplica alterações posteriores aos filtros. Os resultados são DataFrames de clusters, itemsets frequentes, regras de associação e dados analisados; o gráfico de dispersão é criado nativamente com Plotly.

As dependências adicionais — `scikit-learn`, `mlxtend`, `plotly`, `seaborn`, `matplotlib` e `kagglehub` — são instaladas pelo procedimento normal de `npx`. Em instalações existentes, execute novamente `npx.cmd --yes @danhachuel/thunderbolt@0.2.35 install`; o instalador detecta e reutiliza o que já estiver válido.

## Pipeline: Criação de Vídeos, Criação de Músicas e Automação

O modo `Pexels/Pixabay` representa materiais de stock. Ao seleccionar `full_ia`, o selector `Estilo IA` apresenta os 12 estilos disponíveis. Ao seleccionar `Apenas Música`, a UI obriga a escolher uma música existente, carregar um ficheiro ou solicitar uma música a um endpoint Suno configurado. O vídeo recebe `background_mode=none`, sem fundo Pexels/Pixabay ou IA.

A aba **Automação** lista os canais e vídeos, permite escolher e guardar **Blueprint padrão** e **Voz padrão** por canal, guarda **Automação ON** e valida horários diários no formato `HH:MM`. Os valores ficam sincronizados com o editor existente no cartão da aba **Canais** e são copiados para novas tarefas. O launcher inicia o worker local, que consulta o relógio do computador, cria lotes agendados na fila e evita duplicar o mesmo canal no mesmo dia.

A área **Teste de vozes**, dentro de **Configurações > Configurações Técnicas**, é isolada da pipeline. O preview pode ser reproduzido e descarregado de `storage/voice_previews/`. Caminhos vazios, directórios, ficheiros vazios e previews sem permissões de leitura são ignorados com uma mensagem clara, sem traceback. Se uma instalação antiga mostrar que `edge-tts` está em falta, execute `npx.cmd --yes @danhachuel/thunderbolt install`; o detector reinstala apenas a dependência ausente.

## Upload directo

A subaba **Upload directo** adapta o [YouTube-Video-Upload-Frontend-Api](https://github.com/Nojus10/YouTube-Video-Upload-Frontend-Api). Em cada canal, preencha `DELEGATED_SESSION_ID`; em Configurações, preencha manualmente os cookies `SID`, `SSID`, `HSID`, `APISID`, `SAPISID`, o token `sessionInfo` e `INNERTUBE_API_KEY`. O adaptador valida o vídeo, cria a sessão interna e envia chunks múltiplos de 256 KiB. Estes valores são segredos locais e não devem ser enviados para o Git.

## MCP e integrações externas

A subaba **Client MCP**, em **Configurações > MCP**, é um configurador local de quatro serviços opcionais. As portas iniciais são `3123` para Short Video Maker, `3001` para AutoVio, `8000` como referência editável para OpenMontage e `8787` para a API do OpenCut. A página consulta apenas `http://127.0.0.1:<porta>/` com timeout curto; não clona, instala ou inicia processos externos.

A subaba **Servidor MCP**, em **Configurações > MCP**, disponibiliza, após activação explícita, `http://127.0.0.1:3031/mcp` por JSON-RPC sobre HTTP POST. Para configurar um agente compatível, use esse URL como endpoint MCP. Se o host for alterado para uma interface externa, preencha primeiro um token e trate-o como segredo. O servidor disponibiliza ferramentas de leitura por padrão; a criação de lotes só é exposta quando **Permitir ferramentas de escrita** está activado.

A subaba **Skill**, em **Configurações > MCP**, contém as acções para guardar a skill anexada em `storage/skills/` ou descarregá-la como Markdown. Esta pasta fica fora dos estados JSON e é criada pelo instalador e pelo launcher. Os quatro repositórios continuam fora do pacote npm.

## 12. Limpador de Metadados

A aba **Limpador de Metadados** recebe somente vídeos externos já prontos. O ficheiro enviado é copiado para `storage/metadata_cleaner/originals/`; a aplicação não altera o original. Ao aplicar a operação, o FFmpeg remove os metadados existentes do contentor e cria uma nova versão em `storage/metadata_cleaner/outputs/` com o título, descrição, tags, idioma e outros campos preenchidos.

A descrição combina **Preview**, **Links** e **Timestamps**, seguindo a estrutura do workflow `YTBMetadataGenerator.json`. O preview recomendado tem entre 100 e 200 caracteres; os capítulos devem começar por `00:00`. O manifesto JSON descarregado contém os campos para um fluxo posterior de upload. Esta adaptação local não faz scraping automático via RSS/Apify nem publica directamente no YouTube.

Se a limpeza falhar, confirme a disponibilidade do FFmpeg em **Configurações > Configurações Técnicas > Caminho FFmpeg** ou execute `doctor`. O processo usa `-map_metadata -1` para remover os metadados existentes e `-c copy` para evitar uma re-encodificação desnecessária sempre que o contentor permitir.

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
