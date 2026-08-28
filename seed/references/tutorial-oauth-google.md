# Tutorial completo: configurar OAuth do Google para o Thunderbolt

Este tutorial explica como criar um projecto no Google Cloud, activar a YouTube Data API v3, configurar a tela de consentimento OAuth, criar as credenciais e ligá-las ao Thunderbolt.

## Pré-requisitos

Antes de começar, certifique-se de que tem uma conta Google, acesso ao [Google Cloud Console](https://console.cloud.google.com/) e o Thunderbolt instalado e em execução localmente. A aplicação em execução é necessária para confirmar a URI de redireccionamento OAuth utilizada pelo projecto.

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

No menu lateral, abra **APIs e Serviços → Credenciais** e clique em **+ Criar credenciais → ID do cliente OAuth**. Em **Tipo de aplicativo**, seleccione **Aplicativo da Web** e atribua um nome, por exemplo, `Thunderbolt Web Client`.

### Origens JavaScript autorizadas

Clique em **Adicionar URI** e introduza a origem onde o frontend é executado, por exemplo:

```text
http://localhost:3000
```

Se existir um ambiente de produção, adicione também a origem HTTPS correspondente, por exemplo `https://seudominio.com`.

### URIs de redireccionamento autorizadas

Esta é a parte mais crítica. Clique em **Adicionar URI** e introduza a URI exacta utilizada pelo Thunderbolt para o callback OAuth. Exemplos de desenvolvimento local:

```text
http://localhost:3000/api/auth/google/callback
http://localhost:5173/oauth2callback
```

> **A URI tem de ser exactamente igual à configurada no código do Thunderbolt.** Uma barra final diferente, o uso de `http` em vez de `https` ou uma porta diferente causa o erro `redirect_uri_mismatch`.

Se não souber qual é a URI utilizada, consulte a configuração ou o ficheiro de ambiente do Thunderbolt e confirme também os logs da aplicação.

Clique em **Criar**. Na janela apresentada, copie o **ID do cliente (Client ID)** e a **Chave secreta do cliente (Client Secret)** e guarde-os num local seguro.

> **Nunca partilhe o Client Secret nem o envie para o controlo de versão Git.**

## Passo 7 — Configurar o Thunderbolt

O projecto utiliza variáveis de ambiente para as credenciais OAuth. Localize o ficheiro de ambiente do Thunderbolt, normalmente `.env`, `.env.local` ou o ficheiro de configuração equivalente, e adicione:

```env
GOOGLE_CLIENT_ID=seu_client_id_aqui
GOOGLE_CLIENT_SECRET=sua_client_secret_aqui
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback
```

Substitua `seu_client_id_aqui` e `sua_client_secret_aqui` pelos valores copiados no passo anterior. Confirme que `GOOGLE_REDIRECT_URI` é exactamente igual à URI registada no Google Cloud Console.

## Passo 8 — Testar a autenticação

Reinicie o servidor do Thunderbolt para carregar as novas variáveis de ambiente. Abra a interface e tente iniciar sessão com o Google.

O fluxo esperado é:

1. O Google apresenta a tela de consentimento com o nome do app e os escopos solicitados.
2. O utilizador autoriza o acesso.
3. O Google redirecciona para a URI de callback do Thunderbolt.
4. A autenticação é concluída com sucesso na aplicação.

## Solução de problemas

### Erro `redirect_uri_mismatch`

Este erro significa que a URI enviada pelo Thunderbolt não corresponde exactamente à URI registada no Google Cloud Console.

Verifique a URI utilizada nos logs ou no código do Thunderbolt. Depois, abra **Credenciais**, seleccione o ID do cliente e adicione a URI exacta em **URIs de redireccionamento autorizadas**. Aguarde um a dois minutos para a configuração se propagar, limpe o cache do navegador e tente novamente.

### Erro `invalid_request` ou `access_denied`

Confirme se o seu e-mail foi adicionado como utilizador de teste no passo 5. Verifique também se os escopos necessários estão activos, especialmente `youtube.upload`.

### Mensagem “Acesso bloqueado: solicitação inválida”

Na maioria dos casos, esta mensagem está relacionada com uma URI de redireccionamento incorrecta. Reveja cuidadosamente os passos 6 e 7, verificando protocolo, domínio, porta, caminho e barras finais.

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
