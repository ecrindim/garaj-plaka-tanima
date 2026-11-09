import pytest

from otopark.plate_validator import TurkishPlateValidator, format_for_display

validator = TurkishPlateValidator()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("20 ABC 123", "20ABC123"),
        ("34-a-1234", "34A1234"),
        ("06 AB 1234", "06AB1234"),
        ("2O AB 123", "20AB123"),  # il kodundaki O -> 0
    ],
)
def test_accepts_valid_plates(raw, expected):
    assert validator.parse(raw) == expected


@pytest.mark.parametrize(
    "raw",
    ["99 AB 123", "00 AB 123", "34 A 123", "06 ABC 1234", "MERHABA", ""],
)
def test_rejects_invalid_plates(raw):
    assert validator.parse(raw) is None


def test_formats_for_display():
    assert format_for_display("20ABC123") == "20 ABC 123"
