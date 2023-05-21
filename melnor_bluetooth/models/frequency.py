from __future__ import annotations

import struct
from datetime import datetime, time, timedelta

from tzlocal import get_localzone

from ..utils import date  # pylint: disable=relative-beyond-top-level


class Frequency:
    """A class representing the Frequency schedule for a valve"""

    _attr_bytes: bytes
    _attr_raw_start_time: int

    _attr_duration_minutes: int
    _attr_interval_hours: int

    # Computed values
    _attr_next_run_time: datetime | None
    _attr_is_watering: bool
    _attr_schedule_end: datetime

    def __init__(self) -> None:
        self._attr_duration_minutes = 10
        self._attr_interval_hours = 24
        self._attr_raw_start_time = int(
            datetime.now().replace(tzinfo=get_localzone()).timestamp()
            + date.time_shift()
        )
        self._attr_next_run_time = None

    def __str__(self) -> str:
        return (
            f"Next run time: {self.next_run_time} "
            f"(Frequency: {self._attr_interval_hours} hours, Duration: {self.duration_minutes} minutes)"  # noqa: E501
            f"{' (Watering ends at ' + str(self._attr_schedule_end) + ')' if self._attr_is_watering else ''}"  # noqa: E501
        )

    def to_bytes(self) -> bytes:
        """Convert the frequency to bytes for writing to the device"""
        return struct.pack(
            ">BIHB",
            0,
            self._attr_raw_start_time,
            self._attr_duration_minutes,
            self._attr_interval_hours,
        )

    def _compute_dates(self):
        # Set the start time to the start time yesterday
        # this makes computing the next_run_time easier
        start_time = datetime.today().replace(
            hour=self.start_time.hour,
            minute=self.start_time.minute,
            second=0,
            microsecond=0,
            tzinfo=get_localzone(),
        )

        # Find the next run time by adding the frequency to the start time until it is
        # in the future. If during the loop the current date is between a candidate
        # next_run_time + duration, set is_in_schedule to true
        self._attr_next_run_time = start_time
        self._attr_is_watering = False

        now = datetime.now().replace(tzinfo=get_localzone())
        while self._attr_next_run_time < now:
            if (
                self._attr_next_run_time
                < now
                < self._attr_next_run_time + timedelta(minutes=self.duration_minutes)
            ):
                self._attr_is_watering = True
                self._attr_schedule_end = self._attr_next_run_time + timedelta(
                    minutes=self._attr_duration_minutes
                )

                break

            self._attr_next_run_time += timedelta(hours=self._attr_interval_hours)

    def update_state(self, payload: bytes):
        """Update the state of the frequency from the payload"""
        self._attr_bytes = payload

        (
            _,
            self._attr_raw_start_time,
            self._attr_duration_minutes,
            self._attr_interval_hours,
        ) = struct.unpack_from(">BIHB", self._attr_bytes)

        self._compute_dates()

    @property
    def duration_minutes(self) -> int:
        """The duration of the watering in minutes"""
        return self._attr_duration_minutes

    @duration_minutes.setter
    def duration_minutes(self, value: int) -> None:
        # The Melnor app crashes if the duration is greater than 360 minutes
        value = min([value, 360])
        self._attr_duration_minutes = value

    @property
    def interval_hours(self) -> int:
        """The frequency in hours"""
        return self._attr_interval_hours

    @interval_hours.setter
    def interval_hours(self, value: int) -> None:
        # The Melnor app crashes if the frequency is greater than 168 hours
        value = min([value, 168])
        self._attr_interval_hours = value

    @property
    def start_time(self) -> time:
        """The start time of the watering"""

        if self._attr_raw_start_time == 0:
            return datetime.fromtimestamp(
                datetime.now().replace(tzinfo=get_localzone()).timestamp()
                + float(date.time_shift())
            ).time()

        else:
            # This date we get from the device, even with the time_shift, is always
            # wrong but the time should be correcct
            return datetime.fromtimestamp(
                self._attr_raw_start_time - date.time_shift(), tz=get_localzone()
            ).time()

    @start_time.setter
    def start_time(self, value: time) -> None:
        device_date = datetime.fromtimestamp(
            self._attr_raw_start_time - date.time_shift()
        )

        self._attr_raw_start_time = int(
            device_date.replace(hour=value.hour, minute=value.minute).timestamp()
            + date.time_shift()
        )

    @property
    def is_watering(self) -> bool:
        """True if the valve is currently watering"""
        return self._attr_is_watering

    @property
    def next_run_time(self) -> datetime | None:
        """The next time the valve will run. Only the hour and minute are used.
        The date is always wrong."""
        return self._attr_next_run_time

    @property
    def schedule_end(self) -> datetime:
        """The time the valve will stop watering"""
        return self._attr_schedule_end
