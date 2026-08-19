
## Smoke test da restauração

A UI 0.2.21 iniciou em `http://127.0.0.1:3035` e carregou a navegação sem erro. O código agora usa novamente o `st.multiselect` original, sem marcador externo nem badges separados; os chips são estilizados dentro do próprio campo por `:has(button[aria-label*=...])`.

## Smoke test do widget compacto

Na UI 0.2.21, a página Upload voltou a mostrar o chip `YouTube` dentro do próprio campo `Destinos`, com botão de remoção e botão de abertura do dropdown. O layout não mostra badges/lista externa. O dropdown BaseWeb continua a ser a fonte das opções, enquanto o CSS usa `:has(button[aria-label*=...])` para aplicar a cor de cada plataforma.
