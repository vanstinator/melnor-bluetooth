from melnor_bt.parser.battery import get_batt_val


def test_get_batt_val():

    # Standard case
    assert get_batt_val(b"\x02\xa8") == 55

    # Dead case
    assert get_batt_val(b"\xee\xee") == 0

    # Full Case
    assert get_batt_val(b"\xff\xff") == 100
