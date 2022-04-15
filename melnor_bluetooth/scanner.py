import asyncio
import sys
from typing import Callable, Dict, Tuple

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .device import Device

DeviceCallbackType = Callable[[Device], None]

# We don't use the sensors today but we might as well track it here so we have it
device_valve_count_sensor_map: Dict[str, Tuple[int, bool]] = {
    "5907": (4, True),
    "5908": (4, False),
    "5909": (2, True),
    "5910": (2, False),
    "5911": (1, True),
    "5912": (1, False),
}


def _callback(
    ble_device: BLEDevice,
    ble_advertisement_data: AdvertisementData,
    callback: DeviceCallbackType,
):
    # if advertisement_data.local_name is not None:
    #     if "YM Timer" in advertisement_data.local_name:

    if ble_advertisement_data.manufacturer_data.get(13) is not None:

        data = ble_advertisement_data.manufacturer_data[13]
        model_number = f"{data[0]:02x}{data[1]:02x}"

        print(
            f"Address: {ble_device.address}"
            + f" - Model Number: {model_number}"
            + f" - RSSI: {ble_device.rssi}"
        )

        model_info = device_valve_count_sensor_map.get(model_number)

        if model_info is None:
            # We don't know about this model number
            print(f"Unknown model number: {model_number}")
            return

        callback(
            Device(
                ble_device.address,
                model_info[0],
            )
        )


async def scanner(
    callback: DeviceCallbackType,
    scan_timeout_seconds=60,
):
    """
    Scan for devices.

    :param callback: Callback function.
    :param scan_timeout_seconds: Timeout in seconds. Default 60 seconds
    """

    scanner = BleakScanner()

    scanner.register_detection_callback(
        lambda BLEDevice, AdvertisementData: _callback(
            BLEDevice, AdvertisementData, callback
        )
    )

    await scanner.start()
    if "unittest" not in sys.modules.keys():
        await asyncio.sleep(scan_timeout_seconds)
    await scanner.stop()
