import asyncio
import struct

from bleak import BleakClient, BleakError
from mockito import ANY, verify, when

import melnor_bluetooth.device as device_module
from melnor_bluetooth.device import Device, Valve

zone_byte_payload = struct.pack(
    ">20B",
    # Zone 0
    1,
    1,
    104,
    1,
    104,
    # Zone 2
    0,
    0,
    23,
    0,
    23,
    # Zone 3
    0,
    0,
    42,
    0,
    42,
    # Zone 4
    1,
    0,
    13,
    0,
    13,
)


class TestValveZone:
    def test_zone_0_update_state(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")
        zone = Valve(0, device)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == True
        assert zone.manual_watering_minutes == 360

    def test_zone_1_update_state(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")
        zone = Valve(1, device)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == False
        assert zone.manual_watering_minutes == 23

    def test_zone_2_update_state(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")
        zone = Valve(2, device)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == False
        assert zone.manual_watering_minutes == 42

    def test_zone_3_update_state(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")
        zone = Valve(3, device)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == True
        assert zone.manual_watering_minutes == 13

    def test_zone_properties(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")
        zone = Valve(0, device)

        zone.is_watering = True
        zone.manual_watering_minutes = 10

        assert zone.is_watering == True
        assert zone.manual_watering_minutes == 10

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
    async def test_device_connect_retry(self):
        device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")

        failure = asyncio.Future()
        failure.set_exception(BleakError("Connection failed"))

        success = asyncio.Future()
        success.set_result(True)

        when(BleakClient).connect().thenReturn(failure).thenReturn(success)
        when(device_module).BleakClient(
            "FDBC1347-8D0B-DB0E-8D79-7341E825AC2A", disconnected_callback=ANY
        ).thenReturn(BleakClient)

        await device.connect()

        verify(BleakClient, times=2).connect()

    # @patch("melnor_bluetooth.device.BleakClient")
    # async def test_device_push_state(self, mock: MagicMock):

    #     mock.return_value = MockBleakClient("12345")

    #     device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")

    #     await device.connect()
    #     # await device.push_state()
    #     mock.assert_called_once_with("test")
