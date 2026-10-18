"""Unit tests para IdleSessionTimer (sem Qt)."""

from __future__ import annotations

from erp.shared.ui.idle_timer import IdleSessionTimer


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def advance(self, seconds: float) -> None:
        self.now += seconds

    def __call__(self) -> float:
        return self.now


def test_idle_timer_not_expired_when_active() -> None:
    clock = FakeClock()
    timer = IdleSessionTimer(timeout_seconds=600.0, clock=clock)

    assert timer.is_expired() is False
    assert timer.seconds_until_expiry() == 600.0


def test_idle_timer_expires_after_timeout() -> None:
    clock = FakeClock()
    timer = IdleSessionTimer(timeout_seconds=600.0, clock=clock)

    clock.advance(600.0)
    assert timer.is_expired() is True
    assert timer.seconds_until_expiry() == 0.0


def test_idle_timer_register_activity_resets() -> None:
    clock = FakeClock()
    timer = IdleSessionTimer(timeout_seconds=600.0, clock=clock)

    clock.advance(300.0)
    timer.register_activity()
    clock.advance(400.0)

    assert timer.is_expired() is False
    assert timer.seconds_until_expiry() == 200.0


def test_idle_timer_timeout_must_be_positive() -> None:
    import pytest

    with pytest.raises(ValueError):
        IdleSessionTimer(timeout_seconds=0)


def test_idle_timer_default_clock_is_monotonic() -> None:
    timer = IdleSessionTimer(timeout_seconds=60.0)
    first = timer.seconds_until_expiry()
    assert first <= 60.0