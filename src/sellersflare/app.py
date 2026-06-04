from __future__ import annotations

from pathlib import Path
import html
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .risk_engine import ListingInput, RiskResponse, analyze_listing


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
STATIC_DIR = ROOT / "static"


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def create_app() -> FastAPI:
    load_dotenv()

    app = FastAPI(
        title="Sellersflare",
        version="0.1.0",
        description="Software risk support для предварительной проверки карточек маркетплейса.",
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "sellersflare", "env": _env("APP_ENV", "local")}

    @app.head("/health")
    def health_head() -> None:
        return None

    @app.get("/ready")
    def ready() -> dict[str, object]:
        return {
            "ok": True,
            "service": "sellersflare",
            "checks": {
                "docs": DOCS_DIR.exists(),
                "static": STATIC_DIR.exists(),
                "research_markdown": (DOCS_DIR / "2026-05-23-research.md").exists(),
            },
        }

    @app.head("/ready")
    def ready_head() -> None:
        return None

    @app.post("/api/risk/check", response_model=RiskResponse)
    def check_risk(listing: ListingInput) -> RiskResponse:
        return analyze_listing(listing)

    @app.get("/research.pdf")
    def research_pdf() -> FileResponse:
        pdf_path = DOCS_DIR / "2026-05-23-research.pdf"
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="Research PDF is not packaged")
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="sellersflare-research-2026-05-23.pdf",
        )

    @app.get("/research.md", response_class=PlainTextResponse)
    def research_markdown() -> str:
        return (DOCS_DIR / "2026-05-23-research.md").read_text(encoding="utf-8")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _index_html()

    return app


def _index_html() -> str:
    sample_title = html.escape("Совместимый чехол в стиле известного бренда")
    sample_description = html.escape("Фото производителя, документы поставщика не приложены.")
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sellersflare</title>
  <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
  <main class="shell">
    <section class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">Marketplace risk support</p>
          <h1>Sellersflare</h1>
        </div>
        <a class="doc-link" href="/research.md">Research notes</a>
      </header>

      <section class="grid">
        <form id="risk-form" class="panel" data-endpoint="/api/risk/check">
          <label>Маркетплейс
            <select name="marketplace">
              <option value="ozon">Ozon</option>
              <option value="wb">Wildberries</option>
              <option value="manual">Manual</option>
            </select>
          </label>
          <label>Название товара
            <input name="title" value="{sample_title}" required maxlength="500">
          </label>
          <label>Описание
            <textarea name="description" rows="5" maxlength="5000">{sample_description}</textarea>
          </label>
          <div class="two">
            <label>Бренд
              <input name="brand" placeholder="если указан">
            </label>
            <label>Категория
              <input name="category" value="electronics">
            </label>
          </div>
          <label>URL изображений
            <input name="image_urls" placeholder="через запятую">
          </label>
          <label>Контекст продажи
            <select name="seller_context">
              <option value="unknown">Неизвестно</option>
              <option value="original">Оригинальный товар</option>
              <option value="own_brand">Собственный бренд</option>
              <option value="resale">Ресейл</option>
              <option value="parallel_import">Параллельный импорт</option>
            </select>
          </label>
          <button type="submit">Проверить риск</button>
        </form>

        <section class="panel result">
          <div class="score">
            <span id="score">--</span>
            <small id="level">ожидает проверки</small>
          </div>
          <p id="summary">Заполните карточку и запустите rules-first оценку. Это не юридическое заключение.</p>
          <div id="breakdown" class="breakdown"></div>
          <h2>Рекомендации</h2>
          <ul id="recommendations"></ul>
          <h2>Неопределенность</h2>
          <ul id="uncertainty"></ul>
        </section>
      </section>
    </section>
  </main>
  <script src="/static/app.js"></script>
</body>
</html>"""
