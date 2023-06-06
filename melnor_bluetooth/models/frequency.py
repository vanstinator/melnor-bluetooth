from __future__ import annotations

import struct
from datetime import datetime, time

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
            datetime.now(tz=get_localzone()).timestamp() + date.time_shift()
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
        if (
            self._attr_raw_start_time == 0
            or self._attr_interval_hours == 0
            or self._attr_duration_minutes == 0
        ):
            self._attr_next_run_time = None
            self._attr_is_watering = False
            return

        # Get the actual date for the start time
        start_time = date.to_start_time(self._attr_raw_start_time)
        start_time_seconds = start_time.timestamp()
        current_time_seconds = datetime.now(tz=get_localzone()).timestamp()

        # The device clock could have the start time as years ago, so we need to
        # calculate the next run time based on the current time
        interval_seconds = self._attr_interval_hours * 3600
        seconds_since_start_time = current_time_seconds - start_time_seconds
        remainder_seconds = seconds_since_start_time % (interval_seconds)

        last_run_time_seconds = current_time_seconds - remainder_seconds
        next_run_time_seconds = last_run_time_seconds + (interval_seconds)

        if (
            last_run_time_seconds + (self._attr_duration_minutes * 60)
            > current_time_seconds
        ):
            self._attr_is_watering = True
            self._attr_next_run_time = datetime.fromtimestamp(
                last_run_time_seconds, tz=get_localzone()
            )
            self._attr_schedule_end = datetime.fromtimestamp(
                last_run_time_seconds + (self._attr_duration_minutes * 60),
                tz=get_localzone(),
            )

        else:
            self._attr_is_watering = False
            self._attr_next_run_time = datetime.fromtimestamp(
                next_run_time_seconds, tz=get_localzone()
            )
            self._attr_schedule_end = datetime.fromtimestamp(
                next_run_time_seconds + (self._attr_duration_minutes * 60),
                tz=get_localzone(),
            )

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
        self._compute_dates()

    @property
    def interval_hours(self) -> int:
        """The frequency in hours"""
        return self._attr_interval_hours

    @interval_hours.setter
    def interval_hours(self, value: int) -> None:
        # The Melnor app crashes if the frequency is greater than 168 hours
        value = min([value, 168])
        self._attr_interval_hours = value
        self._compute_dates()

    @property
    def start_time(self) -> time:
        """The start time of the watering"""

        if self._attr_raw_start_time == 0:
            self._attr_raw_start_time = date.from_start_time(datetime.now())

        # This date we get from the device, even with the time_shift, is always
        # wrong but the time should be correcct
        return date.to_start_time(self._attr_raw_start_time).time()

    @start_time.setter
    def start_time(self, value: time) -> None:
        self._attr_raw_start_time = date.from_start_time(
            datetime.now().replace(
                hour=value.hour,
                minute=value.minute,
                microsecond=0,
            )
        )
        self._compute_dates()

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
