import re
from decimal import Decimal


def parse_brl(text: str) -> Decimal:
    digits = re.sub(r"[^\d,]", "", text)
    if not re.fullmatch(r"\d+(,\d{1,2})?", digits):
        raise ValueError(f"valor inválido: {text!r}")
    return Decimal(digits.replace(",", "."))


def format_brl(value: Decimal) -> str:
    formatted = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"
