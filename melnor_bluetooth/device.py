import asyncio
import struct
import sys
from typing import Any

from bleak import BleakClient, BleakError

from melnor_bluetooth.parser.date import get_timestamp, time_shift

from .constants import (
    UPDATED_AT_UUID,
    VALVE_MANUAL_SETTINGS_UUID,
    VALVE_MANUAL_STATES_UUID,
)


class Valve:

    _device: Any
    _id: int
    _is_watering: bool
    _manual_minutes: int

    def __init__(self, id: int, device) -> None:
        self._device = device
        self._id = id
        self._is_watering = False
        self._manual_minutes = 20
        self._end_time = 0

    def update_state(self, bytes: bytes, uuid: str) -> None:

        offset = self._id * 5

        if uuid == VALVE_MANUAL_SETTINGS_UUID:
            """Parses a 5 byte segment from the device and updates the state of the zone
            [
                0   - 0x00, # is_watering - boolean
                1-2 - 0x00, # manual_watering_time - unsigned short
                3-4 - 0x00, # duplicate of byte 1
            ]
            """

            self._is_watering = struct.unpack_from(">?", bytes, offset)[0]
            self._manual_minutes = struct.unpack_from(">H", bytes, offset + 1)[0]

        elif uuid == VALVE_MANUAL_STATES_UUID:
            """byte segment for manual watering time left
            [
                0   - 0x00, # unclear, 0-2
                1-4 - 0x00, # timestamp - unsigned int
            ]
            """
            parsed_time = self._end_time = struct.unpack_from(">I", bytes, offset + 1)[
                0
            ]

            self._end_time = parsed_time - time_shift() if parsed_time != 0 else 0

    @property
    def is_watering(self) -> bool:
        """Returns whether the zone is currently watering"""
        return self._is_watering == 1

    @is_watering.setter
    def is_watering(self, value: bool) -> None:
        """Sets the watering state of the zone"""
        self._is_watering = value

    @property
    def manual_minutes(self) -> int:
        """Returns the number of seconds the zone has been manually watering for"""
        return self._manual_minutes

    @manual_minutes.setter
    def manual_watering_minutes(self, value: int) -> None:
        """Set the number of seconds the zone should manually watering for"""
        self._manual_minutes = value

    @property
    def watering_end_time(self) -> int:
        """Unix timestamp in seconds when watering will end"""
        return self._end_time

    @property
    def manual_setting_bytes(self) -> bytes:
        """Returns the 5 byte payload to be written to the device"""

        return struct.pack(
            ">?HH",
            self._is_watering,
            self._manual_minutes,
            self._manual_minutes,
        )

    def __str__(self) -> str:
        return (
            f"      Valve(id={self._id}|"
            + f"is_watering={self._is_watering}|"
            + f"manual_minutes={self._manual_minutes}|"
            + f"seconds_left={self._end_time}"
            + ")"
        )


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

        uuids = [VALVE_MANUAL_SETTINGS_UUID, VALVE_MANUAL_STATES_UUID]

        bytes_array = await asyncio.gather(
            *[self._read(uuid) for uuid in uuids],
            return_exceptions=True,
        )

        for i, bytes in enumerate(bytes_array):
            for valve in self._valves:
                bytes = uuids.index(uuids[i])
                valve.update_state(bytes_array[bytes], uuids[i])

    async def _read(self, uuid: str) -> bytes:
        """Reads the given characteristic from the device"""

        return await self._connection.read_gatt_char(uuid)

    async def push_state(self) -> None:
        """Pushes the state of the device to the device"""

        onOff = self._connection.services.get_characteristic(VALVE_MANUAL_SETTINGS_UUID)

        await self._connection.write_gatt_char(
            onOff.handle,
            (
                self._valves[0].manual_setting_bytes
                + self._valves[1].manual_setting_bytes
                + self._valves[2].manual_setting_bytes
                + self._valves[3].manual_setting_bytes
            ),
            True,
        )

        updatedAt = self._connection.services.get_characteristic(UPDATED_AT_UUID)

        await self._connection.write_gatt_char(
            updatedAt.handle, struct.pack(">I", get_timestamp()), True
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

    def __str__(self) -> str:
        str = f"{self.__class__.__name__}(\n    valves=(\n"
        for valve in self._valves:
            str += f"{valve}\n"
        return f"{str}    )\n)"
