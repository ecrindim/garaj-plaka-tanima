from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class PlateRead:
    """Modelin tek bir karede okuduğu ham plaka metni."""

    text: str
    confidence: float


class EventType(Enum):
    ENTRY = "GİRİŞ"
    EXIT = "ÇIKIŞ"


@dataclass(frozen=True)
class GateEvent:
    plate: str
    event_type: EventType
    timestamp: datetime


@dataclass(frozen=True)
class Visit:
    """Bir aracın otoparka bir girişi ve (varsa) çıkışı."""

    id: int
    plate: str
    entry_time: datetime
    exit_time: datetime | None
