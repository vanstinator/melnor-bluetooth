from melnor_bluetooth.utils import battery


class TestBatteryParser:
    def test_standard_response(self):
        assert battery.parse_battery_value(b"\x02\xa8") == 55
        assert battery.parse_battery_value(b"\x02\x90") == 38

    def test_dead_case(self):
        assert battery.parse_battery_value(b"\xee\xee") == 0

    def test_full_Case(self):
        assert battery.parse_battery_value(b"\xff\xff") == 100
