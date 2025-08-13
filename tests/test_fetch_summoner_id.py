import pytest
from fetch_summoner_id import (
    get_summoner_puuids_high_tier,
    get_summoner_puuids,
)

MAX_TEST_SUMMONERS = 180


@pytest.mark.parametrize("tier", ["challenger", "grandmaster", "master"])
def test_get_summoner_puuids_high_tier_real(tier):
    puuids = get_summoner_puuids_high_tier(tier)

    assert isinstance(puuids, list)
    assert all(isinstance(p, str) and len(p) > 10 for p in puuids)
    assert len(puuids) <= MAX_TEST_SUMMONERS


@pytest.mark.parametrize(
    "tier", ["DIAMOND", "EMERALD", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]
)
def test_get_summoner_puuids_real(tier):
    puuids = get_summoner_puuids(tier)

    assert isinstance(puuids, list)
    assert all(isinstance(p, str) and len(p) > 10 for p in puuids)
    assert len(puuids) == MAX_TEST_SUMMONERS
