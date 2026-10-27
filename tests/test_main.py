import json
import sys
from argparse import Namespace
from pathlib import Path

import pytest

from streamstats.__main__ import main, run_analyze


def test_main_analyzes_csv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_file = tmp_path / "events.csv"
    report_file = tmp_path / "report.json"

    input_file.write_text(
        "timestamp,level,source,message\n"
        "2026-10-23T10:00:00,INFO,app,Started\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "csv",
            "--output",
            str(report_file),
        ],
    )

    result = main()

    assert result == 0

    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["events_by_level"] == {"INFO": 1}


def test_main_skips_invalid_jsonl(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_file = tmp_path / "events.jsonl"
    report_file = tmp_path / "report.json"

    input_file.write_text(
        '{"timestamp":"2026-10-23T10:00:00",'
        '"level":"INFO","source":"app","message":"Started"}\n'
        "{invalid json}\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "jsonl",
            "--output",
            str(report_file),
            "--skip-invalid",
        ],
    )

    result = main()

    assert result == 0

    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["skipped_count"] == 1


def test_main_handles_missing_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_file = tmp_path / "missing.csv"
    report_file = tmp_path / "report.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "csv",
            "--output",
            str(report_file),
        ],
    )

    result = main()

    assert result == 2
    assert "Входной файл не найден" in capsys.readouterr().err


def test_main_rejects_same_input_and_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_file = tmp_path / "events.csv"

    input_file.write_text(
        "timestamp,level,source,message\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "csv",
            "--output",
            str(input_file),
        ],
    )

    result = main()

    assert result == 2
    assert "не должен совпадать" in capsys.readouterr().err


def test_main_handles_output_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_file = tmp_path / "events.csv"
    output_directory = tmp_path / "report_directory"
    output_directory.mkdir()

    input_file.write_text(
        "timestamp,level,source,message\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "streamstats",
            "analyze",
            str(input_file),
            "--format",
            "csv",
            "--output",
            str(output_directory),
        ],
    )

    result = main()

    assert result == 2
    assert "Ошибка при работе с файлом" in capsys.readouterr().err


def test_run_analyze_rejects_unsupported_format(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    input_file = tmp_path / "events.csv"
    report_file = tmp_path / "report.json"

    input_file.write_text(
        "timestamp,level,source,message\n",
        encoding="utf-8",
    )

    arguments = Namespace(
        inputs=[input_file],
        output=report_file,
        format="xml",
        skip_invalid=False,
    )

    result = run_analyze(arguments)

    assert result == 2
    assert "Неподдерживаемый формат" in capsys.readouterr().err