# Mapeamento do workflow AI Influencers

## Princípio

O Thunderbolt usa os workflows do episódio 35 como referência funcional, mas não executa n8n. Os formulários, `Data Table`, `Switch`, `Wait` e subworkflows são implementados por páginas Streamlit, adapters Python, uma camada de persistência dual e os workers/notificações já existentes.

| Workflow n8n | Thunderbolt | Estado |
|---|---|---|
| Formulário **Add influencer** | `AI Influencers > Personagens` | Implementado com nome, bio, idioma, Instagram Business ID opcional e uploader múltiplo |
| Campo único `image` | `influencer_assets` | Implementado para várias imagens e documentos `.md`/`.json`, com hash e metadados |
| `influencer` Data Table | `influencers` em Supabase ou SQLite | Implementado |
| `influencer_weekly_plans` Data Table | `influencer_weekly_plans` em Supabase ou SQLite | Schema preparado para a próxima etapa de planeamento |
| Formulário **Create weekly plan** | Serviço de planeamento de AI Influencers | O schema está preparado; geração de plano semanal será ligada numa evolução posterior |
| Formulário **Create post** | `AI Influencers > Geração de Conteúdo IA` | Implementado nas subabas Imagens e Vídeos |
| Subworkflow FAL Nano Banana | `hermes_ui.media_generation` + pool de imagem | Reutilizado; o provider é seleccionado pelo cartão activo |
| Subworkflow FAL Veo 3.1 | `hermes_ui.media_generation` + pool de vídeo | Reutilizado como padrão assíncrono, sem hardcode de Veo; KIE, FAL, Pollinations e Replicate podem ser seleccionados |
| `Wait` + `Get status` | Polling bounded dos adapters | Implementado para resultados com `task_id`/prediction ID |
| `influencer_posts` Data Table | `influencer_content` | Implementado para imagem/vídeo, prompt, caption, provider, modelo, estado e artefacto |
| Facebook Graph API / Instagram publish | Integrações de publicação existentes | Continua separado e requer acção explícita; a geração não publica automaticamente |

## Schema e backends

As tabelas lógicas são `influencers`, `influencer_assets`, `influencer_weekly_plans` e `influencer_content`. O SQL idempotente está em `seed/references/ai_influencers_schema.sql`. SQLite usa o mesmo desenho através de `hermes_ui.influencers.SQLiteInfluencerRepository`; Supabase usa `SupabaseInfluencerRepository` com `create_client(project_url, api_key)` e Data API.

No SQLite os ficheiros ficam em `storage/influencers/<id>/` e o banco em `storage/state/ai_influencers.db`. No Supabase os ficheiros de referência são enviados para o bucket configurado e as tabelas guardam somente path, hash, MIME type, tamanho e metadados. A API key nunca é incluída neste documento, nos workflows, logs ou testes.

## Estados de conteúdo

`queued` representa a criação persistida antes da chamada ao provider; `running` representa uma chamada em curso; `completed` indica artefacto guardado; `failed` conserva uma mensagem segura de erro; `cancelled` e `blocked` ficam disponíveis para execução controlada e quotas. Todas as operações concluídas ou falhadas geram evento no centro de Notificações.

## Providers de vídeo

A UI deriva as opções do `Pool Vídeo` em `hermes_ui.media_providers`. O cartão contém a credencial, Base URL, modelo e prioridade. Replicate usa `POST /v1/predictions` com `version` e `input`, consulta `GET /v1/predictions/{id}` e aceita estados `starting`, `processing`, `succeeded`, `failed` e `canceled`. KIE e FAL permanecem adaptados a respostas assíncronas próprias; os endpoints e campos específicos devem ser mantidos nos cartões configurados, sem apresentar parâmetros Veo obrigatórios.
