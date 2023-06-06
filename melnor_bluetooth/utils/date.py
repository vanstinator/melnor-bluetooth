import logging
import time
import zoneinfo
from datetime import datetime, timedelta, tzinfo

from tzlocal import get_localzone

_LOGGER = logging.getLogger(__name__)


def _time_offset(tz: tzinfo = get_localzone()):
    """
    Returns the archaic timezone offset in seconds.

    The valve accepts a 4 byte unsigned integer and the official app
    appears to deduct ~30 years from the current time to fit into a 4 byte size.


    All watering operations are keyed off this value and the mobile app _and valves_
    will show bad info we don't replicate the algorithm
    """

    base_time = datetime.now(tz=zoneinfo.ZoneInfo("Asia/Shanghai"))
    local_time = datetime.now(tz=tz)

    base_offset = base_time.utcoffset()
    local_offset = local_time.utcoffset()

    if (
        base_offset is None
        or local_offset is None
        or base_time is None
        or local_time is None
    ):
        # TODO log or throw an exception here. caller should handle this
        return 0

    if base_offset is None or local_offset is None:
        # TODO log or throw an exception here. caller should handle this
        return 0

    is_dst = time.daylight and time.localtime().tm_isdst > 0
    dst_offset = timedelta(hours=1) if is_dst else timedelta(hours=0)

    return (
        int(base_offset.total_seconds() - local_offset.total_seconds())
        + dst_offset.total_seconds()
    )


def time_shift(tz: tzinfo = get_localzone()) -> int:
    date = datetime(1970, 1, 1, tzinfo=tz).replace(fold=1)

    return int((date + timedelta(seconds=-_time_offset(tz) - 946656000)).timestamp())


def get_timestamp(tz: tzinfo = get_localzone()) -> int:
    """
    Returns the current timestamp as a byte array.
    """

    return int(datetime.now(tz).timestamp() + time_shift(tz))


def to_start_time(timestamp: int, tz: tzinfo = get_localzone()) -> datetime:
    """
    Returns the current timestamp as a byte array.
    """

    return datetime.fromtimestamp(
        timestamp,
    ).replace(
        tzinfo=tz
    ) - timedelta(seconds=time_shift())


def from_start_time(timestamp: datetime) -> int:
    """
    Returns the current timestamp as a byte array.
    """

    return int(timestamp.timestamp() + time_shift())
