import datetime
from time import sleep, time

from melnor_bluetooth.parser.battery import get_batt_val

try:
    import zoneinfo  # type: ignore
except ImportError:
    from backports import zoneinfo

from bluepy import btle

from melnor_bluetooth.constants import (
    BATTERY_CHARACTERISTIC_UUID,
    DEVICE_USER_NAME_CHARACTERISTIC_UUID,
    GATEWAY_ON_OFF_CHARACTERISTIC_UUID,
    MAX_UNSIGNED_INTEGER,
)


def timeOffset():
    """Returns the archaic timezone offset in seconds that the device uses as a monotonic clock for operations"""

    base_time = datetime.datetime.now(tz=zoneinfo.ZoneInfo("Asia/Shanghai"))
    local_time = datetime.datetime.now(tz=zoneinfo.ZoneInfo("localtime"))

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


print("Connecting...")
dev = btle.Peripheral("58:93:D8:AC:9F:2A")

updated = dev.getCharacteristics(uuid="ec09")[0]

# print(b"\x29\xc8\xf9\x4c".decode("ascii"))
curTime = int(time() + (-timeOffset() - 946656000))

print(int(time()))
print(curTime)
print(int.from_bytes(updated.read(), "big"))


val = dev.getCharacteristics(uuid=BATTERY_CHARACTERISTIC_UUID)[0].read()
print(f"Battery life: {get_batt_val(val)}%")
print(f"Battery life: {val}%")


onOff = dev.getCharacteristics(uuid=GATEWAY_ON_OFF_CHARACTERISTIC_UUID)[0]

timeOffset()

value = 360
value2 = 20

from struct import *

dev.writeCharacteristic(
    handle=onOff.getHandle(),
    val=bytes(
        [
            # Valve 1
            0x01,  # On/Off Control bit
            0x01,  # runtime >> 8 - seems to control default setting and runtime
            0x68,  # runtime & 255 - seems to control default setting and runtime
            0x01,  # runtime >> 8 - does nothing?
            0x68,  # runtime & 255 - does nothing?
            # Valve 2
            0x01,
            (value2 >> 8) & MAX_UNSIGNED_INTEGER,
            value2 & MAX_UNSIGNED_INTEGER,
            (value >> 8) & MAX_UNSIGNED_INTEGER,
            value & MAX_UNSIGNED_INTEGER,
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
        ],
    ),
    withResponse=True,
)

dev.writeCharacteristic(
    handle=updated.getHandle(), val=curTime.to_bytes(byteorder="big", length=4)
)

# ",0x00,0x01,0x68,0x01,0x68,0x00,0x00,0x14,0x00,0x00,0x00,0x00,0x5a,0x00,0x5a,0x00,0x00,0x1e,0x00,0x1e"


# print("Services...")

# for char in dev.getCharacteristics():
#     print(char)

# for svc in dev.services:
#     print(svc)

dev.disconnect()


# import time
# from functools import partial, wraps


# def wrap(func):
#     @wraps(func)
#     async def run(*args, loop=None, executor=None, **kwargs):
#         if loop is None:
#             loop = asyncio.get_event_loop()
#         pfunc = partial(func, *args, **kwargs)
#         return await loop.run_in_executor(executor, pfunc)

#     return run


# @wrap
# def sleep_async(delay):
#     time.sleep(delay)
#     return "I slept asynchronously"
