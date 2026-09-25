from rich.console import Console
from rich.table import Table

from price_scout.cep import format_cep
from price_scout.models import Offer, SiteResult
from price_scout.money import format_brl
from price_scout.selection import best_option

EMPTY = "—"
HEADERS = ("Site", "Oferta", "Preço", "Frete", "Total", "Status")
TITLE_COLUMN = 1
MIN_TITLE_WIDTH = 10
MAX_TITLE_WIDTH = 50
MONEY_HEADERS = ("Preço", "Frete", "Total")


def render(results: list[SiteResult], console: Console) -> None:
    best = best_option(results)
    console.print(_table(results, best, console.width))
    console.print()
    if best is not None:
        _print_best(best.site.name, best.offer, console)
    elif any(result.offer for result in results):
        console.print("Nenhuma oferta com frete conhecido para o CEP informado.")
    else:
        console.print("Nenhuma oferta encontrada.")


def render_details(results: list[SiteResult], console: Console) -> None:
    for result in results:
        if result.detail:
            console.print(f"{result.site.name}: {result.detail}", style="dim", soft_wrap=True)


def render_header(product: str, cep: str, site_count: int, console: Console) -> None:
    console.print(f'Buscando "{product}" para o CEP {format_cep(cep)} em {site_count} sites...\n')


def _table(results: list[SiteResult], best: SiteResult | None, console_width: int) -> Table:
    rows = [(result.site.name, *_offer_cells(result.offer), result.status.value) for result in results]
    widths = [max(len(header), *(len(row[i]) for row in rows)) for i, header in enumerate(HEADERS)]
    borders = 3 * len(HEADERS) + 1
    fixed = sum(widths) - widths[TITLE_COLUMN]
    widths[TITLE_COLUMN] = max(MIN_TITLE_WIDTH, min(MAX_TITLE_WIDTH, console_width - fixed - borders))

    table = Table()
    for header, width in zip(HEADERS, widths):
        if header in MONEY_HEADERS:
            table.add_column(header, justify="right", min_width=width, no_wrap=True)
        elif header == "Oferta":
            table.add_column(header, width=width, no_wrap=True, overflow="ellipsis")
        else:
            table.add_column(header, max_width=width)
    for result, row in zip(results, rows):
        table.add_row(*row, style="bold green" if result is best else None)
    return table


def _offer_cells(offer: Offer | None) -> tuple[str, str, str, str]:
    if offer is None:
        return EMPTY, EMPTY, EMPTY, EMPTY
    total = EMPTY if offer.total is None else format_brl(offer.total)
    return offer.title, format_brl(offer.unit_price), _shipping_text(offer), total


def _shipping_text(offer: Offer) -> str:
    if offer.shipping is None:
        return "Indisponível"
    if offer.shipping == 0:
        return "Grátis"
    return format_brl(offer.shipping)


def _print_best(site_name: str, offer: Offer, console: Console) -> None:
    console.print(f"Melhor opção: {site_name} — {offer.title}", style="bold")
    shipping = "frete grátis" if offer.shipping == 0 else f"frete {format_brl(offer.shipping)}"
    console.print(f"Total: {format_brl(offer.total)} ({format_brl(offer.unit_price)} + {shipping})")
    console.print(f"Link: {offer.url}", soft_wrap=True)

