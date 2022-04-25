import asyncio
import sys
from typing import Callable

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

DeviceCallbackType = Callable[[str], None]

lock = asyncio.Lock()


def _callback(
    ble_device: BLEDevice,
    ble_advertisement_data: AdvertisementData,
    callback: DeviceCallbackType,
):
    if ble_advertisement_data.manufacturer_data.get(13) is not None:

        #  we need to ignore the aadvertisement data for now
        # https://github.com/vanstinator/melnor-bluetooth/issues/17
        # data = ble_advertisement_data.manufacturer_data[13]
        # model_number = f"{data[0]:02x}{data[1]:02x}"

        callback(ble_device.address)


async def scanner(
    callback: DeviceCallbackType,
    scan_timeout_seconds=60,
):
    """
    Scan for devices.

    :param callback: Callback function.
    :param scan_timeout_seconds: Timeout in seconds. Default 60 seconds
    """

    _scanner = BleakScanner()

    def _callback_wrapper(
        ble_device: BLEDevice,
        ble_advertisement_data: AdvertisementData,
    ):
        _callback(ble_device, ble_advertisement_data, callback)

    _scanner.register_detection_callback(_callback_wrapper)

    await _scanner.start()
    if "unittest" not in sys.modules.keys():
        await asyncio.sleep(scan_timeout_seconds)
    await _scanner.stop()
