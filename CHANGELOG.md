# Changelog

## 0.5.90 — 2026-09-05

- Adicionada em **Documentação** a aba **Tutorial YouTube Data API Key (Public Data)**, baseada no documento fornecido do Google Drive.
- O tutorial explica a criação, restrição, configuração no campo `INNERTUBE_API_KEY`, quota e segurança da chave para dados públicos.

## 0.5.89 — 2026-09-05

- Corrigida a orientação do tutorial OAuth: o fluxo de callback local requer uma credencial **Aplicativo para computador (Desktop app)**, não **Aplicativo da Web**.
- A mensagem `redirect_uri_mismatch` agora identifica explicitamente o tipo correcto de credencial e o callback loopback utilizado.
- Actualizada a configuração documentada para usar os campos Client ID e Client Secret em **Contas Google** na interface do Thunderbolt.

## 0.5.88 — 2026-09-04

- Corrigido o erro Windows `WinError 10048` ao autorizar contas Google via OAuth quando a porta local `8765` já está ocupada.
- O callback OAuth tenta primeiro a porta configurada e faz retry automático numa porta loopback livre, mantendo a autenticação normal do Google.
- Adicionado teste de regressão que reproduz a porta ocupada e confirma a autorização na porta dinâmica.

## 0.5.87 — 2026-09-04

- Corrigida a renovação de `sessionInfo` quando o executável Chromium do Playwright não existe no cache do Windows.
- O instalador passa a executar `playwright install chromium` depois de instalar as dependências Python.
- A renovação tenta primeiro o Google Chrome instalado e, se necessário, instala automaticamente o Chromium gerido pelo Playwright antes de falhar.
- Adicionada validação explícita da dependência Playwright no diagnóstico do launcher e cobertura de testes para o fallback do browser.

## 0.5.86 — 2026-09-04

- Adicionada a dependência Python `deno`, com binário gerido automaticamente e suporte multiplataforma.
- O downloader yt-dlp passa a receber explicitamente `--js-runtimes deno:<caminho>` através da API Python.
- Actualizado o yt-dlp para o extra `default`, incluindo os scripts EJS necessários para os desafios JavaScript do YouTube.
- Adicionado fallback para um executável `deno` disponível no `PATH` e diagnóstico do runtime em `dependency_status()`.

## 0.5.85 — 2026-09-04

- Corrigido o `UnboundLocalError` em Automação Youtube ao renderizar o Thumbnail Blueprint dos cards de canais.
- O valor inicial é agora calculado antes da renderização e continua a ser actualizado após a selecção do Blueprint.

## 0.5.84 — 2026-09-04

- Corrigida a regressão de percentagem nos cards de vídeos em `doing` quando tarefas antigas são retomadas.
- O progresso persistido passa a ser monotónico: uma actualização posterior nunca reduz o maior avanço confirmado.
- Mantido o watchdog de actividade para marcar tarefas sem heartbeat como falhadas, evitando execução indefinida.

## 0.5.83 — 2026-09-04

- Adicionados ao Analista Growth Youtube os indicadores de configuração da YouTube Data API v3 e da YouTube Analytics API.
- Os estados usam o padrão visual existente: verde “Configured” e amarelo “Missing configuration”.

## 0.5.82 — 2026-09-04

- Reorganizados os cards de canais da aba Automação Youtube numa grelha compacta de duas linhas.
- Removidos o selector Formato e a informação Formato redundantes dos cards de canais.
- Reduzido o espaço vertical vazio e ajustadas as larguras dos controlos.
- O botão Guardar passou a usar o estilo azul primário da interface.

## 0.5.81 — 2026-09-04

- Implementado o Dashboard de Growth Youtube com Nota Geral do canal e oito cards categorizados.
- Adicionados os três cards de destaque — Validação de Nicho, Thumbnail e Título dos Vídeos — e cinco cards secundários com tabelas KPI, Valor, Meta e Status.
- Adicionada a indicação “Análise concluída” junto ao botão de análise.
- KPIs sem dados disponíveis continuam identificados como “A verificar”, sem inventar métricas privadas do YouTube Analytics.

## 0.5.80 — 2026-09-04

- Corrigida a rotação das chaves individuais das fontes de vídeo stock.
- Os cartões Pexels e Pixabay activos passam a ser tentados pela prioridade configurada, uma chave por tentativa, antes de avançar para o provider seguinte.
- Falhas de actividade, quota ou credenciais numa chave passam correctamente para a próxima chave elegível; a configuração legada sem cartões mantém o comportamento anterior.

## 0.5.79 — 2026-09-04

- Corrigido o refresh da versão 0.5.78: as páginas completas de Automação Youtube e Automação Tiktok deixaram de ser fragmentos.
- O refresh automático de cinco segundos ficou limitado exclusivamente às secções dos cards de vídeos e respectivas barras de progresso.

## 0.5.78 — 2026-09-04

- Corrigida a actualização das barras de progresso nas abas **Automação Youtube** e **Automação Tiktok**.
- As duas filas passam a actualizar automaticamente a cada cinco segundos enquanto a aba está aberta, sem necessidade de premir F5.
- O refresh só ocorre enquanto a respectiva aba está aberta, sem afectar as restantes páginas.

## 0.5.77 — 2026-09-04

- Aplicado à aba **Automação Tiktok** o mesmo arranque manual do pipeline usado no YouTube.
- O botão **Start** de tarefas TikTok agora usa a rotina comum para iniciar tarefas `to_do` e `doing` ou repetir tarefas `blocked`/`failed`, permitindo ao launcher iniciar o worker e o processo de geração do vídeo sem automação horária activa.

## 0.5.76 — 2026-09-04

- Corrigido o arranque do pipeline ao clicar em **Start** num vídeo parado, mesmo quando não existe nenhum canal com automação activa.
- O launcher passa a monitorizar os estados `to_do` e `doing`, que são os estados realmente consumidos pelo worker do pipeline.

## 0.5.56 — 2026-09-04

- Corrigido o encerramento por `Ctrl+C` no launcher Streamlit.
- O handler SIGINT agora tenta parar o event loop, aguarda uma janela curta de drenagem e encerra sem callbacks tardios.
- Mantidos os shims UTF-8, as variáveis de ambiente e a protecção contra substituição do handler pelo Streamlit.
- Reduzida a poluição do terminal causada por tracebacks `RuntimeError: Event loop is closed` e `asyncio.exceptions.CancelledError` durante o shutdown.
