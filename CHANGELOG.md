# Changelog

## 0.5.56 — 2026-09-04

- Corrigido o encerramento por `Ctrl+C` no launcher Streamlit.
- O handler SIGINT agora tenta parar o event loop, aguarda uma janela curta de drenagem e encerra sem callbacks tardios.
- Mantidos os shims UTF-8, as variáveis de ambiente e a protecção contra substituição do handler pelo Streamlit.
- Reduzida a poluição do terminal causada por tracebacks `RuntimeError: Event loop is closed` e `asyncio.exceptions.CancelledError` durante o shutdown.
