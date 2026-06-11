2026-06-11 "Sellersflare SaaS Lite: Supabase integration plan"

## Goal

Turn the current OSS MVP into a small SaaS shell without changing the explainable rules-first risk engine.

The first SaaS version should provide:

- user identity;
- saved check history;
- stored risk results;
- downloadable report metadata;
- a safe boundary for later billing and manual review.

## Current boundary

Sellersflare remains software risk support. It is not legal advice and does not assert that a listing violates someone else's rights.

Do not store marketplace credentials, supplier contracts, private documents, cookies, access tokens, or private marketplace payloads in this MVP.

## Proposed Supabase scope

Use Supabase for:

- Auth;
- Postgres app state;
- Row Level Security;
- Storage for generated reports and review artifacts.

Keep Python/FastAPI responsible for:

- deterministic rules-first scoring;
- report generation;
- future integrations with external sources after ToS/security review.

## Data model

Initial tables are defined in `supabase/migrations/001_saas_lite.sql`:

- `profiles`;
- `check_requests`;
- `risk_results`;
- `report_exports`.

All user-owned tables must have RLS enabled before real users are accepted.

## First rollout sequence

1. Create a Supabase project or isolated self-host instance.
2. Apply `supabase/migrations/001_saas_lite.sql`.
3. Create a private reports bucket named by `SELLERSFLARE_REPORTS_BUCKET`.
4. Configure deployment secrets:
   - `SUPABASE_URL`;
   - `SUPABASE_ANON_KEY`;
   - `SUPABASE_SERVICE_ROLE_KEY`;
   - `SELLERSFLARE_SAAS_LITE_ENABLED=true`.
5. Smoke `/api/saas/readiness`.
6. Add authenticated history only after RLS select/insert checks pass.

## Non-goals for this patch

- No real Supabase credentials.
- No payment integration.
- No storage of supplier documents.
- No marketplace API connection.
- No legal conclusion language.
