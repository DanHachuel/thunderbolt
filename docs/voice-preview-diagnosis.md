# Diagnóstico do Teste de vozes

A instância limpa da UI 0.2.25 iniciou em `http://127.0.0.1:3039` com storage temporário vazio. O dashboard carregou sem `PermissionError`, sem `voice_preview_path` no estado e com a navegação normal. O próximo passo é abrir Configurações e confirmar que o painel Teste de vozes permanece carregado sem preview.

A aba **Configurações** abriu normalmente na versão 0.2.25. O painel **Teste de vozes** mostrou Provider, Voz, Velocidade, Texto de teste e `Testar voz`; não surgiu PermissionError nem player vazio, porque o storage temporário não tinha `voice_preview_path`.

Após descer até ao fim da página, o painel Teste de vozes ficou visível com provider `edge`, voz `en-US-AriaNeural-Female`, velocidade `+0%`, texto de teste e botão `Testar voz`. Não houve erro antes da execução.

Ao executar `Testar voz` na instância limpa, o erro de leitura de `Path('.')` não ocorreu. Como o ambiente de teste não tinha o pacote `edge_tts`, o painel mostrou a mensagem tratada `Não foi possível gerar o preview: No module named 'edge_tts'`, sem traceback. A release deve também tornar essa mensagem mais orientadora; a instalação normal já deve fornecer edge-tts através de requirements.txt.
