import asyncio
import datetime
import struct
from typing import Type
from zoneinfo import ZoneInfo

import freezegun
import pytest
from bleak import BleakClient, BleakError
from mockito import ANY, mock, verify, when

import melnor_bluetooth.device as device_module
from melnor_bluetooth.constants import (
    VALVE_MANUAL_SETTINGS_UUID,
    VALVE_MANUAL_STATES_UUID,
)
from melnor_bluetooth.device import Device, Valve
from tests.constants import TEST_UUID

zone_manual_setting_bytes = struct.pack(
    ">?HH?HH?HH?HH",
    # Valve 1
    True,
    5,
    5,
    # Valve 2
    True,
    10,
    10,
    # Valve 3
    True,
    15,
    15,
    # Valve 4
    True,
    20,
    20,
)


@pytest.fixture
def client_mock() -> Type:
    connect = asyncio.Future()
    connect.set_result(True)

    client_mock = mock(spec=BleakClient)

    when(device_module).BleakClient(TEST_UUID, disconnected_callback=ANY).thenReturn(
        client_mock
    )

    when(client_mock).connect().thenReturn(connect)

    return client_mock


class TestValveZone:
    def test_zone_update_state(self):
        device = Device(TEST_UUID, 4)

        device.zone1.update_state(zone_manual_setting_bytes, VALVE_MANUAL_SETTINGS_UUID)

        assert device.zone1.is_watering == True
        assert device.zone1.manual_watering_minutes == 5

    def test_zone_properties(self):
        device = Device(TEST_UUID, 4)

        device.zone1.is_watering = True

        assert device.zone1.manual_watering_minutes == 20

    def test_zone_defaults(self):
        device = Device(TEST_UUID, 4)
        zone = Valve(0, device)

        assert zone.is_watering == False
        assert zone.manual_watering_minutes == 20

    def test_zone_byte_payload(self):
        device = Device(TEST_UUID, 2)
        zone = Valve(0, device)

        zone.is_watering = True
        zone.manual_watering_minutes = 10

        assert zone._manual_setting_bytes() == b"\x01\x00\n\x00\n"


class TestDevice:
    def test_get_item(self):
        device = Device(TEST_UUID, 4)

        assert device["zone1"] is device.zone1
        assert device["zone2"] is device.zone2
        assert device["zone3"] is device.zone3
        assert device["zone4"] is device.zone4

    def test_1_valve_device(self):
        device = Device(TEST_UUID, 1)

        assert device.zone1 is not None
        assert device.zone2 is None
        assert device.zone3 is None
        assert device.zone4 is None

    def test_2_valve_device(self):
        device = Device(TEST_UUID, 2)

        assert device.zone1 is not None
        assert device.zone2 is not None
        assert device.zone3 is None
        assert device.zone4 is None

    def test_1_valve_has_all_bytes(self):
        device = Device(TEST_UUID, 1)

        device.zone1.is_watering = True
        device.zone1.manual_watering_minutes = 10

        assert (
            (
                device._valves[0]._manual_setting_bytes()
                + device._valves[1]._manual_setting_bytes()
                + device._valves[2]._manual_setting_bytes()
                + device._valves[3]._manual_setting_bytes()
            )
            == b"\x01\x00\n\x00\n\x00\x00\x14\x00\x14\x00\x00\x14\x00\x14\x00\x00\x14\x00\x14"  # noqa: E501
        )

    def test_1_valve_has_internal_valves(self):
        device = Device(TEST_UUID, 1)

        device.zone1.is_watering = True
        device.zone1.manual_watering_minutes = 10

        assert device.zone1 is not None
        assert device.zone2 is None
        assert device.zone3 is None
        assert device.zone4 is None

        assert device._valves[1] is not None
        assert device._valves[2] is not None
        assert device._valves[3] is not None

    async def test_device_connect_retry(self):
        device = Device(TEST_UUID, 2)

        failure = asyncio.Future()
        failure.set_exception(BleakError("Connection failed"))

        success = asyncio.Future()
        success.set_result(True)

        when(BleakClient).connect().thenReturn(failure).thenReturn(success)
        when(device_module).BleakClient(
            TEST_UUID, disconnected_callback=ANY
        ).thenReturn(BleakClient)

        await device.connect()

        verify(BleakClient, times=2).connect()

    @freezegun.freeze_time(datetime.datetime.now(tz=ZoneInfo("UTC")))
    async def test_fetch(self, client_mock):
        device = Device(TEST_UUID, 4)

        read_manual_settings = asyncio.Future()
        read_manual_settings.set_result(
            struct.pack(
                ">?HH?HH?HH?HH",
                # Valve 1
                False,
                0,
                0,
                # Valve 2
                False,
                0,
                0,
                # Valve 3
                False,
                0,
                0,
                # Valve 4
                False,
                0,
                0,
            )
        )

        read_manual_state = asyncio.Future()
        read_manual_state.set_result(
            struct.pack(
                ">bIbIbIbI",
                # Valve 1
                1,
                4294967295,
                # Valve 2
                1,
                0,
                # Valve 3
                1,
                0,
                # Valve 4
                1,
                0,
            )
        )

        when(client_mock).read_gatt_char(VALVE_MANUAL_SETTINGS_UUID).thenReturn(
            read_manual_settings
        )

        when(client_mock).read_gatt_char(VALVE_MANUAL_STATES_UUID).thenReturn(
            read_manual_state
        )

        await device.connect()

        await device.fetch_state()

        verify(client_mock).read_gatt_char(VALVE_MANUAL_SETTINGS_UUID)

        print(device.zone1.watering_end_time)

        assert device.zone1.is_watering == False
        assert device.zone1.manual_watering_minutes == 0
        # TODO: Test this more aggressively in date utils
        assert device.zone1.watering_end_time != 0

        assert device.zone2 is not None
        assert device.zone2.is_watering == False
        assert device.zone2.manual_watering_minutes == 0
        assert device.zone2.watering_end_time == 0

        assert device.zone3 is not None
        assert device.zone3.is_watering == False
        assert device.zone3.manual_watering_minutes == 0
        assert device.zone3.watering_end_time == 0

        assert device.zone4 is not None
        assert device.zone4.is_watering == False
        assert device.zone4.manual_watering_minutes == 0
        assert device.zone4.watering_end_time == 0

    def test_str(self, snapshot):
        device = Device(TEST_UUID, 4)

        actual = device.__str__()

        assert actual == snapshot
