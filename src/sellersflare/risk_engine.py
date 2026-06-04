from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ListingInput(BaseModel):
    marketplace: str = Field(default="manual", max_length=32)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=5000)
    brand: str = Field(default="", max_length=160)
    category: str = Field(default="", max_length=160)
    image_urls: list[str] = Field(default_factory=list, max_length=20)
    seller_context: str = Field(
        default="unknown",
        description="original, own_brand, resale, parallel_import, unknown",
        max_length=80,
    )


class RiskBucket(BaseModel):
    score: int
    level: RiskLevel
    triggers: list[str]
    explanation: str


class RiskResponse(BaseModel):
    risk_score: int
    risk_level: RiskLevel
    breakdown: dict[str, RiskBucket]
    summary: str
    recommendations: list[str]
    uncertainty: list[str]
    disclaimer: str


@dataclass(frozen=True)
class RuleHit:
    bucket: str
    points: int
    trigger: str


RISKY_CATEGORIES = {
    "fashion",
    "одежда",
    "обувь",
    "beauty",
    "косметика",
    "electronics",
    "электроника",
    "accessories",
    "аксессуары",
    "toys",
    "игрушки",
    "auto",
    "авто",
    "tools",
    "инструменты",
}

TEXT_PATTERNS: tuple[tuple[str, str, int, str], ...] = (
    ("trademark", r"\b(replica|copy|fake|like|style)\b", 28, "В тексте есть слова, похожие на указание копии или стилизации."),
    ("trademark", r"(реплик|копи[яи]|подделк|в стиле|как у|аналог)", 28, "В тексте есть формулировки про копию, аналог или стиль чужого бренда."),
    ("trademark", r"(совместим[а-я ]+с|для\s+[A-ZА-Я][A-Za-zА-Яа-я0-9-]{2,})", 12, "Есть формулировка совместимости с чужим обозначением."),
    ("content", r"(описание производителя|текст производителя|скопирован|как на сайте)", 18, "Описание может быть заимствовано из внешнего источника."),
    ("image", r"(фото производителя|фото бренда|фото с сайта|чужое фото|из интернета)", 24, "Есть риск использования чужих изображений."),
    ("documents", r"(без документ|нет документ|сертификат отсутств|неизвестн[а-я ]+поставщик)", 22, "Не хватает подтверждающих документов или понятного происхождения товара."),
)


def _level(score: int) -> RiskLevel:
    if score >= 70:
        return RiskLevel.HIGH
    if score >= 35:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _bucket(score: int, triggers: list[str], fallback: str) -> RiskBucket:
    score = min(100, max(0, score))
    return RiskBucket(
        score=score,
        level=_level(score),
        triggers=triggers,
        explanation=" ".join(triggers) if triggers else fallback,
    )


def analyze_listing(listing: ListingInput) -> RiskResponse:
    text = " ".join([listing.title, listing.description, listing.brand, listing.category]).strip()
    text_lower = text.lower()
    hits: list[RuleHit] = []

    for bucket, pattern, points, trigger in TEXT_PATTERNS:
        if re.search(pattern, text_lower, flags=re.IGNORECASE):
            hits.append(RuleHit(bucket, points, trigger))

    if not listing.brand.strip():
        hits.append(RuleHit("trademark", 10, "Бренд не указан: сложнее понять, чей товар и какие права затронуты."))
        hits.append(RuleHit("documents", 8, "Без бренда выше неопределенность по документам и происхождению товара."))

    category = listing.category.strip().lower()
    if category in RISKY_CATEGORIES:
        hits.append(RuleHit("category", 18, "Категория относится к зонам, где чаще встречаются IP/документные риски."))

    context = listing.seller_context.strip().lower()
    if context in {"resale", "parallel_import", "unknown", ""}:
        hits.append(RuleHit("documents", 14, "Контекст продажи требует проверки права реализации и документов происхождения."))

    if listing.image_urls:
        hits.append(RuleHit("image", 8, "Есть изображения: стоит подтвердить права на фото и источник каждого файла."))
    else:
        hits.append(RuleHit("image", 6, "Изображения не переданы: image-risk невозможно проверить полноценно."))

    buckets: dict[str, list[RuleHit]] = {
        "trademark": [],
        "image": [],
        "content": [],
        "category": [],
        "documents": [],
    }
    for hit in hits:
        buckets[hit.bucket].append(hit)

    breakdown = {
        name: _bucket(
            sum(hit.points for hit in bucket_hits),
            [hit.trigger for hit in bucket_hits],
            fallback,
        )
        for name, bucket_hits, fallback in (
            ("trademark", buckets["trademark"], "Явных trademark-триггеров не найдено."),
            ("image", buckets["image"], "Явных image-триггеров не найдено."),
            ("content", buckets["content"], "Явных признаков копирования описания не найдено."),
            ("category", buckets["category"], "Категория не выглядит повышенно рискованной по базовым правилам."),
            ("documents", buckets["documents"], "Явных документных триггеров не найдено."),
        )
    }

    weighted = (
        breakdown["trademark"].score * 0.3
        + breakdown["image"].score * 0.22
        + breakdown["content"].score * 0.16
        + breakdown["category"].score * 0.12
        + breakdown["documents"].score * 0.2
    )
    total = min(100, round(weighted * 1.45))
    level = _level(total)

    uncertainty = [
        "Нет проверки официальных реестров товарных знаков в этом MVP.",
        "Нет настоящего поиска похожих изображений по пикселям или внешним площадкам.",
        "Нет проверки документов поставщика и договоров.",
    ]
    if not listing.description.strip():
        uncertainty.append("Описание пустое: content-risk оценен неполно.")
    if not listing.image_urls:
        uncertainty.append("Нет ссылок на изображения: image-risk оценен как неопределенный.")

    recommendations = [
        "Проверить товарный знак и право использования бренда/обозначений.",
        "Использовать собственные фото или документы, подтверждающие право на изображения.",
        "Убрать формулировки про копии, реплики и стилизацию под чужой бренд.",
        "Подготовить документы происхождения товара, особенно для ресейла и параллельного импорта.",
    ]
    if level == RiskLevel.LOW:
        recommendations.insert(0, "Сохранить текущую доказательную базу: источник товара, фото и описание.")

    return RiskResponse(
        risk_score=total,
        risk_level=level,
        breakdown=breakdown,
        summary=f"Базовая rules-first проверка оценила карточку как {level.value} risk с баллом {total}/100.",
        recommendations=recommendations,
        uncertainty=uncertainty,
        disclaimer="Это software risk support, а не юридическая консультация и не вывод о факте нарушения.",
    )
