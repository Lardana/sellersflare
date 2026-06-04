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
