"""Kullanım: python -m otopark [--preview]"""

import argparse
import logging
import time
from collections.abc import Callable
from contextlib import ExitStack

from otopark.camera import Frame, FrameSource, PiCameraSource
from otopark.config import Settings
from otopark.gate_service import GateService
from otopark.models import FrameAnalysis, GateEvent
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


FrameObserver = Callable[[Frame, FrameAnalysis, float], None]


def run(
    camera: FrameSource,
    monitor: PlateMonitor,
    interval_seconds: float,
    observer: FrameObserver | None = None,
) -> None:
    while True:
        frame = camera.capture()
        started = time.monotonic()
        analysis = monitor.analyze(frame)
        process_seconds = time.monotonic() - started
        for event in analysis.events:
            log_event(event)
        if observer is not None:
            observer(frame, analysis, process_seconds)
        time.sleep(interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m otopark")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Kamera görüntüsünü okuma bilgileriyle tarayıcıda canlı göster",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = Settings()
    repository = VisitRepository(settings.database_path)
    try:
        monitor = build_monitor(settings, repository)
        with ExitStack() as stack:
            camera = stack.enter_context(PiCameraSource(settings.frame_size))
            observer = None
            if args.preview:
                from otopark.preview import LivePreview

                preview = LivePreview(settings.preview_port, settings.votes_required)
                observer = stack.enter_context(preview).show
            logger.info("Sistem çalışıyor. Durdurmak için Ctrl+C.")
            run(camera, monitor, settings.frame_interval_seconds, observer)
    except KeyboardInterrupt:
        logger.info("Sistem durduruldu.")
    finally:
        repository.close()


if __name__ == "__main__":
    main()
