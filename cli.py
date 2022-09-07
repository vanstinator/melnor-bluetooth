import asyncio
import logging
import sys
from typing import List

import aioconsole
from bleak.backends.device import BLEDevice

from melnor_bluetooth.device import Device, Valve
from melnor_bluetooth.scanner import scanner
from melnor_bluetooth.utils.formatter import CustomFormatter

logging.basicConfig(level=logging.DEBUG)
logging.getLogger().handlers[0].setFormatter(CustomFormatter())
logging.getLogger("bleak").setLevel(logging.WARNING)

devices: List[Device] = []

_LOGGER = logging.getLogger(__name__)


def detection_callback(ble_device: BLEDevice):

    address = ble_device.address

    has_device = [d for d in devices if d.mac == address]

    if len(has_device) == 0:
        device = Device(ble_device)
        devices.append(device)
        _LOGGER.info("Found device %s", device.mac)


async def main():

    await scanner(detection_callback, scan_timeout_seconds=10)

    if len(devices) == 0:
        _LOGGER.warning("No devices found")
        return

    device = devices[0]

    await device.connect()

    while True:

        await device.fetch_state()

        # Take user input
        line = await aioconsole.ainput(
            "Format command as [zone, state, minutes] i.e. '1, on, 10'"
            + "\nOr 'd' to disconnect:\n"
        )

        if line != "d":
            args = line.split(",")
            zone = args[0]
            minutes = None
            state = None

            if len(args) > 1:
                state = args[1]

            if len(args) > 2:
                minutes = int(args[2])

            valve = device[f"zone{zone}"]
            if valve is None:
                _LOGGER.warning("Zone %s not found", zone)
                continue

            _LOGGER.info("Setting zone %s to %s for %s minutes", zone, state, minutes)
            if minutes is not None:
                await valve.async_update_prop(Valve.manual_watering_minutes, int(1))

            if state is None:
                await valve.async_update_prop(Valve.is_watering, not valve.is_watering)
            else:
                await valve.async_update_prop(Valve.is_watering, state == "on")

            await device.push_state()

        elif line == "d":
            await device.disconnect()
            sys.exit(0)
        else:
            _LOGGER.error("Invalid command")

        await device.push_state()
        continue


asyncio.run(main())
