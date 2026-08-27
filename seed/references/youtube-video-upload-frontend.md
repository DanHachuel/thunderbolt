# Tutorial YouTube Video-Upload Frontend

Este tutorial explica como utilizar, de forma responsável, o fluxo **Direct upload** do Thunderbolt para vídeos já concluídos. A rota é uma integração técnica baseada em comportamentos do frontend do YouTube e pode mudar sem aviso. Use-a somente em contas e canais que controla e respeite as políticas aplicáveis do YouTube.

> **Segurança primeiro:** dados de sessão, cookies de autenticação, identificadores de canal e material de credencial são confidenciais. Nunca os copie para conversas, capturas de ecrã, issues, ficheiros versionados ou campos de texto comuns. Configure-os exclusivamente nos campos protegidos da aplicação local.

## 1. Antes de começar

Confirme que o vídeo foi concluído no **Video Backlog** e que o respectivo canal YouTube está seleccionado no Thunderbolt. No formulário de Upload, confirme título, descrição, tags, privacidade, categoria e idioma antes de autorizar qualquer envio.

O Thunderbolt oferece dois percursos distintos: o fluxo oficial, que utiliza a integração de API autorizada, e o fluxo directo, destinado a uma sessão válida e a uma conta controlada pelo utilizador. Estes percursos não devem ser usados para contornar políticas, limites da plataforma ou permissões de canal.

| Elemento | Finalidade | Boa prática |
| --- | --- | --- |
| Vídeo | Ficheiro final da tarefa concluída | Verifique duração, áudio, miniatura e legendas antes do envio. |
| Metadados | Título, descrição, tags, idioma e privacidade | Reveja manualmente antes de publicar. A descrição por IA pode ser editada. |
| Canal | Destino associado à conta autorizada | Confirme que é o canal correcto, sobretudo em contas com vários canais. |
| Sessão | Autorização temporária de upload directo | Mantenha-a apenas em armazenamento local protegido e actualize-a quando expirar. |

## 2. Preparar a autenticação de forma segura

No Thunderbolt, abra **Upload > Direct upload** e utilize os controlos de autorização fornecidos pela interface. Complete o procedimento somente no seu navegador e conta YouTube. Não partilhe dados de sessão, cookies, tokens temporários, IDs de canal ou chaves de integração com terceiros.

Se a verificação de saúde indicar sessão expirada, interrompa o envio e renove a autorização pela interface. O sistema deve apresentar o diagnóstico sem mostrar os valores protegidos. Nunca use valores de exemplo ou chaves encontradas em documentos públicos.

## 3. Envio em partes e memória

O envio directo pode transferir o ficheiro em partes, em vez de carregar todo o vídeo para a memória de uma só vez. Esta estratégia é adequada para ficheiros grandes e reduz a pressão de memória no computador. O Thunderbolt mantém o vídeo no armazenamento local e regista apenas o estado e o resultado do processo.

## 4. Executar o envio

Abra **Upload > Conventional upload** para rever os metadados. Utilize **Gerar descrição com IA** apenas quando quiser uma sugestão editorial; o resultado permanece editável. O campo **Idioma** é detectado da tarefa ou canal e é mostrado numa lista suspensa para evitar códigos escritos incorrectamente.

Depois de confirmar o canal, a privacidade e os metadados, seleccione o fluxo de envio apropriado. Um envio publica ou cria conteúdo numa plataforma externa; por isso, o Thunderbolt deve exigir a confirmação explícita do utilizador antes da acção.

## 5. Diagnóstico e manutenção

| Situação | Acção recomendada |
| --- | --- |
| Sessão expirada ou não autorizada | Renove a autorização na interface e volte a executar a verificação de saúde. |
| Canal incorrecto | Cancele antes do envio e seleccione o canal certo. |
| Falha de rede | Não repita automaticamente sem confirmar se o vídeo foi criado no YouTube Studio. |
| Metadados incompletos | Corrija título, descrição, tags, idioma ou privacidade no formulário antes de enviar. |
| Limite ou política da plataforma | Pare o processo e siga as políticas e limites actualmente aplicáveis do YouTube. |

## Referência técnica

O material fornecido pelo utilizador cita o repositório [Nojus10/YouTube-Video-Upload-Frontend-Api](https://github.com/Nojus10/YouTube-Video-Upload-Frontend-Api). O Thunderbolt apresenta este tutorial como orientação de integração segura; não replica segredos, valores de autenticação nem instruções de extracção de credenciais.
