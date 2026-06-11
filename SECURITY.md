# Security Policy

## Supported versions

Sellersflare is an early MVP. Security fixes are applied to the current `main` branch.

## Reporting a vulnerability

Please open a private security advisory on GitHub if the repository is hosted there.

Do not include real marketplace credentials, seller documents, API keys, cookies, access tokens, private webhook payloads, or personal data in public issues.

## Data handling

Sellersflare is designed as software risk support. The MVP should not store supplier documents, marketplace credentials, or private customer data in the repository. Runtime secrets belong in local environment variables or a deployment secret store.

## Supabase SaaS Lite

`SUPABASE_SERVICE_ROLE_KEY` is server-side only and must never be exposed to browser code, public logs, screenshots, docs, or client bundles.

Before accepting real users, verify that Row Level Security is enabled for every user-owned table and that each user can read only their own `profiles`, `check_requests`, `risk_results`, and `report_exports` rows.
