import asyncio
from dataclasses import replace
from decimal import Decimal
from urllib.parse import quote_plus

from playwright.async_api import BrowserContext, Page
from playwright.async_api import TimeoutError as PlaywrightTimeout

from price_scout.adapters.errors import SiteBlocked
from price_scout.matching import matches
from price_scout.models import Offer
from price_scout.money import parse_brl
from price_scout.selection import cheapest_candidates

SITE_ID = "amazon"
BASE_URL = "https://www.amazon.com.br"
CEP_ATTEMPTS = 2
CEP_BUDGET_SECONDS = 20


async def search(context: BrowserContext, product: str, cep: str) -> list[Offer]:
    page = await context.new_page()
    cep_confirmed = await _set_cep_within_budget(page, cep)
    await page.goto(f"{BASE_URL}/s?k={quote_plus(product)}", wait_until="domcontentloaded")
    await raise_if_blocked(page)

    offers = [offer for offer in await parse_search(page) if matches(product, offer.title)]
    chosen = cheapest_candidates(offers)
    if not cep_confirmed:
        return chosen
    shipping = await asyncio.gather(*(_quote(context, offer) for offer in chosen))
    return [replace(offer, shipping=price) for offer, price in zip(chosen, shipping)]


async def _set_cep_within_budget(page: Page, cep: str) -> bool:
    try:
        async with asyncio.timeout(CEP_BUDGET_SECONDS):
            return await set_cep(page, cep)
    except TimeoutError:
        return False


async def set_cep(page: Page, cep: str) -> bool:
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await raise_if_blocked(page)
    for _ in range(CEP_ATTEMPTS):
        try:
            await page.click("#nav-global-location-popover-link")
            await page.wait_for_selector("#GLUXZipUpdateInput_0", state="visible", timeout=8000)
            await page.wait_for_timeout(1000)
            await page.fill("#GLUXZipUpdateInput_0", cep[:5])
            await page.fill("#GLUXZipUpdateInput_1", cep[5:])
            async with page.expect_response(lambda r: "glow/address-change" in r.url, timeout=6000):
                await page.click("#GLUXZipUpdate input")
            await page.goto(BASE_URL, wait_until="domcontentloaded")
            label = await page.inner_text("#glow-ingress-block")
            return cep in label.replace("-", "")
        except PlaywrightTimeout:
            await page.reload(wait_until="domcontentloaded")
    return False


async def raise_if_blocked(page: Page) -> None:
    if "Algo deu errado" in await page.title():
        raise SiteBlocked("página de erro da Amazon")
    if await page.locator('form[action*="validateCaptcha"]').count():
        raise SiteBlocked("captcha da Amazon")


async def parse_search(page: Page) -> list[Offer]:
    offers = []
    cards = page.locator('div[data-component-type="s-search-result"]')
    for index in range(await cards.count()):
        card = cards.nth(index)
        asin = await card.get_attribute("data-asin")
        title = card.locator("h2")
        price = card.locator(".a-price .a-offscreen")
        if not asin or not await title.count() or not await price.count():
            continue
        offers.append(
            Offer(
                site_id=SITE_ID,
                title=(await title.first.inner_text()).strip(),
                unit_price=parse_brl(await price.first.text_content()),
                shipping=None,
                url=f"{BASE_URL}/dp/{asin}",
            )
        )
    return offers


async def read_delivery(page: Page) -> Decimal | None:
    element = page.locator("#deliveryBlockContainer [data-csa-c-delivery-price]").first
    if not await element.count():
        return None
    return parse_delivery(
        await element.get_attribute("data-csa-c-delivery-price"),
        await element.get_attribute("data-csa-c-delivery-condition"),
    )


def parse_delivery(price: str | None, condition: str | None) -> Decimal | None:
    if not price or (condition or "").strip():
        return None
    if price.strip().upper() == "GRÁTIS":
        return Decimal(0)
    try:
        return parse_brl(price)
    except ValueError:
        return None


async def _quote(context: BrowserContext, offer: Offer) -> Decimal | None:
    page = await context.new_page()
    try:
        await page.goto(offer.url, wait_until="domcontentloaded")
        return await read_delivery(page)
    finally:
        await page.close()
