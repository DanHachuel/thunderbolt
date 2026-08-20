# Diagnóstico da importação pública de canais

Data: 2026-08-19.

## Resultado actual

O adaptador actual funciona para um canal público conhecido (`UC_x5XG1OV2P6uZZ5FSM9Ttw`) e para `https://www.youtube.com/@GoogleDevelopers` sem API Key. No entanto, o caso reproduzido a partir da captura (`https://www.youtube.com/channel/UC7Q2SsM0stL1MQRROcbCmrA`) devolve `ok=True` apenas porque o ID foi extraído do URL, mas os restantes campos ficam vazios: nome, handle, descrição, thumbnail e métricas.

A página desse canal responde HTTP 200 com aproximadamente 753 KiB e contém o ID no HTML, mas não contém os marcadores `channelMetadataRenderer`, `pageHeaderViewModel`, `og:title` ou um título/canonical útil reconhecível pelo parser actual. O feed público `https://www.youtube.com/feeds/videos.xml?channel_id=UC7Q2SsM0stL1MQRROcbCmrA` responde HTTP 404, pelo que o fallback RSS actual não pode fornecer dados para este canal.

## Implicação

A implementação actual considera a presença do ID suficiente para sucesso, mesmo quando a importação não preenche dados úteis. O comportamento correcto deve distinguir entre resolução do ID e importação de metadados: o formulário deve receber dados úteis ou uma mensagem clara de que a página não forneceu metadados, em vez de apresentar uma importação aparentemente concluída vazia.

O parser deve também reconhecer estruturas alternativas presentes no HTML actual, canonical/JSON-LD e redireccionamentos. Não deve tentar contornar CAPTCHA, login ou bloqueios; quando o YouTube não disponibilizar metadados públicos, deve indicar a limitação e manter o cadastro manual como alternativa.

## Smoke test da UI

A UI 0.2.23 iniciou em `http://127.0.0.1:3036` com a navegação normal e mostrou a versão 0.2.23. A aba **Canais** está disponível como botão lateral; o próximo passo do smoke test é validar o formulário **Importar do YouTube** e a mensagem de resultado sem API Key.

## Smoke test funcional

Na UI 0.2.23, com **Página pública — sem API Key** seleccionada e sem qualquer API Key configurada, o URL `https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw` foi pesquisado com sucesso. A UI mostrou a mensagem de sucesso e abriu o formulário de revisão com `Google for Developers`, URL canónico `https://www.youtube.com/@GoogleDevelopers`, handle `@GoogleDevelopers`, descrição, 267 inscritos e 6086 vídeos. Isto confirma que o fluxo público não depende da Data API Key e que os dados chegam ao formulário de revisão.

## Regressão visual detectada e correcção necessária

Ao pesquisar na UI o link da captura, a mensagem correcta apareceu: `O YouTube indicou que este canal não existe ou não está disponível: Este canal não existe.` Contudo, o formulário da pesquisa anterior permaneceu visível porque o estado `yt_import` era mantido mesmo quando `yt_ok=False`. Esse formulário obsoleto pode dar a impressão de que a importação falhou ou que o canal errado foi encontrado. A UI será ajustada para renderizar o formulário apenas quando o último resultado tiver `yt_ok=True`.

Após o recarregamento do Streamlit, o formulário anterior desapareceu e ficaram apenas a mensagem clara de canal inexistente e a instrução para introduzir um novo URL. A UI deixou de apresentar dados obsoletos depois de uma falha.
