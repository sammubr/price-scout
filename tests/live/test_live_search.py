import time

import pytest

from price_scout.models import Site, Status
from price_scout.search import run_search

pytestmark = pytest.mark.live


async def test_americanas_and_amazon():
    sites = [Site("americanas", "Americanas"), Site("amazon", "Amazon")]
    start = time.monotonic()
    results = await run_search(sites, "fone bluetooth", "01310100")
    elapsed = time.monotonic() - start
    by_site = {result.site.id: result for result in results}
    assert by_site["americanas"].status is Status.OK
    assert by_site["amazon"].status in (Status.OK, Status.SHIPPING_UNAVAILABLE, Status.BLOCKED)
    assert elapsed < 60
