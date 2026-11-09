from dataclasses import replace
from typing import Protocol

import numpy as np

from otopark.camera import Frame
from otopark.models import PlateRead


class PlateReader(Protocol):
    def read(self, frame: Frame) -> list[PlateRead]: ...


class FastAlprReader:
    """FastALPR'ın hazır eğitilmiş modelleriyle plaka okur."""

    def __init__(self, detector_model: str, ocr_model: str) -> None:
        from fast_alpr import ALPR

        self._alpr = ALPR(detector_model=detector_model, ocr_model=ocr_model)

    def read(self, frame: Frame) -> list[PlateRead]:
        return [
            PlateRead(
                text=result.ocr.text,
                confidence=_average(result.ocr.confidence),
                box=_box(result.detection),
            )
            for result in self._alpr.predict(frame)
            if result.ocr is not None
        ]


def _average(confidence: float | list[float]) -> float:
    """Güven değeri tek sayı ya da karakter başına liste olabilir."""
    values = np.atleast_1d(np.asarray(confidence, dtype=float))
    return float(values.mean()) if values.size else 0.0


def _box(detection) -> tuple[int, int, int, int] | None:
    bbox = getattr(detection, "bounding_box", None)
    if bbox is None:
        return None
    return int(bbox.x1), int(bbox.y1), int(bbox.x2), int(bbox.y2)


Region = tuple[float, float, float, float]


def region_to_pixels(region: Region, width: int, height: int) -> tuple[int, int, int, int]:
    """Oransal bölgeyi (0.0-1.0) piksel koordinatlarına çevirir."""
    left, top, right, bottom = region
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise ValueError(f"Geçersiz bölge: {region} (0.0-1.0 arası, sol<sağ, üst<alt olmalı)")
    return round(left * width), round(top * height), round(right * width), round(bottom * height)


class RegionReader:
    """Kareden yalnızca belirlenen bölgeyi okuyucuya verir.

    Kutu koordinatları tam kareye göre geri çevrilir, böylece önizleme doğru çizer.
    """

    def __init__(self, reader: PlateReader, region: Region) -> None:
        region_to_pixels(region, 1, 1)  # Ayarı başlangıçta doğrula
        self._reader = reader
        self._region = region

    def read(self, frame: Frame) -> list[PlateRead]:
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = region_to_pixels(self._region, width, height)
        return [_shift(read, x1, y1) for read in self._reader.read(frame[y1:y2, x1:x2])]


def _shift(read: PlateRead, dx: int, dy: int) -> PlateRead:
    if read.box is None:
        return read
    x1, y1, x2, y2 = read.box
    return replace(read, box=(x1 + dx, y1 + dy, x2 + dx, y2 + dy))
