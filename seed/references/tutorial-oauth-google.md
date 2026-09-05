# Tutorial completo: configurar OAuth do Google para o Thunderbolt

Este tutorial explica como criar um projecto no Google Cloud, activar a YouTube Data API v3, configurar a tela de consentimento OAuth, criar as credenciais e ligá-las ao Thunderbolt.

## Pré-requisitos

Antes de começar, certifique-se de que tem uma conta Google, acesso ao [Google Cloud Console](https://console.cloud.google.com/) e o Thunderbolt instalado e em execução localmente. A aplicação em execução é necessária para concluir o callback OAuth local.

## Passo 1 — Aceder ao Google Cloud Console

Abra o [Google Cloud Console](https://console.cloud.google.com/) e faça login com a sua conta Google. Se for a primeira utilização, aceite os Termos de Serviço apresentados.

## Passo 2 — Criar ou seleccionar um projecto

No topo da página, clique no selector de projectos, junto a **Google Cloud**. No diálogo apresentado, seleccione **Novo projecto** e preencha os campos seguintes:

| Campo | Valor sugerido |
|---|---|
| Nome do projecto | `Thunderbolt` |
| Organização | Deixe em branco ou seleccione a organização predefinida |

Clique em **Criar**, aguarde a conclusão e use o selector de projectos para mudar para o projecto criado.

## Passo 3 — Activar a YouTube Data API v3

No menu lateral, abra **APIs e Serviços → Biblioteca**. Pesquise por **YouTube Data API v3**, abra o resultado correspondente e clique em **Activar**.

Se a **Google+ API** ainda aparecer como opção no seu projecto, a sua activação é opcional e pode ser útil para funcionalidades legadas que dependam dela.

## Passo 4 — Configurar a tela de consentimento OAuth

> **Este é um passo obrigatório.** A tela de consentimento é apresentada ao utilizador quando o Thunderbolt solicita autorização para aceder à conta Google/YouTube.

No menu lateral, abra **APIs e Serviços → Tela de consentimento OAuth**. Clique em **Começar** ou **Configurar tela de consentimento**, conforme a opção apresentada.

Em **Tipo de utilizador**, seleccione **Externo** e clique em **Criar**. Na secção **Informações do app**, preencha:

| Campo | Valor sugerido |
|---|---|
| Nome do app | `Thunderbolt` ou o nome pretendido |
| E-mail para suporte do utilizador | O seu e-mail |
| Logótipo do app | Opcional; pode deixar em branco |
| Domínio da página inicial | Deixe em branco ou utilize `localhost` para desenvolvimento local |
| Política de privacidade | Opcional nesta fase |
| Termos de serviço | Opcional nesta fase |

Clique em **Próxima**. Em **Público**, mantenha a opção **Externo** e avance novamente.

Em **Escopos**, clique em **Adicionar ou remover escopos**, pesquise por `youtube` e seleccione:

| Escopo | Finalidade |
|---|---|
| `https://www.googleapis.com/auth/youtube` | Gerir a sua conta do YouTube |
| `https://www.googleapis.com/auth/youtube.upload` | Gerir os seus vídeos do YouTube e efectuar uploads |
| `https://www.googleapis.com/auth/youtube.readonly` | Visualizar a sua conta do YouTube; opcional |

Clique em **Actualizar** e depois em **Próxima**. Em **Informações de contacto**, indique o seu e-mail para receber notificações do Google e avance.

Na página **Concluir**, leia a Política de Dados do Utilizador, marque a caixa de concordância e clique em **Continuar** e, depois, em **Criar**.

> **Importante:** depois de criada, a tela de consentimento não pode ser removida, embora possa ser editada posteriormente.

## Passo 5 — Adicionar utilizadores de teste

Enquanto a aplicação estiver com o estado **Não verificado**, o Google exige que os utilizadores de teste sejam adicionados manualmente para permitir o login.

Na página da tela de consentimento OAuth, abra o separador **Público-alvo** e, na área **Utilizadores de teste**, clique em **Adicionar utilizadores**. Introduza o seu e-mail, clique em **Adicionar** e depois em **Guardar**.

## Passo 6 — Criar as credenciais OAuth

No menu lateral, abra **APIs e Serviços → Credenciais** e clique em **+ Criar credenciais → ID do cliente OAuth**. Em **Tipo de aplicativo**, seleccione **Aplicativo para computador** (também apresentado como **Desktop app**) e atribua um nome, por exemplo, `Thunderbolt Desktop Client`.

> **Importante:** o Thunderbolt usa `InstalledAppFlow` com um callback local loopback. Não seleccione **Aplicativo da Web**. Essa credencial exige URIs fixas e causa `Erro 400: redirect_uri_mismatch` neste fluxo.

Uma credencial **Desktop app** não precisa de **Origens JavaScript autorizadas** nem de adicionar manualmente uma URI de redireccionamento. O Thunderbolt inicia o callback local em `http://127.0.0.1:8765/`; se essa porta estiver ocupada, escolhe automaticamente outra porta loopback livre.

Clique em **Criar**. Na janela apresentada, copie o **ID do cliente (Client ID)** e a **Chave secreta do cliente (Client Secret)** e guarde-os num local seguro.

> **Nunca partilhe o Client Secret nem o envie para o controlo de versão Git.**

## Passo 7 — Configurar o Thunderbolt

Na aba **Configurações → Configuração API → API Keys Upload → Contas Google**, crie ou edite a conta Google e cole o **Client ID** e o **Client Secret** da credencial **Desktop app**. Guarde a conta e clique em **Autorizar/Reautorizar**.

Não é necessário configurar `GOOGLE_REDIRECT_URI` nem adicionar uma URI de callback de `localhost` no Google Cloud Console: o callback loopback é criado pelo `InstalledAppFlow` durante a autorização.

## Passo 8 — Testar a autenticação

Abra a interface do Thunderbolt e tente autorizar a conta Google.

O fluxo esperado é:

1. O Google apresenta a tela de consentimento com o nome do app e os escopos solicitados.
2. O utilizador autoriza o acesso.
3. O Google redirecciona para o callback local do Thunderbolt.
4. A autenticação é concluída e o token é guardado no storage local da conta.

## Solução de problemas

### Erro `redirect_uri_mismatch`

Este erro ocorre normalmente quando foi criada uma credencial **Aplicativo da Web** para o fluxo local. Abra **APIs e Serviços → Credenciais**, crie uma nova credencial **ID do cliente OAuth → Aplicativo para computador (Desktop app)**, substitua o Client ID e o Client Secret na conta Google do Thunderbolt e tente novamente. Não tente corrigir este fluxo adicionando uma URI de `localhost` numa credencial Web.

### Erro `invalid_request` ou `access_denied`

Confirme se o seu e-mail foi adicionado como utilizador de teste no passo 5. Verifique também se os escopos necessários estão activos, especialmente `youtube.upload`.

### Mensagem “Acesso bloqueado: solicitação inválida”

Confirme primeiro que a credencial é **Aplicativo para computador (Desktop app)** e não **Aplicativo da Web**. Depois confirme que a conta Google foi adicionada como utilizador de teste e que a YouTube Data API v3 está activa.

## Escopos importantes para o YouTube

Para efectuar uploads de vídeos, o Thunderbolt utiliza principalmente os seguintes escopos OAuth:

| Escopo | Descrição |
|---|---|
| `https://www.googleapis.com/auth/youtube` | Gerir a sua conta do YouTube |
| `https://www.googleapis.com/auth/youtube.upload` | Gerir os seus vídeos do YouTube e efectuar uploads |
| `https://www.googleapis.com/auth/youtube.readonly` | Visualizar a sua conta do YouTube; opcional |

> **Boa prática de segurança:** mantenha o Client Secret fora do código, dos ficheiros versionados e de mensagens públicas. Use variáveis de ambiente e restrinja o acesso às credenciais.

## Referências

- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [Documentação OAuth 2.0 do Google](https://developers.google.com/identity/protocols/oauth2)
