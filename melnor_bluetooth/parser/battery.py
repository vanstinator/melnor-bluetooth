# See _getBattValue from DataUtils.java
def parse_battery_value(bytes: bytes) -> int:
    """Converts the little endian 2 byte array to the battery life %"""
    if (bytes[0] & 255 == 238) and (bytes[1] & 255 == 238):
        return 0
    else:
        rawVal = (
            ((bytes[0] & 255) + (bytes[1] & 255) / 256) - 2.35
        ) * 181.81818181818187

        if rawVal > 100:
            return 100

        return int(rawVal)
