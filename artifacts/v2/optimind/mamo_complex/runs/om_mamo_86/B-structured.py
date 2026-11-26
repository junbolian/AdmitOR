# IR: {"sets":{"days":[1,2,3,4,5,6,7]},"params":{"d1":"day 1 demand","d2":"day 2 demand","d3":"day 3 demand","d4":"day 4 demand","d5":"day 5 demand","d6":"day 6 demand","d7":"day 7 demand"},"variables":{"nurses_starting[s]":"nonnegative continuous; nurses starting a five-day work block on day s"},"constraints":["For each day j: sum(nurses_starting[s] for s in days if (j-s)%7<5) >= demand[j]; work blocks wrap around the weekly boundary."],"objective":"minimize sum(nurses_starting[s] for s in days)","output":"Return the optimal objective rounded to the nearest integer, represented as a float."}

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
    model.demand = pyo.Param(model.days, initialize=demands)
    model.nurses_starting = pyo.Var(
        model.days, domain=pyo.NonNegativeReals
    )

    def coverage_rule(instance, day):
        return sum(
            instance.nurses_starting[start_day]
            for start_day in instance.days
            if (day - start_day) % 7 < 5
        ) >= instance.demand[day]

    model.coverage = pyo.Constraint(model.days, rule=coverage_rule)
    model.total_nurses = pyo.Objective(
        expr=sum(model.nurses_starting[start_day] for start_day in model.days),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_nurses))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    obj_val = float(round(obj_val))
    return {"objective": obj_val, "status": "optimal"}