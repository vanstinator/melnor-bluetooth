import asyncio
from typing import Callable, Dict, Type, TypedDict

import pytest
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from mockito import ANY, mock, spy, verify, when

import melnor_bluetooth.scanner as scanner_module
from melnor_bluetooth.scanner import _callback, scanner


async def unrecognized_ble(callback: Callable[[str], None]):
    device = BLEDevice(
        address="00:00:00:00:00:00",
        rssi=0,
        name="Something else",
        manufacturer_data={47: b"\x00\x00\x00\x00\x00\x00\x00\x00"},
    )

    advertisement_data = AdvertisementData(
        local_name=device.name,
        manufacturer_data=device.metadata["manufacturer_data"],
    )

    return _callback(device, advertisement_data, callback)


async def recognized_ble(callback: Callable[[str], None]):
    device = BLEDevice(
        address="00:00:00:00:00:00",
        rssi=0,
        name="YM Timer",
        manufacturer_data={13: b"\x59\x08"},
    )

    advertisement_data = AdvertisementData(
        local_name=device.name,
        manufacturer_data=device.metadata["manufacturer_data"],
    )

    return _callback(device, advertisement_data, callback)


class ScanOptions(TypedDict):
    address: str
    manufacturer_data: Dict[int, bytes]
    name: str
    rssi: int


async def ble_response(callback: Callable[[str], None], options: ScanOptions):
    device = BLEDevice(
        address=options["address"],
        rssi=options["rssi"],
        name=options["name"],
        manufacturer_data=options["manufacturer_data"],
    )

    advertisement_data = AdvertisementData(
        local_name=device.name,
        manufacturer_data=device.metadata["manufacturer_data"],
    )

    _callback(device, advertisement_data, callback)


@pytest.fixture
def scanner_mock() -> Type:

    scanner_mock = mock(spec=BleakScanner)

    when(scanner_module).BleakScanner().thenReturn(scanner_mock)

    start = asyncio.Future()
    start.set_result(None)
    when(scanner_mock).start().thenReturn(start)

    stop = asyncio.Future()
    stop.set_result(None)
    when(scanner_mock).stop().thenReturn(stop)

    callback = asyncio.Future()
    callback.set_result(None)
    when(scanner_mock).register_detection_callback(ANY).thenReturn(callback)

    return scanner_mock


class TestScanner:
    async def test_scanner_expected_device(self, scanner_mock):
        def cb(address: str):
            assert address is not None

        callback = spy(cb)

        when(scanner_mock).start().thenReturn(
            ble_response(
                callback,
                {
                    "address": "00:00:00:00:00:00",
                    "manufacturer_data": {13: b"\x59\x08"},
                    "name": "YM Timer",
                    "rssi": 0,
                },
            )
        )

        await scanner(callback)

        verify(callback, times=1).__call__(ANY)

        assert callback

    async def test_scanner_unexpected_device(self, scanner_mock):
        """Test that a device that is not recognized by the scanner is not added"""

        def cb(address: str):
            assert address is not None

        callback = spy(cb)

        when(scanner_mock).start().thenReturn(
            ble_response(
                callback,
                {
                    "address": "00:00:00:00:00:00",
                    "manufacturer_data": {47: b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                    "name": "Something Else",
                    "rssi": 0,
                },
            )
        )

        await scanner(callback)

        assert callback

    async def test_scanner_malformed_device(self, scanner_mock):
        def cb(address: str):
            assert address is not None

        callback = spy(cb)

        when(scanner_mock).start().thenReturn(
            ble_response(
                callback,
                {
                    "address": "00:00:00:00:00:00",
                    "manufacturer_data": {13: b"\x00\x00\x00\x00\x00\x00\x00\x00"},
                    "name": "YM Timer",
                    "rssi": 0,
                },
            )
        )

        await scanner(callback)

        assert callback
