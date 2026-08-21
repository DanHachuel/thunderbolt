# Auditoria do YouTube-Video-Upload-Frontend-Api

Fonte: https://github.com/Nojus10/YouTube-Video-Upload-Frontend-Api

O projecto é TypeScript/JavaScript e implementa um upload não oficial através dos endpoints internos do frontend do YouTube. O README documenta cinco cookies necessários (`SID`, `SSID`, `HSID`, `APISID`, `SAPISID`), o `INNERTUBE_API_KEY`, o token manual `sessionInfo` e o `pageId`, que é obtido através de `ytcfg.data_.DELEGATED_SESSION_ID` quando a conta possui vários canais. O upload é feito em chunks a partir do disco, com `chunk_size` múltiplo de 262144 bytes.

O Thunderbolt não deve copiar cookies nem automatizar a extracção de sessões do navegador. A integração local aceita um documento JSON fornecido pelo utilizador, guarda-o por conta Google fora do Git e mantém no documento um mapa `delegated_session_ids` por canal. A UI não expõe os valores nem cria inputs para cookies, `sessionInfo`, `INNERTUBE_API_KEY`, chunk size ou `DELEGATED_SESSION_ID`. A implementação directa valida o documento, valida MP4 e envia o ficheiro em chunks; falha claramente quando faltar qualquer entrada obrigatória.

O documento por Gmail é guardado em `storage/youtube_direct_accounts/<account-id>/credentials.json` e contém cookies, sessionInfo, INNERTUBE_API_KEY, chunk_size e o mapa de IDs delegados. O repositório não inclui documentos de credenciais nem o projecto de referência no pacote npm.

O método não substitui o upload oficial via `youtube-automation-agent`; é uma opção de upload directo separada e experimental, dependente do documento JSON local fornecido pelo utilizador.
