import pytest

from price_scout.matching import matches


@pytest.mark.parametrize(
    ("query", "title"),
    [
        ("iphone 15", "Apple iPhone 15 128GB"),
        ("capinha iphone 15", "Capinha para iPhone 15"),
        ("fone bluetooth", "Fone Bluetooth TWS com case carregador, bateria 30h"),
        ("fone bluetooth", "Fone Bluetooth e cabo P2"),
        ("pelicula iphone", "Película de vidro iPhone 13"),
        ("FONE Bluetooth", "fone bluetooth jbl"),
        ("cafe", "Café Pilão 500g"),
    ],
)
def test_matches(query, title):
    assert matches(query, title)


@pytest.mark.parametrize(
    ("query", "title"),
    [
        ("iphone 15", "Capinha para iPhone 15"),
        ("fone bluetooth", "Case para fone bluetooth JBL"),
        ("fone bluetooth", "Cabo p/ fone bluetooth"),
        ("fone bluetooth", "Estojo fone bluetooth"),
        ("fone bluetooth", "Fone de ouvido com fio"),
        ("", "Qualquer coisa"),
    ],
)
def test_rejects(query, title):
    assert not matches(query, title)
