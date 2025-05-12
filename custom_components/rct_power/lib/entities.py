from __future__ import annotations

import re

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from rctclient.registry import REGISTRY

from .const import EntityUpdatePriority
from .device_info_helpers import get_battery_device_info, get_inverter_device_info
from .entity import (
    RctPowerBitfieldSensorEntityDescription,
    RctPowerSensorEntityDescription,
)
from .state_helpers import (
    available_battery_status,
    get_first_api_response_value_as_absolute_state,
    get_first_api_response_value_as_battery_status,
    get_first_api_response_value_as_timestamp,
    sum_api_response_values_as_state,
)


def get_matching_names(expression: str) -> list[str]:
    compiled_expression = re.compile(expression)
    return [
        object_info.name
        for object_info in REGISTRY.all()
        if compiled_expression.match(object_info.name) is not None
    ]


battery_sensor_entity_descriptions: list[RctPowerSensorEntityDescription] = [
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.stored_energy",
        name="Battery Stored Energy",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.used_energy",
        name="Battery Used Energy",
        update_priority=EntityUpdatePriority.FREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="power_mng.bat_next_calib_date",
        name="Next Battery Calibration Date",
        update_priority=EntityUpdatePriority.INFREQUENT,
        device_class=SensorDeviceClass.TIMESTAMP,
        get_native_value=get_first_api_response_value_as_timestamp,
    ),
]

inverter_sensor_entity_descriptions: list[RctPowerSensorEntityDescription] = [
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="android_description",
        name="Inverter Device Name",
        update_priority=EntityUpdatePriority.STATIC,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_load_day",
        name="Consumer Energy Consumption Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_load_total",
        name="Consumer Energy Consumption Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_feed_day",
        name="Grid Energy Production Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_feed_month",
        name="Grid Energy Production Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_feed_absolute_total",
        unique_id="energy.e_grid_feed_absolute_total",  # to avoid collision
        object_names=["energy.e_grid_feed_total"],
        name="Grid Energy Production Absolute Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
        get_native_value=get_first_api_response_value_as_absolute_state,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_load_day",
        name="Grid Energy Consumption Day",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_load_month",
        name="Grid Energy Consumption Month",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_grid_load_total",
        name="Grid Energy Consumption Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    RctPowerSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="energy.e_dc_total",
        object_names=["energy.e_dc_total[0]", "energy.e_dc_total[1]"],
        name="All Generators Energy Production Total",
        update_priority=EntityUpdatePriority.INFREQUENT,
        state_class=SensorStateClass.TOTAL_INCREASING,
        get_native_value=sum_api_response_values_as_state,
    ),
]

bitfield_sensor_entity_descriptions: list[RctPowerBitfieldSensorEntityDescription] = [
    RctPowerBitfieldSensorEntityDescription(
        get_device_info=get_inverter_device_info,
        key="fault.flt",
        object_names=[
            "fault[0].flt",
            "fault[1].flt",
            "fault[2].flt",
            "fault[3].flt",
        ],
        name="Faults",
        update_priority=EntityUpdatePriority.FREQUENT,
        unique_id=f"{0x37F9D5CA}",  # for backwards-compatibility
    ),
    RctPowerBitfieldSensorEntityDescription(
        get_device_info=get_battery_device_info,
        key="battery.bat_status",
        name="Battery Status",
        update_priority=EntityUpdatePriority.FREQUENT,
        get_native_value=get_first_api_response_value_as_battery_status,
        options=available_battery_status,
    ),
]

sensor_entity_descriptions = [
    *battery_sensor_entity_descriptions,
    *inverter_sensor_entity_descriptions,
    *bitfield_sensor_entity_descriptions,
]

all_entity_descriptions = [
    *sensor_entity_descriptions,
]
