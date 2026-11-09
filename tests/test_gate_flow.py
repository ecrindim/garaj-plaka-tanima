from datetime import datetime, timedelta

from otopark.gate_service import GateService
from otopark.models import EventType, PlateRead, ReadStatus
from otopark.plate_confirmer import PlateConfirmer
from otopark.plate_monitor import PlateMonitor
from otopark.plate_validator import TurkishPlateValidator
from otopark.visit_repository import VisitRepository


class FakeReader:
    def __init__(self, reads: list[PlateRead]) -> None:
        self.reads = reads

    def read(self, _frame) -> list[PlateRead]:
        return self.reads


def make_gate(start: datetime) -> tuple[GateService, VisitRepository, list[datetime]]:
    times = [start]
    repository = VisitRepository(":memory:")
    return GateService(repository, clock=lambda: times[0]), repository, times


def test_first_sighting_is_entry_second_is_exit():
    start = datetime(2026, 11, 9, 8, 0)
    gate, repository, times = make_gate(start)

    assert gate.register("20ABC123").event_type is EventType.ENTRY
    times[0] = start + timedelta(hours=2)
    assert gate.register("20ABC123").event_type is EventType.EXIT

    visit = repository.recent_visits()[0]
    assert visit.entry_time == start
    assert visit.exit_time == start + timedelta(hours=2)


def test_monitor_filters_low_confidence_and_invalid_reads():
    gate, repository, _ = make_gate(datetime(2026, 11, 9, 8, 0))
    reader = FakeReader(
        [
            PlateRead("20 ABC 123", 0.95),
            PlateRead("34 XYZ 99", 0.30),  # düşük güven
            PlateRead("ABCDEF", 0.99),     # geçersiz format
        ]
    )
    monitor = PlateMonitor(
        reader=reader,
        validator=TurkishPlateValidator(),
        confirmer=PlateConfirmer(votes_required=1, window_seconds=1, quiet_period_seconds=1),
        gate=gate,
        min_confidence=0.6,
    )

    events = monitor.process(frame=None)

    assert [e.plate for e in events] == ["20ABC123"]
    assert len(repository.recent_visits()) == 1


def test_analyze_reports_status_of_every_read():
    gate, _, _ = make_gate(datetime(2026, 11, 9, 8, 0))
    reader = FakeReader([PlateRead("20 ABC 123", 0.95), PlateRead("ABCDEF", 0.99)])
    monitor = PlateMonitor(
        reader=reader,
        validator=TurkishPlateValidator(),
        confirmer=PlateConfirmer(votes_required=2, window_seconds=10, quiet_period_seconds=10),
        gate=gate,
        min_confidence=0.6,
    )

    first = monitor.analyze(frame=None)
    second = monitor.analyze(frame=None)

    assert [(r.status, r.votes) for r in first.readings] == [
        (ReadStatus.PENDING, 1),
        (ReadStatus.INVALID, 0),
    ]
    assert first.events == []
    assert second.readings[0].status is ReadStatus.CONFIRMED
    assert [e.plate for e in second.events] == ["20ABC123"]
