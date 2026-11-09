import time
import urllib.request
from datetime import datetime

import numpy as np

from otopark.models import EventType, FrameAnalysis, GateEvent, PlateRead, Reading, ReadStatus
from otopark.preview import FpsCounter, LivePreview, OverlayInfo, describe, draw_overlay


def test_fps_counter_uses_recent_ticks():
    times = iter([0.0, 0.25, 0.5, 0.75, 1.0])
    counter = FpsCounter(window_seconds=2.0, clock=lambda: next(times))

    assert counter.tick() == 0.0
    for _ in range(4):
        fps = counter.tick()

    assert fps == 4.0


def test_describe_shows_progress_for_pending_plate():
    reading = Reading(PlateRead("20ABC123", 0.92), ReadStatus.PENDING, "20ABC123", votes=2)

    assert describe(reading, votes_required=3) == "20 ABC 123  92%  2/3"


def test_describe_uses_ascii_for_rejected_read():
    reading = Reading(PlateRead("ABCDEF", 0.40), ReadStatus.LOW_CONFIDENCE)

    assert describe(reading, votes_required=3) == "ABCDEF  40%  dusuk guven"


def test_draw_overlay_keeps_frame_untouched_and_draws_box():
    frame = np.zeros((360, 640, 3), dtype=np.uint8)
    reading = Reading(
        PlateRead("20ABC123", 0.9, box=(300, 200, 420, 240)),
        ReadStatus.CONFIRMED,
        "20ABC123",
    )
    event = GateEvent("20ABC123", EventType.ENTRY, datetime(2026, 11, 9, 8, 0))
    info = OverlayInfo(fps=4.8, process_ms=180, votes_required=3, recent_events=[event])

    image = draw_overlay(frame, FrameAnalysis([reading], [event]), info)

    assert image.shape == frame.shape
    assert not frame.any()
    assert image[220, 300].any()  # kutunun sol kenarı çizildi


def test_live_preview_serves_page_and_stream():
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    with LivePreview(port=0, votes_required=3) as preview:
        port = preview._server.server_address[1]
        page = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5).read()
        assert b'src="/stream"' in page

        stream = urllib.request.urlopen(f"http://127.0.0.1:{port}/stream", timeout=5)
        for _ in range(50):  # izleyici kaydolana kadar kare gönder
            preview.show(frame, FrameAnalysis([], []), 0.01)
            if preview._stream.has_viewers():
                preview.show(frame, FrameAnalysis([], []), 0.01)
                break
            time.sleep(0.05)
        chunk = stream.read(64)
        stream.close()

    assert chunk.startswith(b"--frame")
