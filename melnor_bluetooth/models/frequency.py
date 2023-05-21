import struct
from datetime import datetime, time, timedelta

from ..utils import date  # pylint: disable=relative-beyond-top-level


class Frequency:
    """A class representing the Frequency schedule for a valve"""

    _payload: bytes
    _raw_start_time: int

    _duration_minutes: int
    _interval_hours: int

    # Computed values
    _next_run_time: datetime
    _is_watering: bool
    _watering_end_time: datetime

    def __init__(self, payload: bytes) -> None:
        self.update_state(payload)

    def __str__(self) -> str:
        return (
            f"Next run time: {self.next_run_time} "
            f"(Frequency: {self._interval_hours} hours, Duration: {self.duration_minutes} minutes)"  # noqa: E501
            f"{' (Watering ends at ' + str(self._watering_end_time) + ')' if self._is_watering else ''}"  # noqa: E501
        )

    def to_bytes(self) -> bytes:
        """Convert the frequency to bytes for writing to the device"""
        return struct.pack(
            ">BIHB",
            0,
            self._raw_start_time,
            self.duration_minutes,
            self._interval_hours,
        )

    def _compute_dates(self):
        # This date is always wrong, but the time should be correcct
        device_date = datetime.fromtimestamp(self._raw_start_time - date.time_shift())

        # Set the start time to the start time yesterday
        # this makes computing the next_run_time easier
        start_time = datetime.today().replace(
            hour=device_date.hour, minute=device_date.minute, second=0, microsecond=0
        ) - timedelta(days=1)

        # Find the next run time by adding the frequency to the start time until it is
        # in the future. If during the loop the current date is between a candidate
        # next_run_time + duration, set is_in_schedule to true
        next_run_time = start_time
        self._is_watering = False
        while next_run_time < datetime.now():
            next_run_time += timedelta(hours=self._interval_hours)
            self._next_run_time = next_run_time
            if (
                next_run_time
                < datetime.now()
                < next_run_time + timedelta(minutes=self.duration_minutes)
            ):
                self._is_watering = True
                self._watering_end_time = next_run_time + timedelta(
                    minutes=self.duration_minutes
                )
                break

    def update_state(self, payload: bytes):
        """Update the state of the frequency from the payload"""
        self._payload = payload

        (
            _,
            self._raw_start_time,
            self._duration_minutes,
            self._interval_hours,
        ) = struct.unpack_from(">BIHB", self._payload)

        self._compute_dates()

    @property
    def next_run_time(self) -> datetime:
        """The next time the valve will run. Only the hour and minute are used.
        The date is always wrong."""
        return self._next_run_time

    @property
    def duration_minutes(self) -> int:
        """The duration of the watering in minutes"""
        return self._duration_minutes

    @duration_minutes.setter
    def duration_minutes(self, value: int) -> None:
        # The Melnor app crashes if the duration is greater than 360 minutes
        value = min([value, 360])
        self._duration_minutes = value

    @property
    def interval_hours(self) -> int:
        """The frequency in hours"""
        return self._frequency_hours

    @interval_hours.setter
    def interval_hours(self, value: int) -> None:
        # The Melnor app crashes if the frequency is greater than 168 hours
        value = min([value, 168])
        self._frequency_hours = value

    @property
    def is_watering(self) -> bool:
        """True if the valve is currently watering"""
        return self._is_watering

    @property
    def start_time(self) -> time:
        """The start time of the watering"""
        return self.next_run_time.time()

    @start_time.setter
    def start_time(self, value: time) -> None:
        device_date = datetime.fromtimestamp(self._raw_start_time - date.time_shift())

        self._raw_start_time = int(
            device_date.replace(hour=value.hour, minute=value.minute).timestamp()
            + date.time_shift()
        )

    @property
    def watering_end_time(self) -> datetime:
        """The time the valve will stop watering"""
        return self._watering_end_time
