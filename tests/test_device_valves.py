# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

import datetime
import struct
from unittest.mock import AsyncMock, Mock, patch
from zoneinfo import ZoneInfo

import freezegun
import pytest
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClient  # type: ignore - this is a valid import

from melnor_bluetooth.constants import (
    BATTERY_UUID,
    MANUFACTURER_UUID,
    VALVE_0_MODE_UUID,
    VALVE_1_MODE_UUID,
    VALVE_2_MODE_UUID,
    VALVE_3_MODE_UUID,
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


@pytest.fixture(name="mocked_ble_device")
def fixture_mocked_ble_device() -> BLEDevice:
    """Mocks a BLEDevice object"""

    ble_device = Mock(spec=BLEDevice)
    ble_device.address = TEST_UUID
    ble_device.details = {"name": "Test"}
    ble_device.rssi = 6

    ble_device.set_disconnected_callback = Mock()

    return ble_device


def mocked_bleak_client(
    manufacturer_bytes: bytes = b"111110400",
    valve_manual_settings_bytes: bytes = struct.pack(
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
    valve_manual_states_bytes: bytes = struct.pack(
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
    valve_frequency_bytes: bytes = struct.pack(">BIHB", 0, 333333, 10, 10),
):
    """Mock a BleakClient"""

    bleak_client = Mock(spec=BleakClient)

    # Services
    bleak_client.services = Mock()
    gatt_service = Mock(spec=BleakGATTCharacteristic)
    gatt_service.handle = 1
    bleak_client.services.get_characteristic = Mock(return_value=gatt_service)

    # Read/Write Characteristics
    def read_gatt_char_side_effect(*args):
        if args[0] == VALVE_MANUAL_SETTINGS_UUID:
            return valve_manual_settings_bytes
        if args[0] == VALVE_MANUAL_STATES_UUID:
            return valve_manual_states_bytes
        if args[0] == BATTERY_UUID:
            return b"\x02\x85"
        if args[0] == MANUFACTURER_UUID:
            return manufacturer_bytes
        if (
            args[0] == VALVE_0_MODE_UUID
            or args[0] == VALVE_1_MODE_UUID
            or args[0] == VALVE_2_MODE_UUID
            or args[0] == VALVE_3_MODE_UUID
        ):
            return valve_frequency_bytes

    bleak_client.read_gatt_char = AsyncMock(side_effect=read_gatt_char_side_effect)
    bleak_client.write_gatt_char = AsyncMock()

    return bleak_client


def patch_establish_connection(bleak_client: BleakClient = mocked_bleak_client()):
    return patch(
        "melnor_bluetooth.device.establish_connection",
        return_value=bleak_client,
    )


class TestValveZone:
    async def test_zone_update_state(self, mocked_ble_device):
        with patch_establish_connection():
            device = Device(ble_device=mocked_ble_device)
            await device.connect()

            device.zone1.update_state(
                zone_manual_setting_bytes, VALVE_MANUAL_SETTINGS_UUID
            )

            assert device.zone1.is_watering is True
            assert device.zone1.manual_watering_minutes == 5

    async def test_atomic_zone_setters(self, mocked_ble_device):
        with patch_establish_connection():
            device = Device(ble_device=mocked_ble_device)
            await device.connect()

            await device.zone1.set_is_watering(True)

            assert device.zone1.manual_watering_minutes == 20

    async def test_zone_properties(self, mocked_ble_device):
        with patch_establish_connection():
            device = Device(ble_device=mocked_ble_device)
            await device.connect()

            device.zone1.is_watering = True
            device.zone1.manual_watering_minutes = 10

            assert device.zone1.manual_watering_minutes == 10

    async def test_zone_defaults(self, mocked_ble_device):
        with patch_establish_connection():
            device = Device(ble_device=mocked_ble_device)
            await device.connect()

            zone = Valve(0, device)

            assert zone.is_watering is False
            assert zone.manual_watering_minutes == 20

    async def test_zone_byte_payload(self, mocked_ble_device):
        with patch_establish_connection():
            device = Device(ble_device=mocked_ble_device)
            await device.connect()

            zone = Valve(0, device)

            await zone.set_is_watering(True)
            await zone.set_manual_watering_minutes(10)

            # pylint: disable=protected-access
            assert zone._manual_setting_bytes() == b"\x01\x00\n\x00\n"


class TestDevice:
    async def test_properties(self, mocked_ble_device):
        with patch_establish_connection():
            device = Device(ble_device=mocked_ble_device)
            await device.connect()

            assert device.name == "4 Valve Timer"
            assert device.model == "11111"
            assert device.mac == TEST_UUID
            assert device.valve_count == 4
            assert device.rssi == mocked_ble_device.rssi

    async def test_get_item(self, mocked_ble_device):
        with patch_establish_connection():
            device = Device(ble_device=mocked_ble_device)

            await device.connect()

            assert device["zone1"] is device.zone1
            assert device["zone2"] is device.zone2
            assert device["zone3"] is device.zone3
            assert device["zone4"] is device.zone4

    async def test_1_valve_device(self, mocked_ble_device):
        with patch_establish_connection(
            mocked_bleak_client(manufacturer_bytes=b"111110100")
        ):
            device = Device(ble_device=mocked_ble_device)

            await device.connect()

            assert device.zone1 is not None
            assert device.zone2 is None
            assert device.zone3 is None
            assert device.zone4 is None

    async def test_2_valve_device(self, mocked_ble_device):
        with patch_establish_connection(
            mocked_bleak_client(manufacturer_bytes=b"111110200")
        ):
            device = Device(ble_device=mocked_ble_device)

            await device.connect()

            assert device.zone1 is not None
            assert device.zone2 is not None
            assert device.zone3 is None
            assert device.zone4 is None

    async def test_1_valve_has_all_bytes(self, mocked_ble_device):
        with patch_establish_connection(
            mocked_bleak_client(manufacturer_bytes=b"111110200")
        ):
            device = Device(ble_device=mocked_ble_device)

            await device.connect()

            await device.zone1.set_is_watering(True)
            await device.zone1.set_manual_watering_minutes(10)

            assert (
                (
                    # pylint: disable=protected-access
                    # pylint: disable=line-too-long
                    device._valves[0]._manual_setting_bytes()
                    + device._valves[1]._manual_setting_bytes()
                    + device._valves[2]._manual_setting_bytes()
                    + device._valves[3]._manual_setting_bytes()
                )
                == b"\x01\x00\n\x00\n\x00\x00\x14\x00\x14\x00\x00\x14\x00\x14\x00\x00\x14\x00\x14"  # noqa: E501
            )

    async def test_1_valve_has_internal_valves(self, mocked_ble_device):
        with patch_establish_connection(
            mocked_bleak_client(manufacturer_bytes=b"111110100")
        ):
            device = Device(ble_device=mocked_ble_device)

            await device.connect()

            await device.zone1.set_is_watering(True)
            await device.zone1.set_manual_watering_minutes(10)

            assert device.zone1 is not None
            assert device.zone2 is None
            assert device.zone3 is None
            assert device.zone4 is None

            # pylint: disable=protected-access
            assert device._valves[1] is not None
            assert device._valves[2] is not None
            assert device._valves[3] is not None

    async def test_device_connect_noop_when_connected(self, mocked_ble_device):
        with patch_establish_connection() as mocked_establish_connection:
            device = Device(ble_device=mocked_ble_device)

            await device.connect()
            await device.connect()
            await device.connect()
            await device.connect()

            assert mocked_establish_connection.call_count == 1

    @freezegun.freeze_time(datetime.datetime.now(tz=ZoneInfo("UTC")))
    async def test_fetch(self, mocked_ble_device):
        with patch_establish_connection():
            device = Device(ble_device=mocked_ble_device)

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

    async def test_str(self, snapshot, mocked_ble_device):
        device = Device(ble_device=mocked_ble_device)

        actual = str(device)

        assert actual == snapshot
