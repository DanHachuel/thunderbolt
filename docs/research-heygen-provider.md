# Pesquisa: provider HeyGen para vídeo

## Fontes oficiais consultadas

- Quick Start: https://developers.heygen.com/docs/quick-start
- Create Video: https://developers.heygen.com/reference/create-video
- API Key: https://developers.heygen.com/docs/api-key
- List Videos: https://developers.heygen.com/reference/list-videos

## Contrato confirmado

A API usa a base `https://api.heygen.com` e autenticação através do header `X-Api-Key: <key>`. O health-check read-only recomendado é `GET /v3/users/me`.

A criação de vídeo de avatar usa `POST /v3/videos`. O pedido inclui `type: "avatar"`, `avatar_id`, `script` ou áudio, `aspect_ratio` e `output_format: "mp4"`; `voice_id` é opcional quando o avatar possui voz predefinida. A resposta devolve `data.video_id` e `data.status`.

O estado é consultado através de `GET /v3/videos/{video_id}`. A resposta concluída contém `data.status: "completed"` e `data.video_url`; falhas podem conter `data.failure_code` e `data.failure_message`. Os estados documentados incluem `pending`, `processing`, `completed` e `failed`. A documentação também indica suporte a `Idempotency-Key` no endpoint de criação para retries seguros.

## Decisão de integração

O cartão Thunderbolt usa `api_style: "heygen"`, `supports_video: true`, base URL por defeito `https://api.heygen.com` e os campos adicionais `avatar_id` e `voice_id`. O adapter usa `X-Api-Key`, `POST /v3/videos`, polling em `/v3/videos/{id}` e descarrega o MP4 com o mesmo header. O teste de cartão nunca cria vídeo: chama apenas `GET /v3/users/me`.

Nano Banana, Hugging Face Inference API e InferencePort Proxy permanecem visíveis no catálogo/lista Full IA, mas só entram na execução de vídeo se o cartão declarar capacidade de vídeo e tiver um contrato de endpoint compatível. Não se deve declarar suporte de vídeo real para providers que apenas expõem geração de imagem.
