# IR: {"sets":{"D":"{1,...,7}"},"params":{"d[j]":"params['d']; seven-element sequence or mapping keyed 1,...,7"},"variables":{"x[i]":"continuous nonnegative; nurses starting a five-day work block on day i"},"constraints":["For each j in D: sum(x[i] for i in D if (j-i)%7 < 5) >= d[j]"],"objective":"minimize sum(x[i] for i in D)","report":"Return the objective rounded to the nearest integer as a float."}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = params["d"]
    days = range(1, 8)
    demand = {
        day: (
            demand_data[day]
            if isinstance(demand_data, Mapping)
            else demand_data[day - 1]
        )
        for day in days
    }

    model = pyo.ConcreteModel()
    model.days = pyo.Set(initialize=days, ordered=True)
    model.demand = pyo.Param(model.days, initialize=demand)
    model.starts = pyo.Var(model.days, domain=pyo.NonNegativeReals)

    def coverage_rule(block, day):
        return sum(
            block.starts[start_day]
            for start_day in block.days
            if (day - start_day) % 7 < 5
        ) >= block.demand[day]

    model.coverage = pyo.Constraint(model.days, rule=coverage_rule)
    model.total_nurses = pyo.Objective(
        expr=sum(model.starts[day] for day in model.days),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_nurses))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}