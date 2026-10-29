"""Запуск: python -m snp_heuristic [папка_с_данными]  (по умолчанию data/)."""

import sys
from pathlib import Path

from .allocator import allocate
from .loader import load_cases


def main(argv: list[str]) -> None:
    data_dir = Path(argv[0]) if argv else Path("data")
    cases, warnings = load_cases(data_dir)
    for warning in warnings:
        print(f"! {warning}")
    for case in cases:
        alloc = allocate(case.available_qty, case.requests)
        distributed = sum(alloc.values())
        print(
            f"\n{case.case_id}: доступно {case.available_qty}, "
            f"отгружено {distributed}, не распределено {case.available_qty - distributed}"
        )
        for r in case.requests:
            print(f"  {r.request_id}  приоритет {r.priority}  запрос {r.demand_qty:>4}  получит {alloc[r.request_id]:>4}")


if __name__ == "__main__":
    main(sys.argv[1:])
