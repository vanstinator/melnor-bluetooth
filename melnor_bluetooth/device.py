import asyncio
import struct
import sys
from typing import Any

from bleak import BleakClient, BleakError
from tzlocal import get_localzone

from melnor_bluetooth.parser.date import get_timestamp

from .constants import (
    BATTERY_CHARACTERISTIC_UUID,
    GATEWAY_ON_OFF_CHARACTERISTIC_UUID,
    UPDATED_AT_CHARACTERISTIC_UUID,
)
from .parser.battery import parse_battery_value


class Valve:

    _device: Any
    _id: int
    _is_watering: int
    _manual_watering_minutes: int

    def __init__(self, id: int, device) -> None:
        self._device = device
        self._id = id
        self._is_watering = False
        self._manual_watering_minutes = 20

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

        self._is_watering = bytes[self._id * 5]

        self._manual_watering_minutes = (bytes[(self._id * 5) + 1] * 256) + bytes[
            self._id * 5 + 2
        ]

    @property
    def is_watering(self) -> bool:
        """Returns whether the zone is currently watering"""
        return self._is_watering == 1

    @is_watering.setter
    def is_watering(self, value: bool) -> None:
        """Sets the watering state of the zone"""
        self._is_watering = 1 if value else 0

    @property
    def manual_watering_minutes(self) -> int:
        """Returns the number of seconds the zone has been manually watering for"""
        return self._manual_watering_minutes

    @manual_watering_minutes.setter
    def manual_watering_minutes(self, value: int) -> None:
        """Set the number of seconds the zone should manually watering for"""
        self._manual_watering_minutes = value

    @property
    def byte_payload(self) -> list[int]:
        """Returns the 5 byte payload to be written to the device"""

        return [
            self._is_watering,
            self._manual_watering_minutes >> 8,
            self._manual_watering_minutes & 255,
            self._manual_watering_minutes >> 8,
            self._manual_watering_minutes & 255,
        ]


class Device:

    _connection: BleakClient
    _is_connected: bool = False
    _mac: str
    _valves: list[Valve] = []

    def __init__(self, mac: str) -> None:
        self._mac = mac

        # TODO we need to figure out where to find the valve count
        self._valves = [Valve(0, self), Valve(1, self), Valve(2, self), Valve(3, self)]

    def disconnected_callback(self, client):
        print("Disconnected from:", self._mac)

        loop = asyncio.get_event_loop()
        loop.create_task(self.connect())

    async def connect(self) -> None:

        try:
            print("Connecting to:", self._mac)
            self._connection = BleakClient(
                self._mac, disconnected_callback=self.disconnected_callback
            )

            await self._connection.connect()
            self._is_connected = True
            print("Success:", self._mac)

        except BleakError:
            print("Failed to connect to:", self._mac)
            self._is_connected = False

            if "unittest" not in sys.modules.keys():
                await asyncio.sleep(5)

            print("Retrying...")
            await self.connect()

    async def disconnect(self) -> None:
        await self._connection.disconnect()

    async def fetch_state(self) -> None:
        """Updates the state of the device with the given bytes"""

        state = await self._connection.read_gatt_char(
            GATEWAY_ON_OFF_CHARACTERISTIC_UUID
        )

        for valve in self._valves:
            valve.update_state(state)

    async def push_state(self) -> None:
        """Pushes the state of the device to the device"""

        onOff = self._connection.services.get_characteristic(
            GATEWAY_ON_OFF_CHARACTERISTIC_UUID
        )

        await self._connection.write_gatt_char(
            onOff.handle,
            bytes(
                self._valves[0].byte_payload
                + self._valves[1].byte_payload
                + self._valves[2].byte_payload
                + self._valves[3].byte_payload
            ),
            True,
        )

        updatedAt = self._connection.services.get_characteristic(
            UPDATED_AT_CHARACTERISTIC_UUID
        )

        await self._connection.write_gatt_char(
            updatedAt.handle, struct.pack(">i", get_timestamp(get_localzone())), True
        )

    @property
    def is_connected(self) -> bool:
        """Returns whether the device is currently connected"""
        return self._is_connected

    @property
    def zone1(self) -> Valve:
        return self._valves[0]

    @property
    def zone2(self) -> Valve:
        return self._valves[1]

    @property
    def zone3(self) -> Valve:
        return self._valves[2]

    @property
    def zone4(self) -> Valve:
        return self._valves[3]

    # async def get_battery_life(self) -> int:
    #     battery_characteristic = self._connection.getCharacteristics(
    #         uuid=BATTERY_CHARACTERISTIC_UUID
    #     )[0]
    # return get_batt_val(battery_characteristic.read())
