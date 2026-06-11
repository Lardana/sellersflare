# Sellersflare

Sellersflare — OSS MVP-сервис для предварительной проверки карточки товара маркетплейса на IP/контентные риски до публикации.

Sellersflare не является юридической консультацией и не утверждает факт нарушения. Сервис помогает продавцу увидеть риск-сигналы, неопределенность и безопасные следующие шаги: что переписать, какие документы проверить и где требуется ручная правовая оценка.

## Возможности MVP

- Web-форма проверки карточки.
- `POST /api/risk/check` с rules-first scoring.
- Supabase-ready SaaS Lite blueprint:
  - `GET /api/saas/blueprint`;
  - `GET /api/saas/readiness`;
  - SQL skeleton in `supabase/migrations/001_saas_lite.sql`.
- Breakdown по направлениям:
  - trademark;
  - image;
  - content;
  - category;
  - documents.
- `GET /health` и `GET /ready`.
- Research-документ в Markdown.

## Для кого

- продавцы маркетплейсов, которые хотят проверить карточку до публикации;
- агентства, которые заводят карточки для клиентов;
- разработчики, которым нужен простой пример explainable risk scoring без утверждения юридических фактов.

## Чего MVP не делает

- не проверяет официальные реестры товарных знаков;
- не делает поиск похожих изображений по пикселям;
- не подключается к аккаунтам Ozon/WB;
- не хранит документы поставщиков;
- не заменяет юриста или ручной review.

## Локальный запуск

```bash
cd sellersflare
make setup
make test
make run
```

Проверка:

```bash
curl http://127.0.0.1:8088/health
curl http://127.0.0.1:8088/ready
```

## Docker

```bash
cp .env.example .env
docker compose up -d --build
curl http://127.0.0.1:18120/health
```

## API

```bash
curl -sS http://127.0.0.1:8088/api/risk/check \
  -H 'Content-Type: application/json' \
  -d '{
    "marketplace": "ozon",
    "title": "Совместимый чехол в стиле известного бренда",
    "description": "Без документов поставщика, фото от производителя.",
    "brand": "",
    "category": "electronics",
    "image_urls": ["https://example.com/image.jpg"],
    "seller_context": "resale"
  }'
```

## Документы

- `docs/2026-05-23-research.md`
- `docs/2026-06-04-validation-update.md`
- `docs/2026-06-04-validation-cases.json`
- `docs/2026-06-11-supabase-saas-lite-plan.md`

## SaaS Lite / Supabase

Supabase is prepared as a SaaS shell, not as a replacement for the risk engine.

Intended split:

- Supabase Auth owns user identity.
- Supabase Postgres stores check history, results, and report metadata with RLS.
- Supabase Storage stores generated report artifacts.
- Sellersflare Python/FastAPI keeps deterministic scoring and future report generation.

Safe rollout order:

```bash
curl http://127.0.0.1:8088/api/saas/blueprint
curl http://127.0.0.1:8088/api/saas/readiness
```

Then apply `supabase/migrations/001_saas_lite.sql` to a real Supabase project only after secrets are configured outside the repository.

## Разработка

```bash
make setup
make test
make compile
```

CI запускает тесты на Python 3.12.

## Безопасность и данные

- реальные токены, API-ключи, cookie, пользовательские документы и приватные payload не должны попадать в репозиторий;
- `.env` используется только локально и игнорируется git;
- входные данные карточки считаются пользовательским контентом;
- результат API — software risk support, а не юридическое заключение.

## Лицензия

MIT. См. `LICENSE`.
