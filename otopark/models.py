from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class PlateRead:
    """Modelin tek bir karede okuduğu ham plaka metni."""

    text: str
    confidence: float
    box: tuple[int, int, int, int] | None = None  # (x1, y1, x2, y2) piksel


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


class ReadStatus(Enum):
    LOW_CONFIDENCE = "düşük güven"
    INVALID = "geçersiz format"
    PENDING = "doğrulanıyor"
    CONFIRMED = "onaylandı"


@dataclass(frozen=True)
class Reading:
    """Bir okumanın sistemde ne olduğu: elendi mi, doğrulanıyor mu, onaylandı mı."""

    read: PlateRead
    status: ReadStatus
    plate: str | None = None  # Geçerli formattaysa normalize edilmiş plaka
    votes: int = 0            # PENDING iken şimdiye kadarki okuma sayısı


@dataclass(frozen=True)
class FrameAnalysis:
    readings: list[Reading]
    events: list[GateEvent]
