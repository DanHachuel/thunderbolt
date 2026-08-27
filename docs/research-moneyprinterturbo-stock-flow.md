# Evidência de referência — pipeline stock do MoneyPrinterTurbo

Fonte principal: https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README-en.md
Fonte de materiais: https://github.com/harry0703/MoneyPrinterTurbo/blob/main/app/services/material.py
Checkout local: `/tmp/MoneyPrinterTurbo`, branch `main`, commit observado `ab1c790`.

O README oficial descreve uma pipeline que recebe tema/palavra-chave, gera roteiro, associa footage, cria legendas e música de fundo e produz um vídeo HD. A lista de funcionalidades confirma suporte a formatos vertical 9:16 e horizontal 16:9, lote de vídeos, duração dos clips, música de fundo ajustável, assets locais e footage gratuito de Pexels, Pixabay e Coverr. O código do serviço de materiais pesquisa termos, aplica orientação e duração mínima, recolhe candidatos, evita URLs duplicadas, pode ordenar aleatoriamente ou sequencialmente, descarrega os clips e entrega ficheiros locais para a composição.

No MoneyPrinterTurbo, Pexels e Pixabay são fontes de materiais stock e não providers de geração de vídeo Full IA. A integração usa chaves específicas da fonte, pesquisa por termos extraídos do roteiro, escolhe rendições compatíveis com a orientação/resolução e passa os ficheiros locais ao estágio de composição. MoviePy/FFmpeg é usado na infraestrutura de composição do projecto.

No Thunderbolt, antes desta correcção, a UI já persistia `style_wide`/`background_mode`/`music_mode`, mas o worker encaminhava apenas `--subject` e, em alguns casos, `--custom-audio-file` ao helper. O helper assumia Pexels quando não recebia `--video-source`, enquanto os semânticos `full_ia` e `music` não eram separados nesse ponto. O worker também possuía uma rota externa independente através do pool de vídeo. A implementação actual separa explicitamente as três rotas e garante a ordem Tema → Script → Título → Keywords opcional → Vídeo → Prompt Thumbnail JSON → Thumbnail → Upload.
