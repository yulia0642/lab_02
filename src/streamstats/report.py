import json
from pathlib import Path

from streamstats.analysis import AnalysisStats, get_top_error_sources


def build_report(
    stats: AnalysisStats,
    skipped_count: int = 0,
) -> dict[str, object]:
    earliest_timestamp = None
    latest_timestamp = None

    if stats.earliest_timestamp is not None:
        earliest_timestamp = stats.earliest_timestamp.isoformat()

    if stats.latest_timestamp is not None:
        latest_timestamp = stats.latest_timestamp.isoformat()

    top_error_sources = []

    for source, count in get_top_error_sources(stats):
        top_error_sources.append(
            {
                "source": source,
                "count": count,
            }
        )

    report = {
        "total_events": stats.total_events,
        "events_by_level": stats.events_by_level,
        "events_by_source": stats.events_by_source,
        "top_error_sources": top_error_sources,
        "earliest_timestamp": earliest_timestamp,
        "latest_timestamp": latest_timestamp,
        "skipped_count": skipped_count,
    }

    return report


def write_report(report: dict[str, object], path: Path) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)