from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel


class SaaSTable(BaseModel):
    name: str
    purpose: str
    owner_scope: str


class SaaSBlueprint(BaseModel):
    product: str
    mode: Literal["saas_lite"]
    auth: list[str]
    storage: list[str]
    tables: list[SaaSTable]
    worker_boundary: str
    security_notes: list[str]
    next_steps: list[str]


class SaaSReadiness(BaseModel):
    enabled: bool
    supabase_url_configured: bool
    anon_key_configured: bool
    service_role_configured: bool
    storage_bucket: str
    safe_to_accept_real_customer_data: bool
    notes: list[str]


def _configured(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def get_saas_readiness() -> SaaSReadiness:
    url_configured = _configured("SUPABASE_URL")
    anon_configured = _configured("SUPABASE_ANON_KEY")
    service_configured = _configured("SUPABASE_SERVICE_ROLE_KEY")
    bucket = os.environ.get("SELLERSFLARE_REPORTS_BUCKET", "sellersflare-reports").strip()
    enabled = os.environ.get("SELLERSFLARE_SAAS_LITE_ENABLED", "false").strip().lower() == "true"

    notes = [
        "Readiness endpoint intentionally reports only whether env names are configured, never secret values.",
        "SaaS Lite must keep marketplace credentials, supplier documents, cookies, and private payloads out of the repository.",
    ]
    if not enabled:
        notes.append("SaaS Lite is disabled until SELLERSFLARE_SAAS_LITE_ENABLED=true is set.")
    if enabled and not (url_configured and anon_configured):
        notes.append("Frontend Supabase access is not ready until SUPABASE_URL and SUPABASE_ANON_KEY are configured.")
    if enabled and not service_configured:
        notes.append("Server-side report writes are not ready until SUPABASE_SERVICE_ROLE_KEY is configured in a secret store.")

    return SaaSReadiness(
        enabled=enabled,
        supabase_url_configured=url_configured,
        anon_key_configured=anon_configured,
        service_role_configured=service_configured,
        storage_bucket=bucket or "sellersflare-reports",
        safe_to_accept_real_customer_data=False,
        notes=notes,
    )


def get_saas_blueprint() -> SaaSBlueprint:
    return SaaSBlueprint(
        product="Sellersflare SaaS Lite",
        mode="saas_lite",
        auth=[
            "Supabase Auth owns user identity for the SaaS shell.",
            "Application code keeps the existing rules-first risk engine as the scoring authority.",
        ],
        storage=[
            "Supabase Storage bucket for generated reports and review artifacts.",
            "Do not store supplier contracts, marketplace credentials, cookies, or raw private marketplace payloads in the MVP.",
        ],
        tables=[
            SaaSTable(
                name="profiles",
                purpose="Public user profile linked to auth.users, plan marker, and safe display fields.",
                owner_scope="user can select/update only own profile through RLS",
            ),
            SaaSTable(
                name="check_requests",
                purpose="Normalized listing inputs submitted by the user for rules-first scoring.",
                owner_scope="user can access only own requests through RLS",
            ),
            SaaSTable(
                name="risk_results",
                purpose="Stored score, level, breakdown, recommendations, uncertainty, and disclaimer.",
                owner_scope="user can access only results for own requests through RLS",
            ),
            SaaSTable(
                name="report_exports",
                purpose="Metadata for downloadable reports generated from reviewed risk results.",
                owner_scope="user can access only exports for own requests through RLS",
            ),
        ],
        worker_boundary=(
            "Supabase stores SaaS state; the Python service remains responsible for deterministic scoring "
            "and future report generation. Privileged writes must happen only server-side."
        ),
        security_notes=[
            "Never expose SUPABASE_SERVICE_ROLE_KEY to browser code.",
            "Enable RLS before accepting real users.",
            "Treat listing text and image URLs as user content.",
            "Keep all output framed as software risk support, not legal advice.",
        ],
        next_steps=[
            "Create a Supabase project or isolated self-host instance.",
            "Apply supabase/migrations/001_saas_lite.sql.",
            "Configure env variables in deployment secret storage.",
            "Wire authenticated history after RLS smoke tests pass.",
            "Add billing only after a manual validation batch proves demand.",
        ],
    )
