# Smoke test das subabas MCP

Na instância limpa da versão local 0.2.26, a aba MCP apresentou exactamente três subabas: **Client MCP**, **Servidor MCP** e **Skill**.

A subaba Client MCP manteve as quatro integrações existentes — Short Video Maker, AutoVio, OpenMontage e OpenCut — com links oficiais, portas editáveis, detecção passiva e toggle Activo. A interface deixou de misturar a skill com o catálogo de clientes.

O próximo passo é abrir Servidor MCP, iniciar o endpoint local e validar uma chamada JSON-RPC externa. Depois será validada a subaba Skill.

A subaba **Servidor MCP** mostra os campos Host (`127.0.0.1`), Porta (`3031`), token opcional, toggle **Permitir ferramentas de escrita**, botão de guardar/iniciar e estado parado. A tentativa de alternar o checkbox através do índice acessível não mudou o estado visual, por isso a validação seguinte usa o nó DOM exacto para evitar um falso resultado do driver.

O driver visual por coordenadas não foi fiável nesta viewport e uma tentativa acabou por abrir Automação em vez do checkbox. Isto não indica falha do código da UI. A validação funcional do Servidor MCP será feita pelo runtime HTTP e, em seguida, a subaba MCP será reaberta para confirmar o estado publicado.

O smoke test HTTP passou no endpoint temporário `http://127.0.0.1:3041`: `/health` respondeu `ok: true`, `initialize` devolveu `Thunderbolt MCP Server`, `tools/list` expôs quatro ferramentas de leitura e `tools/call` executou `thunderbolt_get_status` com sucesso. A ferramenta de escrita não apareceu enquanto `write_enabled` estava desactivado.

A subaba **Skill** foi validada e apresenta apenas as acções `Guardar skill localmente` e `Descarregar skill .md`. A skill deixou de aparecer misturada no Client MCP.

Após reabrir a UI com `mcp_server.json` activo, a subaba **Servidor MCP** confirmou o arranque automático em `http://127.0.0.1:3042/mcp`, health em `/health`, transporte `Streamable HTTP / JSON-RPC POST` e `write_tools: false`. A configuração persistida foi lida correctamente.
