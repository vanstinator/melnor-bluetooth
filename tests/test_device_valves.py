import struct

from melnor_bluetooth.device import Device, Valve
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

device = Device("FDBC1347-8D0B-DB0E-8D79-7341E825AC2A")


class TestValveZone:
    def test_zone_0_update_state(self):
        zone = Valve(0, device)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == True
        assert zone.manual_watering_minutes == 360

    def test_zone_1_update_state(self):
        zone = Valve(1, device)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == False
        assert zone.manual_watering_minutes == 23

    def test_zone_2_update_state(self):
        zone = Valve(2, device)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == False
        assert zone.manual_watering_minutes == 42

    def test_zone_3_update_state(self):
        zone = Valve(3, device)

        print(zone_byte_payload)

        zone.update_state(zone_byte_payload)

        assert zone.is_watering == True
        assert zone.manual_watering_minutes == 13

    def test_zone_properties(self):
        zone = Valve(0, device)

        zone.is_watering = True
        zone.manual_watering_minutes = 10

        assert zone.is_watering == True
        assert zone.manual_watering_minutes == 10

    def test_zone_defaults(self):
        zone = Valve(0, device)

        assert zone.is_watering == False
        assert zone.manual_watering_minutes == 20

    def test_zone_byte_payload(self):
        zone = Valve(0, device)

        zone.is_watering = True
        zone.manual_watering_minutes = 10

        assert zone.byte_payload == [1, 0, 10, 0, 10]
