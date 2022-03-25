import asyncio
import datetime
import struct
from calendar import c
from time import time

from bleak import BleakClient, BleakScanner

try:
    import zoneinfo  # type: ignore
except ImportError:
    from backports import zoneinfo

from melnor_bt.constants import (
    BATTERY_CHARACTERISTIC_UUID,
    GATEWAY_ON_OFF_CHARACTERISTIC_UUID,
    MAX_UNSIGNED_INTEGER,
    UPDATED_AT_CHARACTERISTIC_UUID,
)

address = "FDBC1347-8D0B-DB0E-8D79-7341E825AC2A"


def timeOffset():
    """Returns the archaic timezone offset in seconds that the device uses as a monotonic clock for operations"""

    base_time = datetime.datetime.now(tz=zoneinfo.ZoneInfo("Asia/Shanghai"))
    local_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

    print("base_time:", base_time)
    print("local_time:", local_time)

    base_offset = base_time.utcoffset()
    local_offset = local_time.utcoffset()

    if base_time.dst() is not None and base_time.dst() != 0:
        base_offset = base_offset - base_time.dst()  # type: ignore
        print("base_offset:", base_offset)

    if local_time.dst() is not None and local_time.dst() != 0:
        local_offset = local_offset - local_time.dst()  # type: ignore
        print("local_offset:", local_offset)

    print(base_offset.total_seconds() - local_offset.total_seconds())  # type: ignore

    return base_offset.total_seconds() - local_offset.total_seconds()  # type: ignore


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

            current_time = int(time() + (-timeOffset() - 946656000))

            updated = await client.read_gatt_char(updatedAt.handle)

            print(int(time()))
            print(current_time)
            print(int.from_bytes(updated, "big"))

            await client.write_gatt_char(
                updatedAt.handle, struct.pack(">i", current_time), True
            )

    except Exception as e:
        print(e)
    finally:
        await client.disconnect()


asyncio.run(main())
