import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from playwright.async_api import BrowserContext, async_playwright
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from price_scout.adapters import ADAPTERS, Adapter
from price_scout.adapters.errors import SiteBlocked, SiteUnsupported
from price_scout.models import Offer, Site, SiteResult, Status
from price_scout.selection import best_offer, order_results

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
)
NAVIGATION_TIMEOUT_MS = 20_000
SITE_TIMEOUT_SECONDS = 45
NETWORK_ERRORS = ("ERR_NAME_NOT_RESOLVED", "ERR_CONNECTION", "ERR_INTERNET_DISCONNECTED")

NewContext = Callable[[], Awaitable[BrowserContext]]


@asynccontextmanager
async def chromium_contexts() -> AsyncIterator[NewContext]:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()

        async def new_context() -> BrowserContext:
            context = await browser.new_context(locale="pt-BR", user_agent=USER_AGENT)
            context.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
            return context

        try:
            yield new_context
        finally:
            await browser.close()


async def run_search(
    sites: list[Site],
    product: str,
    cep: str,
    adapters: dict[str, Adapter] = ADAPTERS,
    context_factory=chromium_contexts,
) -> list[SiteResult]:
    async with context_factory() as new_context:
        results = await asyncio.gather(
            *(_search_site(site, product, cep, adapters.get(site.id), new_context) for site in sites)
        )
    return order_results(list(results))


async def _search_site(
    site: Site, product: str, cep: str, adapter: Adapter | None, new_context: NewContext
) -> SiteResult:
    if adapter is None:
        return SiteResult(site, Status.UNSUPPORTED)
    try:
        async with asyncio.timeout(SITE_TIMEOUT_SECONDS):
            offers = await _run_adapter(adapter, product, cep, new_context)
    except TimeoutError:
        return SiteResult(site, Status.TIMEOUT, detail=f"mais de {SITE_TIMEOUT_SECONDS} s")
    except PlaywrightTimeoutError as exc:
        return SiteResult(site, Status.TIMEOUT, detail=str(exc).splitlines()[0])
    except SiteBlocked as exc:
        return SiteResult(site, Status.BLOCKED, detail=str(exc))
    except SiteUnsupported as exc:
        return SiteResult(site, Status.UNSUPPORTED, detail=str(exc))
    except PlaywrightError as exc:
        status = Status.UNREACHABLE if any(code in str(exc) for code in NETWORK_ERRORS) else Status.ERROR
        return SiteResult(site, status, detail=str(exc).splitlines()[0])
    except Exception as exc:
        return SiteResult(site, Status.ERROR, detail=f"{type(exc).__name__}: {exc}")
    status, offer = best_offer(offers)
    return SiteResult(site, status, offer)


async def _run_adapter(adapter: Adapter, product: str, cep: str, new_context: NewContext) -> list[Offer]:
    context = await new_context()
    try:
        return await adapter(context, product, cep)
    finally:
        await context.close()
