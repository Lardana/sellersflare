from fastapi.testclient import TestClient

from sellersflare.app import create_app


def test_health_ready() -> None:
    client = TestClient(create_app())

    assert client.get("/health").json()["status"] == "ok"
    ready = client.get("/ready").json()
    assert ready["ok"] is True
    assert ready["checks"]["docs"] is True


def test_risk_check_flags_high_risk_copy_language() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/risk/check",
        json={
            "marketplace": "ozon",
            "title": "Реплика аксессуара в стиле известного бренда",
            "description": "Фото производителя, документов нет.",
            "brand": "",
            "category": "fashion",
            "image_urls": ["https://example.com/a.jpg"],
            "seller_context": "resale",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_score"] >= 35
    assert payload["breakdown"]["trademark"]["score"] > 0
    assert payload["breakdown"]["documents"]["score"] > 0


def test_index_page_contains_form() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Sellersflare" in response.text
    assert "/api/risk/check" in response.text


def test_research_markdown_is_available() -> None:
    client = TestClient(create_app())

    response = client.get("/research.md")

    assert response.status_code == 200
    assert "Sellersflare" in response.text


def test_saas_blueprint_exposes_safe_supabase_plan() -> None:
    client = TestClient(create_app())

    response = client.get("/api/saas/blueprint")

    assert response.status_code == 200
    payload = response.json()
    assert payload["product"] == "Sellersflare SaaS Lite"
    assert {table["name"] for table in payload["tables"]} == {
        "profiles",
        "check_requests",
        "risk_results",
        "report_exports",
    }
    assert any("SERVICE_ROLE_KEY" in note for note in payload["security_notes"])


def test_saas_readiness_does_not_leak_secret_values(monkeypatch) -> None:
    monkeypatch.setenv("SELLERSFLARE_SAAS_LITE_ENABLED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-secret-value")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-secret-value")
    client = TestClient(create_app())

    response = client.get("/api/saas/readiness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled"] is True
    assert payload["supabase_url_configured"] is True
    assert payload["anon_key_configured"] is True
    assert payload["service_role_configured"] is True
    assert "secret-value" not in response.text
