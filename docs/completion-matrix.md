# Matriz de conclusão do Thunderbolt

Estado auditado para o release final 0.2.20.

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
| Aba Automação com toggle e horário diário por canal | Concluído como UI | Renderer, estado por canal e validação HH:MM; não inicia worker em segundo plano, conforme pedido “apenas UI por enquanto”. |
| Instagram e Facebook Pages no Upload | Concluído como UI | Destinos, chips rosa/azul e botões desactivados para publicação futura. |
| Pexels/Pixabay como rótulo, Estilo IA condicional e Apenas Música | Concluído | Labels, lista de 12 estilos IA e task com `background_mode=none` para música. |
| Agente de música, Suno/pasta local e vídeo wide musical | Concluído como integração configurável | `hermes_ui/music.py`, storage/music, upload local e endpoint Suno explicitamente configurado. |
| Área de teste de vozes em Configurações | Concluído | Preview isolado com Edge/Azure Speech e providers HTTP, reprodução e download. |
| Upload directo via YouTube-Video-Upload-Frontend-Api | Concluído como adaptador experimental | `integrations/youtube_direct_upload.py`, sessão manual, metadata e chunks múltiplos de 256 KiB. |
| `DELEGATED_SESSION_ID`, Blueprint padrão e voz padrão por canal | Concluído | Campos por canal, selectors e propagação para tasks. |
| Agendamento real em segundo plano | Fora do escopo actual de UI | O pedido de Automação foi definido como “apenas UI por enquanto”; não executar jobs até existir backend aprovado. |

## Regra de release

A publicação directa Instagram/Facebook continua deliberadamente desactivada: o requisito do checklist pede apenas a camada de front end. A Automação também é apenas UI, sem worker agendado. Suno e Upload directo dependem de endpoints/sessões fornecidos pelo utilizador e recusam execução quando faltam credenciais.


Nenhum release será descrito como final enquanto os itens marcados como pendentes nesta matriz não estiverem implementados, testados ou explicitamente classificados como dependências externas pelo utilizador.
