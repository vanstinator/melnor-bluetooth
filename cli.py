import asyncio
import sys
from typing import List

import aioconsole
from bleak.backends.device import BLEDevice

from melnor_bluetooth.device import Device
from melnor_bluetooth.scanner import scanner

devices: List[Device] = []


def detection_callback(ble_device: BLEDevice):

    address = ble_device.address

    has_device = [d for d in devices if d.mac == address]

    if len(has_device) == 0:
        device = Device(address, ble_device)
        devices.append(device)
        print(f"Found device: {device.__str__()}")


async def main():

    await scanner(detection_callback, scan_timeout_seconds=10)

    if len(devices) == 0:
        print("No devices found")
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
                print(f"Zone {zone} not found")
                continue

            print(f"Setting zone {zone} to {state} for {minutes} minutes")
            if minutes is not None:
                valve.manual_watering_minutes = int(minutes)

            if state is None:
                valve.is_watering = not valve.is_watering
            else:
                valve.is_watering = state == "on"

            await device.push_state()

        elif line == "d":
            await device.disconnect()
            sys.exit(0)
        else:
            print("Invalid input")

        await device.push_state()
        continue


asyncio.run(main())
