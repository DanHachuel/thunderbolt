# Guia para criar e configurar uma conta Supabase

Este guia mostra como criar uma conta gratuita no Supabase e preparar as tabelas e o armazenamento necessários para utilizar a base de dados com automações n8n e com o módulo AI Influencers do Thunderbolt.

Comece por abrir o [Supabase](https://supabase.com/) e criar uma nova conta gratuita.

## 1. Criar as tabelas da base de dados

Quando a conta estiver pronta, abra o `Table Editor`.

![Table Editor](https://github.com/user-attachments/assets/03f22c7c-18d5-4de0-81e0-f4fcee127647)

Para criar uma tabela nova, clique no botão `New table`.

![New table](https://github.com/user-attachments/assets/2a8e59f5-d20c-470e-abc8-c15966f438c1)

### Criar a tabela `plans`

A tabela `plans` deve ter quatro campos:

1. `id` (`int8`) — chave primária; utilize as definições predefinidas.
2. `period_type` (`text`) — identifica os períodos. Os valores possíveis são `quarter`, `month` e `week`.
3. `period_index` (`text`) — guarda o índice do período, por exemplo `2025-Q2` para o segundo trimestre de 2025.
4. `plan_value` (`text`) — guarda o valor efectivo do plano para o período indicado.

![Campos da tabela plans](https://github.com/user-attachments/assets/d308dd34-8fde-4cd4-8347-d2e97db1d648)

Quando terminar, clique em `Save`.

### Criar a tabela `posts`

Crie a tabela `posts` com os seguintes campos:

1. `id` (`int8`) — chave primária; utilize as definições predefinidas.
2. `created_at` (`timestamp`) — valor predefinido `now()`.
3. `post_summary` (`text`) — guarda o resumo de cada publicação para manter consistência entre publicações.
4. `image_path` (`text`) — guarda o caminho da imagem gerada e carregada para o bucket do Supabase Storage.

![Campos da tabela posts](https://github.com/user-attachments/assets/917d2556-eb3d-48a1-9095-65332882fd0c)

## 2. Criar o bucket de Storage

No menu do Supabase, clique em `Storage`.

![Menu Storage](https://github.com/user-attachments/assets/e7cbd532-b7bd-4404-a169-2965932be24e)

Clique em `New bucket`.

![New bucket](https://github.com/user-attachments/assets/9deca74e-1798-4733-8593-0b5593857ab4)

Dê ao bucket o nome `instagram-images` ou outro nome compatível com as regras de nomenclatura. Guarde esse nome, porque será necessário configurá-lo no n8n.

![Nome do bucket](https://github.com/user-attachments/assets/10cf6666-63bb-4404-a169-2965932be24e)

Depois, carregue a imagem de referência para o bucket usando o botão `Upload files`.

![Upload files](https://github.com/user-attachments/assets/6cc83262-b92c-4f74-86c3-a45c9c0456f8)

## 3. AI Influencers no Thunderbolt

Para usar **AI Influencers > Personagens** e **Geração de Conteúdo IA** com Supabase, aplique o ficheiro `seed/references/ai_influencers_schema.sql` no SQL Editor. Ele cria as tabelas `influencers`, `influencer_assets`, `influencer_weekly_plans` e `influencer_content`, além dos índices e da activação de RLS.

No Thunderbolt, abra **Configurações > Configuração API > AI Influencers > Banco de Dados Influencers**, seleccione **Supabase** e preencha o **Supabase Project URL**, a **Supabase API key** e o bucket de Storage. Crie o bucket com o mesmo nome configurado, por defeito `ai-influencers`, e confirme as políticas RLS/Storage antes de guardar imagens ou documentos. A chave não deve ser colocada no GitHub, nos workflows JSON ou em screenshots.

O Thunderbolt usa o Supabase como backend seleccionado, não como executor de n8n: os assets são enviados ao Storage, os metadados ficam nas tabelas e os estados de geração ficam em `influencer_content`. Para uma execução totalmente local, seleccione **SQLite** no mesmo painel; a alternativa cria `storage/state/ai_influencers.db` e não utiliza a conta Supabase.

A conta Supabase está pronta para ser utilizada pela automação.

Fonte original: [guide-supabase.md no GitHub](https://github.com/gyoridavid/ai_agents_az/blob/main/episode_8/guide-supabase.md)
