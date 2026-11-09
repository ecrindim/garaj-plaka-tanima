from typing import Any, Protocol

Frame = Any  # BGR sıralı numpy dizisi


class FrameSource(Protocol):
    def capture(self) -> Frame: ...


class PiCameraSource:
    """Raspberry Pi kamerasından (AI Camera dahil) kare okur."""

    def __init__(self, frame_size: tuple[int, int]) -> None:
        from picamera2 import Picamera2

        self._camera = Picamera2()
        # Picamera2'de "RGB888", numpy'da BGR sıralı dizi verir; OpenCV ile uyumludur.
        config = self._camera.create_video_configuration(
            main={"size": frame_size, "format": "RGB888"}
        )
        self._camera.configure(config)

    def __enter__(self) -> "PiCameraSource":
        self._camera.start()
        return self

    def __exit__(self, *_exc_info) -> None:
        self._camera.stop()
        self._camera.close()

    def capture(self) -> Frame:
        return self._camera.capture_array()
