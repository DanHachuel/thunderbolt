# YouTube em lote por conta Google

Fonte oficial: https://developers.google.com/youtube/v3/docs/channels/list

`channels.list` aceita o filtro `mine=true` apenas numa requisição correctamente autorizada. Esse filtro instrui a API a devolver apenas canais pertencentes ao utilizador autenticado. A resposta inclui `items`, `pageInfo` e `nextPageToken`; `maxResults` aceita até 50 itens, portanto o cliente deve suportar paginação mesmo que uma conta normalmente devolva menos canais.

Fonte oficial: https://developers.google.com/youtube/v3/guides/auth/installed-apps

Uma aplicação instalada deve usar OAuth 2.0 num browser do sistema e redirect loopback local. O scope `https://www.googleapis.com/auth/youtube.readonly` permite ver a conta YouTube; uma API Key isolada não substitui a autorização da conta para `mine=true`.

Decisão de produto: a subaba chama-se `Canais em lote gmail` por referência à conta Google/Gmail, mas não lê caixa de entrada, mensagens ou contactos. Cada conta configurada no Thunderbolt terá e-mail identificador, OAuth Client ID, OAuth Client Secret e token local próprio. A importação criará apenas os canais seleccionados, com deduplicação por `youtube_channel_id`, preservando o OAuth global já existente para upload.
