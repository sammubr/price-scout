import pytest

from price_scout.cep import format_cep, normalize_cep


@pytest.mark.parametrize("text", ["01310100", "01310-100", " 01310-100 "])
def test_valid(text):
    assert normalize_cep(text) == "01310100"


@pytest.mark.parametrize("text", ["123", "0131-0100", "01310-10a", "", "013101000"])
def test_invalid(text):
    with pytest.raises(ValueError, match="CEP inválido"):
        normalize_cep(text)


def test_format():
    assert format_cep("01310100") == "01310-100"
