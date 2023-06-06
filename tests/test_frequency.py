# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring

import datetime

import freezegun
from tzlocal import get_localzone

from melnor_bluetooth.device import Frequency

start_date = datetime.datetime(year=2023, month=6, day=5, tzinfo=get_localzone())


class TestFrequency:
    async def test_zero_state(self):
        frequency = Frequency()

        assert frequency.duration_minutes == 10
        assert frequency.interval_hours == 24
        assert frequency.next_run_time is None

    @freezegun.freeze_time(start_date.replace(hour=1, minute=0))
    async def test_schedule_not_running(self):
        frequency = Frequency()

        frequency.duration_minutes = 10
        frequency.interval_hours = 6
        frequency.start_time = datetime.time(hour=0, minute=0)

        assert frequency.is_watering is False
        assert frequency.next_run_time == start_date.replace(hour=6, minute=0)

    @freezegun.freeze_time(start_date.replace(hour=0, minute=5))
    async def test_frequency_currently_running(self):
        frequency = Frequency()

        frequency.duration_minutes = 10
        frequency.interval_hours = 6
        frequency.start_time = start_date.replace(hour=0, minute=0)

        assert frequency.is_watering is True
        assert frequency.next_run_time == start_date.replace(hour=0, minute=0)
        assert frequency.schedule_end == start_date.replace(hour=0, minute=10)
