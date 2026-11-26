# IR: {"sets":{"D":[1,2,3,4,5,6,7],"K":[0,1,2,3,4]},"params":{"demand[j]":"params['d'+str(j)] for j in D"},"variables":{"starts[j]":{"type":"continuous nonnegative","index":"j in D","meaning":"nurses beginning five consecutive workdays on day j"}},"constraints":["For each j in D: sum(starts[1+((j-k-1)%7)] for k in K) >= demand[j]; schedule repeats weekly."],"objective":{"sense":"minimize","expression":"sum(starts[j] for j in D)"},"reporting":{"objective":"optimal objective rounded to the nearest integer and returned as a float"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demands = {
        1: params["d1"],
        2: params["d2"],
        3: params["d3"],
        4: params["d4"],
        5: params["d5"],
        6: params["d6"],
        7: params["d7"],
    }

    model = pyo.ConcreteModel()
    model.days = pyo.RangeSet(1, 7)
    model.work_offsets = pyo.RangeSet(0, 4)

    model.demand = pyo.Param(model.days, initialize=demands)
    model.starts = pyo.Var(model.days, domain=pyo.NonNegativeReals)

    def coverage_rule(schedule, day):
        return sum(
            schedule.starts[1 + ((day - offset - 1) % 7)]
            for offset in schedule.work_offsets
        ) >= schedule.demand[day]

    model.coverage = pyo.Constraint(model.days, rule=coverage_rule)

    model.total_nurses = pyo.Objective(
        expr=sum(model.starts[day] for day in model.days),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_nurses))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}