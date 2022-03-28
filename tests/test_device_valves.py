import asyncio
import struct
from typing import Type

import pytest
from bleak import BleakClient, BleakError
from mockito import ANY, mock, verify, when

import melnor_bluetooth.device as device_module
from melnor_bluetooth.constants import GATEWAY_ON_OFF_CHARACTERISTIC_UUID
from melnor_bluetooth.device import Device, Valve

zone_byte_payload = struct.pack(
    ">20B",
    # Zone 0
    1,
    0,
    5,
    0,
    5,
    # Zone 2
    1,
    0,
    10,
    0,
    10,
    # Zone 3
    1,
    0,
    15,
    0,
    15,
    # Zone 4
    1,
    0,
    20,
    0,
    20,
)


@pytest.fixture
def client_mock() -> Type:
    connect = asyncio.Future()
    connect.set_result(True)

    client_mock = mock(spec=BleakClient)

    when(device_module).BleakClient(
        "FDBC1347-8D0B-DB0E-8D79-7341E825AC2A", disconnected_callback=ANY
    ).thenReturn(client_mock)

    when(client_mock).connect().thenReturn(connect)

    client_mock.__class__
    return client_mock


class TestValveZone:
    def test_zone_update_state(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")

        device.zone1.update_state(zone_byte_payload)

        assert device.zone1.is_watering == True
        assert device.zone1.manual_watering_minutes == 5

    def test_zone_properties(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")

        device.zone1.is_watering = True
        device.zone2.is_watering = True
        device.zone3.is_watering = True
        device.zone4.is_watering = True

        assert device.zone1.manual_watering_minutes == 20

    def test_zone_defaults(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")
        zone = Valve(0, device)

        assert zone.is_watering == False
        assert zone.manual_watering_minutes == 20

    def test_zone_byte_payload(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")
        zone = Valve(0, device)

        zone.is_watering = True
        zone.manual_watering_minutes = 10

        assert zone.byte_payload == [1, 0, 10, 0, 10]


class TestDevice:
    # async def test_device_connect_retry(self):
    #     device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")

    #     failure = asyncio.Future()
    #     failure.set_exception(BleakError("Connection failed"))

    #     success = asyncio.Future()
    #     success.set_result(True)

    #     when(BleakClient).connect().thenReturn(failure).thenReturn(success)
    #     when(device_module).BleakClient(
    #         "FDBC1347-8D0B-DB0E-8D79-7341E825AC2A", disconnected_callback=ANY
    #     ).thenReturn(BleakClient)

    #     await device.connect()

    #     verify(BleakClient, times=2).connect()

    # @patch("melnor_bluetooth.device.BleakClient")
    async def test_fetch(self, client_mock):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")

        read = asyncio.Future()
        read.set_result(
            struct.pack(
                ">20B",
                # Zone 0
                0,
                0,
                0,
                0,
                0,
                # Zone 2
                0,
                0,
                0,
                0,
                0,
                # Zone 3
                0,
                0,
                0,
                0,
                0,
                # Zone 4
                0,
                0,
                0,
                0,
                0,
            )
        )

        when(client_mock).read_gatt_char(GATEWAY_ON_OFF_CHARACTERISTIC_UUID).thenReturn(
            read
        )

        await device.connect()

        await device.fetch_state()

        verify(client_mock).read_gatt_char(GATEWAY_ON_OFF_CHARACTERISTIC_UUID)

        assert device.zone1.is_watering == False
        assert device.zone1.manual_watering_minutes == 0

        assert device.zone2.is_watering == False
        assert device.zone2.manual_watering_minutes == 0

        assert device.zone3.is_watering == False
        assert device.zone3.manual_watering_minutes == 0

        assert device.zone4.is_watering == False
        assert device.zone4.manual_watering_minutes == 0
