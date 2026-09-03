# Changelog

## 0.5.26

Corrigida a renderização dos cards de Imagem e Video IA para os apresentar imediatamente pela ordem do campo Prioridade, fazendo o card subir ou descer na fila após ser guardado.

## 0.5.17

Removidos da secção Imagem e Video IA os selectores de provider principal de imagem, provider principal de vídeo e a checkbox de pool de vídeo externo. A ordem dos pools passa a ser definida pelos campos de Prioridade nos próprios cartões.

## 0.5.16

Adicionado um handler SIGINT no entry point do Streamlit que encerra o processo de forma controlada antes do handler de shutdown do Streamlit chamar `click.secho`, eliminando o caminho que provocava `LookupError: unknown encoding: utf-16-le` ao pressionar Ctrl+C no Windows.

## 0.5.15 (normalizado pelo npm para 0.5.15)

Aplicada a correcção definitiva do caminho de saída do Click no Windows, com shim UTF-8 carregado antes do Streamlit e teste de regressão para stdout com encoding `utf-16-le`.

## 0.5.09 (normalizado pelo npm para 0.5.9)

Adicionado um shim de compatibilidade que intercepta a escrita de saída do Click antes do carregamento do Streamlit e grava directamente em UTF-8, evitando o caminho nativo que volta a procurar `utf-16-le` durante o shutdown do Windows. Incluídos testes com um console simulado em `utf-16-le`.

## 0.5.08 (normalizado pelo npm para 0.5.8)

Corrigido o erro `LookupError: unknown encoding: utf-16-le` que podia ocorrer durante o shutdown do Streamlit no Windows. O launcher Node agora materializa as variáveis de encoding e `CLICK_NO_WIN_CONSOLE` no processo pai antes de iniciar Python; os workers de automação e pipeline também aplicam as mesmas definições antes dos imports restantes.
