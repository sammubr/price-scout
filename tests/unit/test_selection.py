from decimal import Decimal

from price_scout.models import Offer, Site, SiteResult, Status
from price_scout.selection import best_offer, best_option, cheapest_candidates, order_results


def offer(price, shipping="0", site_id="s"):
    return Offer(
        site_id=site_id,
        title=f"item {price}",
        unit_price=Decimal(price),
        shipping=None if shipping is None else Decimal(shipping),
        url="https://example.com",
    )


def result(name, status, item=None):
    return SiteResult(Site(name.lower(), name), status, item)


def test_cheapest_candidates_respects_limit_and_order():
    offers = [offer(str(price)) for price in (70, 10, 60, 20, 50, 30, 40)]
    assert [o.unit_price for o in cheapest_candidates(offers)] == [10, 20, 30, 40, 50]


def test_best_offer_uses_total_not_unit_price():
    status, best = best_offer([offer("100", "50"), offer("120", "0")])
    assert status is Status.OK
    assert best.unit_price == 120


def test_best_offer_without_known_shipping():
    status, best = best_offer([offer("100", None), offer("90", None)])
    assert status is Status.SHIPPING_UNAVAILABLE
    assert best.unit_price == 90


def test_best_offer_prefers_quoted_offer():
    status, best = best_offer([offer("50", None), offer("100", "10")])
    assert status is Status.OK
    assert best.unit_price == 100


def test_best_offer_empty():
    assert best_offer([]) == (Status.NOT_FOUND, None)


def test_order_breaks_ties_by_shipping_then_name():
    results = [
        result("Zeta", Status.OK, offer("90", "10")),
        result("Beta", Status.OK, offer("100", "0")),
        result("Alfa", Status.OK, offer("100", "0")),
    ]
    assert [r.site.name for r in order_results(results)] == ["Alfa", "Beta", "Zeta"]


def test_order_groups_ok_then_unquoted_then_failures():
    results = [
        result("Bloq", Status.BLOCKED),
        result("SemFrete", Status.SHIPPING_UNAVAILABLE, offer("10", None)),
        result("Caro", Status.OK, offer("500", "0")),
        result("Ausente", Status.NOT_FOUND),
    ]
    assert [r.site.name for r in order_results(results)] == ["Caro", "SemFrete", "Ausente", "Bloq"]


def test_best_option():
    cheap = result("A", Status.OK, offer("10", "5"))
    assert best_option([result("B", Status.OK, offer("20", "0")), cheap]) == cheap
    assert best_option([result("C", Status.SHIPPING_UNAVAILABLE, offer("1", None))]) is None


def test_cheapest_candidates_with_key():
    items = [("c", Decimal(3)), ("a", Decimal(1)), ("b", Decimal(2))]
    assert cheapest_candidates(items, limit=2, key=lambda item: item[1]) == [("a", Decimal(1)), ("b", Decimal(2))]
