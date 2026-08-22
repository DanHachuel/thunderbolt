# Integração Gemini Nano Banana

## Fonte oficial consultada

- https://ai.google.dev/gemini-api/docs/image-generation
- https://ai.google.dev/gemini-api/docs/models
- https://ai.google.dev/gemini-api/docs/api-key

## Decisões

- Nano Banana 2 usa o modelo `gemini-3.1-flash-image`.
- A documentação oficial recomenda a Interactions API para os modelos mais recentes.
- A geração usa `client.interactions.create(model=..., input=...)` e a resposta de imagem fica em `interaction.output_image.data`, codificada em base64.
- O formato pode incluir `response_format` com `type: image`, `mime_type`, `aspect_ratio` e `image_size`.
- Para thumbnails do sistema, o padrão escolhido será `gemini-3.1-flash-image`, proporção `16:9` e tamanho `1K`, com a possibilidade de configuração futura.
- A chave deve ser tratada como segredo e não deve ser gravada em código, logs ou repositório. Na aplicação local, ficará em `settings.json` através do campo de API Keys, e será enviada apenas no cabeçalho da chamada ao endpoint Gemini.
- A chave específica de geração de imagens será separada da chave usada pelo provider LLM textual: `gemini_image_api_key`.

## Endpoint REST confirmado

A referência oficial da Interactions API documenta o endpoint `POST https://generativelanguage.googleapis.com/v1beta/interactions`. A implementação usará o cabeçalho `x-goog-api-key` e um corpo com `model`, `input` e `response_format` para solicitar a imagem.
