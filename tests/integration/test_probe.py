import pytest
from playwright.async_api import async_playwright

from price_scout.adapters.errors import SiteBlocked, SiteUnsupported
from price_scout.adapters.probe import make_probe


@pytest.fixture
async def context():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context()

        async def serve(route):
            url = route.request.url
            status = 403 if "forbidden" in url else 200
            title = "Acesso negado - Não é possível acessar" if "challenge" in url else "Resultados"
            await route.fulfill(status=status, content_type="text/html; charset=utf-8", body=f"<title>{title}</title>")

        await context.route("**/*", serve)
        yield context
        await browser.close()


@pytest.mark.parametrize(
    ("url", "markers"),
    [
        ("https://loja.test/challenge/{q}", ["Não é possível acessar"]),
        ("https://loja.test/verify/{q}", ["/verify/"]),
        ("https://loja.test/forbidden/{q}", []),
    ],
)
async def test_blocked(context, url, markers):
    with pytest.raises(SiteBlocked):
        await make_probe(url, markers)(context, "fone bluetooth", "01310100")


async def test_clean_page_is_unsupported(context, monkeypatch):
    monkeypatch.setattr("price_scout.adapters.probe.REDIRECT_WAIT_MS", 1_000)
    probe = make_probe("https://loja.test/busca/{q}", ["/verify/"])
    with pytest.raises(SiteUnsupported):
        await probe(context, "fone bluetooth", "01310100")
