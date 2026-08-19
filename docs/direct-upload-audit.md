# Auditoria do YouTube-Video-Upload-Frontend-Api

Fonte: https://github.com/Nojus10/YouTube-Video-Upload-Frontend-Api

O projecto é TypeScript/JavaScript e implementa um upload não oficial através dos endpoints internos do frontend do YouTube. O README documenta cinco cookies necessários (`SID`, `SSID`, `HSID`, `APISID`, `SAPISID`), o `INNERTUBE_API_KEY`, o token manual `sessionInfo` e o `pageId`, que é obtido através de `ytcfg.data_.DELEGATED_SESSION_ID` quando a conta possui vários canais. O upload é feito em chunks a partir do disco, com `chunk_size` múltiplo de 262144 bytes.

O Thunderbolt não deve copiar cookies nem automatizar a extracção de sessões do navegador. A integração local deve aceitar os valores fornecidos manualmente pelo utilizador, guardar o `DELEGATED_SESSION_ID` por canal fora do Git e expor a subaba **Upload directo** apenas quando a configuração necessária existir. A implementação directa deve usar um adaptador Python configurável, validar MP4 e enviar o ficheiro em chunks; deve falhar claramente quando faltarem cookies, `sessionInfo`, `INNERTUBE_API_KEY` ou `DELEGATED_SESSION_ID`.

O repositório é antigo e não documenta uma API HTTP estável para consumo como serviço separado. Por isso, a adaptação é interna e não inclui o repositório no pacote npm. O método não substitui o upload oficial via `youtube-automation-agent`; é uma opção de upload directo separada e experimental, dependente de credenciais/sessão manuais.
