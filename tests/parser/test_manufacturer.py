from melnor_bluetooth.constants import MELNOR
from melnor_bluetooth.parser.manufacturer import parse_manufacturer


class TestManufacturerParser:
    def test_melnor(self):

        assert parse_manufacturer(b"ML_001") == MELNOR

    def test_unknown(self):
        assert parse_manufacturer(b"UN_001") == "UN_001"
