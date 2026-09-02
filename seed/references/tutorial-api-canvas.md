# Guia de Configuração: API Keys da Canva para o Thunderbolt

Este guia explica como criar e configurar uma integração no **Canva Developer Portal** para obter as credenciais (`Client ID` e `Client Secret`) usadas pelo módulo de geração de thumbnails do Thunderbolt.

## Pré-requisitos

É necessária uma conta Canva activa, gratuita ou paga, com **autenticação de dois factores (MFA)** activada. Sem MFA, o Developer Portal não permite criar a integração.

## 1. Aceder ao Developer Portal

1. Abra o [Canva Developer Portal](https://www.canva.com/developers/) e inicie sessão.
2. No menu superior, abra **Your integrations** ou aceda directamente a [https://www.canva.com/developers/integrations](https://www.canva.com/developers/integrations).

## 2. Criar uma integração

1. Clique em **Create an integration**.
2. Escolha **Public** ou **Private**. A opção Public requer revisão da Canva; a opção Private está disponível apenas para equipas Canva Enterprise. Para testes, use Private quando tiver acesso ao Canva Enterprise; caso contrário, use uma integração Public em modo de desenvolvimento.
3. Aceite os **Canva Developer Terms** e clique em **Create integration**.

## 3. Obter o Client ID e o Client Secret

Na configuração da integração, defina um nome como `Thunderbolt Thumbnail Generator`, copie o **Client ID** e clique em **Generate secret** para criar o **Client Secret**. Guarde o secret imediatamente num local seguro, pois a Canva não o volta a apresentar.

> Nunca publique estas credenciais, nem as inclua em commits, screenshots ou mensagens. Se forem expostas, revogue-as e gere um novo secret.

## 4. Configurar os scopes

No menu **Scopes**, active apenas as permissões necessárias:

| Scope | Acesso | Finalidade |
| --- | --- | --- |
| `design:content` | Read and Write | Criar, editar e exportar designs |
| `design:meta` | Read | Ler metadados dos designs |
| `asset:content` | Read and Write | Gerir imagens, fontes e outros assets |
| `profile` | Read | Ler informações básicas do perfil |

Para Brand Templates com Autofill, pode activar opcionalmente `brandtemplate:meta` (Read) e `brandtemplate:content` (Read). Integrações públicas devem justificar cada scope durante a revisão.

## 5. Configurar as URLs de redireccionamento

A Canva Connect API usa OAuth 2.0 com PKCE. Em **Authentication > Authorized redirects**, adicione exactamente:

```text
http://127.0.0.1:3001/oauth/redirect
```

Para activar o retorno de navegação, habilite **Enable return navigation** e use:

```text
http://127.0.0.1:3001/return-nav
```

É possível adicionar até dez URLs. O protocolo, host, porta e caminho devem coincidir exactamente com os valores usados pelo Thunderbolt.

## 6. Configurar as credenciais no Thunderbolt

Na raiz do projecto, localize ou crie o ficheiro `.env` e adicione:

```dotenv
CANVA_CLIENT_ID=seu_client_id_aqui
CANVA_CLIENT_SECRET=seu_client_secret_aqui
```

O `.env` já deve estar protegido pelo `.gitignore`. Não faça commit deste ficheiro.

## 7. Configurar um template de thumbnails (opcional)

Se utilizar a skill `bulk-create` com templates predefinidos, adicione também:

```dotenv
CANVA_THUMBNAIL_TEMPLATE_ID=id_do_template_canva
```

O ID pode ser obtido na URL do design no Canva ou através de `GET /v1/brand-templates`.

## 8. Testar a integração

1. Inicie o Thunderbolt.
2. Abra **Canva Skills** no Streamlit.
3. Seleccione uma skill, como **Resize for Social Media**.
4. Introduza um `design_id` válido e execute a operação.
5. Autorize o Thunderbolt quando o fluxo OAuth 2.0 com PKCE o redireccionar para a Canva.

Após a autorização, o Thunderbolt recebe e armazena o token necessário para executar as operações.

## Dados necessários

| Variável | Onde encontrar | Exemplo |
| --- | --- | --- |
| `CANVA_CLIENT_ID` | Developer Portal → integração → Credentials | `1234567890abcdef` |
| `CANVA_CLIENT_SECRET` | Gerado no Developer Portal; guardar imediatamente | `ghi_jklmnopqrstuvwxyz123456` |
| `CANVA_THUMBNAIL_TEMPLATE_ID` | URL do template ou `GET /v1/brand-templates` | `DAF1234567890` |

## Diagnóstico rápido

| Problema | Solução |
| --- | --- |
| **MFA required** | Active a autenticação de dois factores nas definições da conta Canva. |
| Erro 401 ou token expirado | Verifique o armazenamento do `refresh_token`; o Thunderbolt implementa refresh automático. |
| Erro 429 | Aguarde e tente novamente; a API aplica limites de frequência. |
| Design não encontrado | Confirme o `design_id`; designs criados via API e não editados durante sete dias podem ser eliminados permanentemente. |
| URL de redireccionamento inválida | Compare a URL do Developer Portal com a usada pelo Thunderbolt, incluindo protocolo e porta. |

## Referências

- [Canva Developer Portal](https://www.canva.com/developers/)
- [Criar integrações](https://www.canva.dev/docs/connect/creating-integrations/)
- [Autenticação OAuth 2.0 com PKCE](https://www.canva.dev/docs/connect/authentication/)
- [Scopes disponíveis](https://www.canva.dev/docs/connect/appendix/scopes/)
- [Canva Connect API Starter Kit](https://github.com/canva-sdks/canva-connect-api-starter-kit)

Depois de configurar as credenciais, é possível testar a geração de thumbnails na interface Streamlit, integrar a operação ao callback `on_video_completed` e ajustar as dimensões das plataformas em `app/modules/canva_skills/resize.py`.
