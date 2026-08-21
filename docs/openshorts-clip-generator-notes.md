# Notas de análise — OpenShorts Clip Generator

## OpenShorts

A página pública `https://www.openshorts.app/#app` apresenta o Clip Generator numa composição escura, com navegação lateral compacta e detalhes brass/dourados. O fluxo visível é: upload de ficheiro ou URL, selecção de formato 9:16 / 1:1 / 16:9, opções avançadas, confirmação de direitos sobre o conteúdo e botão Generate Clips. Depois da submissão, a interface apresenta Live Analysis, estado da execução, logs e uma grelha de Generated Shorts com contagem, preview e downloads.

O repositório `https://github.com/mutonby/openshorts` separa o dashboard React do backend. O componente principal referencia o Clip Generator como ferramenta `dashboard`, usa estados de processamento e resultados, e apresenta opções de formatos, upload/URL e painel de resultados. A integração do Thunderbolt não copiará o código nem as dependências cloud do OpenShorts; apenas adaptará a composição e o fluxo à UI Streamlit local.

## Thunderbolt actual

A navegação já contém `Edição` como menu expansível, com `Limpador de Metadados`, `Cortes` e `Editor Python`. A rota `Cortes` aponta actualmente para `render_edit_placeholder("Cortes", ...)`.

O módulo `hermes_ui/python_editor.py` já disponibiliza utilidades para listar vídeos, guardar uploads, cortar vídeo, remover/extrair/substituir áudio, alterar velocidade, redimensionar, criar registos e escrever manifestos. A nova aba deverá reutilizar os padrões de segurança e armazenamento existentes, mas ficará num módulo dedicado `hermes_ui/cuts.py` para não acoplar a lógica ao editor Python.

## Decisões aprovadas

A primeira versão será local e funcional: fonte por upload, URL ou vídeos gerados, modo manual e modo automático conservador, formatos 9:16/1:1/16:9, opções avançadas, confirmação de direitos, execução FFmpeg controlada, manifestos, histórico, preview e downloads. A análise “viral” por IA será uma extensão posterior; sem transcrição/provider disponível a UI deve manter um fallback manual explícito e não inventar resultados.
