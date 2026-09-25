import tomllib
from pathlib import Path

from price_scout.models import Site


class SitesFileError(Exception):
    pass


def load_sites(path: Path) -> list[Site]:
    if not path.is_file():
        raise SitesFileError(f"Arquivo de sites não encontrado: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise SitesFileError(f"Arquivo de sites inválido ({path}): {exc}") from exc

    entries = data.get("sites")
    if not isinstance(entries, list):
        raise SitesFileError(f"Arquivo de sites inválido ({path}): lista [[sites]] ausente")

    sites = [_parse_entry(entry, path) for entry in entries]
    ids = [site.id for site in sites]
    duplicates = sorted({site_id for site_id in ids if ids.count(site_id) > 1})
    if duplicates:
        raise SitesFileError(f"Arquivo de sites inválido ({path}): id repetido: {', '.join(duplicates)}")
    return sites


def _parse_entry(entry: object, path: Path) -> Site:
    def invalid(reason: str) -> SitesFileError:
        return SitesFileError(f"Arquivo de sites inválido ({path}): {reason}")

    if not isinstance(entry, dict):
        raise invalid("cada site deve ser uma tabela [[sites]]")
    site_id = entry.get("id")
    name = entry.get("name")
    enabled = entry.get("enabled", True)
    if not isinstance(site_id, str) or not site_id.strip():
        raise invalid("site sem 'id'")
    if site_id != site_id.lower():
        raise invalid(f"o id '{site_id}' deve estar em minúsculas")
    if not isinstance(name, str) or not name.strip():
        raise invalid(f"site '{site_id}' sem 'name'")
    if not isinstance(enabled, bool):
        raise invalid(f"'enabled' do site '{site_id}' deve ser true ou false")
    return Site(id=site_id, name=name.strip(), enabled=enabled)
