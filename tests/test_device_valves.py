import asyncio
import datetime
import struct
from typing import Dict
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import freezegun
import pytest
from bleak import BleakClient
from pytest_mock import MockerFixture

from melnor_bluetooth.constants import (
    BATTERY_UUID,
    MANUFACTURER_UUID,
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


def _patch_bleak_client_read_gatt_char(
    mocker: MockerFixture, param_map: Dict[str, bytes] = {}
):
    def fake_read_gatt_char(uuid: str):
        return param_map.get(uuid)

    mocker.patch(
        "bleak.BleakClient.read_gatt_char",
        side_effect=fake_read_gatt_char,
    )


@pytest.fixture
def connect_mock():
    return AsyncMock(return_value=True)


@pytest.fixture
def client_mock(connect_mock, mocker: MockerFixture):
    """Mock the BleakClient class"""

    def _fake_client(read: Dict[str, bytes] = {}):
        _patch_bleak_client_read_gatt_char(mocker, read)

        mocker.patch("bleak.BleakClient.connect", side_effect=connect_mock)

        mocker.patch("bleak.BleakClient", new=AsyncMock(spec=BleakClient))

    return _fake_client


# @pytest.fixture
# def client_mock() -> Type:

#     connect = asyncio.Future()
#     connect.set_result(True)

#     client_mock = mock(spec=BleakClient)

#     when(device_module).BleakClient(TEST_UUID, disconnected_callback=ANY).thenReturn(
#         client_mock
#     )

#     read_manufacturer = asyncio.Future()
#     read_manufacturer.set_result(b"111110400")
#     when(client_mock).read_gatt_char(MANUFACTURER_UUID).thenReturn(read_manufacturer)

#     when(client_mock).connect(timeout=60).thenReturn(connect)

#     return client_mock


class TestValveZone:
    def test_zone_update_state(self, client_mock):
        device = Device(mac=TEST_UUID)

        device.zone1.update_state(zone_manual_setting_bytes, VALVE_MANUAL_SETTINGS_UUID)

        assert device.zone1.is_watering == True
        assert device.zone1.manual_watering_minutes == 5

    def test_zone_properties(self, client_mock):
        device = Device(mac=TEST_UUID)

        device.zone1.is_watering = True

        assert device.zone1.manual_watering_minutes == 20

    def test_zone_defaults(self, client_mock):
        device = Device(mac=TEST_UUID)

        zone = Valve(0, device)

        assert zone.is_watering == False
        assert zone.manual_watering_minutes == 20

    def test_zone_byte_payload(self, client_mock):
        device = Device(mac=TEST_UUID)
        zone = Valve(0, device)

        zone.is_watering = True
        zone.manual_watering_minutes = 10

        assert zone._manual_setting_bytes() == b"\x01\x00\n\x00\n"  # type: ignore


class TestDevice:
    @pytest.mark.asyncio()
    async def test_properties(self, client_mock):

        client_mock({MANUFACTURER_UUID: b"111110400"})

        device = Device(mac=TEST_UUID)

        await device.connect()

        assert device.name == "4 Valve Timer"
        assert device.model == "11111"
        assert device.mac == TEST_UUID
        assert device.valve_count == 4

    @pytest.mark.asyncio()
    async def test_get_item(self, client_mock):
        client_mock({MANUFACTURER_UUID: b"111110400"})

        device = Device(mac=TEST_UUID)

        await device.connect()

        assert device["zone1"] is device.zone1
        assert device["zone2"] is device.zone2
        assert device["zone3"] is device.zone3
        assert device["zone4"] is device.zone4

    @pytest.mark.asyncio()
    async def test_1_valve_device(self, client_mock):

        client_mock({MANUFACTURER_UUID: b"111110100"})

        device = Device(mac=TEST_UUID)

        await device.connect()

        assert device.zone1 is not None
        assert device.zone2 is None
        assert device.zone3 is None
        assert device.zone4 is None

    @pytest.mark.asyncio()
    async def test_2_valve_device(self, client_mock):

        client_mock(read={MANUFACTURER_UUID: b"111110200"})

        device = Device(mac=TEST_UUID)

        await device.connect()

        assert device.zone1 is not None
        assert device.zone2 is not None
        assert device.zone3 is None
        assert device.zone4 is None

    @pytest.mark.asyncio()
    async def test_1_valve_has_all_bytes(self, client_mock):

        client_mock(read={MANUFACTURER_UUID: b"111110100"})

        device = Device(mac=TEST_UUID)

        await device.connect()

        device.zone1.is_watering = True
        device.zone1.manual_watering_minutes = 10

        assert (
            (
                device._valves[0]._manual_setting_bytes()  # type:ignore
                + device._valves[1]._manual_setting_bytes()  # type:ignore
                + device._valves[2]._manual_setting_bytes()  # type:ignore
                + device._valves[3]._manual_setting_bytes()  # type:ignore
            )
            == b"\x01\x00\n\x00\n\x00\x00\x14\x00\x14\x00\x00\x14\x00\x14\x00\x00\x14\x00\x14"  # noqa: E501
        )

    @pytest.mark.asyncio()
    async def test_1_valve_has_internal_valves(self, client_mock):

        client_mock(read={MANUFACTURER_UUID: b"111110100"})

        device = Device(mac=TEST_UUID)

        await device.connect()

        device.zone1.is_watering = True
        device.zone1.manual_watering_minutes = 10

        assert device.zone1 is not None
        assert device.zone2 is None
        assert device.zone3 is None
        assert device.zone4 is None

        assert device._valves[1] is not None  # type:ignore
        assert device._valves[2] is not None  # type:ignore
        assert device._valves[3] is not None  # type:ignore

    @pytest.mark.asyncio()
    async def test_device_connect_lock(self, connect_mock, client_mock):
        client_mock(read={MANUFACTURER_UUID: b"111110100"})

        device = Device(mac=TEST_UUID)

        # We'll verify we only call the bleak client connect once
        loop = asyncio.get_event_loop()
        one = loop.create_task(device.connect())
        two = loop.create_task(device.connect())
        three = loop.create_task(device.connect())
        four = loop.create_task(device.connect())

        # await the tasks to ensure they're done
        await asyncio.gather(one, two, three, four)

        assert connect_mock.mock_calls.__len__() == 1

    @pytest.mark.asyncio()
    async def test_device_connect_noop_when_connected(self, mocker):

        device = Device(mac=TEST_UUID)

        success = asyncio.Future()
        success.set_result(True)

        bleak_mock = AsyncMock(spec=BleakClient)
        mocker.patch("bleak.BleakClient.connect", return_value=success)
        mocker.patch("bleak.BleakClient", new=AsyncMock(spec=bleak_mock))

        await device.connect()
        await device.connect()
        await device.connect()
        await device.connect()

    @freezegun.freeze_time(datetime.datetime.now(tz=ZoneInfo("UTC")))
    @pytest.mark.asyncio()
    async def test_fetch(self, client_mock):
        device = Device(mac=TEST_UUID)

        client_mock(
            read={
                BATTERY_UUID: b"\x02\x85",
                MANUFACTURER_UUID: b"111110400",
                VALVE_MANUAL_SETTINGS_UUID: struct.pack(
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
                ),
                VALVE_MANUAL_STATES_UUID: struct.pack(
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
                ),
            }
        )

        await device.connect()

        await device.fetch_state()

        assert device.battery_level == 30
        # assert device.brand == MELNOR

        assert device.zone1.is_watering is False
        assert device.zone1.manual_watering_minutes == 0
        # TODO: Test this more aggressively in date utils
        assert device.zone1.watering_end_time != 0

        assert device.zone2 is not None
        assert device.zone2.is_watering is False
        assert device.zone2.manual_watering_minutes == 0
        assert device.zone2.watering_end_time == 0

        assert device.zone3 is not None
        assert device.zone3.is_watering is False
        assert device.zone3.manual_watering_minutes == 0
        assert device.zone3.watering_end_time == 0

        assert device.zone4 is not None
        assert device.zone4.is_watering is False
        assert device.zone4.manual_watering_minutes == 0
        assert device.zone4.watering_end_time == 0

    def test_str(self, snapshot):
        device = Device(mac=TEST_UUID)

        actual = device.__str__()

        assert actual == snapshot
