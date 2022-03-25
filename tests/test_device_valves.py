import struct

from melnor_bluetooth.device import Valve
from melnor_bluetooth.parser.battery import parse_battery_value

zone_byte_payload = struct.pack(
    ">20B",
    # Zone 0
    1,
    1,
    104,
    1,
    104,
    # Zone 2
    0,
    0,
    23,
    0,
    23,
    # Zone 3
    0,
    0,
    42,
    0,
    42,
    # Zone 4
    1,
    0,
    13,
    0,
    13,
)


class TestValveZone:
    def test_zone_0_update_state(self):
        zone = Valve(0)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == True
        assert zone.manual_watering_seconds == 360

    def test_zone_1_update_state(self):
        zone = Valve(1)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == False
        assert zone.manual_watering_seconds == 23

    def test_zone_2_update_state(self):
        zone = Valve(2)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == False
        assert zone.manual_watering_seconds == 42

    def test_zone_3_update_state(self):
        zone = Valve(3)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == True
        assert zone.manual_watering_seconds == 13

    def test_zone_property(self):
        zone = Valve(0)

        assert zone.is_watering == False
        assert zone.manual_watering_seconds == 20 * 60

        zone.is_watering = True
        zone.manual_watering_seconds = 10

        assert zone.is_watering == True
        assert zone.manual_watering_seconds == 10
