from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from sellersflare.risk_engine import ListingInput, RiskLevel, analyze_listing


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "docs" / "2026-06-04-validation-cases.json"
EXPECTED_SIGNALS = {
    "no_obvious_ip_or_content_signal",
    "compatibility_wording_review",
    "document_origin_review",
    "content_rewrite_review",
    "high_trademark_document_image_risk",
    "high_trademark_content_document_risk",
    "insufficient_data_review",
}


def _load_cases() -> list[dict[str, object]]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def test_validation_cases_cover_four_product_scenarios() -> None:
    cases = _load_cases()

    assert len(cases) == 20
    assert Counter(case["segment"] for case in cases) == {
        "safe": 5,
        "ambiguous": 5,
        "risky": 5,
        "insufficient_data": 5,
    }
    assert len({case["id"] for case in cases}) == 20
    assert {case["expected_signal"] for case in cases} <= EXPECTED_SIGNALS

    for case in cases:
        assert str(case["rationale"]).strip()
        assert str(case["review_note"]).strip()


def test_validation_cases_expected_signals_match_segments() -> None:
    expected_by_segment = {
        "safe": {"no_obvious_ip_or_content_signal"},
        "ambiguous": {"compatibility_wording_review", "document_origin_review", "content_rewrite_review"},
        "risky": {"high_trademark_document_image_risk", "high_trademark_content_document_risk"},
        "insufficient_data": {"insufficient_data_review"},
    }

    for case in _load_cases():
        assert case["expected_signal"] in expected_by_segment[case["segment"]]


def test_validation_cases_are_supported_by_explainable_engine() -> None:
    scores_by_segment: dict[str, list[int]] = defaultdict(list)

    for case in _load_cases():
        listing = ListingInput.model_validate(case["input"])
        result = analyze_listing(listing)
        segment = str(case["segment"])
        scores_by_segment[segment].append(result.risk_score)

        assert result.disclaimer
        assert result.uncertainty
        assert set(result.breakdown) == {"trademark", "image", "content", "category", "documents"}
        for bucket in result.breakdown.values():
            assert bucket.explanation

        if segment == "safe":
            assert result.risk_level == RiskLevel.LOW
        if segment == "risky":
            assert result.risk_score >= 35
            assert result.breakdown["trademark"].score > 0
            assert result.breakdown["documents"].score > 0
        if str(case["expected_signal"]).startswith("high_trademark"):
            assert result.breakdown["trademark"].score >= 28
        if case["expected_signal"] == "content_rewrite_review":
            assert result.breakdown["content"].score > 0
        if case["expected_signal"] == "compatibility_wording_review":
            assert result.breakdown["trademark"].score > 0
        if segment == "insufficient_data":
            assert any("изображен" in item.lower() for item in result.uncertainty)

    safe_average = sum(scores_by_segment["safe"]) / len(scores_by_segment["safe"])
    ambiguous_average = sum(scores_by_segment["ambiguous"]) / len(scores_by_segment["ambiguous"])
    risky_average = sum(scores_by_segment["risky"]) / len(scores_by_segment["risky"])

    assert safe_average < ambiguous_average < risky_average
