from __future__ import annotations

from datetime import timedelta
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

    async def _async_update_data(self) -> RctPowerData:
        fresh_data = await self.client.async_get_data(object_ids=self.object_ids)
        previous_data = cast(RctPowerData | None, getattr(self, "data", None)) or {}

        return {
            object_id: self._keep_last_valid_response(
                fresh_response=fresh_response,
                previous_response=previous_data.get(object_id),
            )
            for object_id, fresh_response in fresh_data.items()
        }

    def _keep_last_valid_response(
        self,
        *,
        fresh_response: ValidApiResponse | InvalidApiResponse,
        previous_response: ValidApiResponse | InvalidApiResponse | None,
    ) -> ValidApiResponse | InvalidApiResponse:
        if isinstance(fresh_response, ValidApiResponse):
            return fresh_response

        if isinstance(previous_response, ValidApiResponse):
            LOGGER.debug(
                "Keeping last valid RCT Power value for object %x after invalid response: %s",
                fresh_response.object_id,
                fresh_response.cause,
            )
            return previous_response

        return fresh_response
