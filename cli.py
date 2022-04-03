import asyncio
import sys

import aioconsole

from melnor_bluetooth.device import Device

address = "FDBC1347-8D0B-DB0E-8D79-7341E825AC2A"


async def main():

    device = Device(address)

    await device.connect()

    while True:

        print(device.__str__())

        await device.fetch_state()

        # Take user input
        line = await aioconsole.ainput("on or off or d: ")

        if line == "on":
            device.zone1.is_watering = True
        elif line == "off":
            device.zone1.is_watering = False
        elif line == "d":
            await device.disconnect()
            sys.exit(0)
        else:
            print("Invalid input")

        await device.push_state()
        continue


asyncio.run(main())
