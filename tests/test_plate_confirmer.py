from otopark.plate_confirmer import PlateConfirmer


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def make_confirmer(clock: FakeClock) -> PlateConfirmer:
    return PlateConfirmer(
        votes_required=3, window_seconds=2, quiet_period_seconds=10, clock=clock
    )


def test_confirms_after_enough_votes():
    clock = FakeClock()
    confirmer = make_confirmer(clock)
    assert [confirmer.submit("20ABC123") for _ in range(3)] == [False, False, True]


def test_ignores_votes_outside_window():
    clock = FakeClock()
    confirmer = make_confirmer(clock)
    confirmer.submit("20ABC123")
    confirmer.submit("20ABC123")
    clock.now = 5
    assert confirmer.submit("20ABC123") is False


def test_does_not_reconfirm_while_plate_stays_in_view():
    clock = FakeClock()
    confirmer = make_confirmer(clock)
    for _ in range(3):
        confirmer.submit("20ABC123")
    for second in range(1, 30):
        clock.now = second
        assert confirmer.submit("20ABC123") is False


def test_confirms_again_after_quiet_period():
    clock = FakeClock()
    confirmer = make_confirmer(clock)
    for _ in range(3):
        confirmer.submit("20ABC123")
    clock.now = 60
    assert [confirmer.submit("20ABC123") for _ in range(3)] == [False, False, True]
