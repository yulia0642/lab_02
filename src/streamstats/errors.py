
class StreamStatsError(Exception):
    """Базовая ошибка потокового анализатора."""


class UnsupportedFormatError(StreamStatsError):
    """Ошибка неподдерживаемого формата входных данных."""


class InvalidEventError(StreamStatsError):
    """Ошибка некорректного события."""


class InvalidTimestampError(InvalidEventError):
    """Ошибка некорректной даты или времени события."""


class CLIConfigError(StreamStatsError):
    """Ошибка конфигурации командной строки."""
