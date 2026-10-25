import json
from datetime import datetime
from pathlib import Path

from streamstats.analysis import AnalysisStats
from streamstats.report import build_report, write_report


def test_build_report() -> None:
    stats = AnalysisStats(
        total_events=2,
        events_by_level={
            "INFO": 1,
            "ERROR": 1,
        },
        events_by_source={
            "server": 1,
            "database": 1,
        },
        error_sources={
            "database": 1,
        },
        earliest_timestamp=datetime.fromisoformat("2026-10-23T10:15:00"),
        latest_timestamp=datetime.fromisoformat("2026-10-23T10:20:00"),
    )

    report = build_report(stats, skipped_count=3)

    assert report["total_events"] == 2
    assert report["events_by_level"] == {
        "INFO": 1,
        "ERROR": 1,
    }
    assert report["events_by_source"] == {
        "server": 1,
        "database": 1,
    }
    assert report["top_error_sources"] == [
        {
            "source": "database",
            "count": 1,
        }
    ]
    assert report["earliest_timestamp"] == "2026-10-23T10:15:00"
    assert report["latest_timestamp"] == "2026-10-23T10:20:00"
    assert report["skipped_count"] == 3


def test_write_report_with_unicode(tmp_path: Path) -> None:
    path = tmp_path / "report.json"

    report = {
        "message": "Ошибка соединения",
        "total_events": 1,
    }

    write_report(report, path)

    saved_text = path.read_text(encoding="utf-8")
    saved_report = json.loads(saved_text)

    assert "Ошибка соединения" in saved_text
    assert saved_report == report