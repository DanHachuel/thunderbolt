-- Thunderbolt AI Influencers schema
-- Apply in Supabase SQL Editor. Storage bucket creation is optional and may be
-- performed from the dashboard with the configured bucket name.

create table if not exists public.influencers (
  id text primary key,
  name text not null,
  bio text not null default '',
  instagram_business_id text not null default '',
  language text not null default '',
  profile_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.influencer_assets (
  id text primary key,
  influencer_id text not null references public.influencers(id) on delete cascade,
  asset_type text not null check (asset_type in ('image', 'document')),
  original_name text not null,
  stored_path text not null,
  public_url text not null default '',
  mime_type text not null default 'application/octet-stream',
  size_bytes bigint not null default 0,
  sha256 text not null,
  document_json jsonb,
  created_at timestamptz not null default now(),
  unique (influencer_id, sha256)
);
create index if not exists idx_influencer_assets_influencer on public.influencer_assets(influencer_id, created_at);

create table if not exists public.influencer_weekly_plans (
  id text primary key,
  influencer_id text not null references public.influencers(id) on delete cascade,
  week text not null,
  plan text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (influencer_id, week)
);

create table if not exists public.influencer_content (
  id text primary key,
  influencer_id text not null references public.influencers(id) on delete cascade,
  content_type text not null check (content_type in ('image', 'video')),
  prompt text not null default '',
  caption text not null default '',
  provider text not null default '',
  model text not null default '',
  platform text not null default '',
  state text not null default 'queued',
  artifact_path text not null default '',
  provider_request_id text not null default '',
  error text not null default '',
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_influencer_content_influencer on public.influencer_content(influencer_id, created_at);
create index if not exists idx_influencer_content_state on public.influencer_content(state, updated_at);

alter table public.influencers enable row level security;
alter table public.influencer_assets enable row level security;
alter table public.influencer_weekly_plans enable row level security;
alter table public.influencer_content enable row level security;

-- Configure least-privilege policies for the key used by Thunderbolt in your
-- deployment. Do not make these tables public unless that is intentional.
-- Example for a trusted local service_role key is deliberately omitted here.
