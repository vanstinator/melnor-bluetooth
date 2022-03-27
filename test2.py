import asyncio
import sys

import aioconsole

from melnor_bluetooth.constants import (
    BATTERY_CHARACTERISTIC_UUID,
    GATEWAY_ON_OFF_CHARACTERISTIC_UUID,
    MAX_UNSIGNED_INTEGER,
    UPDATED_AT_CHARACTERISTIC_UUID,
)
from melnor_bluetooth.device import Device
from melnor_bluetooth.parser.date import get_timestamp

address = "FDBC1347-8D0B-DB0E-8D79-7341E825AC2A"


async def main():

    device = Device(address)

    await device.connect()

    await device.fetch_state()

    while True:

        # Take an user input
        line = await aioconsole.ainput("on or off: ")

        if line == "on":
            device.zone1.is_watering = True
        elif line == "off":
            device.zone1.is_watering = False
        else:
            print("Invalid input")

        await device.push_state()
        continue

        # await device.push_state()

        # device.zone1.manual_watering_minutes = 200

    # device.zone2.manual_watering_minutes = 200
    # device.zone2.is_watering = watering

    # device.zone3.manual_watering_minutes = 200
    # device.zone3.is_watering = watering

    # device.zone4.manual_watering_minutes = 200
    # device.zone4.is_watering = watering


asyncio.run(main())
