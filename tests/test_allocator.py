import random
from pathlib import Path

import pytest

from snp_heuristic.allocator import Request, allocate
from snp_heuristic.loader import load_cases

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def req(request_id, priority=1, demand=100, min_lot=0, rounding=1):
    return Request(request_id, priority, demand, min_lot, rounding)


EXPECTED_CSV = {
    "CASE_01": {"R-101": 25, "R-102": 25, "R-103": 25},
    "CASE_02": {"R-201": 0, "R-202": 40, "R-203": 30, "R-204": 30},
    "CASE_03": {"R-301": 0, "R-302": 0, "R-303": 30, "R-304": 30},
    "CASE_04": {"R-401": 20, "R-402": 20, "R-403": 19, "R-404": 19, "R-405": 19},
    "CASE_05": {"R-501": 25, "R-502": 30, "R-503": 5},
    "CASE_06": {"R-601": 100, "R-602": 0, "R-603": 77},
    "CASE_07": {"R-701": 100, "R-702": 0, "R-703": 0},
}


def test_csv_cases_match_hand_calculation():
    """Фиксирует результат на шести кейсах из CSV; ломается при любом изменении правила."""
    cases, _ = load_cases(DATA_DIR)
    for case in cases:
        assert allocate(case.available_qty, case.requests) == EXPECTED_CSV[case.case_id], case.case_id


def test_strict_priority_serves_tier_one_before_tier_two():
    """Тир 2 ничего не получает, пока тир 1 не покрыт; сломается при весовом приоритете вместо строгого."""
    result = allocate(100, [req("A", priority=1, demand=100), req("B", priority=2, demand=50)])
    assert result == {"A": 100, "B": 0}


def test_rounding_never_pushes_shipment_above_demand():
    """Demand 40 при кратности 25 даёт 25, а не 50; сломается, если разрешить перебор ради кратности."""
    assert allocate(100, [req("A", demand=40, rounding=25)]) == {"A": 25}


def test_min_lot_drops_request_and_gives_its_share_to_others():
    """Заявка с долей меньше min_lot получает 0, а объём уходит остальным; сломается, если min_lot игнорировать."""
    result = allocate(100, [req("A", demand=90), req("B", demand=10, min_lot=30)])
    assert result == {"A": 90, "B": 0}


def test_ties_are_broken_by_request_id():
    """Равные заявки: остаток уходит первой по request_id; сломается при другом тай-брейке (например, порядке входа)."""
    result = allocate(50, [req("B", demand=50, rounding=10), req("A", demand=50, rounding=10)])
    assert result == {"A": 30, "B": 20}


def test_input_order_does_not_change_result():
    """Перемешивание входа не меняет план; сломается при зависимости результата от порядка строк в CSV."""
    requests = [req(f"R{i}", priority=1 + i % 3, demand=10 + 7 * i, rounding=1 + i % 4) for i in range(12)]
    expected = allocate(60, requests)
    rng = random.Random(0)
    for _ in range(20):
        shuffled = requests[:]
        rng.shuffle(shuffled)
        assert allocate(60, shuffled) == expected


def test_zero_or_negative_available_gives_nothing():
    """Нулевой или отрицательный доступный объём даёт нулевой план; сломается при отгрузке из пустого склада."""
    requests = [req("A"), req("B")]
    assert allocate(0, requests) == {"A": 0, "B": 0}
    assert allocate(-5, requests) == {"A": 0, "B": 0}


@pytest.mark.parametrize("seed", range(200))
def test_random_plans_keep_hard_constraints(seed):
    """На случайных входах сумма ≤ доступного, каждая отгрузка 0 или кратна rounding, ≥ min_lot и ≤ demand; сломается при нарушении жёстких требований."""
    rng = random.Random(seed)
    requests = [
        req(f"R{i}", priority=rng.randint(1, 3), demand=rng.randint(0, 200),
            min_lot=rng.choice([0, 0, 10, 30]), rounding=rng.randint(1, 25))
        for i in range(rng.randint(1, 8))
    ]
    available = rng.randint(0, 300)
    result = allocate(available, requests)
    assert sum(result.values()) <= available
    for r in requests:
        qty = result[r.request_id]
        assert qty == 0 or (qty >= r.smallest_lot and qty % r.rounding_value == 0 and qty <= r.demand_qty)
