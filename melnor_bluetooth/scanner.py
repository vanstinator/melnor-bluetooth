import asyncio
import sys
from typing import Callable

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from melnor_bluetooth.constants import MODEL_NAME_MAP, MODEL_SENSOR_MAP, MODEL_VALVE_MAP

from .device import Device

DeviceCallbackType = Callable[[Device], None]


def _callback(
    ble_device: BLEDevice,
    ble_advertisement_data: AdvertisementData,
    callback: DeviceCallbackType,
):
    if ble_advertisement_data.manufacturer_data.get(13) is not None:

        data = ble_advertisement_data.manufacturer_data[13]
        model_number = f"{data[0]:02x}{data[1]:02x}"

        print(
            f"Address: {ble_device.address}"
            + f" - Model Number: {model_number}"
            + f" - RSSI: {ble_device.rssi}"
        )

        model_name = MODEL_NAME_MAP.get(model_number)
        model_valves = MODEL_VALVE_MAP.get(model_number)
        model_sensors = MODEL_SENSOR_MAP.get(model_number)

        if model_name is None or model_valves is None or model_sensors is None:
            # We don't know about this model info
            print(
                "Missing required model info"
                + f" - name: {model_number}"
                + f" - valves: {model_valves}"
                + f" - sensors: {model_sensors}"
            )
            return

        callback(
            Device(
                mac=ble_device.address,
                name=model_name,
                sensor=model_sensors,
                valves=model_valves,
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
