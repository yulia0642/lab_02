from datetime import datetime

from streamstats.analysis import (
    AnalysisStats,
    analyze_events,
    get_top_error_sources,
)
from streamstats.models import Event


def test_analyze_events() -> None:
    events = [
        Event(
            timestamp=datetime.fromisoformat("2026-10-23T10:15:00"),
            level="INFO",
            source="server",
            message="Server started",
        ),
        Event(
            timestamp=datetime.fromisoformat("2026-10-23T10:17:00"),
            level="ERROR",
            source="database",
            message="Connection failed",
        ),
        Event(
            timestamp=datetime.fromisoformat("2026-10-23T10:16:00"),
            level="CRITICAL",
            source="database",
            message="Database unavailable",
        ),
        Event(
            timestamp=datetime.fromisoformat("2026-10-23T10:18:00"),
            level="WARNING",
            source="server",
            message="Slow response",
        ),
    ]

    stats = analyze_events(events)

    assert stats.total_events == 4

    assert stats.events_by_level == {
        "INFO": 1,
        "ERROR": 1,
        "CRITICAL": 1,
        "WARNING": 1,
    }

    assert stats.events_by_source == {
        "server": 2,
        "database": 2,
    }

    assert stats.error_sources == {
        "database": 2,
    }

    assert stats.earliest_timestamp == datetime.fromisoformat(
        "2026-10-23T10:15:00"
    )

    assert stats.latest_timestamp == datetime.fromisoformat(
        "2026-10-23T10:18:00"
    )


def test_analyze_events_accumulates_statistics() -> None:
    first_event = Event(
        timestamp=datetime.fromisoformat("2026-10-23T10:15:00"),
        level="INFO",
        source="server",
        message="Server started",
    )

    second_event = Event(
        timestamp=datetime.fromisoformat("2026-10-23T10:20:00"),
        level="ERROR",
        source="database",
        message="Connection failed",
    )

    stats = analyze_events([first_event])
    analyze_events([second_event], stats)

    assert stats.total_events == 2
    assert stats.events_by_level == {"INFO": 1, "ERROR": 1}
    assert stats.events_by_source == {"server": 1, "database": 1}
    assert stats.error_sources == {"database": 1}


def test_get_top_error_sources() -> None:
    stats = AnalysisStats(
        error_sources={
            "server": 2,
            "database": 2,
            "auth": 1,
            "payment": 3,
            "cache": 2,
            "queue": 1,
        }
    )

    top_sources = get_top_error_sources(stats)

    assert top_sources == [
        ("payment", 3),
        ("cache", 2),
        ("database", 2),
        ("server", 2),
        ("auth", 1),
    ]
