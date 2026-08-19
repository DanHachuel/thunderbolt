# Smoke test visual da aba MCP

A aplicação Streamlit iniciou correctamente em `http://127.0.0.1:3032` com a versão `0.2.19`. A barra lateral apresentou a entrada **MCP** entre **Upload** e **Limpador de metadado**, sem erro de arranque. O teste ficou limitado à renderização inicial porque o navegador não expôs o botão lateral como elemento DOM interactivo seleccionável; a compilação Python, a suíte de 21 testes, o launcher e o `npm pack --dry-run` foram validados separadamente.
