from otopark.camera import Frame
from otopark.gate_service import GateService
from otopark.models import FrameAnalysis, GateEvent, PlateRead, Reading, ReadStatus
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
        return self.analyze(frame).events

    def analyze(self, frame: Frame) -> FrameAnalysis:
        """Kareyi işler; olayların yanında her okumanın durumunu da döndürür."""
        readings: list[Reading] = []
        events: list[GateEvent] = []
        for read in self._reader.read(frame):
            readings.append(self._evaluate(read, events))
        return FrameAnalysis(readings, events)

    def _evaluate(self, read: PlateRead, events: list[GateEvent]) -> Reading:
        if read.confidence < self._min_confidence:
            return Reading(read, ReadStatus.LOW_CONFIDENCE)

        plate = self._validator.parse(read.text)
        if plate is None:
            return Reading(read, ReadStatus.INVALID)

        if self._confirmer.submit(plate):
            events.append(self._gate.register(plate))

        if self._confirmer.is_confirmed(plate):
            return Reading(read, ReadStatus.CONFIRMED, plate)
        return Reading(read, ReadStatus.PENDING, plate, self._confirmer.votes(plate))
