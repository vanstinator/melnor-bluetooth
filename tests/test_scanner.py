import asyncio
from typing import Callable, Type

import pytest
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from mockito import ANY, mock, spy, verify, verifyZeroInteractions, when

import melnor_bluetooth.scanner as scanner_module
from melnor_bluetooth.device import Device
from melnor_bluetooth.scanner import _callback, scanner


async def unrecognized_ble(callback: Callable[[Device], None]):
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


async def recognized_ble(callback: Callable[[Device], None]):
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

    return scanner_mock


class TestScanner:
    async def test_scanner_expected_device(self, scanner_mock):
        def cb(device: Device):

            assert device is not None
            assert device.zone2 is not None

        callback = spy(cb)

        when(scanner_mock).start().thenReturn(recognized_ble(callback))

        await scanner(callback)

        verify(callback, times=1).__call__(ANY)

        assert callback

    async def test_scanner_unexpected_device(self, scanner_mock):
        def cb(device: Device):

            assert device is None
            assert device.zone2 is None

        callback = spy(cb)

        when(scanner_mock).start().thenReturn(unrecognized_ble(callback))

        await scanner(callback)

        verifyZeroInteractions(callback)

        assert callback
