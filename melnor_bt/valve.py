import struct

from bluepy import btle

from .constants import BATTERY_CHARACTERISTIC_UUID
from .parser.battery import get_batt_val


class Valve:

    _connection: btle.Peripheral
    _mac: str

    def __init__(self, mac: str) -> None:
        self._mac = mac

    async def connect(self) -> None:
        try:
            self._connection = btle.Peripheral(self._mac)
        except btle.BTLEDisconnectError:
            print("Could not connect to device")
            return

    async def disconnect(self) -> None:
        self._connection.disconnect()

    async def get_battery_life(self) -> int:
        battery_characteristic = self._connection.getCharacteristics(
            uuid=BATTERY_CHARACTERISTIC_UUID
        )[0]
        return get_batt_val(battery_characteristic.read())


class Zone:

    _id: int
    _is_watering: bool
    _manual_watering_seconds: int

    def __init__(self, id: int) -> None:
        self._id = id
        self._is_watering = False
        self._manual_watering_seconds = 20 * 60

    def update_state(self, bytes: bytes) -> None:
        """Parses a 5 byte response from the device and updates the state of the zone
        [
            0 - 0x00, # is_watering
            1 - 0x00, # number of max unsigned bytes (0-255) in the run time total
            2 - 0x00, # remainder of the run time total in seconds
            3 - 0x00, # see index 1
            4 - 0x00, # see index 2
        ]

        Get the watering total by multiplying the unpacked int in position 2 and adding the int in position 3
        """

        self._is_watering = bytes[self._id * 5] == 1

        self._manual_watering_seconds = (bytes[(self._id * 5) + 1] * 256) + bytes[
            self._id * 5 + 2
        ]

    @property
    def is_watering(self) -> bool:
        """Returns whether the zone is currently watering"""
        return self._is_watering

    @is_watering.setter
    def is_watering(self, value: bool) -> None:
        """Sets the watering state of the zone"""
        self._is_watering = value

    @property
    def manual_watering_seconds(self) -> int:
        """Returns the number of seconds the zone has been manually watering for"""
        return self._manual_watering_seconds

    @manual_watering_seconds.setter
    def manual_watering_seconds(self, value: int) -> None:
        """Set the number of seconds the zone should manually watering for"""
        self._manual_watering_seconds = value
