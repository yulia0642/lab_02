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

    first_file_before = first_file.read_bytes()
    second_file_before = second_file.read_bytes()
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

    assert report["earliest_timestamp"] == "2026-10-23T10:15:00+00:00"
    assert report["latest_timestamp"] == "2026-10-23T10:18:00+00:00"
    assert report["skipped_count"] == 0
    assert first_file.read_bytes() == first_file_before
    assert second_file.read_bytes() == second_file_before


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


def test_cli_handles_mixed_timezones(tmp_path: Path) -> None:
    input_file = tmp_path / "events.jsonl"
    report_file = tmp_path / "report.json"

    input_file.write_text(
        '{"timestamp": "2026-10-23T10:15:00", '
        '"level": "INFO", "source": "server", '
        '"message": "First event"}\n'
        '{"timestamp": "2026-10-23T12:16:00+02:00", '
        '"level": "INFO", "source": "server", '
        '"message": "Second event"}\n',
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

    assert result.returncode == 0, result.stderr
    assert report_file.exists()

    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report["total_events"] == 2
    assert report["earliest_timestamp"] == "2026-10-23T10:15:00+00:00"
    assert report["latest_timestamp"] == "2026-10-23T10:16:00+00:00"


def test_csv_and_jsonl_produce_same_report(tmp_path: Path) -> None:
    csv_file = tmp_path / "events.csv"
    jsonl_file = tmp_path / "events.jsonl"
    csv_report_file = tmp_path / "csv_report.json"
    jsonl_report_file = tmp_path / "jsonl_report.json"

    csv_file.write_text(
        "timestamp,level,source,message\n"
        "2026-10-23T10:15:00,INFO,server,Server started\n"
        "2026-10-23T10:16:00,ERROR,database,Connection failed\n"
        "2026-10-23T10:17:00,CRITICAL,server,Server unavailable\n"
        "2026-10-23T10:18:00,WARNING,database,Slow response\n",
        encoding="utf-8",
    )

    jsonl_file.write_text(
        '{"timestamp": "2026-10-23T10:15:00", '
        '"level": "INFO", "source": "server", '
        '"message": "Server started"}\n'
        '{"timestamp": "2026-10-23T10:16:00", '
        '"level": "ERROR", "source": "database", '
        '"message": "Connection failed"}\n'
        '{"timestamp": "2026-10-23T10:17:00", '
        '"level": "CRITICAL", "source": "server", '
        '"message": "Server unavailable"}\n'
        '{"timestamp": "2026-10-23T10:18:00", '
        '"level": "WARNING", "source": "database", '
        '"message": "Slow response"}\n',
        encoding="utf-8",
    )

    csv_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(csv_file),
            "--format",
            "csv",
            "--output",
            str(csv_report_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    jsonl_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(jsonl_file),
            "--format",
            "jsonl",
            "--output",
            str(jsonl_report_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert csv_result.returncode == 0, csv_result.stderr
    assert jsonl_result.returncode == 0, jsonl_result.stderr

    csv_report = json.loads(csv_report_file.read_text(encoding="utf-8"))
    jsonl_report = json.loads(jsonl_report_file.read_text(encoding="utf-8"))

    assert csv_report == jsonl_report


def test_cli_empty_csv_creates_zero_report(tmp_path: Path) -> None:
    input_file = tmp_path / "empty.csv"
    report_file = tmp_path / "report.json"

    input_file.write_text("", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "csv",
            "--output",
            str(report_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert report_file.exists()

    report = json.loads(report_file.read_text(encoding="utf-8"))

    assert report == {
        "total_events": 0,
        "events_by_level": {},
        "events_by_source": {},
        "top_error_sources": [],
        "earliest_timestamp": None,
        "latest_timestamp": None,
        "skipped_count": 0,
    }
