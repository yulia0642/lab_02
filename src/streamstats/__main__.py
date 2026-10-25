import argparse
import logging
import sys
from pathlib import Path

from streamstats.analysis import AnalysisStats, analyze_events
from streamstats.errors import CLIConfigError, StreamStatsError, UnsupportedFormatError
from streamstats.parsers import ParserStats, parse_csv, parse_jsonl
from streamstats.report import build_report, write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Потоковый анализатор файлов CSV и JSONL",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Проанализировать входные файлы",
    )

    analyze_parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        metavar="INPUT",
        help="Путь к входному файлу",
    )

    analyze_parser.add_argument(
        "--format",
        choices=["csv", "jsonl"],
        required=True,
        help="Формат входных файлов",
    )

    analyze_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Путь к JSON-отчёту",
    )

    analyze_parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Пропускать некорректные записи",
    )

    return parser


def run_analyze(arguments: argparse.Namespace) -> int:
    stats = AnalysisStats()
    parser_stats = ParserStats()

    try:
        output_path = arguments.output.resolve()

        for input_path in arguments.inputs:
            if input_path.resolve() == output_path:
                raise CLIConfigError(
                    "Входной файл не должен совпадать с выходным файлом."
                )

            if not input_path.is_file():
                raise CLIConfigError(
                    f"Входной файл не найден: {input_path}"
                )

        for input_path in arguments.inputs:
            if arguments.format == "csv":
                events = parse_csv(
                    input_path,
                    skip_invalid=arguments.skip_invalid,
                    stats=parser_stats,
                )
            elif arguments.format == "jsonl":
                events = parse_jsonl(
                    input_path,
                    skip_invalid=arguments.skip_invalid,
                    stats=parser_stats,
                )
            else:
                raise UnsupportedFormatError(
                    f"Неподдерживаемый формат: {arguments.format}"
                )

            analyze_events(events, stats)

        report = build_report(
            stats,
            skipped_count=parser_stats.skipped_count,
        )

        write_report(report, arguments.output)

    except StreamStatsError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2

    except OSError as error:
        print(f"Ошибка при работе с файлом: {error}", file=sys.stderr)
        return 2

    return 0


def main() -> int:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    parser = build_parser()
    arguments = parser.parse_args()

    return run_analyze(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
