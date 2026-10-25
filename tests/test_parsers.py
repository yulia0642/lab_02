from pathlib import Path

import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.parsers import ParserStats, parse_csv, parse_jsonl


def test_parse_csv(tmp_path: Path) -> None:
    path = tmp_path / "events.csv"

    path.write_text(
        "timestamp,level,source,message\n"
        "2026-10-23T10:15:00,INFO,server,Сервер запущен\n",
        encoding="utf-8",
    )

    events = list(parse_csv(path))

    assert len(events) == 1

    event = events[0]
    assert event.level == "INFO"
    assert event.source == "server"
    assert event.message == "Сервер запущен"


def test_parse_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"

    path.write_text(
        '{"timestamp": "2026-10-23T10:15:00", '
        '"level": "INFO", "source": "server", '
        '"message": "Сервер запущен"}\n',
        encoding="utf-8",
    )

    events = list(parse_jsonl(path))

    assert len(events) == 1

    event = events[0]
    assert event.level == "INFO"
    assert event.source == "server"
    assert event.message == "Сервер запущен"


def test_parse_empty_csv(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")

    events = list(parse_csv(path))

    assert events == []


def test_parse_empty_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")

    events = list(parse_jsonl(path))

    assert events == []


def test_invalid_csv_row(tmp_path: Path) -> None:
    path = tmp_path / "events.csv"

    path.write_text(
        "timestamp,level,source,message\n"
        "2026-10-23T10:15:00,INFO,,Server started\n",
        encoding="utf-8",
    )

    with pytest.raises(InvalidEventError, match="line 2"):
        list(parse_csv(path))


def test_invalid_jsonl_line(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text(
        '{"timestamp": \n',
        encoding="utf-8",
    )

    with pytest.raises(InvalidEventError, match="line 1"):
        list(parse_jsonl(path))


def test_invalid_timestamp(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"

    path.write_text(
        '{"timestamp": "not-a-date", "level": "INFO", '
        '"source": "server", "message": "Started"}\n',
        encoding="utf-8",
    )

    with pytest.raises(InvalidTimestampError, match="timestamp"):
        list(parse_jsonl(path))


def test_parse_csv_skip_invalid(tmp_path: Path) -> None:
    path = tmp_path / "events.csv"

    path.write_text(
        "timestamp,level,source,message\n"
        "2026-10-23T10:15:00,INFO,,Invalid source\n"
        "2026-10-23T10:16:00,INFO,server,Server started\n",
        encoding="utf-8",
    )

    stats = ParserStats()
    events = list(parse_csv(path, skip_invalid=True, stats=stats))

    assert len(events) == 1
    assert events[0].message == "Server started"
    assert stats.skipped_count == 1


def test_parse_jsonl_skip_invalid(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"

    path.write_text(
        "not valid JSON\n"
        '{"timestamp": "2026-10-23T10:16:00", '
        '"level": "INFO", "source": "server", '
        '"message": "Server started"}\n',
        encoding="utf-8",
    )

    stats = ParserStats()
    events = list(parse_jsonl(path, skip_invalid=True, stats=stats))

    assert len(events) == 1
    assert events[0].message == "Server started"
    assert stats.skipped_count == 1