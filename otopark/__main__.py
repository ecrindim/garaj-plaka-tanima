"""Kullanım: python -m otopark"""

import logging
import time

from otopark.camera import FrameSource, PiCameraSource
from otopark.config import Settings
from otopark.gate_service import GateService
from otopark.models import GateEvent
from otopark.plate_confirmer import PlateConfirmer
from otopark.plate_monitor import PlateMonitor
from otopark.plate_reader import FastAlprReader
from otopark.plate_validator import TurkishPlateValidator, format_for_display
from otopark.visit_repository import VisitRepository

logger = logging.getLogger("otopark")


def build_monitor(settings: Settings, repository: VisitRepository) -> PlateMonitor:
    return PlateMonitor(
        reader=FastAlprReader(settings.detector_model, settings.ocr_model),
        validator=TurkishPlateValidator(),
        confirmer=PlateConfirmer(
            settings.votes_required,
            settings.vote_window_seconds,
            settings.quiet_period_seconds,
        ),
        gate=GateService(repository),
        min_confidence=settings.min_confidence,
    )


def log_event(event: GateEvent) -> None:
    logger.info(
        "%-6s %-12s %s",
        event.event_type.value,
        format_for_display(event.plate),
        event.timestamp.strftime("%d.%m.%Y %H:%M:%S"),
    )


def run(camera: FrameSource, monitor: PlateMonitor, interval_seconds: float) -> None:
    while True:
        for event in monitor.process(camera.capture()):
            log_event(event)
        time.sleep(interval_seconds)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = Settings()
    repository = VisitRepository(settings.database_path)
    try:
        monitor = build_monitor(settings, repository)
        with PiCameraSource(settings.frame_size) as camera:
            logger.info("Sistem çalışıyor. Durdurmak için Ctrl+C.")
            run(camera, monitor, settings.frame_interval_seconds)
    except KeyboardInterrupt:
        logger.info("Sistem durduruldu.")
    finally:
        repository.close()


if __name__ == "__main__":
    main()
