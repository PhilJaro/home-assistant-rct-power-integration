from __future__ import annotations

from datetime import datetime, timedelta
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER
from .lib.api import (
    ApiResponseValue,
    InvalidApiResponse,
    RctPowerApiClient,
    RctPowerData,
    ValidApiResponse,
)

MISSING_API_RESPONSE_CAUSE = "MISSING_RESPONSE"


class RctPowerDataUpdateCoordinator(DataUpdateCoordinator[RctPowerData]):
    """Class to manage fetching data from the rct power inverter API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        *,
        client: RctPowerApiClient,
        name_suffix: str,
        object_ids: list[int],
        update_interval: int,  # in seconds
    ) -> None:
        self.client = client
        self.object_ids = object_ids
        self._stale_update_counts: dict[int, int] = {}
        self._stale_causes: dict[int, str] = {}
        super().__init__(
            hass=hass,
            config_entry=entry,
            logger=LOGGER,
            name=f"{DOMAIN} {entry.unique_id} {name_suffix}",
            update_interval=timedelta(seconds=update_interval),
        )

    def get_latest_response(
        self, object_id: int
    ) -> ValidApiResponse | InvalidApiResponse | None:
        return self.data.get(object_id)

    def get_valid_value_or(
        self, object_id: int, default_value: ApiResponseValue
    ) -> ApiResponseValue:
        latest_response = self.get_latest_response(object_id)

        if isinstance(latest_response, ValidApiResponse):
            return latest_response.value
        return default_value

    def has_valid_value(self, object_id: int) -> bool:
        return isinstance(self.get_latest_response(object_id), ValidApiResponse)

    def is_response_stale(self, object_id: int) -> bool:
        """Return whether the current value is kept from an earlier valid update."""

        return self._stale_update_counts.get(object_id, 0) > 0

    def get_stale_update_count(self, object_id: int) -> int:
        """Return consecutive invalid or missing updates for the object."""

        return self._stale_update_counts.get(object_id, 0)

    def get_stale_cause(self, object_id: int) -> str | None:
        """Return the latest cause that made the current value stale."""

        return self._stale_causes.get(object_id)

    async def _async_update_data(self) -> RctPowerData:
        fresh_data = await self.client.async_get_data(object_ids=self.object_ids)
        fresh_data = fresh_data or {}
        previous_data = cast(RctPowerData | None, getattr(self, "data", None)) or {}

        return {
            object_id: self._keep_last_valid_response(
                object_id=object_id,
                fresh_response=fresh_data.get(object_id),
                previous_response=previous_data.get(object_id),
            )
            for object_id in self.object_ids
        }

    def _keep_last_valid_response(
        self,
        *,
        object_id: int,
        fresh_response: ValidApiResponse | InvalidApiResponse | None,
        previous_response: ValidApiResponse | InvalidApiResponse | None,
    ) -> ValidApiResponse | InvalidApiResponse:
        if isinstance(fresh_response, ValidApiResponse):
            self._stale_update_counts.pop(object_id, None)
            self._stale_causes.pop(object_id, None)
            return fresh_response

        invalid_response = (
            fresh_response
            if fresh_response is not None
            else InvalidApiResponse(
                object_id=object_id,
                time=datetime.now(),
                cause=MISSING_API_RESPONSE_CAUSE,
            )
        )

        if isinstance(previous_response, ValidApiResponse):
            self._stale_update_counts[object_id] = (
                self._stale_update_counts.get(object_id, 0) + 1
            )
            self._stale_causes[object_id] = invalid_response.cause
            LOGGER.debug(
                "Keeping last valid RCT Power value for object %x after invalid response: %s",
                object_id,
                invalid_response.cause,
            )
            return previous_response

        self._stale_update_counts.pop(object_id, None)
        self._stale_causes.pop(object_id, None)
        return invalid_response
