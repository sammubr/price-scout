import re
import unicodedata

ACCESSORY_TERMS = {
    "capa", "capinha", "pelicula", "case", "suporte", "cabo", "carregador",
    "adaptador", "protetor", "estojo", "skin", "adesivo", "bateria",
}
CONNECTORS = {"para", "p"}


def tokens(text: str) -> list[str]:
    decomposed = unicodedata.normalize("NFKD", text)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.findall(r"[a-z0-9]+", plain.casefold())


def matches(query: str, title: str) -> bool:
    query_tokens = set(tokens(query))
    title_tokens = tokens(title)
    if not query_tokens or not query_tokens <= set(title_tokens):
        return False
    return not _is_accessory_listing(title_tokens, ACCESSORY_TERMS - query_tokens)


def _is_accessory_listing(title_tokens: list[str], terms: set[str]) -> bool:
    if title_tokens and title_tokens[0] in terms:
        return True
    return any(
        current in terms and following in CONNECTORS
        for current, following in zip(title_tokens, title_tokens[1:])
    )
