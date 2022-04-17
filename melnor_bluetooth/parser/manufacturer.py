from melnor_bluetooth.constants import MELNOR


def parse_manufacturer(bytes: bytes) -> str:
    """Converts the little endian 2 byte array to the battery life %"""

    string = bytes.decode("utf-8")

    if string.startswith("ML_"):
        return MELNOR

    return string
