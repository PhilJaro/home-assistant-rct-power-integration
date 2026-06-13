from __future__ import annotations

# pyright: reportAttributeAccessIssue=false, reportPrivateUsage=false, reportUnknownMemberType=false
from datetime import datetime

from custom_components.rct_power.coordinator import (
    MISSING_API_RESPONSE_CAUSE,
    RctPowerDataUpdateCoordinator,
)
from custom_components.rct_power.lib.api import (
    InvalidApiResponse,
    RctPowerData,
    ValidApiResponse,
)


class _Client:
    def __init__(self, data: RctPowerData | None) -> None:
        self.data = data

    async def async_get_data(self, object_ids: list[int]) -> RctPowerData | None:
        return self.data


def _coordinator() -> RctPowerDataUpdateCoordinator:
    coordinator = object.__new__(RctPowerDataUpdateCoordinator)
    coordinator._stale_update_counts = {}
    coordinator._stale_causes = {}
    return coordinator


def test_keep_last_valid_response_returns_fresh_valid_response() -> None:
    coordinator = _coordinator()
    fresh_response = ValidApiResponse(object_id=1, time=datetime.now(), value=42)

    response = coordinator._keep_last_valid_response(
        object_id=1,
        fresh_response=fresh_response,
        previous_response=ValidApiResponse(object_id=1, time=datetime.now(), value=21),
    )

    assert response is fresh_response
    assert not coordinator.is_response_stale(1)


def test_keep_last_valid_response_keeps_previous_valid_response() -> None:
    coordinator = _coordinator()
    previous_response = ValidApiResponse(object_id=1, time=datetime.now(), value=42)

    response = coordinator._keep_last_valid_response(
        object_id=1,
        fresh_response=InvalidApiResponse(
            object_id=1, time=datetime.now(), cause="OBJECT_READ_TIMEOUT"
        ),
        previous_response=previous_response,
    )

    assert response is previous_response
    assert coordinator.is_response_stale(1)
    assert coordinator.get_stale_update_count(1) == 1
    assert coordinator.get_stale_cause(1) == "OBJECT_READ_TIMEOUT"


def test_keep_last_valid_response_tracks_repeated_invalid_updates() -> None:
    coordinator = _coordinator()
    previous_response = ValidApiResponse(object_id=1, time=datetime.now(), value=42)

    for _ in range(2):
        coordinator._keep_last_valid_response(
            object_id=1,
            fresh_response=InvalidApiResponse(
                object_id=1, time=datetime.now(), cause="CRC_ERROR"
            ),
            previous_response=previous_response,
        )

    assert coordinator.get_stale_update_count(1) == 2
    assert coordinator.get_stale_cause(1) == "CRC_ERROR"


def test_keep_last_valid_response_handles_missing_fresh_response() -> None:
    coordinator = _coordinator()
    previous_response = ValidApiResponse(object_id=1, time=datetime.now(), value=42)

    response = coordinator._keep_last_valid_response(
        object_id=1,
        fresh_response=None,
        previous_response=previous_response,
    )

    assert response is previous_response
    assert coordinator.get_stale_cause(1) == MISSING_API_RESPONSE_CAUSE


def test_keep_last_valid_response_returns_invalid_without_previous_valid_response() -> (
    None
):
    coordinator = _coordinator()
    fresh_response = InvalidApiResponse(
        object_id=1, time=datetime.now(), cause="OBJECT_READ_TIMEOUT"
    )

    response = coordinator._keep_last_valid_response(
        object_id=1,
        fresh_response=fresh_response,
        previous_response=None,
    )

    assert response is fresh_response
    assert not coordinator.is_response_stale(1)


async def test_async_update_data_keeps_previous_values_for_missing_responses() -> None:
    coordinator = _coordinator()
    coordinator.object_ids = [1, 2]
    coordinator.client = _Client(
        {1: ValidApiResponse(object_id=1, time=datetime.now(), value=84)}
    )
    coordinator.data = {
        1: ValidApiResponse(object_id=1, time=datetime.now(), value=42),
        2: ValidApiResponse(object_id=2, time=datetime.now(), value=21),
    }

    data = await coordinator._async_update_data()

    assert data[1] == ValidApiResponse(object_id=1, time=data[1].time, value=84)
    assert data[2] is coordinator.data[2]
    assert coordinator.get_stale_cause(2) == MISSING_API_RESPONSE_CAUSE
