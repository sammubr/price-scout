from price_scout.models import Site, Status
from price_scout.search import run_search

from .fakes import fake_context_factory, offer, returning


async def test_unknown_site_is_unsupported_without_context():
    created = []
    results = await run_search(
        [Site("kabum", "Kabum"), Site("a", "Loja A")],
        "fone",
        "01310100",
        adapters={"a": returning(offer("a", "10"))},
        context_factory=fake_context_factory(created),
    )
    statuses = {result.site.id: result.status for result in results}
    assert statuses == {"kabum": Status.UNSUPPORTED, "a": Status.OK}
    assert len(created) == 1
    assert created[0].closed


async def test_best_offer_per_site_and_order():
    results = await run_search(
        [Site("a", "Loja A"), Site("b", "Loja B"), Site("c", "Loja C")],
        "fone",
        "01310100",
        adapters={
            "a": returning(offer("a", "100", "10"), offer("a", "105", "0")),
            "b": returning(offer("b", "50", None)),
            "c": returning(),
        },
        context_factory=fake_context_factory(),
    )
    assert [(r.site.id, r.status) for r in results] == [
        ("a", Status.OK),
        ("b", Status.SHIPPING_UNAVAILABLE),
        ("c", Status.NOT_FOUND),
    ]
    assert results[0].offer.unit_price == 105


def raising(exc):
    async def adapter(context, product, cep):
        raise exc

    return adapter


async def test_failures_are_mapped_and_isolated(monkeypatch):
    import asyncio

    from playwright.async_api import Error as PlaywrightError
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    from price_scout import search
    from price_scout.adapters.errors import SiteBlocked

    async def slow(context, product, cep):
        await asyncio.sleep(1)
        return []

    monkeypatch.setattr(search, "SITE_TIMEOUT_SECONDS", 0.05)
    created = []
    results = await run_search(
        [Site(i, i.title()) for i in ("ok", "slow", "nav", "blocked", "dns", "boom", "pw")],
        "fone",
        "01310100",
        adapters={
            "ok": returning(offer("ok", "10")),
            "slow": slow,
            "nav": raising(PlaywrightTimeoutError("Page.goto: Timeout 20000ms exceeded.")),
            "blocked": raising(SiteBlocked("captcha")),
            "dns": raising(PlaywrightError("net::ERR_NAME_NOT_RESOLVED at https://x")),
            "boom": raising(RuntimeError("falhou")),
            "pw": raising(PlaywrightError("Target crashed")),
        },
        context_factory=fake_context_factory(created),
    )
    statuses = {result.site.id: result.status for result in results}
    assert statuses == {
        "ok": Status.OK,
        "slow": Status.TIMEOUT,
        "nav": Status.TIMEOUT,
        "blocked": Status.BLOCKED,
        "dns": Status.UNREACHABLE,
        "boom": Status.ERROR,
        "pw": Status.ERROR,
    }
    assert results[0].site.id == "ok"
    assert all(context.closed for context in created)
    details = {result.site.id: result.detail for result in results}
    assert details["boom"] == "RuntimeError: falhou"
