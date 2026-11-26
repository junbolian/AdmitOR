# IR: {"sets":{"P":"{(a,b) in Z_+^2: a+b>=1, a*piece_3m_length+b*piece_4m_length<=raw_length}"},"params":["stock_3m_count","stock_4m_count","raw_length","piece_3m_length","piece_4m_length"],"variables":{"cuts[a,b]":"nonnegative integer for (a,b) in P"},"constraints":["sum(a*cuts[a,b] for (a,b) in P) = stock_3m_count","sum(b*cuts[a,b] for (a,b) in P) = stock_4m_count"],"objective":"minimize sum(cuts[a,b] for (a,b) in P)"}

from fractions import Fraction

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_3 = params["stock_3m_count"]
    demand_4 = params["stock_4m_count"]
    raw_length = Fraction(str(params["raw_length"]))
    length_3 = Fraction(str(params["piece_3m_length"]))
    length_4 = Fraction(str(params["piece_4m_length"]))

    if (
        demand_3 < 0
        or demand_4 < 0
        or int(demand_3) != demand_3
        or int(demand_4) != demand_4
        or raw_length <= 0
        or length_3 <= 0
        or length_4 <= 0
    ):
        return {"objective": None, "status": "invalid_parameters"}

    # Enumerate every feasible, nonempty cutting pattern.
    # Rational arithmetic avoids rounding errors at length boundaries.
    patterns = []
    for count_3 in range(int(raw_length // length_3) + 1):
        remaining_length = raw_length - count_3 * length_3
        for count_4 in range(int(remaining_length // length_4) + 1):
            if count_3 + count_4 > 0:
                patterns.append((count_3, count_4))

    model = pyo.ConcreteModel()

    model.cut_patterns = pyo.Set(dimen=2, initialize=patterns)
    model.cuts = pyo.Var(
        model.cut_patterns,
        domain=pyo.NonNegativeIntegers,
    )

    # Equality bounds also support an empty pattern set.
    model.demand_3_constraint = pyo.Constraint(
        expr=(
            int(demand_3),
            pyo.quicksum(
                count_3 * model.cuts[count_3, count_4]
                for count_3, count_4 in model.cut_patterns
            ),
            int(demand_3),
        )
    )
    model.demand_4_constraint = pyo.Constraint(
        expr=(
            int(demand_4),
            pyo.quicksum(
                count_4 * model.cuts[count_3, count_4]
                for count_3, count_4 in model.cut_patterns
            ),
            int(demand_4),
        )
    )

    # With exact demand, minimizing raw bars also minimizes total waste.
    model.total_raw_bars = pyo.Objective(
        expr=pyo.quicksum(
            model.cuts[count_3, count_4]
            for count_3, count_4 in model.cut_patterns
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_raw_bars))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}