import json
from decimal import Decimal
from pathlib import Path

from price_scout.adapters.americanas import parse_search, parse_shipping

FIXTURES = Path(__file__).parents[1] / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_search_builds_offers_with_ids():
    candidates = parse_search(load("americanas_search.json"))
    assert len(candidates) == 12
    first = candidates[1]
    assert first.item_id == "7707262"
    assert first.seller_id == "1"
    assert first.offer.unit_price == Decimal("99.99")
    assert first.offer.shipping is None
    assert first.offer.url.startswith("https://www.americanas.com.br/")


def test_parse_search_skips_unavailable_sellers():
    data = load("americanas_search.json")[:1]
    data[0]["items"][0]["sellers"][0]["commertialOffer"]["AvailableQuantity"] = 0
    data[0]["items"][0]["sellers"] = data[0]["items"][0]["sellers"][:1]
    assert parse_search(data) == []


def test_parse_shipping_ignores_pickup():
    assert parse_shipping(load("americanas_simulation.json")) == Decimal("12.90")


def test_parse_shipping_undeliverable():
    assert parse_shipping(load("americanas_simulation_undeliverable.json")) is None
