# Matriz de conclusão do Thunderbolt

Estado auditado para o release 0.2.50.

| Requisito | Estado auditado | Evidência / pendência |
|---|---|---|
| UI Streamlit, launcher npx, storage local, Blueprints, Brandings, Canais e Novo vídeo base | Parcialmente concluído | Estrutura existente e publicada. |
| Importação pública de canais sem API Key, Data API opcional e cadastro manual | Concluído | `render_channels()` e `YouTubeAdapter.fetch_channel_public()`. |
| Vídeos como subaba de Novo vídeo | Concluído | `render_new_video()` cria as subabas. |
| YouTube upload via lógica adaptada do youtube-automation-agent com OAuth fallback | Concluído | `integrations/youtube_upload.py`. |
| Aba MCP e skill local | Concluído na camada UI | Catálogo, portas, toggle, detecção passiva e download; cliente MCP operacional por serviço ainda requer integração de endpoints/comandos. |
| Lista ampliada de idiomas | Concluído | `VIDEO_LANGUAGE_OPTIONS`, com os rótulos na ordem solicitada. |
| Alinhamento dos nomes da barra lateral à esquerda | Concluído | CSS da sidebar força alinhamento do wrapper, markdown e parágrafo à esquerda. |
| Botão Apagar canal abaixo de Activo | Concluído | `delete_channel()` com confirmação inline e preservação de tarefas/artefactos. |
| Aba Automação com toggle e horário diário por canal | Concluído | Renderer, estado por canal, validação HH:MM e worker local baseado no relógio do computador; o worker gera conteúdo específico por canal quando o provider LLM está configurado e regista erros sem usar placeholder. |
| Instagram e Facebook Pages no Upload | Concluído como UI | Destinos, chips rosa/azul e botões desactivados para publicação futura. |
| Pexels/Pixabay como rótulo, Estilo IA condicional e Apenas Música | Concluído | Labels, lista de 12 estilos IA e task com `background_mode=none` para música. |
| Agente de música, Suno/pasta local e vídeo wide musical | Concluído como integração configurável | `hermes_ui/music.py`, storage/music, upload local e endpoint Suno explicitamente configurado. |
| Área de teste de vozes em Configurações | Concluído | Preview isolado com Edge/Azure Speech e providers HTTP, reprodução e download. |
| OpenAI/ NVIDIA NIM — descoberta de modelos OpenAI-compatible | Concluído | `integrations/openai_model_discovery.py` consulta explicitamente `/models`, valida `data[].id`, envia Bearer API key sem a expor, apresenta selector e mantém fallback manual; `openai_model_name` continua sincronizado com o MoneyPrinterTurbo. A chamada do modelo manual usa `help`, compatível com o Streamlit suportado, e não `help_text`. |
| Upload directo via YouTube-Video-Upload-Frontend-Api | Concluído como adaptador experimental | `integrations/youtube_direct_upload.py`, sessão manual, metadata e chunks múltiplos de 256 KiB; credenciais directas passam a ser lidas por conta Google associada. |
| Upload directo com documento JSON completo por conta Google | Concluído | `integrations/youtube_direct_credentials.py` valida `credentials.json` com SID/SSID/HSID/APISID/SAPISID, `sessionInfo`, `INNERTUBE_API_KEY`, `chunk_size` e `delegated_session_ids` por canal; guarda em `storage/youtube_direct_accounts/<account-id>/credentials.json`; o upload lê exclusivamente este documento. |
| UI sem campos técnicos de Upload directo | Concluído | A UI mostra o uploader do documento por Gmail, o campo sessionInfo específico da conta e a associação do canal; não renderiza inputs separados de cookies, INNERTUBE_API_KEY, chunk size ou DELEGATED_SESSION_ID. O sessionInfo do formulário é sincronizado no `credentials.json`. |
| `DELEGATED_SESSION_ID`, Blueprint padrão e voz padrão por canal | Concluído | O ID delegado é lido do documento JSON da conta pelo identificador do canal; Blueprint e voz continuam com selectors próprios da pipeline. |
| Agendamento real em segundo plano | Fora do escopo actual de UI | O worker de Automação é local e baseado no relógio; não é usado pelo Niche Finder Apify. |
| Blueprints com nome personalizado na criação a partir de link | Concluído | O formulário exige `Nome do Blueprint`; `create_blueprint_from_link()` persiste o valor em `name` e `save_generated_blueprint()` usa-o no nome do ficheiro JSON, inclusive no fluxo com Branding completo. |
| OAuth Google com URI loopback determinística | Concluído | Os fluxos de contas em lote, upload principal e fallback usam `http://127.0.0.1:8765/`, aceitam override por ambiente e devolvem instruções accionáveis para `redirect_uri_mismatch`. |
| Niche Finder Kaggle e Niche Finder Apify | Concluído como alternativas independentes | Kaggle usa `app/modules/niche_finder/core.py` e `data_loader.py`; Apify usa `app/modules/niche_finder/apify.py`, `summarizer.py`, estado `niche_apify_runs.json` e credencial própria. |
| Niche Finder Apify baseado no YTB Outlier Finder | Concluído como integração configurável | Actor Apify, polling, dataset, normalização SRT, VSC Ratio, sumarização LLM opcional e exportação JSON/CSV; não grava automaticamente no Airtable do workflow. |
| Editor Python baseado no PYEdit | Concluído como editor local seguro | Vídeos gerados pelos artefactos, selecção de pasta, upload manual, corte, áudio, velocidade, redimensionamento, histórico próprio e edição/guarda de scripts sem execução de código. |
| Canais em lote por conta Google/YouTube | Concluído como integração OAuth configurável | Contas múltiplas com e-mail, Client ID, Client Secret e sessionInfo próprios; botão de repetição de campos, eliminação individual com limpeza de tokens/documentos/associações, tokens separados, `channels.list(mine=true)` com paginação, selecção, deduplicação por `youtube_channel_id` e importação incremental; não lê Gmail. |
| Configurações Técnicas organizadas em subabas | Concluído | `render_settings()` apresenta, sem numeração visível e nesta ordem, `Contas Google/YouTube — canais em lote`, `API Keys` e `Teste de vozes`; os blocos de contas, API Keys e preview de voz permanecem isolados. |
| Geração de tópico/briefing por IA na Criação de Vídeos | Concluído como integração configurável | `hermes_ui/creative_generation.py` usa o provider OpenAI-compatible de API Keys, incorpora Blueprint/descrição/idioma/voz e só chama o endpoint depois do botão ou do horário do worker; falhas são accionáveis e não produzem placeholder. |
| Título automático e pacote de thumbnail | Concluído como integração configurável | O serviço exige 20+ candidatos de título e 3–5 variantes de thumbnail, aplica as referências em `seed/references/`, persiste título, scores, conceito, overlay, composição, prompt e estado; o PNG final depende de provider de imagem configurado e nunca é falsificado. |
| Lote geral por canal independente | Concluído | O modo geral remove `Canais incluídos`, usa todos os canais cadastrados e cria exactamente uma task por canal com `options.channel_payloads`, tópico, título, thumbnail, Blueprint e voz próprios. |

## Regra de release

A publicação directa Instagram/Facebook continua deliberadamente desactivada: o requisito do checklist pede apenas a camada de front end. A Automação tem worker local baseado no relógio do computador e usa o serviço criativo quando o provider LLM está configurado; Suno, Upload directo e a geração final de imagens dependem de endpoints/sessões/providers fornecidos pelo utilizador e recusam execução quando faltam credenciais.


Nenhum release será descrito como final enquanto os itens marcados como pendentes nesta matriz não estiverem implementados, testados ou explicitamente classificados como dependências externas pelo utilizador.
