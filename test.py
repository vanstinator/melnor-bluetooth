import asyncio
import datetime
import struct
from zoneinfo import ZoneInfo

from bleak import BleakClient, BleakScanner

from melnor_bluetooth.constants import (
    BATTERY_CHARACTERISTIC_UUID,
    GATEWAY_ON_OFF_CHARACTERISTIC_UUID,
    MAX_UNSIGNED_INTEGER,
    UPDATED_AT_CHARACTERISTIC_UUID,
)
from melnor_bluetooth.parser.date import get_timestamp

address = "FDBC1347-8D0B-DB0E-8D79-7341E825AC2A"


async def main():
    # devices = await BleakScanner.discover()
    # for d in devices:
    #     print(d.address)
    client = BleakClient(address)
    try:
        await client.connect()
        model_number = await client.read_gatt_char(
            "00002a29-0000-1000-8000-00805f9b34fb"
        )
        if model_number is not None:
            print("model_number:", model_number)

            onOff = client.services.get_characteristic(
                GATEWAY_ON_OFF_CHARACTERISTIC_UUID
            )

            await client.write_gatt_char(
                onOff.handle,
                bytes(
                    [
                        # Valve 1
                        0x01,  # On/Off Control bit
                        0x01,  # runtime >> 8 - seems to control default setting and runtime
                        0x68,  # runtime & 255 - seems to control default setting and runtime
                        0x01,  # runtime >> 8 - does nothing?
                        0x68,  # runtime & 255 - does nothing?
                        # Valve 2
                        0x01,
                        (360 >> 8) & MAX_UNSIGNED_INTEGER,
                        360 & MAX_UNSIGNED_INTEGER,
                        (360 >> 8) & MAX_UNSIGNED_INTEGER,
                        360 & MAX_UNSIGNED_INTEGER,
                        # Valve 3
                        0x00,
                        0x00,
                        0x5A,
                        0x00,
                        0x5A,
                        # Valve 4
                        0x00,
                        0x00,
                        0x1E,
                        0x00,
                        0x1E,
                    ]
                ),
                True,
            )

            updatedAt = client.services.get_characteristic(
                UPDATED_AT_CHARACTERISTIC_UUID
            )

            print("updated_handle:", updatedAt.handle)

            print("get_timestamp:", get_timestamp())
            print("is int", isinstance(get_timestamp(), int))

            tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo

            print(tz)

            if tz is None:
                return

            await client.write_gatt_char(
                updatedAt.handle,
                struct.pack(">i", get_timestamp(tz)),
                True,
            )

    except Exception as e:
        print(e)
    finally:
        await client.disconnect()


asyncio.run(main())
