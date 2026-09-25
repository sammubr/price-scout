from contextlib import asynccontextmanager
from decimal import Decimal

from price_scout.models import Offer


class FakeContext:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


def fake_context_factory(created: list | None = None):
    @asynccontextmanager
    async def factory():
        async def new_context():
            context = FakeContext()
            if created is not None:
                created.append(context)
            return context

        yield new_context

    return factory


def returning(*offers: Offer):
    async def adapter(context, product, cep):
        return list(offers)

    return adapter


def offer(site_id: str, price: str, shipping: str | None = "0") -> Offer:
    return Offer(
        site_id=site_id,
        title=f"Fone {site_id}",
        unit_price=Decimal(price),
        shipping=None if shipping is None else Decimal(shipping),
        url=f"https://{site_id}.example/p",
    )
