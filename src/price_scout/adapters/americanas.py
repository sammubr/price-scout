import asyncio
from dataclasses import dataclass, replace
from decimal import Decimal
from urllib.parse import quote

from playwright.async_api import BrowserContext

from price_scout.matching import matches
from price_scout.models import Offer
from price_scout.selection import cheapest_candidates

SITE_ID = "americanas"
BASE_URL = "https://www.americanas.com.br"
SEARCH_URL = BASE_URL + "/api/catalog_system/pub/products/search?ft={query}&_from=0&_to=49"
SIMULATION_URL = BASE_URL + "/api/checkout/pub/orderForms/simulation"


@dataclass(frozen=True)
class Candidate:
    offer: Offer
    item_id: str
    seller_id: str


def parse_search(data: list[dict]) -> list[Candidate]:
    candidates = []
    for product in data:
        for item in product.get("items", [])[:1]:
            seller = next(
                (s for s in item.get("sellers", []) if s["commertialOffer"].get("AvailableQuantity", 0) > 0),
                None,
            )
            if seller is None or not seller["commertialOffer"].get("Price"):
                continue
            offer = Offer(
                site_id=SITE_ID,
                title=product["productName"],
                unit_price=Decimal(str(seller["commertialOffer"]["Price"])),
                shipping=None,
                url=product["link"],
            )
            candidates.append(Candidate(offer, item["itemId"], seller["sellerId"]))
    return candidates


def parse_shipping(data: dict) -> Decimal | None:
    prices = [
        sla["price"]
        for info in data.get("logisticsInfo", [])
        for sla in info.get("slas", [])
        if sla.get("deliveryChannel") == "delivery"
    ]
    if not prices:
        return None
    return Decimal(min(prices)) / 100


async def search(context: BrowserContext, product: str, cep: str) -> list[Offer]:
    response = await context.request.get(SEARCH_URL.format(query=quote(product)))
    candidates = [c for c in parse_search(await response.json()) if matches(product, c.offer.title)]
    chosen = cheapest_candidates(candidates, key=lambda candidate: candidate.offer.unit_price)
    shipping = await asyncio.gather(*(_quote(context, c, cep) for c in chosen))
    return [replace(c.offer, shipping=price) for c, price in zip(chosen, shipping)]


async def _quote(context: BrowserContext, candidate: Candidate, cep: str) -> Decimal | None:
    response = await context.request.post(
        SIMULATION_URL,
        data={
            "items": [{"id": candidate.item_id, "quantity": 1, "seller": candidate.seller_id}],
            "postalCode": cep,
            "country": "BRA",
        },
    )
    if not response.ok:
        return None
    return parse_shipping(await response.json())
