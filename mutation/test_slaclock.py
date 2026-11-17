# ai-generated: 100% - GitHub Copilot wrote behavioural boundary tests from mutation/README.md and slaclock.py docstrings
from datetime import datetime, timedelta

import pytest

import slaclock


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [
        (1, 1, "P1"),
        (1, 2, "P2"),
        (2, 1, "P2"),
        (1, 3, "P3"),
        (2, 2, "P3"),
        (3, 1, "P3"),
        (2, 3, "P4"),
        (3, 2, "P4"),
        (3, 3, "P4"),
    ],
)
def test_priority_matrix(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency) == expected


@pytest.mark.parametrize(
    ("impact", "urgency"),
    [(0, 1), (4, 1), (1, 0), (1, 4), (2.0, 1), (1, 2.0), (True, 1), (1, False), ("1", 1)],
)
def test_priority_rejects_invalid_values(impact, urgency):
    with pytest.raises(ValueError):
        slaclock.priority_of(impact, urgency)


@pytest.mark.parametrize(
    ("impact", "urgency", "expected"),
    [(1, 1, "P1"), (1, 2, "P2"), (2, 2, "P2"), (3, 3, "P2")],
)
def test_vip_priority_floor(impact, urgency, expected):
    assert slaclock.priority_of(impact, urgency, vip=True) == expected


@pytest.mark.parametrize(
    ("priority", "expected"),
    [("P1", (15, 240)), ("P2", (60, 480)), ("P3", (240, 1440)), ("P4", (480, 4320))],
)
def test_targets(priority, expected):
    assert slaclock.targets(priority) == expected


@pytest.mark.parametrize("priority", ["p1", " P1", "P5", ""])
def test_targets_rejects_unknown_priority(priority):
    with pytest.raises(ValueError):
        slaclock.targets(priority)


@pytest.mark.parametrize(
    ("elapsed", "target", "expected"),
    [(0, 15, "ok"), (11, 15, "ok"), (12, 15, "warning"), (15, 15, "warning"), (16, 15, "breached")],
)
def test_sla_state_boundaries(elapsed, target, expected):
    assert slaclock.sla_state(elapsed, target) == expected


@pytest.mark.parametrize(("elapsed", "target"), [(-1, 15), (0, 0), (0, -1)])
def test_sla_state_rejects_invalid_clock_values(elapsed, target):
    with pytest.raises(ValueError):
        slaclock.sla_state(elapsed, target)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [
        (datetime(2026, 11, 16, 7, 59), False),
        (datetime(2026, 11, 16, 8, 0), True),
        (datetime(2026, 11, 16, 15, 59), True),
        (datetime(2026, 11, 16, 16, 0), False),
        (datetime(2026, 11, 20, 12, 0), True),
        (datetime(2026, 11, 21, 12, 0), False),
        (datetime(2026, 11, 22, 12, 0), False),
    ],
)
def test_business_time_window(moment, expected):
    assert slaclock.is_business_time(moment) is expected


@pytest.mark.parametrize(
    ("start", "minutes", "expected"),
    [
        (datetime(2026, 11, 16, 9, 15, 30), 0, datetime(2026, 11, 16, 9, 15)),
        (datetime(2026, 11, 16, 7, 30), 0, datetime(2026, 11, 16, 8, 0)),
        (datetime(2026, 11, 16, 16, 0), 0, datetime(2026, 11, 17, 8, 0)),
        (datetime(2026, 11, 20, 15, 30), 30, datetime(2026, 11, 20, 16, 0)),
        (datetime(2026, 11, 20, 15, 30), 31, datetime(2026, 11, 23, 8, 1)),
        (datetime(2026, 11, 21, 10, 0), 60, datetime(2026, 11, 23, 9, 0)),
    ],
)
def test_add_business_minutes_boundaries(start, minutes, expected):
    assert slaclock.add_business_minutes(start, minutes) == expected


def test_add_business_minutes_rejects_negative_duration():
    with pytest.raises(ValueError):
        slaclock.add_business_minutes(datetime(2026, 11, 16, 9, 0), -1)


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        (datetime(2026, 11, 16, 7, 0), datetime(2026, 11, 16, 17, 0), 480),
        (datetime(2026, 11, 20, 15, 30), datetime(2026, 11, 23, 8, 30), 60),
        (datetime(2026, 11, 16, 9, 0), datetime(2026, 11, 16, 9, 0), 0),
    ],
)
def test_business_minutes_between(start, end, expected):
    assert slaclock.business_minutes_between(start, end) == expected


def test_business_minutes_between_rejects_reverse_order_and_long_span():
    start = datetime(2026, 1, 1)
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(start, start - timedelta(minutes=1))
    with pytest.raises(ValueError):
        slaclock.business_minutes_between(start, start.replace(year=2027, month=1, day=3))


@pytest.mark.parametrize(
    ("priority", "breached", "reopens", "expected"),
    [
        ("P1", False, 0, 1),
        ("P2", False, 0, 1),
        ("P3", False, 0, 0),
        ("P4", False, 0, 0),
        ("P1", True, 0, 3),
        ("P2", True, 0, 2),
        ("P3", True, 0, 1),
        ("P4", False, 2, 1),
        ("P2", True, 2, 3),
    ],
)
def test_escalation_tier(priority, breached, reopens, expected):
    assert slaclock.escalation_tier(priority, breached, reopens) == expected


@pytest.mark.parametrize(("priority", "reopens"), [("P5", 0), ("P1", -1)])
def test_escalation_tier_rejects_invalid_values(priority, reopens):
    with pytest.raises(ValueError):
        slaclock.escalation_tier(priority, False, reopens)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("90m", 90),
        ("4h", 240),
        ("1h30m", 90),
        ("2d", 2880),
        ("1d4h", 1680),
        ("1d0h5m", 1445),
        ("0h60m", 60),
        (" 15m ", 15),
    ],
)
def test_parse_duration(text, expected):
    assert slaclock.parse_duration(text) == expected


@pytest.mark.parametrize("text", ["", "0m", "1.5h", "30m1h", "-5m", "1 h", "1H", "1h60m", "1d60m"])
def test_parse_duration_rejects_invalid_values(text):
    with pytest.raises(ValueError):
        slaclock.parse_duration(text)