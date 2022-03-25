import datetime
from zoneinfo import ZoneInfo


def _time_offset():
    """
    Returns the archaic timezone offset in seconds.

    The valve accepts a 4 byte unsigned integer and the official app
    appears to deduct ~30 years from the current time to fit into a 4 byte size.


    All watering operations are keyed off this value and the mobile app _and valves_ will show bad info we don't replicate the algorithm
    """

    base_time = datetime.datetime.now(tz=ZoneInfo("Asia/Shanghai"))
    local_time = datetime.datetime.now(datetime.timezone.utc).astimezone()

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


def get_timestamp():
    """
    Returns the current timestamp as a byte array.
    """

    return int(datetime.datetime.now().timestamp() + (-_time_offset() - 946656000))
