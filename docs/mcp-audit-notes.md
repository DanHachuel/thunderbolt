# Auditoria preliminar das integrações MCP

Data: 2026-08-19

## Repositórios indicados

| Repositório | Observação inicial |
|---|---|
| `gyoridavid/short-video-maker` | Aplicação TypeScript/Remotion com Docker; não deve ser incluída no pacote Thunderbolt. |
| `Auto-Vio/autovio` | Pipeline de vídeo self-hosted, descrito pelo repositório como MCP-ready; licença declarada como Other, devendo ser tratado como software externo. |
| `calesthio/OpenMontage` | Sistema agentic de produção de vídeo com licença AGPL-3.0; software externo, não copiar para o pacote. |
| `OpenCut-app/OpenCut` | Editor open-source alternativo ao CapCut com licença MIT; software externo, não copiar para o pacote. |

## Decisão de integração

A aba local deve ser um catálogo/configurador de integrações opcionais, não um instalador e não um empacotador dos quatro repositórios. Cada item terá URL oficial, porta local editável, estado Activo e disponibilidade detectada. Activar uma linha guardará a preferência local; não iniciará processos desconhecidos nem fará download automático.

A skill `moneyprinterturbo-video.md` será guardada somente em `storage/skills/` quando o utilizador clicar na acção de download. O ficheiro não será adicionado ao `package.json`, ao tarball npm nem ao repositório como parte da instalação.
