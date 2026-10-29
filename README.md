# SNP Heuristic: распределение дефицита

Тестовое задание: распределить ограниченный доступный объём между заявками. Правило и открытые вопросы описаны в `REPORT.md`.

## Запуск

Нужен Python 3.10+. Внешних зависимостей для запуска нет.

```bash
python -m snp_heuristic data
```

Выводит предупреждения по данным и план по каждому кейсу из `data/`.

## Тесты

```bash
pip install -r requirements-dev.txt
pytest
```

## Структура

- `snp_heuristic/allocator.py` — ядро алгоритма (`allocate`).
- `snp_heuristic/loader.py` — чтение CSV и предупреждения о некорректных данных.
- `snp_heuristic/__main__.py` — CLI.
- `tests/test_allocator.py` — эталонные кейсы из CSV и собственные тесты.
- `REPORT.md` — журнал решений, вопросы аналитику, масштаб, многопериодность.
