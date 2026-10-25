from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from streamstats.models import Event


@dataclass
class AnalysisStats:
    total_events: int = 0
    events_by_level: dict[str, int] = field(default_factory=dict)
    events_by_source: dict[str, int] = field(default_factory=dict)
    error_sources: dict[str, int] = field(default_factory=dict)
    earliest_timestamp: datetime | None = None
    latest_timestamp: datetime | None = None


def analyze_events(
    events: Iterable[Event],
    stats: AnalysisStats | None = None,
) -> AnalysisStats:
    if stats is None:
        stats = AnalysisStats()

    for event in events:
        stats.total_events += 1

        if event.level not in stats.events_by_level:
            stats.events_by_level[event.level] = 0

        stats.events_by_level[event.level] += 1

        if event.source not in stats.events_by_source:
            stats.events_by_source[event.source] = 0

        stats.events_by_source[event.source] += 1

        if event.level == "ERROR" or event.level == "CRITICAL":
            if event.source not in stats.error_sources:
                stats.error_sources[event.source] = 0

            stats.error_sources[event.source] += 1

        if (
            stats.earliest_timestamp is None
            or event.timestamp < stats.earliest_timestamp
        ):
            stats.earliest_timestamp = event.timestamp

        if (
            stats.latest_timestamp is None
            or event.timestamp > stats.latest_timestamp
        ):
            stats.latest_timestamp = event.timestamp

    return stats


def get_top_error_sources(
    stats: AnalysisStats,
    limit: int = 5,
) -> list[tuple[str, int]]:
    source_counts = list(stats.error_sources.items())
    source_counts.sort(key=lambda item: (-item[1], item[0]))

    return source_counts[:limit]