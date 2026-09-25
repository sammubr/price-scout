from collections.abc import Awaitable, Callable

from playwright.async_api import BrowserContext

from price_scout.adapters.amazon import search as amazon_search
from price_scout.adapters.americanas import search as americanas_search
from price_scout.adapters.probe import make_probe
from price_scout.models import Offer

Adapter = Callable[[BrowserContext, str, str], Awaitable[list[Offer]]]

ADAPTERS: dict[str, Adapter] = {
    "amazon": amazon_search,
    "americanas": americanas_search,
    "magalu": make_probe("https://www.magazineluiza.com.br/busca/{q}/", ["Não é possível acessar"]),
    "mercadolivre": make_probe("https://lista.mercadolivre.com.br/{q}", ["account-verification"]),
    "shopee": make_probe("https://shopee.com.br/search?keyword={q}", ["/verify/"]),
    "submarino": make_probe("https://www.submarino.com.br/busca/{q}", []),
}
