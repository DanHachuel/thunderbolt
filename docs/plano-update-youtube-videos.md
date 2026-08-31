# Plano técnico — Update Youtube Vídeos

**Autor:** Manus AI  
**Estado:** Planeamento, sem alterações funcionais implementadas

## Objectivo

Criar em **Pipeline Vídeos**, imediatamente abaixo de **Uploads**, a aba **Update Youtube Vídeos**. A aba deverá listar os vídeos publicados dos canais YouTube seleccionados, permitir editar título, descrição e thumbnail sem substituir o ficheiro de vídeo, e enviar as alterações através da operação interna `YOUTUBE_UPDATE_VIDEO`, distinta de `YOUTUBE_UPLOAD_VIDEO`.

## Pesquisa técnica

A operação oficial `videos.update` actualiza metadados de um vídeo e tem custo de quota de 50 unidades por chamada. Para uma actualização de `snippet`, o corpo precisa conter `id`, `snippet.title` e `snippet.categoryId`; a API permite alterar `snippet.title` e `snippet.description`, entre outros campos. A documentação alerta que os campos mutáveis incluídos em `part` podem ser substituídos integralmente e que valores omitidos podem ser apagados, portanto a implementação deve primeiro carregar o recurso actual e enviar um payload completo e controlado. A operação exige OAuth com, no mínimo, `youtube`, `youtube.force-ssl` ou `youtubepartner`.[1]

A thumbnail não deve ser enviada dentro de `videos.update`. A API possui a operação separada `thumbnails.set`, que recebe `videoId` e upload binário, aceita JPEG/PNG e impõe limite de 2 MB; a operação tem custo aproximado de 50 unidades e requer autorização adequada, como `youtube.upload`, `youtube` ou `youtube.force-ssl`.[2]

A autenticação deve continuar a utilizar as credenciais Google já configuradas no Thunderbolt. A documentação oficial confirma que o YouTube Data API usa OAuth 2.0 para dados privados e que contas de serviço não são suportadas para acesso a contas YouTube.[3]

## Arquitectura recomendada

A solução recomendada é implementar um adaptador dedicado em `integrations/youtube_update.py`, preservando a separação entre a operação oficial de metadados e a operação de thumbnail. O adaptador deverá receber o canal, a conta Google seleccionada e o `video_id`, carregar o vídeo actual, calcular um patch seguro e executar `videos.update` apenas quando houver alterações de título ou descrição. Se houver thumbnail nova, deverá normalizar a imagem para JPEG/PNG, garantir tamanho inferior a 2 MB e chamar `thumbnails.set` separadamente.

A interface deverá ficar em `app/main.py`, com uma função dedicada `render_update_youtube_videos()`. O selector de canal deve listar apenas canais cujo `platform` seja YouTube. Depois de seleccionado o canal, a aplicação deverá carregar os vídeos através da API autenticada, usando paginação e uma cache curta por canal. Cada vídeo aparecerá num card com thumbnail actual, título, descrição resumida, data, estado e URL. O card deverá abrir os campos editáveis e os botões de IA.

A operação de persistência deverá criar ou actualizar um registo local de auditoria com `video_id`, canal, campos alterados, resultado, timestamp e erro sanitizado. A fila ou tarefa deverá usar explicitamente `YOUTUBE_UPDATE_VIDEO`, nunca o fluxo de upload. O worker deverá reconhecer essa operação como uma tarefa de metadados e não procurar ficheiro de vídeo nem executar qualquer etapa de renderização.

## Fluxo de utilização

1. O utilizador abre **Pipeline Vídeos > Update Youtube Vídeos**.
2. Selecciona um canal YouTube; canais TikTok ficam excluídos.
3. O sistema lista os vídeos desse canal por API, com paginação e indicação de carregamento/erro.
4. O utilizador abre um card, revê título, descrição e thumbnail actual e altera apenas os campos desejados.
5. Pode escrever directamente ou usar um dos três comandos: **Gerar título**, **Gerar descrição** ou **Gerar título e descrição**. Não haverá botão de IA para thumbnail.
6. Cada comando de IA deve usar como contexto o idioma do vídeo/canal, o roteiro local associado quando existir, o título/descrição actuais e o Blueprint do canal. O resultado deve preencher os campos para revisão, nunca publicar automaticamente.
7. O botão **Actualizar no YouTube** mostra um resumo do que será enviado e executa `YOUTUBE_UPDATE_VIDEO` após a acção do utilizador.
8. O sistema apresenta o resultado por campo: metadados actualizados, thumbnail actualizada, ou erro específico.

## Contexto para geração por IA

A resolução do contexto deverá seguir esta ordem: idioma explícito do vídeo, idioma padrão do canal e, por último, idioma da configuração global. O roteiro deve ser procurado pelo `video_id`, `task_id` ou associação local do vídeo; quando não existir, o sistema deve informar que a geração foi feita sem roteiro. O Blueprint deve ser resolvido pelos mesmos helpers usados na criação de vídeos, incluindo o Blueprint de thumbnail apenas como referência visual se o título for gerado; ele não deve ser enviado à API do YouTube.

As instruções de geração devem exigir que o idioma seja respeitado, que o título seja adequado ao limite e às políticas do YouTube, que a descrição preserve links e informações importantes quando solicitado, e que nenhum texto seja publicado sem revisão. A saída estruturada deve conter apenas `title` e/ou `description`, conforme o botão escolhido.

## Layout proposto

| Área | Componente | Comportamento |
| --- | --- | --- |
| Cabeçalho | Selector de canal YouTube | Apenas canais YouTube activos ou seleccionados; botão para actualizar a lista |
| Lista | Cards dos vídeos | Thumbnail, título, descrição, data, estado, URL e video ID visível em modo secundário |
| Título | Text input | Valor actual; botão **Gerar título** |
| Descrição | Text area | Valor actual; botão **Gerar descrição** |
| IA combinada | Botão **Gerar título e descrição** | Preenche ambos os campos para revisão |
| Thumbnail | Upload de imagem | Sem botão de geração por IA; pré-visualização e validação JPEG/PNG até 2 MB |
| Acção | **Actualizar no YouTube** | Envia somente os campos alterados através de `YOUTUBE_UPDATE_VIDEO` |
| Resultado | Status e auditoria | Mostra sucesso parcial ou falha sem esconder o detalhe técnico útil |

## Segurança e integridade

O payload de `videos.update` deve usar `part=snippet` e preservar obrigatoriamente `categoryId`, título e descrição. Não deve incluir `status`, `recordingDetails`, `localizations` ou outras partes não editadas, para evitar alterações acidentais de privacidade, publicação ou configuração. Se o utilizador alterar apenas a descrição, o título actual deve ser reenviado; se alterar apenas o título, a descrição actual deve ser reenviada.

A operação deve validar que o `video_id` pertence ao canal seleccionado e que as credenciais correspondem à conta Google autorizada. Erros `401/403` devem indicar autorização insuficiente ou conta incorrecta; `404` deve indicar vídeo inexistente; `400` deve mostrar a validação relevante sem expor tokens. A thumbnail deve ser comprimida antes do upload e a imagem original deve permanecer no storage local para reprocessamento.

## Alternativas consideradas

| Abordagem | Trade-offs | Custo | Complexidade de configuração |
| --- | --- | --- | --- |
| **Adaptador oficial YouTube Data API + `YOUTUBE_UPDATE_VIDEO` recomendado** | Mais confiável, auditável e compatível com OAuth; exige quota e escopo de escrita | 50 unidades para `videos.update` e aproximadamente 50 para `thumbnails.set` | Média |
| Reutilizar o mecanismo directo do YouTube Studio | Pode aproveitar cookies e `DELEGATED_SESSION_ID`, mas é um contrato não oficial, mais frágil e difícil de manter; não deve substituir a operação solicitada | Sem quota oficial conhecida, mas com maior risco operacional | Alta |
| Apenas guardar alterações localmente para sincronização posterior | Mais simples e reversível, mas não satisfaz a necessidade de alterar o vídeo via API imediatamente | Baixo | Baixa |

## Fases de implementação

**Fase 1 — Contrato e adaptador.** Criar `YOUTUBE_UPDATE_VIDEO`, modelos de resultado e adaptador oficial para listar vídeos, actualizar snippet e enviar thumbnail. Adicionar testes com sessões HTTP simuladas, verificando preservação de `categoryId`, exclusão do vídeo e tratamento de erros.

**Fase 2 — Interface.** Criar a aba abaixo de **Uploads**, selector exclusivo de canais YouTube, cards paginados, campos editáveis, preview da thumbnail e estado de sincronização.

**Fase 3 — IA.** Ligar os três botões aos helpers de geração existentes, com contexto de idioma, roteiro e Blueprint. Os resultados devem preencher os campos sem publicar automaticamente.

**Fase 4 — Fila e auditoria.** Integrar `YOUTUBE_UPDATE_VIDEO` no pipeline/worker, criar histórico local e garantir que a tarefa não tenta processar ou substituir o ficheiro de vídeo.

**Fase 5 — Validação.** Executar testes unitários, validação sintática, teste manual com um vídeo de teste e validação de permissões OAuth. Só depois actualizar a versão, enviar ao GitHub e publicar através do workflow `publish-npm.yml`.

## Decisão recomendada

Implementar pela **YouTube Data API oficial**, mantendo `YOUTUBE_UPDATE_VIDEO` como contrato explícito da aplicação. A alteração de título/descrição será feita por `videos.update`; a thumbnail será feita separadamente por `thumbnails.set`. A interface apresentará os resultados de IA para revisão e exigirá uma acção explícita do utilizador para publicar, sem tocar no ficheiro de vídeo.

## Referências

[1]: https://developers.google.com/youtube/v3/docs/videos/update "Videos: update — YouTube Data API"
[2]: https://developers.google.com/youtube/v3/docs/thumbnails/set "Thumbnails: set — YouTube Data API"
[3]: https://developers.google.com/youtube/v3/guides/authentication "Implementing OAuth 2.0 Authorization — YouTube Data API"
[4]: https://developers.google.com/youtube/v3/guides/uploading_a_video "Uploading a Video — YouTube Data API"

## Nota de escopo

Este documento é um plano. Nenhuma alteração funcional da nova aba foi aplicada nesta etapa.
