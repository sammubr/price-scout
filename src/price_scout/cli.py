import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import Error as PlaywrightError
from rich.console import Console

from price_scout.adapters import ADAPTERS
from price_scout.cep import normalize_cep
from price_scout.models import SearchRequest
from price_scout.report import render, render_details, render_header
from price_scout.search import run_search
from price_scout.sites_file import SitesFileError, load_sites

EXIT_FOUND = 0
EXIT_NOT_FOUND = 1
EXIT_USAGE = 2


class PortugueseHelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        super().add_usage(usage, actions, groups, prefix or "uso: ")


class PortugueseArgumentParser(argparse.ArgumentParser):
    def error(self, message: str):
        self.print_usage(sys.stderr)
        self.exit(EXIT_USAGE, f"erro: {_translate(message)}\n")


def _translate(message: str) -> str:
    if message.startswith("unrecognized arguments:"):
        return "argumentos não reconhecidos:" + message.removeprefix("unrecognized arguments:")
    if message.endswith("expected one argument"):
        return message.replace("expected one argument", "requer um valor")
    return message


def build_parser() -> argparse.ArgumentParser:
    parser = PortugueseArgumentParser(
        prog="price-scout",
        description="Compara o preço de um produto (preço + frete para o CEP) em sites de e-commerce.",
        formatter_class=PortugueseHelpFormatter,
        add_help=False,
    )
    arguments = parser.add_argument_group("argumentos")
    arguments.add_argument("produto", nargs="?", help='nome do produto (use aspas se tiver espaços)')
    arguments.add_argument("cep", nargs="?", help="CEP de entrega, ex.: 01310-100")
    options = parser.add_argument_group("opções")
    options.add_argument("-h", "--ajuda", action="help", help="mostra esta ajuda e sai")
    options.add_argument(
        "--sites", type=Path, default=Path("sites.toml"), metavar="ARQUIVO", help="arquivo de sites (padrão: sites.toml)"
    )
    options.add_argument(
        "--verbose", action="store_true", help="mostra detalhes técnicos das falhas"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.produto is None or args.cep is None:
        parser.error("informe o produto e o CEP")

    product = args.produto.strip()
    if not product:
        return _usage_error(parser, "Informe o nome do produto.")
    try:
        request = SearchRequest(product, normalize_cep(args.cep))
    except ValueError as exc:
        return _usage_error(parser, str(exc))
    try:
        sites = [site for site in load_sites(args.sites) if site.enabled]
    except SitesFileError as exc:
        return _usage_error(parser, str(exc))
    if not sites:
        return _usage_error(
            parser, f"Nenhum site habilitado em {args.sites}. Defina enabled = true em pelo menos um site."
        )
    for site in sites:
        if site.id not in ADAPTERS:
            print(f"Aviso: site '{site.id}' não é suportado e aparecerá como 'Não suportado'.", file=sys.stderr)

    console = Console()
    render_header(request.product, request.cep, len(sites), console)
    try:
        results = asyncio.run(run_search(sites, request.product, request.cep))
    except PlaywrightError as exc:
        if "Executable doesn't exist" not in str(exc):
            raise
        print("Navegador não instalado. Execute: uv run playwright install chromium", file=sys.stderr)
        return EXIT_USAGE
    render(results, console)
    if args.verbose:
        console.print()
        render_details(results, console)
    return EXIT_FOUND if any(result.offer for result in results) else EXIT_NOT_FOUND


def _usage_error(parser: argparse.ArgumentParser, message: str) -> int:
    print(message, file=sys.stderr)
    parser.print_usage(sys.stderr)
    return EXIT_USAGE
