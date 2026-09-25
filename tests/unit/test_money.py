from decimal import Decimal

import pytest

from price_scout.money import format_brl, parse_brl


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("R$ 99,99", Decimal("99.99")),
        ("R$1.234,56", Decimal("1234.56")),
        ("R$ 1.234.567,89", Decimal("1234567.89")),
        ("R$ 99,00", Decimal("99.00")),
        ("R$\xa0149,90", Decimal("149.90")),
        ("1234,56", Decimal("1234.56")),
        ("R$ 150", Decimal("150")),
    ],
)
def test_parse_brl(text, expected):
    assert parse_brl(text) == expected


@pytest.mark.parametrize("text", ["", "R$", "abc", "1,2,3"])
def test_parse_brl_rejects_invalid(text):
    with pytest.raises(ValueError):
        parse_brl(text)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Decimal("99.99"), "R$ 99,99"),
        (Decimal("1234.56"), "R$ 1.234,56"),
        (Decimal("0"), "R$ 0,00"),
        (Decimal("1234567.8"), "R$ 1.234.567,80"),
    ],
)
def test_format_brl(value, expected):
    assert format_brl(value) == expected


def test_round_trip():
    assert parse_brl(format_brl(Decimal("4321.09"))) == Decimal("4321.09")
