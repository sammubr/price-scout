from decimal import Decimal
from pathlib import Path

import pytest

from price_scout import cli
from price_scout.models import Offer, Site, SiteResult, Status

SITES = Path(__file__).parents[2] / "sites.toml"


def fake_search(results):
    calls = []

    async def run_search(sites, product, cep):
        calls.append((sites, product, cep))
        return results

    run_search.calls = calls
    return run_search


def ok_result():
    offer = Offer("americanas", "Fone X", Decimal("99.99"), Decimal("12.90"), "https://a/p")
    return SiteResult(Site("americanas", "Americanas"), Status.OK, offer)


def test_found_exits_zero(monkeypatch, capsys):
    search = fake_search([ok_result()])
    monkeypatch.setattr(cli, "run_search", search)
    assert cli.main(["fone bluetooth", "01310-100", "--sites", str(SITES)]) == 0
    out = capsys.readouterr().out
    assert "Melhor opção: Americanas — Fone X" in out
    sites, product, cep = search.calls[0]
    assert (product, cep) == ("fone bluetooth", "01310100")


def test_nothing_found_exits_one(monkeypatch, capsys):
    monkeypatch.setattr(cli, "run_search", fake_search([SiteResult(Site("s", "Shopee"), Status.BLOCKED)]))
    assert cli.main(["xyz", "01310100", "--sites", str(SITES)]) == 1
    assert "Nenhuma oferta encontrada." in capsys.readouterr().out


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["fone", "123"], 'CEP inválido: "123". Use 8 dígitos, com ou sem hífen (ex.: 01310-100).'),
        (["  ", "01310100"], "Informe o nome do produto."),
        (["fone", "01310100", "--sites", "nao-existe.toml"], "Arquivo de sites não encontrado: nao-existe.toml"),
    ],
)
def test_usage_errors_exit_two(monkeypatch, capsys, argv, message):
    monkeypatch.setattr(cli, "run_search", fake_search([]))
    assert cli.main(argv) == 2
    err = capsys.readouterr().err
    assert message in err
    assert "uso:" in err


def test_missing_arguments_in_portuguese(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "uso:" in err
    assert "informe o produto e o CEP" in err
    assert "usage:" not in err
    assert "error:" not in err


def test_unknown_option_in_portuguese(capsys):
    with pytest.raises(SystemExit):
        cli.main(["fone", "01310100", "--foo"])
    assert "argumentos não reconhecidos: --foo" in capsys.readouterr().err


def write_sites(tmp_path, content):
    path = tmp_path / "sites.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_disabled_sites_are_not_searched(monkeypatch, tmp_path):
    search = fake_search([ok_result()])
    monkeypatch.setattr(cli, "run_search", search)
    path = write_sites(
        tmp_path,
        '[[sites]]\nid = "americanas"\nname = "Americanas"\n'
        '[[sites]]\nid = "shopee"\nname = "Shopee"\nenabled = false\n',
    )
    cli.main(["fone", "01310100", "--sites", str(path)])
    sites, _, _ = search.calls[0]
    assert [site.id for site in sites] == ["americanas"]


def test_all_disabled_exits_two(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cli, "run_search", fake_search([]))
    path = write_sites(tmp_path, '[[sites]]\nid = "shopee"\nname = "Shopee"\nenabled = false\n')
    assert cli.main(["fone", "01310100", "--sites", str(path)]) == 2
    assert "Nenhum site habilitado" in capsys.readouterr().err


def test_unknown_site_warns(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cli, "run_search", fake_search([ok_result()]))
    path = write_sites(tmp_path, '[[sites]]\nid = "kabum"\nname = "Kabum"\n')
    cli.main(["fone", "01310100", "--sites", str(path)])
    assert "Aviso: site 'kabum' não é suportado" in capsys.readouterr().err


def test_verbose_prints_details(monkeypatch, capsys):
    blocked = SiteResult(Site("shopee", "Shopee"), Status.BLOCKED, detail="verificação anti-robô")
    monkeypatch.setattr(cli, "run_search", fake_search([ok_result(), blocked]))
    cli.main(["fone", "01310100", "--sites", str(SITES), "--verbose"])
    assert "Shopee: verificação anti-robô" in capsys.readouterr().out


def test_missing_browser(monkeypatch, capsys):
    from playwright.async_api import Error as PlaywrightError

    async def no_browser(sites, product, cep):
        raise PlaywrightError("BrowserType.launch: Executable doesn't exist at /x/chrome")

    monkeypatch.setattr(cli, "run_search", no_browser)
    assert cli.main(["fone", "01310100", "--sites", str(SITES)]) == 2
    assert "Navegador não instalado. Execute: uv run playwright install chromium" in capsys.readouterr().err
