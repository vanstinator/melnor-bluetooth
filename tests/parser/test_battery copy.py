from melnor_bt.parser.battery import get_batt_val


class TestBatteryParser:
    def test_standard_response(self):
        assert get_batt_val(b"\x02\xa8") == 55
        assert get_batt_val(b"\x02\x90") == 38

    def test_dead_case(self):
        assert get_batt_val(b"\xee\xee") == 0

    def test_full_Case(self):
        assert get_batt_val(b"\xff\xff") == 100
