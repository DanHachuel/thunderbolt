# Smoke test — defaults por canal

A UI 0.2.23 iniciou em `http://127.0.0.1:3037` com um canal de demonstração no storage temporário. O dashboard mostrou `Canais 1` e `1 activos`. O próximo passo é confirmar os editores de Blueprint e voz em Canais e Automação e a persistência dos valores.

A aba **Canais** mostrou o expander `Definir Blueprint e voz padrão`, com os selectores `Blueprint padrão`, `Voz padrão` e botão `Guardar Blueprint e voz`. A aba **Automação** mostrou os mesmos dois selectores no cartão do canal, junto do botão `Guardar` do agendamento. Ambos começam sincronizados com os valores persistidos (`Sem Blueprint padrão` e `Sem voz padrão` no canal de demonstração).

O selector de Blueprint na Automação abriu e mostrou 14 opções, incluindo os seeds `CELEBRITIES`, `BlueprintCocomelon`, `BlueprintUniverso` e outros. A selecção automática por índice não persistiu através da camada de automação do navegador, pelo que a validação continuará usando entrada directa/Enter e verificação do storage, sem tratar este comportamento do driver como falha da UI.

Na Automação, seleccionei `BlueprintCocomelon` e introduzi `pt-BR-FranciscaNeural-Female`; após clicar em `Guardar`, o cartão passou a mostrar `Blueprint actual: BlueprintCocomelon · Voz actual: pt-BR-FranciscaNeural-Female`. Os dois selectores permaneceram com esses valores, confirmando a persistência no canal.

Ao voltar a **Canais**, o expander mostrou automaticamente `BlueprintCocomelon` e `pt-BR-FranciscaNeural-Female` já seleccionados. Isto confirma que Canais e Automação lêem os mesmos campos persistidos do canal.
