# Лабораторная работа 2. Потоковый анализатор файлов `streamstats`


`streamstats` — программа на Python для потокового анализа журналов событий в форматах CSV и JSONL. Программа читает входные файлы построчно, проверяет корректность записей, подсчитывает статистику и сохраняет результат в JSON-файл.

## Функционал

- Чтение CSV- и JSONL-файлов.
- Проверка обязательных полей событий.
- Подсчёт общего количества событий.
- Подсчёт событий каждого уровня: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- Подсчёт событий по источникам.
- Поиск top-5 источников с наибольшим количеством событий уровней `ERROR` и `CRITICAL`.
- Определение первой и последней временной метки.
- Объединение статистики нескольких входных файлов.
- Обработка некорректных записей с возможностью их пропуска.
- Сохранение JSON-отчёта.

## Установка

Требуется Python 3.12 или новее.

Создайте виртуальное окружение:

```bash
python -m venv .venv
```

Активируйте его.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS:

```bash
source .venv/bin/activate
```

Установите проект и зависимости для разработки и тестирования:

```bash
python -m pip install -e ".[dev]"
```

## Форматы входных данных

### CSV

Первая строка содержит названия столбцов:

```csv
timestamp,level,source,message
2026-10-23T10:15:00,INFO,server,Server started
2026-10-23T10:16:00,ERROR,database,Connection failed
```

### JSONL

Каждая строка содержит отдельный JSON-объект:

```jsonl
{"timestamp": "2026-10-23T10:15:00", "level": "INFO", "source": "server", "message": "Server started"}
{"timestamp": "2026-10-23T10:16:00", "level": "ERROR", "source": "database", "message": "Connection failed"}
```

Каждое событие должно содержать поля `timestamp`, `level`, `source` и `message`.

- `timestamp` — дата и время в формате ISO 8601. Если часовой пояс не указан, время считается временем UTC. Временные метки с часовым поясом переводятся в UTC перед анализом.
- `level` — один из пяти допустимых уровней.
- `source` — непустое название источника.
- `message` — текст сообщения.

## Запуск программы

### Анализ CSV-файла

```bash
python -m streamstats analyze events.csv --format csv --output report.json
```

### Анализ JSONL-файла

```bash
python -m streamstats analyze events.jsonl --format jsonl --output report.json
```

### Анализ нескольких файлов

```bash
python -m streamstats analyze first.csv second.csv --format csv --output report.json
```


### Пропуск некорректных записей

```bash
python -m streamstats analyze events.jsonl --format jsonl --output report.json --skip-invalid
```

Без параметра `--skip-invalid` программа останавливается при первой некорректной записи и возвращает код завершения `2`.

С параметром `--skip-invalid` программа выводит предупреждение, пропускает некорректную запись и продолжает обработку. Количество пропусков сохраняется в отчёте.

## Отчёт

Программа формирует JSON-файл со следующими полями:

- `total_events` — общее количество обработанных событий.
- `events_by_level` — количество событий каждого уровня.
- `events_by_source` — количество событий по источникам.
- `top_error_sources` — до пяти источников с наибольшим количеством событий `ERROR` и `CRITICAL`.
- `earliest_timestamp` — время самого раннего события.
- `latest_timestamp` — время самого позднего события.
- `skipped_count` — количество пропущенных записей.

При одинаковом количестве ошибок источники сортируются по алфавиту. Если события отсутствуют, временные границы имеют значение `null`.

## Структура проекта

```text
lab_02/
├── pyproject.toml
├── README.md
├── src/
│   └── streamstats/
│       ├── __init__.py
│       ├── __main__.py
│       ├── analysis.py
│       ├── errors.py
│       ├── models.py
│       ├── parsers.py
│       └── report.py
└── tests/
    ├── test_analysis.py
    ├── test_cli.py
    ├── test_parsers.py
    └── test_report.py
```

## Тестирование

Запуск всех тестов:

```bash
python -m pytest
```

Проверка кода с помощью Ruff:

```bash
ruff check .
```

Просмотр справки:

```bash
python -m streamstats --help
```
