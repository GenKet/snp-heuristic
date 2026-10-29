"""Чтение CSV и приведение данных к виду, с которым работает allocator."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .allocator import Request


@dataclass(frozen=True)
class Case:
    case_id: str
    available_qty: int
    requests: list[Request]


def load_cases(data_dir: Path) -> tuple[list[Case], list[str]]:
    warnings: list[str] = []
    supply: dict[str, int] = {}
    with open(data_dir / "supply.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            available = int(row["available_qty"])
            if available < 0:
                warnings.append(f"{row['case_id']}: available_qty={available}, считаю 0")
            supply[row["case_id"]] = max(available, 0)

    requests: dict[str, list[Request]] = {}
    with open(data_dir / "requests.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            request = _to_request(row, warnings)
            if row["case_id"] not in supply:
                warnings.append(f"{request.request_id}: кейс {row['case_id']} не найден в supply.csv, заявка пропущена")
                continue
            requests.setdefault(row["case_id"], []).append(request)

    for case_id in supply:
        if case_id not in requests:
            warnings.append(f"{case_id}: нет заявок, весь объём не распределён")
    cases = [Case(case_id, available, requests.get(case_id, [])) for case_id, available in supply.items()]
    return cases, warnings


def _to_request(row: dict[str, str], warnings: list[str]) -> Request:
    request_id = row["request_id"]
    demand = int(row["demand_qty"])
    if demand < 0:
        warnings.append(f"{request_id}: demand_qty={demand}, считаю 0")
        demand = 0
    rounding = int(row["rounding_value"])
    if rounding < 1:
        warnings.append(f"{request_id}: rounding_value={rounding}, считаю 1 (без кратности)")
        rounding = 1
    min_lot = max(int(row["min_lot"]), 0)
    request = Request(request_id, int(row["priority"]), demand, min_lot, rounding)
    if not request.feasible:
        warnings.append(
            f"{request_id}: не может получить отгрузку (demand={demand}, min_lot={min_lot}, rounding={rounding})"
        )
    return request
