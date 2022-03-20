import datetime
from time import sleep, time

from melnor_bt.parser.battery import get_batt_val

try:
    import zoneinfo  # type: ignore
except ImportError:
    from backports import zoneinfo

from bluepy import btle

from melnor_bt.constants import (
    BATTERY_CHARACTERISTIC_UUID,
    DEVICE_USER_NAME_CHARACTERISTIC_UUID,
    GATEWAY_ON_OFF_CHARACTERISTIC_UUID,
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

# test = dev.getCharacteristics(uuid="0000ec0b-0000-1000-8000-00805f9b34fb")[0].read()
# print(f"Test: {test}")

# print(
#     binascii.b2a_hex(
#         bytes(
#             [
#                 0x00,
#                 0x01,
#                 0x68,
#                 0x01,
#                 0x68,
#                 0x00,
#                 0x00,
#                 0x14,
#                 0x00,
#                 0x00,
#                 0x00,
#                 0x00,
#                 0x5A,
#                 0x00,
#                 0x5A,
#                 0x00,
#                 0x00,
#                 0x1E,
#                 0x00,
#                 0x1E,
#             ]
#         ),
#     ).decode("utf-8")
# )

# r = dev.getServiceByUUID("ec00")
# for char in r.getCharacteristics():
#     if char.uuid == DEVICE_USER_NAME_CHARACTERISTIC_UUID:
#         d_name = char.read()
#         print(f"Device name: {d_name}")
# print(char.uuid)
# print(char.read())

onOff = dev.getCharacteristics(uuid=GATEWAY_ON_OFF_CHARACTERISTIC_UUID)[0]

# print(onOff.getHandle())
# dev.writeCharacteristic(
#     handle=onOff.getHandle(),
#     val=bytes(
#         [
#             0x00,
#             0x01,
#             0x68,
#             0x01,
#             0x68,
#             0x00,
#             0x00,
#             0x14,
#             0x00,
#             0x00,
#             0x00,
#             0x00,
#             0x5A,
#             0x00,
#             0x5A,
#             0x00,
#             0x00,
#             0x1E,
#             0x00,
#             0x1E,
#         ],
#     ),
#     withResponse=True,
# )


# updated = dev.getCharacteristics(uuid="ec09")[0]
# dev.writeCharacteristic(
#     handle=updated.getHandle(), val=curTime.to_bytes(byteorder="big", length=4)
# )

# sleep(10)

# print(int.from_bytes(0x05, byteorder="big"))

timeOffset()

dev.writeCharacteristic(
    handle=onOff.getHandle(),
    val=bytes(
        [
            0x01,
            0x01,
            0x68,
            0x01,
            0x68,
            0x00,
            0x00,
            0x14,
            0x00,
            0x00,
            0x00,
            0x00,
            0x5A,
            0x00,
            0x5A,
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
