import datetime
import zoneinfo

from tzlocal import get_localzone


def _time_offset(tz: datetime.tzinfo = get_localzone()):
    """
    Returns the archaic timezone offset in seconds.

    The valve accepts a 4 byte unsigned integer and the official app
    appears to deduct ~30 years from the current time to fit into a 4 byte size.


    All watering operations are keyed off this value and the mobile app _and valves_
    will show bad info we don't replicate the algorithm
    """

    base_time = datetime.datetime.now(tz=zoneinfo.ZoneInfo("Asia/Shanghai"))
    local_time = datetime.datetime.now(tz=tz)

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

    if base_time.dst() is not None:
        base_offset = base_offset - base_time.dst()  # type: ignore

    if local_time.dst() is not None:
        local_offset = local_offset - local_time.dst()  # type: ignore

    if base_offset is None or local_offset is None:
        # TODO log or throw an exception here. caller should handle this
        return 0

    return int(base_offset.total_seconds() - local_offset.total_seconds())


def time_shift(tz: datetime.tzinfo = get_localzone()) -> int:
    return -_time_offset(tz) - 946656000


def get_timestamp(tz: datetime.tzinfo = get_localzone()) -> int:
    """
    Returns the current timestamp as a byte array.
    """

    return int(datetime.datetime.now(tz).timestamp() + time_shift(tz))
