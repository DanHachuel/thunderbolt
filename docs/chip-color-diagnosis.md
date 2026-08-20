# Diagnóstico das cores dos chips — 0.2.24

A instância limpa arrancada com o código actual carregou correctamente como Thunderbolt 0.2.24. A instância anterior em `3037` apresentou um `ImportError` porque era um processo Streamlit antigo que não recarregou `set_channel_defaults`; a importação funciona numa execução Python limpa e a instância nova não apresenta esse erro.

A próxima verificação abre **Upload** e inspecciona os elementos reais dos chips antes de substituir o CSS `:has(button[aria-label*=...])`.

Na UI limpa 0.2.24, **Upload** abriu com o chip YouTube dentro do campo. O dropdown compacto expôs exactamente `TikTok`, `Instagram` e `Facebook Pages` além de YouTube. A próxima operação seleccionará os três destinos e recolherá classes, atributos e estilos computados dos quatro chips.

O driver não persistiu o clique/selector acessível de TikTok e a entrada directa no combobox fechou o dropdown sem adicionar o chip. Isto é uma limitação de automação do widget BaseWeb; a análise de cores será feita directamente no DOM e a validação final usará o comportamento visual e os estilos calculados.

A inspecção DOM confirmou a causa: o Streamlit actual renderiza o chip como `span[data-tag][aria-label="YouTube"]`, contendo o texto e o botão `aria-label="Remove YouTube"`. Não existe `data-baseweb="tag"` nesse DOM. A regra anterior só visava `data-baseweb=tag`, por isso não aplicava as cores por plataforma e o tema deixava o chip com o vermelho padrão. A nova regra usa directamente `span[data-tag][aria-label="YouTube|TikTok|Instagram|Facebook Pages"]`, mantendo fallback para versões antigas.

Depois da edição, o Streamlit apresentou `File change` e pediu `Rerun`; antes de aplicar o rerun, o estilo computado continuava no vermelho padrão `rgb(255, 75, 75)`. O rerun foi aplicado e a medição será repetida numa sessão actualizada.

Após o rerun, a cor computada do chip YouTube passou para `rgb(255, 0, 0)`, confirmando que o novo selector funciona. O dropdown voltou a expor `TikTok`, `Instagram` e `Facebook Pages`; a selecção será feita pelo DOM para validar as cores restantes.

A selecção DOM de `TikTok` funcionou: o campo passou a mostrar os chips YouTube e TikTok e o dropdown permaneceu aberto com Instagram e Facebook Pages. A cor visual de TikTok já aparece preta no screenshot, conforme esperado.

A selecção DOM de `Instagram` funcionou. O screenshot mostra YouTube vermelho, TikTok preto e Instagram rosa; o dropdown ficou reduzido à opção `Facebook Pages`, que será adicionada para concluir a validação dos quatro chips.

Validação final com os quatro chips seleccionados na ordem YouTube, TikTok, Instagram, Facebook Pages:

| Chip | Cor computada |
|---|---|
| YouTube | `rgb(255, 0, 0)` |
| TikTok | `rgb(0, 0, 0)` |
| Instagram | `rgb(225, 48, 108)` = `#e1306c` |
| Facebook Pages | `rgb(24, 119, 242)` = `#1877f2` |

Todos os textos e ícones ficaram brancos. O widget continuou compacto dentro do campo e o dropdown mostrou `No results` apenas porque todas as quatro opções já estavam seleccionadas.
