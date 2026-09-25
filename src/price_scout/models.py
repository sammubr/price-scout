from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


@dataclass(frozen=True)
class Site:
    id: str
    name: str
    enabled: bool = True


@dataclass(frozen=True)
class SearchRequest:
    product: str
    cep: str


@dataclass(frozen=True)
class Offer:
    site_id: str
    title: str
    unit_price: Decimal
    shipping: Decimal | None
    url: str

    @property
    def total(self) -> Decimal | None:
        if self.shipping is None:
            return None
        return self.unit_price + self.shipping


class Status(Enum):
    OK = "OK"
    SHIPPING_UNAVAILABLE = "Frete indisponível"
    NOT_FOUND = "Produto não encontrado"
    TIMEOUT = "Tempo esgotado"
    BLOCKED = "Bloqueado"
    UNREACHABLE = "Site indisponível"
    UNSUPPORTED = "Não suportado"
    ERROR = "Erro inesperado"


@dataclass(frozen=True)
class SiteResult:
    site: Site
    status: Status
    offer: Offer | None = None
    detail: str = ""
