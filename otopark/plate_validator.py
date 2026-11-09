import re

_PLATE_PATTERN = re.compile(r"^(0[1-9]|[1-7]\d|8[01])([A-Z]{1,3})(\d{2,4})$")

# Türk plaka standardı: harf sayısına göre izin verilen rakam sayıları
_DIGIT_COUNTS_BY_LETTER_COUNT = {1: {4}, 2: {3, 4}, 3: {2, 3}}

# İl kodunda (ilk iki karakter) sık görülen OCR karışıklıkları
_CITY_CODE_FIXES = str.maketrans({"O": "0", "D": "0", "I": "1", "Z": "2", "S": "5", "B": "8"})


class TurkishPlateValidator:
    """Ham OCR metnini Türk plaka standardına göre düzeltir ve doğrular."""

    def parse(self, raw_text: str) -> str | None:
        """Geçerli plakayı boşluksuz biçimde (ör. '20ABC123') döner, değilse None."""
        text = _fix_city_code(_normalize(raw_text))
        match = _PLATE_PATTERN.fullmatch(text)
        if match is None:
            return None
        _, letters, digits = match.groups()
        if len(digits) not in _DIGIT_COUNTS_BY_LETTER_COUNT[len(letters)]:
            return None
        return text


def format_for_display(plate: str) -> str:
    """'20ABC123' -> '20 ABC 123'"""
    match = _PLATE_PATTERN.fullmatch(plate)
    return " ".join(match.groups()) if match else plate


def _normalize(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _fix_city_code(text: str) -> str:
    return text[:2].translate(_CITY_CODE_FIXES) + text[2:]
