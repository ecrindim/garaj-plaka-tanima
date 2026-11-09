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
