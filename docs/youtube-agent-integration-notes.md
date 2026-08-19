# Auditoria do youtube-automation-agent

Data da auditoria: 2026-08-19.

## Repositório

Fonte: https://github.com/darkzOGx/youtube-automation-agent

O repositório declara licença MIT no metadata do GitHub e contém `LICENSE`. A versão auditada é o commit `cb6a1e78c170da058295b8a7743d00b93d36f254`.

## Arquitectura relevante

O agente é uma aplicação Node.js/Express com um `PublishingSchedulingAgent`. O agente de publicação é inicializado a partir do gestor de credenciais, obtém um cliente YouTube autenticado e publica a partir de um item da fila.

A lógica principal observada em `agents/publishing-scheduling-agent.js` é:

1. Validar que existe um vídeo real, que é ficheiro e que tem extensão `.mp4`; recusar placeholders/simulações.
2. Construir `snippet` com título, descrição, tags, `categoryId`, `defaultLanguage` e `defaultAudioLanguage`.
3. Construir `status` com `privacyStatus`, `publishAt` e `selfDeclaredMadeForKids: false`.
4. Executar `youtube.videos.insert` com as partes `snippet,status` e upload do ficheiro em stream.
5. Depois de receber o ID, tentar publicar thumbnail com `youtube.thumbnails.set` e legendas com `youtube.captions.insert`.
6. Guardar o ID e a URL no item da fila.

O gestor de credenciais do agente usa `googleapis`, OAuth 2.0, `access_type: offline`, `prompt: consent` e guarda tokens localmente. O agente permite uma configuração própria de credenciais e um servidor de callback local. Esta autenticação é a base técnica do agente, não uma automação de navegador.

## Decisão de adaptação

O Thunderbolt não vai arrancar um segundo servidor Node nem depender de uma instalação separada do agente. A lógica de publicação será adaptada para dentro de `integrations/youtube_upload.py`, mantendo a semântica do agente: validação de ficheiro, metadados `snippet/status`, upload resumível, thumbnail, legendas e resultado com ID/URL.

O fluxo primário será nomeado e exposto como `youtube-automation-agent (adaptado)`. O fallback será um caminho OAuth directo separado, chamado apenas quando o adaptador primário falhar. Ambos reutilizam o token OAuth local do Thunderbolt quando necessário, mas a ordem de execução e os estados de erro ficam explícitos na UI.

O token ficará em `storage/state/youtube_oauth_token.json`, coberto pelo `.gitignore` existente. Client ID, Client Secret e Data API Key continuam em settings; o Data API Key será usado apenas para consultas públicas, nunca para publicação.

## Fontes

- Repositório: https://github.com/darkzOGx/youtube-automation-agent
- Agente de publicação: `agents/publishing-scheduling-agent.js`
- Gestor OAuth: `utils/credential-manager.js`, `modern-auth.js` e `oauth-server.js`
- Licença: `LICENSE` no repositório fonte, MIT

## Cadastro público de canais sem API Key

Foi validado em 2026-08-19 que a página pública `https://www.youtube.com/channel/<id>/about` devolve `ytInitialData` com `channelMetadataRenderer`, incluindo nome, descrição, ID, URL pública e thumbnail, sem exigir chave. O HTML público actual pode não incluir inscritos ou total de vídeos para todos os canais; nesses casos o Thunderbolt deixa esses campos como desconhecidos em vez de bloquear a importação ou inventar valores.

A UI oferece agora duas subabas independentes: **Importar do YouTube**, com método padrão **Página pública — sem API Key** e método opcional **YouTube Data API — API Key opcional**; e **Cadastro manual**, que não executa nenhuma consulta nem exige chave. A API Key continua reservada para a opção oficial de métricas quando o utilizador a configurar.
