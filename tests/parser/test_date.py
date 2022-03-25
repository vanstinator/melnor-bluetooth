from freezegun import freeze_time

from melnor_bluetooth.parser.date import _time_offset, get_timestamp


class TestDateTester:
    @freeze_time("2022-03-11")
    def test_time_offset_no_dst(self):
        assert _time_offset() == 46800

    @freeze_time("2022-04-11")
    def test_time_offset_dst(self):
        assert _time_offset() == 46800

    @freeze_time("2022-03-11")
    def test_get_timestamp_bytes(self):
        assert get_timestamp() == 700254000
