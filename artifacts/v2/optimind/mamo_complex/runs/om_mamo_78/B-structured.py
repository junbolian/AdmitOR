# IR: {"sets":{"D":[1,2,3,4,5,6,7],"S":[1,2,3,4,5,6,7]},"params":{"demand":"params['demand']: seven-element sequence ordered by day"},"variables":{"starts[s]":"continuous nonnegative nurses starting a five-day work block on day s"},"constraints":["For every day j: sum(starts[s] for s in S if (j-s)%7 < 5) >= demand[j-1]; work blocks wrap around the weekly boundary."],"objective":"Minimize sum(starts[s] for s in S).","report":"Return the optimal objective rounded to the nearest integer, represented as a float."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    if len(demand) != 7:
        raise ValueError("params['demand'] must contain exactly seven daily demands.")

    model = pyo.ConcreteModel()
    model.days = pyo.RangeSet(1, 7)
    model.start_days = pyo.RangeSet(1, 7)

    model.daily_demand = pyo.Param(
        model.days,
        initialize={day: demand[day - 1] for day in model.days},
        within=pyo.Reals,
    )

    model.starts = pyo.Var(
        model.start_days,
        domain=pyo.NonNegativeReals,
    )

    def coverage_rule(instance, day):
        return sum(
            instance.starts[start_day]
            for start_day in instance.start_days
            if (day - start_day) % 7 < 5
        ) >= instance.daily_demand[day]

    model.coverage = pyo.Constraint(model.days, rule=coverage_rule)

    model.total_nurses = pyo.Objective(
        expr=sum(model.starts[start_day] for start_day in model.start_days),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this error when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_nurses))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}