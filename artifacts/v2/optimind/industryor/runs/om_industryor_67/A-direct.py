import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_3m = params["demand_3m"]
    demand_4m = params["demand_4m"]
    raw_length = params["raw_length"]
    piece_length_3m = params["piece_length_3m"]
    piece_length_4m = params["piece_length_4m"]

    # Enumerate all feasible cutting patterns for one raw bar:
    # each pattern is (count_3m, count_4m)
    patterns = []
    max_3 = int(raw_length // piece_length_3m)
    for i in range(max_3 + 1):
        used = i * piece_length_3m
        remaining = raw_length - used
        if remaining < 0:
            continue
        max_4 = int(remaining // piece_length_4m)
        for j in range(max_4 + 1):
            total = i * piece_length_3m + j * piece_length_4m
            if total <= raw_length:
                patterns.append((i, j))

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, len(patterns) - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    model.cost = pyo.Objective(
        expr=sum(model.x[p] for p in model.P),
        sense=pyo.minimize,
    )

    model.req_3m = pyo.Constraint(
        expr=sum(patterns[p][0] * model.x[p] for p in model.P) >= demand_3m
    )
    model.req_4m = pyo.Constraint(
        expr=sum(patterns[p][1] * model.x[p] for p in model.P) >= demand_4m
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}