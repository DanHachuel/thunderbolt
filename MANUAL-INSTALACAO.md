# Manual de Instalação — Content-Hermes UI

Este manual descreve a instalação local da UI Content-Hermes, baseada no MoneyPrinterTurbo, utilizando o pacote npm `@danhachuel/content-hermes-ui`. O fluxo recomendado instala automaticamente o ambiente Python, as dependências da aplicação, as dependências do MoneyPrinterTurbo, o Streamlit e o suporte FFmpeg através de `imageio-ffmpeg`.

> **Versão deste manual:** 0.2.0  
> **Pacote npm:** `@danhachuel/content-hermes-ui`  
> **Porta padrão da UI:** `localhost:3030`  
> **Repositório:** [github.com/DanHachuel/content-hermes-ui](https://github.com/DanHachuel/content-hermes-ui)

## 1. O que será instalado

A instalação assistida cria um ambiente local separado para evitar misturar as dependências do Content-Hermes com outros projectos Python.

| Componente | Local ou comportamento padrão |
|---|---|
| Python | Python 3.11 ou superior já instalado no sistema |
| Ambiente virtual | `~/Hermes-UI/.venv` (Windows: `C:\Users\<utilizador>\Hermes-UI\.venv`) |
| MoneyPrinterTurbo | `~/Hermes-UI/MoneyPrinterTurbo` (Windows: `C:\Users\<utilizador>\Hermes-UI\MoneyPrinterTurbo`) |
| Storage Content-Hermes | `~/Hermes-UI/storage` (Windows: `C:\Users\<utilizador>\Hermes-UI\storage`) |
| Dependências Content-Hermes | Instaladas a partir do `requirements.txt` incluído no pacote |
| Dependências MoneyPrinterTurbo | Instaladas a partir do `requirements.txt` do repositório oficial |
| Streamlit | Instalado como dependência Python |
| FFmpeg | Disponibilizado pelo pacote Python `imageio-ffmpeg` |
| Porta da aplicação | `3030`, configurável com `HERMES_PORT` |

A aplicação não instala drivers de GPU, Docker, modelos Whisper, chaves de API, cookies, tokens ou credenciais externas. Esses componentes devem ser configurados separadamente quando forem necessários.

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
npx.cmd --yes @danhachuel/content-hermes-ui install
npx.cmd --yes @danhachuel/content-hermes-ui doctor
npx.cmd --yes @danhachuel/content-hermes-ui
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
cmd /c npx.cmd --yes @danhachuel/content-hermes-ui install
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

O Python deve apresentar a versão `3.11` ou superior. Se estiver no Windows sem Python, o instalador tenta executar automaticamente `winget install --exact --id Python.Python.3.11`. Se `winget` não estiver disponível, instale o App Installer/Microsoft Store ou Python a partir de [python.org](https://www.python.org/downloads/windows/) e repita a instalação. Em macOS/Linux, o instalador não assume permissões administrativas para instalar Python no sistema; instale-o pelo gestor de pacotes ou use `HERMES_PYTHON`.

## 3. Instalação recomendada via npx

Execute:

Windows PowerShell ou MobaXterm:

```powershell
npx.cmd --yes @danhachuel/content-hermes-ui@0.2.5 install
```

Linux/macOS:

```bash
npx --yes @danhachuel/content-hermes-ui@0.2.5 install
```

A instalação é **idempotente**: reutiliza a pasta única `Hermes-UI` e não cria uma pasta nova para cada versão do pacote. Em instalações Windows antigas, detecta `C:\Users\<utilizador>\AppData\Local\hermes`, migra os dados para `C:\Users\<utilizador>\Hermes-UI` quando a pasta nova ainda não existe e remove a pasta antiga depois da migração. Se a pasta nova já existir, a instalação antiga é removida para evitar duplicação.

O instalador irá:

1. procurar Python 3.11 ou superior;
2. se estiver no Windows e Python não existir, instalar Python 3.11 automaticamente pelo `winget`;
3. criar o ambiente virtual `~/Hermes-UI/.venv` (Windows: `C:\Users\<utilizador>\Hermes-UI\.venv`);
4. clonar o repositório oficial MoneyPrinterTurbo para `~/Hermes-UI/MoneyPrinterTurbo` (Windows: `C:\Users\<utilizador>\Hermes-UI\MoneyPrinterTurbo`);
5. instalar as dependências do Content-Hermes;
6. instalar as dependências Python do MoneyPrinterTurbo;
7. instalar `imageio-ffmpeg` para disponibilizar FFmpeg no ambiente Python;
8. criar `~/Hermes-UI/storage/state/settings.json` (Windows: `C:\Users\<utilizador>\Hermes-UI\storage\state\settings.json`);
9. registar o caminho local do MoneyPrinterTurbo;
10. deixar o ambiente pronto para o comando de arranque.

No Windows, o caminho padrão é construído a partir de `USERPROFILE`, não de `HOME`. Assim, mesmo em MobaXterm, a pasta padrão será `C:\Users\<utilizador>\Hermes-UI`, salvo se `HERMES_HOME` for definido explicitamente. A limpeza automática pode ser desactivada apenas para uma migração manual através de `HERMES_KEEP_LEGACY=1`, mas isso deixará a instalação antiga no disco.

A instalação pode demorar alguns minutos, especialmente durante a instalação de `faster-whisper` e de bibliotecas de processamento de vídeo.

### 3.1 Usar o instalador com uma cópia existente do MoneyPrinterTurbo

Se já possui o MoneyPrinterTurbo clonado, indique o caminho.

Linux ou macOS:

```bash
MONEYPRINTER_PATH=/caminho/para/MoneyPrinterTurbo \
  npx --yes @danhachuel/content-hermes-ui install
```

Windows PowerShell:

```powershell
$env:MONEYPRINTER_PATH="C:\caminho\MoneyPrinterTurbo"
npx --yes @danhachuel/content-hermes-ui install
```

O instalador reutiliza a pasta existente e instala as suas dependências no ambiente virtual do Content-Hermes.

### 3.2 Instalar apenas a UI

Se pretende testar a interface sem clonar o MoneyPrinterTurbo:

```bash
npx --yes @danhachuel/content-hermes-ui install --skip-moneyprinter
```

Este modo instala o ambiente Python e as dependências da UI, mas não instala o conjunto de dependências do MoneyPrinterTurbo nem configura a integração local com ele.

### 3.3 Controlar os caminhos de instalação

É possível alterar o directório principal e o ambiente Python:

Linux ou macOS:

```bash
HERMES_HOME=/caminho/content-hermes \
MONEYPRINTER_PATH=/caminho/MoneyPrinterTurbo \
HERMES_VENV=/caminho/content-hermes/.venv \
npx --yes @danhachuel/content-hermes-ui install
```

Windows PowerShell:

```powershell
$env:HERMES_HOME="C:\ContentHermes"
$env:MONEYPRINTER_PATH="C:\MoneyPrinterTurbo"
$env:HERMES_VENV="C:\ContentHermes\.venv"
npx --yes @danhachuel/content-hermes-ui install
```

## 4. Diagnóstico antes de iniciar

Depois da instalação, execute:

```bash
npx --yes @danhachuel/content-hermes-ui doctor
```

Também é possível usar:

```bash
npx --yes --package=@danhachuel/content-hermes-ui content-hermes --check
```

Uma saída saudável apresenta versões de Python e Streamlit e um caminho de FFmpeg. Por exemplo:

```text
Ambiente OK. Python: 3.11.x; Streamlit: 1.x.x; FFmpeg: /.../ffmpeg
```

Se o diagnóstico indicar que FFmpeg não foi detectado, execute novamente a instalação ou verifique se `imageio-ffmpeg` está presente no ambiente virtual.

## 5. Iniciar a aplicação

Depois de instalar e diagnosticar:

```bash
npx --yes @danhachuel/content-hermes-ui
```

Abra no navegador:

```text
http://localhost:3030
```

O launcher usa o ambiente virtual em `~/Hermes-UI/.venv` (Windows: `C:\Users\<utilizador>\Hermes-UI\.venv`) quando ele existe. Se for necessário executar numa porta diferente:

Linux ou macOS:

```bash
HERMES_PORT=3040 npx --yes @danhachuel/content-hermes-ui
```

Windows PowerShell:

```powershell
$env:HERMES_PORT="3040"
npx --yes @danhachuel/content-hermes-ui
```

Para parar a aplicação, volte ao terminal e pressione `Ctrl+C`.

## 6. Instalação global via npm

Como alternativa ao `npx`, instale o comando globalmente:

```bash
npm install --global @danhachuel/content-hermes-ui
```

Depois execute:

```bash
content-hermes
```

Diagnóstico:

```bash
content-hermes doctor
```

Instalação assistida:

```bash
content-hermes install
```

A instalação global controla apenas o launcher Node.js. O ambiente Python continua a ser criado em `~/Hermes-UI/.venv` (Windows: `C:\Users\<utilizador>\Hermes-UI\.venv`).

## 7. Instalação manual para desenvolvimento

Use esta opção quando quiser trabalhar directamente a partir do repositório GitHub.

```bash
git clone https://github.com/DanHachuel/content-hermes-ui.git
cd content-hermes-ui
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

Na primeira execução, abra **Configurações** e reveja:

| Configuração | Finalidade |
|---|---|
| Pasta MoneyPrinterTurbo | Indicar onde o projecto base está instalado |
| Porta Streamlit | Definir a porta local da UI |
| URL Hermes | Configurar eventual orquestrador local |
| YouTube Data API key | Permitir importar nome, handle e métricas de canais |
| TikTok Client Key/Secret | Preparar a Content Posting API |
| TikTok Redirect URI | Definir o callback registado no TikTok |
| TikTok access token | Usar uma autorização já concluída, quando aplicável |

As chaves devem ser inseridas apenas na configuração local. Não as coloque no GitHub, no `package.json`, em blueprints ou em ficheiros de estado versionados.

## 9. Testar as áreas principais

Após iniciar a aplicação, valide o seguinte percurso:

1. **Dashboard:** confirme que a UI abre e mostra o estado local.
2. **Blueprints:** coloque um JSON em `~/Hermes-UI/storage/blueprints/importados/` (Windows: `C:\Users\<utilizador>\Hermes-UI\storage\blueprints\importados\`) ou use o carregador da interface.
3. **Brandings:** abra a subaba **Brandings** e confirme a listagem dos ficheiros JSON.
4. **Canais:** cadastre um canal manualmente ou importe-o depois de configurar a YouTube Data API.
5. **Novo vídeo:** teste primeiro o modo **Canal específico** e depois os modos de lote.
6. **Vídeos:** verifique o estado `to_do` e os botões **Iniciar** e **Parar**.
7. **Upload:** confirme os destinos configurados e os estados de pré-requisito.
8. **Configurações:** confirme que os caminhos e credenciais estão locais e não aparecem no Git.

## 10. Problemas frequentes

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
HERMES_PYTHON=/caminho/para/python3.11 npx --yes @danhachuel/content-hermes-ui install
```

No Windows PowerShell:

```powershell
$env:HERMES_PYTHON="C:\Python311\python.exe"
npx --yes @danhachuel/content-hermes-ui install
```

### Git não encontrado

Instale Git a partir de [git-scm.com](https://git-scm.com/downloads), ou forneça uma cópia existente do MoneyPrinterTurbo através de `MONEYPRINTER_PATH`.

### Streamlit não está instalado

Execute:

```bash
npx --yes @danhachuel/content-hermes-ui install
npx --yes @danhachuel/content-hermes-ui doctor
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
npx --yes @danhachuel/content-hermes-ui doctor
```

O MoneyPrinterTurbo também permite indicar um caminho manual para FFmpeg na configuração local quando a detecção automática não funcionar.[1]

### A porta 3030 está ocupada

Use outra porta:

```bash
HERMES_PORT=3040 npx --yes @danhachuel/content-hermes-ui
```

### O MoneyPrinterTurbo não aparece na UI

Confirme o caminho na aba **Configurações** ou execute:

```bash
MONEYPRINTER_PATH=/caminho/MoneyPrinterTurbo npx --yes @danhachuel/content-hermes-ui install --skip-python-deps
```

Depois reinicie a aplicação.

### Dependências Python falham durante a instalação

Actualize pip e tente novamente:

```bash
npx --yes @danhachuel/content-hermes-ui install
```

Se uma dependência específica falhar, guarde o log completo e verifique a compatibilidade da versão Python. Python 3.11 é a opção mais conservadora para o MoneyPrinterTurbo.

### Modelos Whisper não estão disponíveis

A instalação das dependências não baixa necessariamente todos os modelos grandes. O MoneyPrinterTurbo pode descarregar o modelo Whisper na primeira utilização, dependendo da configuração escolhida. Para ambientes sem acesso de rede, siga as instruções do projecto base para descarregar e colocar o modelo localmente.[1]

## 11. Desinstalação

Para remover o pacote global:

```bash
npm uninstall --global @danhachuel/content-hermes-ui
```

Para remover o ambiente e os dados locais:

Linux ou macOS:

```bash
rm -rf ~/Hermes-UI
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force "$HOME\\Hermes-UI"
```

> A remoção de `~/Hermes-UI` (Windows: `C:\Users\<utilizador>\Hermes-UI`) apaga estado JSON, blueprints, configurações e artefactos locais. Faça uma cópia de segurança antes de executar o comando.

## 12. Segurança

Nunca publique ou envie por chat:

- tokens npm;
- chaves YouTube, TikTok ou outros serviços;
- cookies e tokens OAuth;
- ficheiros de configuração com segredos;
- artefactos privados de canais.

Use secrets do GitHub Actions apenas para publicação do pacote. Para execução local, mantenha credenciais fora do repositório e use a área de configurações local ou variáveis de ambiente.

## 13. Referências

[1]: https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README-en.md — MoneyPrinterTurbo: requisitos, instalação, dependências, Streamlit e FFmpeg.

[2]: https://www.npmjs.com/package/@danhachuel/content-hermes-ui — Pacote npm publicado.

[3]: https://github.com/DanHachuel/content-hermes-ui — Repositório GitHub do Content-Hermes UI.
