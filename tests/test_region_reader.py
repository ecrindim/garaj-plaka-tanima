import numpy as np
import pytest

from otopark.models import PlateRead
from otopark.plate_reader import RegionReader, region_to_pixels


class RecordingReader:
    def __init__(self, reads: list[PlateRead]) -> None:
        self.reads = reads
        self.frames = []

    def read(self, frame) -> list[PlateRead]:
        self.frames.append(frame)
        return self.reads


def test_region_to_pixels_scales_to_frame():
    assert region_to_pixels((0.25, 0.5, 0.75, 1.0), 1280, 720) == (320, 360, 960, 720)


@pytest.mark.parametrize("region", [(0.5, 0, 0.4, 1), (0, 0, 1.2, 1), (-0.1, 0, 1, 1)])
def test_invalid_region_is_rejected_at_startup(region):
    with pytest.raises(ValueError):
        RegionReader(RecordingReader([]), region)


def test_reader_sees_only_region_and_boxes_map_back_to_full_frame():
    inner = RecordingReader(
        [PlateRead("20ABC123", 0.9, box=(10, 20, 110, 50)), PlateRead("X", 0.5)]
    )
    reader = RegionReader(inner, (0.25, 0.5, 0.75, 1.0))

    reads = reader.read(np.zeros((720, 1280, 3), dtype=np.uint8))

    assert inner.frames[0].shape == (360, 640, 3)
    assert reads[0].box == (330, 380, 430, 410)
    assert reads[1].box is None
