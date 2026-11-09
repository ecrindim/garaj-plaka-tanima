from collections.abc import Iterator

from otopark.camera import Frame
from otopark.gate_service import GateService
from otopark.models import GateEvent
from otopark.plate_confirmer import PlateConfirmer
from otopark.plate_reader import PlateReader
from otopark.plate_validator import TurkishPlateValidator


class PlateMonitor:
    """Her kareyi işleyip onaylanan giriş/çıkış olaylarını üretir."""

    def __init__(
        self,
        reader: PlateReader,
        validator: TurkishPlateValidator,
        confirmer: PlateConfirmer,
        gate: GateService,
        min_confidence: float,
    ) -> None:
        self._reader = reader
        self._validator = validator
        self._confirmer = confirmer
        self._gate = gate
        self._min_confidence = min_confidence

    def process(self, frame: Frame) -> list[GateEvent]:
        return [
            self._gate.register(plate)
            for plate in self._valid_plates(frame)
            if self._confirmer.submit(plate)
        ]

    def _valid_plates(self, frame: Frame) -> Iterator[str]:
        for read in self._reader.read(frame):
            if read.confidence < self._min_confidence:
                continue
            plate = self._validator.parse(read.text)
            if plate is not None:
                yield plate
