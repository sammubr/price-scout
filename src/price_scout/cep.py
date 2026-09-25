import re


def normalize_cep(text: str) -> str:
    match = re.fullmatch(r"(\d{5})-?(\d{3})", text.strip())
    if not match:
        raise ValueError(f'CEP inválido: "{text}". Use 8 dígitos, com ou sem hífen (ex.: 01310-100).')
    return match.group(1) + match.group(2)


def format_cep(cep: str) -> str:
    return f"{cep[:5]}-{cep[5:]}"
