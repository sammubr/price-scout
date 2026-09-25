from decimal import Decimal

import pytest

from price_scout.adapters.amazon import parse_delivery, parse_search, read_delivery


async def test_parse_search(load_fixture):
    offers = await parse_search(await load_fixture("amazon_search.html"))
    assert len(offers) >= 8
    first = offers[0]
    assert "soundcore" in first.title.lower()
    assert first.unit_price == Decimal("186.76")
    assert first.url.startswith("https://www.amazon.com.br/dp/")
    assert all(offer.shipping is None for offer in offers)


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("amazon_product_paid.html", Decimal("11.04")),
        ("amazon_product_free.html", Decimal("0")),
        ("amazon_product_conditional.html", None),
    ],
)
async def test_read_delivery(load_fixture, fixture, expected):
    assert await read_delivery(await load_fixture(fixture)) == expected


@pytest.mark.parametrize(
    ("price", "condition", "expected"),
    [
        ("GRÁTIS", "", Decimal("0")),
        ("R$\xa011,04", "", Decimal("11.04")),
        ("R$ 1.019,90", None, Decimal("1019.90")),
        ("GRÁTIS", "no seu primeiro pedido", None),
        ("GRÁTIS", "para membros Prime", None),
        ("mais rápida", "", None),
        (None, None, None),
    ],
)
def test_parse_delivery(price, condition, expected):
    assert parse_delivery(price, condition) == expected


async def test_slow_cep_setting_gives_up_without_failing(monkeypatch):
    import asyncio

    from price_scout.adapters import amazon

    async def hanging_set_cep(page, cep):
        await asyncio.sleep(5)
        return True

    monkeypatch.setattr(amazon, "set_cep", hanging_set_cep)
    monkeypatch.setattr(amazon, "CEP_BUDGET_SECONDS", 0.05)
    assert await amazon._set_cep_within_budget(None, "01310100") is False
