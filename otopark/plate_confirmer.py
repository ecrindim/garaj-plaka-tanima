import time
from collections import deque
from collections.abc import Callable

Clock = Callable[[], float]


class PlateConfirmer:
    """Bir plakayı ancak kısa sürede birkaç kez okunduğunda onaylar.

    Tek karedeki hatalı okumaları eler. Onaylanan plaka kamerada görülmeye
    devam ettiği sürece tekrar onaylanmaz; `quiet_period_seconds` boyunca hiç
    görülmezse yeniden algılanabilir hale gelir.
    """

    def __init__(
        self,
        votes_required: int,
        window_seconds: float,
        quiet_period_seconds: float,
        clock: Clock = time.monotonic,
    ) -> None:
        self._votes_required = votes_required
        self._window = window_seconds
        self._quiet_period = quiet_period_seconds
        self._clock = clock
        self._sightings: dict[str, deque[float]] = {}
        self._last_seen_after_confirm: dict[str, float] = {}

    def submit(self, plate: str) -> bool:
        """Okumayı kaydeder; plaka bu okumayla onaylandıysa True döner."""
        now = self._clock()
        self._forget_stale(now)

        if plate in self._last_seen_after_confirm:
            self._last_seen_after_confirm[plate] = now
            return False

        sightings = self._sightings.setdefault(plate, deque())
        sightings.append(now)
        if len(sightings) < self._votes_required:
            return False

        del self._sightings[plate]
        self._last_seen_after_confirm[plate] = now
        return True

    def _forget_stale(self, now: float) -> None:
        for sightings in self._sightings.values():
            while sightings and now - sightings[0] > self._window:
                sightings.popleft()
        self._sightings = {p: s for p, s in self._sightings.items() if s}
        self._last_seen_after_confirm = {
            plate: seen
            for plate, seen in self._last_seen_after_confirm.items()
            if now - seen < self._quiet_period
        }
