import csv
import json
import logging
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import Event

logger = logging.getLogger(__name__)


@dataclass
class ParserStats:
    skipped_count: int = 0

ALLOWED_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def create_event(
    row: Mapping[str, object],
    filename: str,
    line_number: int,
) -> Event:
    timestamp_value = row.get("timestamp")

    if not isinstance(timestamp_value, str) or not timestamp_value:
        raise InvalidTimestampError(
            f"{filename}: line {line_number}: invalid field 'timestamp'"
        )

    try:
        timestamp = datetime.fromisoformat(timestamp_value)
    except ValueError as error:
        raise InvalidTimestampError(
            f"{filename}: line {line_number}: invalid field 'timestamp'"
        ) from error
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    else:
        timestamp = timestamp.astimezone(UTC)

    level = row.get("level")
    if not isinstance(level, str) or level not in ALLOWED_LEVELS:
        raise InvalidEventError(
            f"{filename}: line {line_number}: invalid field 'level'"
        )

    source = row.get("source")
    if not isinstance(source, str) or not source.strip():
        raise InvalidEventError(
            f"{filename}: line {line_number}: invalid field 'source'"
        )

    message = row.get("message")
    if not isinstance(message, str):
        raise InvalidEventError(
            f"{filename}: line {line_number}: invalid field 'message'"
        )

    return Event(
        timestamp=timestamp,
        level=level,
        source=source,
        message=message,
    )


def parse_csv(
    path: Path,
    skip_invalid: bool = False,
    stats: ParserStats | None = None,
) -> Iterator[Event]:
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            return

        for field_name in reader.fieldnames:
            if not field_name.strip():
                raise InvalidEventError(
                    f"{path}: line 1: empty CSV column name"
                )

        seen_fields = set()
        duplicate_fields = set()

        for field_name in reader.fieldnames:
            if field_name in seen_fields:
                duplicate_fields.add(field_name)
            else:
                seen_fields.add(field_name)

        if duplicate_fields:
            duplicate_text = ", ".join(sorted(duplicate_fields))
            raise InvalidEventError(
                f"{path}: line 1: duplicate CSV columns: {duplicate_text}"
            )

        required_fields = {"timestamp", "level", "source", "message"}
        actual_fields = set(reader.fieldnames)
        missing_fields = required_fields - actual_fields

        if missing_fields:
            missing_text = ", ".join(sorted(missing_fields))
            raise InvalidEventError(
                f"{path}: line 1: missing CSV columns: {missing_text}"
            )

        for row in reader:
            line_number = reader.line_num

            try:
                if None in row:
                    raise InvalidEventError(
                        f"{path}: line {line_number}: "
                        "extra values in CSV row"
                    )

                event = create_event(row, str(path), line_number)

            except InvalidEventError as error:
                if not skip_invalid:
                    raise

                logger.warning("%s", error)

                if stats is not None:
                    stats.skipped_count += 1

                continue

            yield event


def parse_jsonl(
    path: Path,
    skip_invalid: bool = False,
    stats: ParserStats | None = None,
) -> Iterator[Event]:
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as error:
                    raise InvalidEventError(
                        f"{path}: line {line_number}: invalid JSON"
                    ) from error

                if not isinstance(row, dict):
                    raise InvalidEventError(
                        f"{path}: line {line_number}: expected a JSON object"
                    )

                event = create_event(row, str(path), line_number)

            except InvalidEventError as error:
                if not skip_invalid:
                    raise

                logger.warning("%s", error)

                if stats is not None:
                    stats.skipped_count += 1

                continue

            yield event
