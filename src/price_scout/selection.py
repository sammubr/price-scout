from collections.abc import Callable
from decimal import Decimal

from price_scout.models import Offer, SiteResult, Status

QUOTE_LIMIT = 5


def cheapest_candidates[T](
    items: list[T],
    limit: int = QUOTE_LIMIT,
    key: Callable[[T], Decimal] = lambda offer: offer.unit_price,
) -> list[T]:
    return sorted(items, key=key)[:limit]


def best_offer(offers: list[Offer]) -> tuple[Status, Offer | None]:
    if not offers:
        return Status.NOT_FOUND, None
    quoted = [offer for offer in offers if offer.total is not None]
    if quoted:
        return Status.OK, min(quoted, key=lambda offer: (offer.total, offer.shipping))
    return Status.SHIPPING_UNAVAILABLE, min(offers, key=lambda offer: offer.unit_price)


def order_results(results: list[SiteResult]) -> list[SiteResult]:
    def key(result: SiteResult):
        offer = result.offer
        if result.status is Status.OK:
            return (0, offer.total, offer.shipping, result.site.name)
        if result.status is Status.SHIPPING_UNAVAILABLE:
            return (1, offer.unit_price, 0, result.site.name)
        return (2, 0, 0, result.site.name)

    return sorted(results, key=key)


def best_option(results: list[SiteResult]) -> SiteResult | None:
    ordered = order_results(results)
    if ordered and ordered[0].status is Status.OK:
        return ordered[0]
    return None
