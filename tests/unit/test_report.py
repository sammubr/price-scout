from decimal import Decimal

from rich.console import Console

from price_scout.models import Offer, Site, SiteResult, Status
from price_scout.report import render, render_header


def offer(site_id, price, shipping):
    return Offer(
        site_id=site_id,
        title=f"Fone {site_id}",
        unit_price=Decimal(price),
        shipping=None if shipping is None else Decimal(shipping),
        url=f"https://{site_id}.example/p",
    )


def output(results):
    console = Console(record=True, width=160)
    render(results, console)
    return console.export_text()


def test_table_and_best_option():
    text = output([
        SiteResult(Site("a", "Americanas"), Status.OK, offer("a", "99.99", "12.90")),
        SiteResult(Site("b", "Amazon"), Status.OK, offer("b", "1234.00", "0")),
        SiteResult(Site("c", "Loja C"), Status.SHIPPING_UNAVAILABLE, offer("c", "50", None)),
        SiteResult(Site("d", "Shopee"), Status.BLOCKED),
    ])
    for header in ("Site", "Oferta", "Preço", "Frete", "Total", "Status"):
        assert header in text
    assert "R$ 1.234,00" in text
    assert "Grátis" in text
    assert "Indisponível" in text
    assert "Bloqueado" in text
    assert "Melhor opção: Americanas — Fone a" in text
    assert "Total: R$ 112,89 (R$ 99,99 + frete R$ 12,90)" in text
    assert "Link: https://a.example/p" in text


def test_free_shipping_summary():
    text = output([SiteResult(Site("b", "Amazon"), Status.OK, offer("b", "10", "0"))])
    assert "Total: R$ 10,00 (R$ 10,00 + frete grátis)" in text


def test_only_unquoted_offers():
    text = output([SiteResult(Site("c", "Loja C"), Status.SHIPPING_UNAVAILABLE, offer("c", "50", None))])
    assert "Nenhuma oferta com frete conhecido para o CEP informado." in text
    assert "Melhor opção" not in text


def test_no_offers():
    text = output([SiteResult(Site("d", "Shopee"), Status.BLOCKED)])
    assert "Nenhuma oferta encontrada." in text
    assert "Melhor opção" not in text


def test_header():
    console = Console(record=True, width=160)
    render_header("fone bluetooth", "01310100", 6, console)
    assert 'Buscando "fone bluetooth" para o CEP 01310-100 em 6 sites...' in console.export_text()
