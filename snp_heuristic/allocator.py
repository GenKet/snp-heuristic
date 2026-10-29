"""Распределение дефицита: одна элементарная операция SNP Heuristic.

Правило (подробнее в REPORT.md):
- заявки делятся на тиры по priority, тир 1 обслуживается первым (строгий приоритет);
- внутри тира объём делится пропорционально demand_qty и округляется вниз до кратности;
- остаток раздаётся по одной кратности за раз, по наибольшей дробной части доли;
- никому не отгружаем больше demand_qty;
- заявка, которой не хватает на минимальную партию, выбывает из тира (отбрасываем с наименьшим demand).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Request:
    request_id: str
    priority: int
    demand_qty: int
    min_lot: int
    rounding_value: int

    @property
    def smallest_lot(self) -> int:
        """Наименьшая ненулевая отгрузка: кратна rounding_value и не меньше min_lot."""
        step = self.rounding_value
        return (max(self.min_lot, 1) + step - 1) // step * step

    @property
    def max_lot(self) -> int:
        """Наибольшая отгрузка: не больше demand_qty и кратна rounding_value."""
        return self.demand_qty // self.rounding_value * self.rounding_value

    @property
    def feasible(self) -> bool:
        return self.smallest_lot <= self.max_lot


def allocate(available_qty: int, requests: Iterable[Request]) -> dict[str, int]:
    """Возвращает отгрузку по каждой заявке; нераспределённый остаток = available - sum(результат)."""
    requests = list(requests)
    result = {r.request_id: 0 for r in requests}
    left = max(available_qty, 0)
    feasible = [r for r in requests if r.feasible]
    for priority in sorted({r.priority for r in feasible}):
        tier = sorted((r for r in feasible if r.priority == priority), key=lambda r: r.request_id)
        shares, left = _split_tier(left, tier)
        result.update(shares)
    return result


def _split_tier(available: int, tier: list[Request]) -> tuple[dict[str, int], int]:
    active = list(tier)
    while active and available > 0:
        total = sum(r.demand_qty for r in active)
        short = [r for r in active if available * r.demand_qty // total < r.smallest_lot]
        if not short:
            break
        active.remove(min(short, key=lambda r: (r.demand_qty, r.request_id)))
    if not active or available <= 0:
        return {}, available

    total = sum(r.demand_qty for r in active)
    alloc = {}
    for r in active:
        share = available * r.demand_qty // total
        alloc[r.request_id] = min(share // r.rounding_value * r.rounding_value, r.max_lot)

    left = available - sum(alloc.values())
    by_fraction = sorted(active, key=lambda r: (-(available * r.demand_qty % total), r.request_id))
    progress = True
    while progress and left > 0:
        progress = False
        for r in by_fraction:
            if left >= r.rounding_value and alloc[r.request_id] + r.rounding_value <= r.max_lot:
                alloc[r.request_id] += r.rounding_value
                left -= r.rounding_value
                progress = True
    return alloc, left
