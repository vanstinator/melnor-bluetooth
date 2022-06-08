import asyncio
import struct
from typing import Any, List, Union

from bleak import BleakClient, BleakError

from melnor_bluetooth.parser.battery import parse_battery_value
from melnor_bluetooth.parser.date import get_timestamp, time_shift

from .constants import (
    BATTERY_UUID,
    MANUFACTURER_UUID,
    UPDATED_AT_UUID,
    VALVE_MANUAL_SETTINGS_UUID,
    VALVE_MANUAL_STATES_UUID,
)

GLOBAL_BLUETOOTH_LOCK: asyncio.Lock = None  # type: ignore


def global_bluetooth_lock():
    """Initialize the global bluetooth lock inside the current event loop."""
    global GLOBAL_BLUETOOTH_LOCK  # pylint: disable=global-statement
    if GLOBAL_BLUETOOTH_LOCK is None:
        GLOBAL_BLUETOOTH_LOCK = asyncio.Lock()
    return GLOBAL_BLUETOOTH_LOCK


class Valve:

    _device: Any
    _id: int
    _is_watering: bool
    _manual_minutes: int

    def __init__(self, id: int, device) -> None:
        global_bluetooth_lock()

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
    def id(self) -> int:
        return self._id

    @property
    def is_watering(self) -> bool:
        """Returns whether the zone is currently watering"""
        return self._is_watering == 1

    @is_watering.setter
    def is_watering(self, value: bool) -> None:
        """Sets the watering state of the zone"""
        self._is_watering = value

    @property
    def manual_watering_minutes(self) -> int:
        """Returns the number of seconds the zone has been manually watering for"""
        return self._manual_minutes

    @manual_watering_minutes.setter
    def manual_watering_minutes(self, value: int) -> None:
        """Set the number of seconds the zone should manually watering for"""
        self._manual_minutes = value

    @property
    def watering_end_time(self) -> int:
        """Unix timestamp in seconds when watering will end"""
        return self._end_time

    def _manual_setting_bytes(self) -> bytes:
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

    _battery: int
    _brand: str
    _connection: BleakClient
    _connection_lock = asyncio.Lock()
    _is_connected: bool
    _mac: str
    _model: str
    _sensor: bool
    _valves: List[Valve]
    _valve_count: int

    def __init__(self, mac: str) -> None:

        self._battery = 0
        self._is_connected = False
        self._mac = mac
        self._valves = []

        # The 1 and 2 valve devices still use 4 valve bytes
        # So we'll instantiate 4 valves to mimic that behavior
        # set of bytes too 🤦‍♂️
        for i in range(4):
            self._valves.append(Valve(i, self))

    async def _init(self):
        """Initializes the device"""

        manufacturer_data = await self._connection.read_gatt_char(MANUFACTURER_UUID)

        string = manufacturer_data.decode("utf-8")

        self._model = string[0:5]
        self._valve_count = int(string[6:7])

    def disconnected_callback(self, client):
        print("Disconnected from:", self._mac)
        self._is_connected = False

    async def connect(self, timeout=60) -> None:
        async with GLOBAL_BLUETOOTH_LOCK:

            if self._is_connected or self._connection_lock.locked():
                return

            async with self._connection_lock:

                try:
                    print("Connecting to:", self._mac)
                    self._connection = BleakClient(
                        self._mac, disconnected_callback=self.disconnected_callback
                    )

                    await self._connection.connect(timeout=timeout)
                    self._is_connected = True

                    await self._init()

                    print("Success:", self._mac)

                except BleakError:
                    print("Failed to connect to:", self._mac)
                    self._is_connected = False

    async def disconnect(self) -> None:
        async with GLOBAL_BLUETOOTH_LOCK:

            await self._connection.disconnect()

    async def fetch_state(self) -> None:
        """Updates the state of the device with the given bytes"""

        async with GLOBAL_BLUETOOTH_LOCK:

            uuids = [
                BATTERY_UUID,
                VALVE_MANUAL_SETTINGS_UUID,
                VALVE_MANUAL_STATES_UUID,
            ]

            try:
                bytes_array: List[bytes] = await asyncio.gather(
                    *[self._read(uuid) for uuid in uuids],
                    return_exceptions=True,
                )

                for i, some_bytes in enumerate(bytes_array):

                    uuid = uuids[i]

                    if uuid == BATTERY_UUID:
                        self._battery = parse_battery_value(some_bytes)

                    for valve in self._valves:
                        some_bytes = uuids.index(uuid)
                        valve.update_state(bytes_array[some_bytes], uuids[i])

            except BleakError as error:
                # Swallow this error if the device is disconnected
                if self._is_connected:
                    raise error

    async def _read(self, uuid: str) -> bytes:
        """Reads the given characteristic from the device"""

        return await self._connection.read_gatt_char(uuid)

    async def push_state(self) -> None:
        """Pushes the state of the device to the device"""
        async with GLOBAL_BLUETOOTH_LOCK:

            on_off = self._connection.services.get_characteristic(
                VALVE_MANUAL_SETTINGS_UUID
            )

            await self._connection.write_gatt_char(
                on_off.handle,
                (
                    self._valves[0]._manual_setting_bytes()
                    + self._valves[1]._manual_setting_bytes()
                    + self._valves[2]._manual_setting_bytes()
                    + self._valves[3]._manual_setting_bytes()
                ),
                True,
            )

            updated_at = self._connection.services.get_characteristic(UPDATED_AT_UUID)

            await self._connection.write_gatt_char(
                updated_at.handle, struct.pack(">I", get_timestamp()), True
            )

    @property
    def battery_level(self) -> int:
        """Returns the battery level of the device"""
        return self._battery

    @property
    def brand(self) -> str:
        """Returns the manufacturer of the device"""
        return self._brand

    @property
    def is_connected(self) -> bool:
        """Returns whether the device is currently connected"""
        return self._is_connected

    @property
    def mac(self) -> str:
        """Returns the MAC address of the device"""
        return self._mac

    @property
    def model(self) -> str:
        """Returns the name of the device"""
        return self._model

    @property
    def name(self) -> str:
        """Returns the name of the device"""
        return f"{self._valve_count} Valve Timer"

    @property
    def valve_count(self) -> int:
        """Returns the number of valves on the device"""
        return self._valve_count

    @valve_count.setter
    def valve_count(self, value: int) -> None:
        """Sets the number of valves on the device"""
        self._valve_count = value

    @property
    def zone1(self) -> Valve:
        """Returns the first zone on the device"""
        return self._valves[0]

    @property
    def zone2(self) -> Union[Valve, None]:
        """Returns the second zone on the device"""
        if self._valve_count > 1:
            return self._valves[1]

    @property
    def zone3(self) -> Union[Valve, None]:
        """Returns the third zone on the device"""
        if self._valve_count > 2:
            return self._valves[2]

    @property
    def zone4(self) -> Union[Valve, None]:
        """Returns the fourth zone on the device"""
        if self._valve_count > 2:
            return self._valves[3]

    def __str__(self) -> str:
        str = f"{self.__class__.__name__}(\n    battery={self._battery}\n    valves=(\n"
        for valve in self._valves:
            str += f"{valve}\n"
        return f"{str}    )\n)"

    def __getitem__(self, key: str) -> Union[Valve, None]:
        if key == "zone1":
            return self.zone1
        elif key == "zone2":
            return self.zone2
        elif key == "zone3":
            return self.zone3
        elif key == "zone4":
            return self.zone4
