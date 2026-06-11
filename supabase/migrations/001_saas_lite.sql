create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  display_name text,
  plan text not null default 'manual_validation',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.check_requests (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  marketplace text not null default 'manual',
  title text not null,
  description text not null default '',
  brand text not null default '',
  category text not null default '',
  image_urls jsonb not null default '[]'::jsonb,
  seller_context text not null default 'unknown',
  status text not null default 'submitted',
  created_at timestamptz not null default now()
);

create table if not exists public.risk_results (
  id uuid primary key default gen_random_uuid(),
  request_id uuid not null references public.check_requests(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  risk_score integer not null,
  risk_level text not null,
  breakdown jsonb not null default '{}'::jsonb,
  recommendations jsonb not null default '[]'::jsonb,
  uncertainty jsonb not null default '[]'::jsonb,
  disclaimer text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.report_exports (
  id uuid primary key default gen_random_uuid(),
  request_id uuid not null references public.check_requests(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  storage_bucket text not null default 'sellersflare-reports',
  storage_path text not null,
  format text not null default 'pdf',
  created_at timestamptz not null default now()
);

create index if not exists check_requests_owner_created_idx
  on public.check_requests(owner_id, created_at desc);

create index if not exists risk_results_owner_created_idx
  on public.risk_results(owner_id, created_at desc);

create index if not exists report_exports_owner_created_idx
  on public.report_exports(owner_id, created_at desc);

alter table public.profiles enable row level security;
alter table public.check_requests enable row level security;
alter table public.risk_results enable row level security;
alter table public.report_exports enable row level security;

create policy "profiles_select_own"
  on public.profiles for select
  using (auth.uid() = id);

create policy "profiles_update_own"
  on public.profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

create policy "check_requests_select_own"
  on public.check_requests for select
  using (auth.uid() = owner_id);

create policy "check_requests_insert_own"
  on public.check_requests for insert
  with check (auth.uid() = owner_id);

create policy "risk_results_select_own"
  on public.risk_results for select
  using (auth.uid() = owner_id);

create policy "report_exports_select_own"
  on public.report_exports for select
  using (auth.uid() = owner_id);

-- Server-side workers should insert risk_results and report_exports with a
-- privileged Supabase service role key held only in deployment secret storage.
