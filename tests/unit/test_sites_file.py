from pathlib import Path

import pytest

from price_scout.models import Site
from price_scout.sites_file import SitesFileError, load_sites

REPO_SITES = Path(__file__).parents[2] / "sites.toml"


def write(tmp_path, content):
    path = tmp_path / "sites.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_shipped_file_has_six_enabled_sites():
    sites = load_sites(REPO_SITES)
    assert {site.id for site in sites} == {
        "amazon", "americanas", "magalu", "mercadolivre", "shopee", "submarino"
    }
    assert all(site.enabled for site in sites)


def test_enabled_defaults_to_true(tmp_path):
    path = write(tmp_path, '[[sites]]\nid = "amazon"\nname = "Amazon"\n')
    assert load_sites(path) == [Site("amazon", "Amazon", True)]


def test_disabled_site(tmp_path):
    path = write(tmp_path, '[[sites]]\nid = "amazon"\nname = "Amazon"\nenabled = false\n')
    assert load_sites(path)[0].enabled is False


def test_missing_file(tmp_path):
    with pytest.raises(SitesFileError, match="não encontrado"):
        load_sites(tmp_path / "nope.toml")


@pytest.mark.parametrize(
    "content",
    [
        "",
        "sites = 1",
        '[[sites]]\nname = "Amazon"\n',
        '[[sites]]\nid = "amazon"\n',
        '[[sites]]\nid = "Amazon"\nname = "Amazon"\n',
        '[[sites]]\nid = "a"\nname = "A"\n[[sites]]\nid = "a"\nname = "B"\n',
        '[[sites]]\nid = "a"\nname = "A"\nenabled = "sim"\n',
        "[[sites]\n",
    ],
)
def test_invalid_files(tmp_path, content):
    with pytest.raises(SitesFileError, match="inválido"):
        load_sites(write(tmp_path, content))
