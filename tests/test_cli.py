import json
import subprocess
import sys
from pathlib import Path


def test_cli_analyze_multiple_csv_files(tmp_path: Path) -> None:
    first_file = tmp_path / "first.csv"
    second_file = tmp_path / "second.csv"
    report_file = tmp_path / "report.json"

    first_file.write_text(
        "timestamp,level,source,message\n"
        "2026-10-23T10:15:00,INFO,server,Server started\n"
        "2026-10-23T10:16:00,ERROR,database,Connection failed\n",
        encoding="utf-8",
    )

    second_file.write_text(
        "timestamp,level,source,message\n"
        "2026-10-23T10:17:00,CRITICAL,database,Database unavailable\n"
        "2026-10-23T10:18:00,WARNING,server,Slow response\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(first_file),
            str(second_file),
            "--format",
            "csv",
            "--output",
            str(report_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert report_file.exists()

    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report["total_events"] == 4

    assert report["events_by_level"] == {
        "INFO": 1,
        "ERROR": 1,
        "CRITICAL": 1,
        "WARNING": 1,
    }

    assert report["events_by_source"] == {
        "server": 2,
        "database": 2,
    }

    assert report["top_error_sources"] == [
        {
            "source": "database",
            "count": 2,
        }
    ]

    assert report["earliest_timestamp"] == "2026-10-23T10:15:00"
    assert report["latest_timestamp"] == "2026-10-23T10:18:00"
    assert report["skipped_count"] == 0


def test_cli_skip_invalid_jsonl(tmp_path: Path) -> None:
    input_file = tmp_path / "events.jsonl"
    report_file = tmp_path / "report.json"

    input_file.write_text(
        "not valid JSON\n"
        '{"timestamp": "2026-10-23T10:16:00", '
        '"level": "INFO", "source": "server", '
        '"message": "Server started"}\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "jsonl",
            "--output",
            str(report_file),
            "--skip-invalid",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "WARNING" in result.stderr
    assert "line 1" in result.stderr
    assert report_file.exists()

    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report["total_events"] == 1
    assert report["skipped_count"] == 1


def test_cli_stop_on_invalid_jsonl(tmp_path: Path) -> None:
    input_file = tmp_path / "events.jsonl"
    report_file = tmp_path / "report.json"

    input_file.write_text(
        "not valid JSON\n"
        '{"timestamp": "2026-10-23T10:16:00", '
        '"level": "INFO", "source": "server", '
        '"message": "Server started"}\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "jsonl",
            "--output",
            str(report_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "line 1" in result.stderr
    assert "invalid JSON" in result.stderr
    assert not report_file.exists()