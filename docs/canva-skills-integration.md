# Integração Canva Skills

## Mapeamento

| Skill oficial | Implementação Thunderbolt | REST utilizado | Estado |
|---|---|---|---|
| resize-for-social-media | `app/modules/canva_skills/resize.py` | cópia de design, exportação | Adaptada: a REST não oferece resize responsivo geral |
| bulk-create | `app/modules/canva_skills/bulk.py` | `POST /rest/v1/autofills`, polling e exports | Funcional quando a conta tem Autofill |
| get-design-feedback | `feedback.py` | `GET /rest/v1/designs/{id}` | Feedback estruturado de metadata; análise visual completa não é exposta |
| implement-feedback | `feedback.py` | preparação de checklist | Sem commit falso: comentários/listagem e edição transaccional não estão disponíveis na REST pública |
| edit-design | `edit.py` | preparação de alterações | Sem commit falso: start/perform/commit são capacidades do MCP, não endpoints Connect REST públicos |
| brand-check | `brand.py` | `GET /rest/v1/brand-templates` e designs | Verificações visuais ficam em `cannot_verify` quando a metadata não contém cores/fontes/logo |

## Configuração

Configure o card **Canva Connect** em **Configuração API > API Keys > Imagem e Video IA**. A integração usa Client ID, Client Secret, Redirect URI e OAuth 2.0 Authorization Code com PKCE. Os scopes configurados para as skills incluem conteúdo e metadata de designs, metadata/conteúdo de Brand Templates e comentários quando esses scopes estiverem disponíveis na integração Canva.

A página **Canva Skills** fica em `app/pages/canva_skills.py`. O card Canva é exclusivo do Pool de Imagem para thumbnails e não declara capacidade de vídeo. O fluxo automático de thumbnails continua a guardar os resultados no storage local normal do Thunderbolt.

## Limitações deliberadas

O documento de requisitos mistura capacidades das Canva Skills via MCP com a Connect REST API. As endpoints públicas verificadas não permitem inventar uma transacção de edição, aplicar alteração visual arbitrária, listar todas as threads ou analisar uma imagem com visão computacional. Por isso o sistema não simula sucesso: devolve `pending_approval`, `manual_action_required` ou itens `cannot_verify` quando a operação precisa do editor Canva/MCP.

O Autofill exige Canva Enterprise ou quota de trial de desenvolvimento. As URLs de exportação expiram após 24 horas; as thumbnails de metadata têm validade menor. Os limites da Canva e os erros 401/429 são tratados pelo cliente comum com refresh e backoff limitado.

## Execução média esperada

As chamadas de metadata e listagem normalmente dependem de uma única resposta HTTP. Exportações e Autofill são jobs assíncronos: o tempo depende do serviço Canva e do número de linhas; o Thunderbolt faz polling bounded para não bloquear indefinidamente. Bulk-create executa sequencialmente por linha para respeitar limites por utilizador e manter resultados recuperáveis.

## Fontes

- [Canva Skills README](https://github.com/canva-sdks/canva-skills)
- [Canva Connect API](https://www.canva.dev/docs/connect/)
- [Autenticação OAuth/PKCE](https://www.canva.dev/docs/connect/authentication/)
- [Create design autofill job](https://www.canva.dev/docs/connect/api-reference/autofills/create-design-autofill-job/)
- [List brand templates](https://www.canva.dev/docs/connect/api-reference/brand-templates/list-brand-templates/)
- [Get design](https://www.canva.dev/docs/connect/api-reference/designs/get-design/)
