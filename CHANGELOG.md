# Changelog

## 0.5.08 (normalizado pelo npm para 0.5.8)

Corrigido o erro `LookupError: unknown encoding: utf-16-le` que podia ocorrer durante o shutdown do Streamlit no Windows. O launcher Node agora materializa as variáveis de encoding e `CLICK_NO_WIN_CONSOLE` no processo pai antes de iniciar Python; os workers de automação e pipeline também aplicam as mesmas definições antes dos imports restantes.
