from datetime import datetime
from zoneinfo import ZoneInfo

from freezegun import freeze_time

from melnor_bluetooth.parser.date import _time_offset, get_timestamp

tz = ZoneInfo("America/Detroit")

no_dst = datetime(2022, 3, 11, 0, 0, 0, tzinfo=tz)
dst = datetime(2022, 3, 13, 0, 0, 0, tzinfo=tz)


class TestDateTester:
    @freeze_time(no_dst)
    def test_time_offset_no_dst(self):
        assert _time_offset(tz) == 46800

    @freeze_time(dst)
    def test_time_offset_dst(self):
        assert _time_offset(tz) == 46800

    # DST is largely irrelevant to this computation as long as the offset is correct which we validate above
    @freeze_time(no_dst)
    def test_get_timestamp_no(self):
        assert get_timestamp() == 700290000
