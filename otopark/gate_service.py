from collections.abc import Callable
from datetime import datetime

from otopark.models import EventType, GateEvent
from otopark.visit_repository import VisitRepository


def _local_now() -> datetime:
    return datetime.now().astimezone()


class GateService:
    """Onaylanan plakayı giriş ya da çıkış olarak kaydeder.

    Tek kameralı kurulum için: araç içeride değilse giriş, içerideyse çıkış.
    """

    def __init__(
        self, repository: VisitRepository, clock: Callable[[], datetime] = _local_now
    ) -> None:
        self._repository = repository
        self._clock = clock

    def register(self, plate: str) -> GateEvent:
        now = self._clock()
        open_visit = self._repository.find_open_visit(plate)

        if open_visit is None:
            self._repository.open_visit(plate, now)
            return GateEvent(plate, EventType.ENTRY, now)

        self._repository.close_visit(open_visit.id, now)
        return GateEvent(plate, EventType.EXIT, now)
