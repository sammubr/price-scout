from urllib.parse import quote

from playwright.async_api import BrowserContext, Page

from price_scout.adapters.errors import SiteBlocked, SiteUnsupported
from price_scout.models import Offer

REDIRECT_WAIT_MS = 8_000
POLL_MS = 500


def make_probe(search_url: str, blocked_markers: list[str]):
    async def search(context: BrowserContext, product: str, cep: str) -> list[Offer]:
        page = await context.new_page()
        response = await page.goto(search_url.format(q=quote(product)), wait_until="domcontentloaded")
        if response is not None and response.status == 403:
            raise SiteBlocked(f"acesso negado (403) em {page.url}")
        for _ in range(REDIRECT_WAIT_MS // POLL_MS):
            if await _has_marker(page, blocked_markers):
                raise SiteBlocked(f"verificação anti-robô em {page.url}")
            await page.wait_for_timeout(POLL_MS)
        raise SiteUnsupported("página carregou, mas este site ainda não tem leitura de ofertas")

    return search


async def _has_marker(page: Page, markers: list[str]) -> bool:
    location = page.url + " " + await page.title()
    return any(marker in location for marker in markers)
