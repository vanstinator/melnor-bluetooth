# See _getBattValue from DataUtils.java
def get_batt_val(bytes: bytes) -> int:

    print(bytes)
    print(bytes[0] & 255)

    """Converts the little endian 2 byte array to the battery life %"""
    if (bytes[0] & 255 == 238) and (bytes[1] & 255 == 238):
        return 0
    else:
        rawVal = (
            ((bytes[0] & 255) + (bytes[1] & 255) / 256) - 2.35
        ) * 181.81818181818187

        if rawVal > 100:
            return 100

        if rawVal > 0:
            return int(rawVal)

        return int(rawVal)
