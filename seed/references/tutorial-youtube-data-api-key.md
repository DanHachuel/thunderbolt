Este tutorial explica como criar uma **YouTube Data API Key** no Google Cloud e configurá-la no Thunderbolt para consultar dados públicos do YouTube, como vídeos, canais e estatísticas públicas.

## Quando usar uma API Key

Uma API Key é suficiente para operações com dados públicos, como pesquisar vídeos, consultar canais públicos e obter estatísticas públicas. Ela **não concede acesso a dados privados** da conta nem substitui o OAuth 2.0 para playlists privadas, inscrições privadas ou uploads.

## Passo 1 — Aceder ao Google Cloud Console

Abra o [Google Cloud Console](https://console.cloud.google.com/) e faça login com a conta Google que irá gerir a credencial.

## Passo 2 — Criar ou seleccionar um projecto

No topo da página, abra o selector de projectos junto ao logótipo do Google Cloud. Seleccione **Novo projecto**, dê-lhe um nome, como `Thunderbolt YouTube`, mantenha a organização e a localização predefinidas quando aplicável e clique em **Criar**. Depois de alguns instantes, seleccione o projecto criado.

## Passo 3 — Activar a YouTube Data API v3

No menu lateral, abra **APIs e Serviços → Biblioteca**. Pesquise por **YouTube Data API v3**, abra o resultado correspondente e clique em **Activar**.

> **Importante:** a API não é activada automaticamente em projectos novos. Sem este passo, a API Key não poderá fazer chamadas à YouTube Data API v3.

## Passo 4 — Criar a credencial API Key

No menu lateral, abra **APIs e Serviços → Credenciais** e clique em **+ Criar credenciais → Chave de API**. O Google irá gerar a chave e apresentá-la numa janela. Copie-a e guarde-a num local seguro; depois clique em **Concluído**.

No Thunderbolt, a chave deve ser configurada em **Configurações → Configuração API → API Keys Upload → API Innertube**, no campo `INNERTUBE_API_KEY`. Esta é a chave global usada pelos fluxos que consultam dados públicos do YouTube.

## Passo 5 — Restringir a chave (recomendado)

A restrição reduz o impacto de uma eventual exposição da chave. Na lista de credenciais do Google Cloud, clique no ícone de edição junto à chave criada e, em **Restrições de API**, seleccione **Restringir chave**. Em **Seleccionar APIs**, marque **YouTube Data API v3** e clique em **Guardar**.

Se a chave for usada apenas por uma aplicação local, reveja também as restrições de aplicação disponíveis no Google Cloud e escolha uma configuração compatível com o ambiente onde o Thunderbolt é executado.

## Passo 6 — Configurar e testar no Thunderbolt

1. Abra **Configurações**.
2. Abra **Configuração API**.
3. Seleccione **API Keys Upload**.
4. Abra **API Innertube**.
5. Cole a YouTube Data API Key no campo `INNERTUBE_API_KEY`.
6. Guarde a configuração.
7. Execute uma funcionalidade que consulte dados públicos, como pesquisa ou importação de um canal público.

A API Key não deve ser colocada nos campos Client ID ou Client Secret das **Contas Google**. Esses campos pertencem ao fluxo OAuth 2.0, que é independente da API Key.

## O que é possível fazer com a chave

Com a YouTube Data API v3 e uma API Key, o Thunderbolt pode consultar, conforme o fluxo utilizado:

- Vídeos e respectivos metadados públicos.
- Canais e informações públicas do canal.
- Estatísticas públicas de vídeos e canais.
- Pesquisas de conteúdos públicos.
- Playlists públicas.

Para criar playlists, fazer uploads, consultar dados privados ou agir em nome da conta Google, utilize o tutorial **OAuth do Google** e autorize a conta através de uma credencial **Aplicativo para computador (Desktop app)**.

## Cota diária

A YouTube Data API v3 aplica uma quota diária por projecto. Cada operação consome unidades de quota diferentes; operações de pesquisa costumam consumir mais unidades do que consultas simples. A quota predefinida é frequentemente apresentada pelo Google como aproximadamente **10.000 unidades por dia**, mas o valor efectivo e as regras podem variar por projecto.

Consulte o consumo em **APIs e Serviços → YouTube Data API v3 → Quotas** no Google Cloud Console. Evite chamadas repetidas desnecessárias e mantenha a chave restrita à API necessária.

## Segurança e manutenção

Nunca publique a API Key em repositórios, capturas de ecrã, mensagens ou páginas públicas. Se a chave for exposta, abra a lista de credenciais no Google Cloud, revogue ou elimine a chave comprometida e crie uma nova. Depois, actualize o valor guardado no Thunderbolt.

A API Key não substitui o Client Secret OAuth e não deve ser partilhada com outras pessoas. Use uma chave separada para cada ambiente quando isso facilitar a auditoria e a revogação.

## Solução de problemas

### A API devolve `SERVICE_DISABLED`

Confirme que o projecto seleccionado é o mesmo projecto associado à API Key e que **YouTube Data API v3** está activa em **APIs e Serviços → Biblioteca**.

### A API devolve `API_KEY_INVALID`

Confirme que copiou a chave completa, sem espaços ou aspas adicionais, e que o valor foi guardado no campo `INNERTUBE_API_KEY` correcto.

### A API devolve `quotaExceeded`

Consulte a quota do projecto no Google Cloud Console, reduza pesquisas repetidas e aguarde a reposição da quota. Se a utilização legítima justificar, consulte as opções de quota apresentadas pelo Google.

### Preciso de dados privados ou uploads

Uma API Key só identifica o projecto e permite chamadas autorizadas para dados públicos. Para dados privados, uploads ou operações em nome de uma conta, configure o OAuth 2.0 através do **Tutorial OAuth do Google**.

## Referências

- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Documentação de quotas da YouTube Data API](https://developers.google.com/youtube/v3/determine_quota_cost)
