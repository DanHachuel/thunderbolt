# Changelog

## 0.5.15 (normalizado pelo npm para 0.5.15)

Aplicada a correcção definitiva do caminho de saída do Click no Windows, com shim UTF-8 carregado antes do Streamlit e teste de regressão para stdout com encoding `utf-16-le`.

## 0.5.09 (normalizado pelo npm para 0.5.9)

Adicionado um shim de compatibilidade que intercepta a escrita de saída do Click antes do carregamento do Streamlit e grava directamente em UTF-8, evitando o caminho nativo que volta a procurar `utf-16-le` durante o shutdown do Windows. Incluídos testes com um console simulado em `utf-16-le`.

## 0.5.08 (normalizado pelo npm para 0.5.8)

Corrigido o erro `LookupError: unknown encoding: utf-16-le` que podia ocorrer durante o shutdown do Streamlit no Windows. O launcher Node agora materializa as variáveis de encoding e `CLICK_NO_WIN_CONSOLE` no processo pai antes de iniciar Python; os workers de automação e pipeline também aplicam as mesmas definições antes dos imports restantes.
