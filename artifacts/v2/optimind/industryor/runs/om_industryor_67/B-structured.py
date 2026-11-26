# IR: {"sets":{"P":"all (a,b) in Z_nonnegative^2 with a*piece_length_3m+b*piece_length_4m<=raw_length, including (0,0)"},"params":["demand_3m","demand_4m","raw_length","piece_length_3m","piece_length_4m"],"variables":{"bars_used[a,b]":"nonnegative integer for each (a,b) in P"},"constraints":["sum(a*bars_used[a,b] for (a,b) in P) == demand_3m","sum(b*bars_used[a,b] for (a,b) in P) == demand_4m"],"objective":"minimize sum(bars_used[a,b] for (a,b) in P)"}

import math
from fractions import Fraction

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Minimize raw bars needed to produce exactly the requested batch."""
    demand_3m = params["demand_3m"]
    demand_4m = params["demand_4m"]
    raw_length = params["raw_length"]
    piece_length_3m = params["piece_length_3m"]
    piece_length_4m = params["piece_length_4m"]

    quantities = (
        demand_3m,
        demand_4m,
        raw_length,
        piece_length_3m,
        piece_length_4m,
    )
    if not all(math.isfinite(quantity) for quantity in quantities):
        return {"objective": None, "status": "invalid_params"}

    if (
        demand_3m < 0
        or demand_4m < 0
        or int(demand_3m) != demand_3m
        or int(demand_4m) != demand_4m
        or raw_length <= 0
        or piece_length_3m <= 0
        or piece_length_4m <= 0
    ):
        return {"objective": None, "status": "invalid_params"}

    # Rational arithmetic avoids floating-point errors at cutting boundaries.
    stock_length = Fraction(str(raw_length))
    short_length = Fraction(str(piece_length_3m))
    long_length = Fraction(str(piece_length_4m))

    patterns = []
    for short_count in range(int(stock_length // short_length) + 1):
        remaining_length = stock_length - short_count * short_length
        for long_count in range(int(remaining_length // long_length) + 1):
            patterns.append((short_count, long_count))

    # The empty pattern keeps the index set nonempty even when no piece fits.
    # It is never used in an optimal solution because it consumes a raw bar.
    model = pyo.ConcreteModel()

    model.patterns = pyo.Set(dimen=2, initialize=patterns)
    model.required_short = pyo.Param(
        initialize=int(demand_3m), within=pyo.NonNegativeIntegers
    )
    model.required_long = pyo.Param(
        initialize=int(demand_4m), within=pyo.NonNegativeIntegers
    )

    model.bars_used = pyo.Var(
        model.patterns, domain=pyo.NonNegativeIntegers
    )

    model.short_demand = pyo.Constraint(
        expr=pyo.quicksum(
            short_count * model.bars_used[short_count, long_count]
            for short_count, long_count in model.patterns
        )
        == model.required_short
    )
    model.long_demand = pyo.Constraint(
        expr=pyo.quicksum(
            long_count * model.bars_used[short_count, long_count]
            for short_count, long_count in model.patterns
        )
        == model.required_long
    )

    model.total_raw_bars = pyo.Objective(
        expr=pyo.quicksum(
            model.bars_used[short_count, long_count]
            for short_count, long_count in model.patterns
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_raw_bars))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}