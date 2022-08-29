""" Constants for Melnor Bluetooth. """


def _uuid(address: str) -> str:
    return f"0000{address}-0000-1000-8000-00805f9b34fb"


BATTERY_UUID = _uuid("ec08")
DEVICE_USER_NAME_UUID = _uuid("ec01")
UPDATED_AT_UUID = _uuid("ec09")
MODEL_NUMBER_UUID = _uuid("2a24")
MANUFACTURER_UUID = _uuid("2a29")

VALVE_MANUAL_SETTINGS_UUID = _uuid("ec0b")
VALVE_ON_OFF_UUID = _uuid("ec0a")

VALVE_MANUAL_STATES_UUID = _uuid("ec06")

VALVE_0_MODE_UUID = _uuid("ec0f")
VALVE_1_MODE_UUID = _uuid("ec10")
VALVE_2_MODE_UUID = _uuid("ec11")
VALVE_3_MODE_UUID = _uuid("ec12")

# Manufacturers
EDEN = "Eden"
MELNOR = "Melnor"


MODEL_BRAND_MAP = {
    "5901": EDEN,
    "5902": EDEN,
    "5903": EDEN,
    "5904": EDEN,
    "5905": EDEN,
    "5906": EDEN,
    "5907": MELNOR,
    "5908": MELNOR,
    "5909": MELNOR,
    "5910": MELNOR,
    "5911": MELNOR,
    "5912": MELNOR,
    "5913": EDEN,
    "5914": EDEN,
    "5915": EDEN,
    "5916": EDEN,
    "5917": EDEN,
    "5918": EDEN,
}

MODEL_NAME_MAP = {
    "5901": "25443",
    "5902": "25439",
    "5903": "25442",
    "5904": "25438",
    "5905": "25441",
    "5906": "25437",
    "5907": "93281",
    "5908": "93280",
    "5909": "93101",
    "5910": "93100",
    "5911": "93016",
    "5912": "93015",
    "5913": "25443",
    "5914": "25439",
    "5915": "25442",
    "5916": "25438",
    "5917": "25441",
    "5918": "25437",
}

MODEL_SENSOR_MAP = {
    "5901": True,
    "5902": False,
    "5903": True,
    "5904": False,
    "5905": True,
    "5906": False,
    "5907": True,
    "5908": False,
    "5909": True,
    "5910": False,
    "5911": True,
    "5912": False,
    "5913": True,
    "5914": False,
    "5915": True,
    "5916": False,
    "5917": True,
    "5918": False,
}

MODEL_VALVE_MAP = {
    "5901": 4,
    "5902": 4,
    "5903": 2,
    "5904": 2,
    "5905": 1,
    "5906": 1,
    "5907": 4,
    "5908": 4,
    "5909": 2,
    "5910": 2,
    "5911": 1,
    "5912": 1,
    "5913": 4,
    "5914": 4,
    "5915": 2,
    "5916": 2,
    "5917": 1,
    "5918": 1,
}
