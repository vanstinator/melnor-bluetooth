from datetime import datetime
from zoneinfo import ZoneInfo

from freezegun import freeze_time

from melnor_bluetooth.utils import date

tz = ZoneInfo("America/Detroit")

no_dst = datetime(2022, 3, 11, 0, 0, 0, tzinfo=tz)
dst = datetime(2022, 3, 13, 0, 0, 0, tzinfo=tz)


class TestDateTester:
    @freeze_time(no_dst)
    def test_time_offset_no_dst(self):
        assert date._time_offset(tz) == 46800  # pylint: disable=protected-access

    @freeze_time(dst)
    def test_time_offset_dst(self):
        assert date._time_offset(tz) == 46800  # pylint: disable=protected-access

    # DST is largely irrelevant to this computation as long
    # as the offset is correct which we validate above
    @freeze_time(no_dst)
    def test_get_timestamp(self):
        assert date.get_timestamp(ZoneInfo("UTC")) == 700290000
