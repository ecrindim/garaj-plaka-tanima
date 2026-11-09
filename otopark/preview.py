"""Canlı önizleme: kamera görüntüsünü okuma bilgileriyle tarayıcıya yayınlar.

`python -m otopark --preview` ile açılır, sonra tarayıcıda
http://<pi-ip-adresi>:8000 adresine gidilir.
"""

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

from otopark.camera import Frame
from otopark.models import FrameAnalysis, GateEvent, Reading, ReadStatus
from otopark.plate_validator import format_for_display

logger = logging.getLogger("otopark.preview")

# OpenCV'nin yazı tipi Türkçe karakterleri çizemez.
_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

# BGR renkler
_COLORS = {
    ReadStatus.LOW_CONFIDENCE: (160, 160, 160),
    ReadStatus.INVALID: (60, 60, 230),
    ReadStatus.PENDING: (0, 210, 255),
    ReadStatus.CONFIRMED: (80, 220, 80),
}
_WHITE = (255, 255, 255)
_FONT = cv2.FONT_HERSHEY_SIMPLEX


class FpsCounter:
    """Son birkaç saniyedeki kare sayısından FPS hesaplar."""

    def __init__(self, window_seconds: float = 2.0, clock: Callable[[], float] = time.monotonic):
        self._window = window_seconds
        self._clock = clock
        self._ticks: deque[float] = deque()

    def tick(self) -> float:
        now = self._clock()
        self._ticks.append(now)
        while now - self._ticks[0] > self._window:
            self._ticks.popleft()
        if len(self._ticks) < 2:
            return 0.0
        return (len(self._ticks) - 1) / (self._ticks[-1] - self._ticks[0])


@dataclass(frozen=True)
class OverlayInfo:
    fps: float
    process_ms: float
    votes_required: int
    recent_events: list[GateEvent]


def describe(reading: Reading, votes_required: int) -> str:
    """Okumayı tek satırlık etikete çevirir, ör. '34 ABC 123  92%  2/3'."""
    text = format_for_display(reading.plate) if reading.plate else reading.read.text
    status = (
        f"{reading.votes}/{votes_required}"
        if reading.status is ReadStatus.PENDING
        else reading.status.value
    )
    return f"{text}  {reading.read.confidence:.0%}  {status}".translate(_ASCII)


def draw_overlay(frame: Frame, analysis: FrameAnalysis, info: OverlayInfo) -> np.ndarray:
    image = np.ascontiguousarray(frame[:, :, :3]).copy()
    for reading in analysis.readings:
        _draw_box(image, reading, info.votes_required)
    _draw_panel(image, analysis, info)
    return image


def _draw_box(image: np.ndarray, reading: Reading, votes_required: int) -> None:
    if reading.read.box is None:
        return
    x1, y1, x2, y2 = reading.read.box
    color = _COLORS[reading.status]
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    label = describe(reading, votes_required)
    (w, h), _ = cv2.getTextSize(label, _FONT, 0.6, 2)
    top = max(y1 - h - 10, 0)
    cv2.rectangle(image, (x1, top), (x1 + w + 8, top + h + 10), color, -1)
    cv2.putText(image, label, (x1 + 4, top + h + 4), _FONT, 0.6, (0, 0, 0), 2, cv2.LINE_AA)


def _draw_panel(image: np.ndarray, analysis: FrameAnalysis, info: OverlayInfo) -> None:
    lines: list[tuple[str, tuple[int, int, int]]] = [
        (f"FPS: {info.fps:.1f}   Islem: {info.process_ms:.0f} ms", _WHITE),
        (f"Okunan plaka: {len(analysis.readings)}", _WHITE),
    ]
    lines += [
        (describe(r, info.votes_required), _COLORS[r.status]) for r in analysis.readings
    ]
    if info.recent_events:
        lines.append(("Son olaylar:", _WHITE))
        lines += [
            (
                f"{e.timestamp:%H:%M:%S}  {e.event_type.value:<6} {format_for_display(e.plate)}"
                .translate(_ASCII),
                _WHITE,
            )
            for e in reversed(info.recent_events)
        ]

    line_height = 24
    width = max(cv2.getTextSize(text, _FONT, 0.55, 1)[0][0] for text, _ in lines) + 20
    height = line_height * len(lines) + 12
    region = image[:height, :width]
    region[:] = (region * 0.35).astype(image.dtype)  # yarı saydam koyu zemin
    for i, (text, color) in enumerate(lines):
        y = 26 + i * line_height
        cv2.putText(image, text, (10, y), _FONT, 0.55, color, 1, cv2.LINE_AA)


class LivePreview:
    """Her işlenen kareyi çizer ve MJPEG olarak HTTP üzerinden yayınlar."""

    def __init__(self, port: int, votes_required: int, max_events: int = 5) -> None:
        self._votes_required = votes_required
        self._fps = FpsCounter()
        self._events: deque[GateEvent] = deque(maxlen=max_events)
        self._stream = _FrameStream()
        self._server = ThreadingHTTPServer(("0.0.0.0", port), _make_handler(self._stream))
        self._server.daemon_threads = True
        self._port = port

    def __enter__(self) -> "LivePreview":
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        logger.info("Canlı önizleme: http://<pi-ip-adresi>:%d", self._port)
        return self

    def __exit__(self, *_exc_info) -> None:
        self._stream.close()
        self._server.shutdown()
        self._server.server_close()

    def show(self, frame: Frame, analysis: FrameAnalysis, process_seconds: float) -> None:
        self._events.extend(analysis.events)
        info = OverlayInfo(
            fps=self._fps.tick(),
            process_ms=process_seconds * 1000,
            votes_required=self._votes_required,
            recent_events=list(self._events),
        )
        if not self._stream.has_viewers():
            return  # İzleyen yoksa çizip sıkıştırmaya gerek yok
        image = draw_overlay(frame, analysis, info)
        ok, jpeg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ok:
            self._stream.publish(jpeg.tobytes())


class _FrameStream:
    """Son JPEG karesini izleyicilere dağıtır."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._jpeg: bytes | None = None
        self._sequence = 0
        self._viewers = 0
        self._closed = False

    def has_viewers(self) -> bool:
        return self._viewers > 0

    def publish(self, jpeg: bytes) -> None:
        with self._condition:
            self._jpeg = jpeg
            self._sequence += 1
            self._condition.notify_all()

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def frames(self):
        """Yeni kare geldikçe JPEG baytlarını verir."""
        with self._condition:
            self._viewers += 1
        try:
            seen = 0
            while True:
                with self._condition:
                    self._condition.wait_for(
                        lambda: self._closed or self._sequence != seen, timeout=1.0
                    )
                    if self._closed:
                        return
                    if self._sequence == seen:
                        continue
                    seen, jpeg = self._sequence, self._jpeg
                yield jpeg
        finally:
            with self._condition:
                self._viewers -= 1


_PAGE = """<!doctype html>
<html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Otopark Canlı</title>
<style>body{margin:0;background:#111;display:flex;justify-content:center}
img{max-width:100%;height:auto}</style></head>
<body><img src="/stream" alt="Canlı kamera"></body></html>
""".encode("utf-8")


def _make_handler(stream: _FrameStream) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/":
                self._send_page()
            elif self.path == "/stream":
                self._send_stream()
            else:
                self.send_error(404)

        def _send_page(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(_PAGE)))
            self.end_headers()
            self.wfile.write(_PAGE)

        def _send_stream(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                for jpeg in stream.frames():
                    self.wfile.write(
                        b"--frame\r\nContent-Type: image/jpeg\r\n"
                        + f"Content-Length: {len(jpeg)}\r\n\r\n".encode()
                        + jpeg
                        + b"\r\n"
                    )
            except (BrokenPipeError, ConnectionResetError):
                pass  # İzleyici sayfayı kapattı

        def log_message(self, *_args) -> None:
            pass  # Her istek için log basma

    return Handler
