# IR: {"sets":{"days":[0,1,2,3,4,5,6]},"params":{"requirements":"params['requirements']; seven daily staffing requirements, Monday through Sunday"},"variables":{"starts[d]":"nonnegative integer; employees beginning a five-day work stretch on day d"},"constraints":["For each day d: sum(starts[s] for s in days if (d-s)%7 < 5) >= requirements[d]."],"objective":"Minimize sum(starts[d] for d in days)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    requirements = list(params["requirements"])
    if len(requirements) != 7:
        raise ValueError("requirements must contain seven daily values.")

    model = pyo.ConcreteModel()
    model.days = pyo.RangeSet(0, 6)

    model.required_staff = pyo.Param(
        model.days,
        initialize={day: requirements[day] for day in range(7)},
        within=pyo.NonNegativeReals,
    )

    model.starts = pyo.Var(
        model.days,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, day):
        return sum(
            instance.starts[start_day]
            for start_day in instance.days
            if (day - start_day) % 7 < 5
        ) >= instance.required_staff[day]

    model.daily_coverage = pyo.Constraint(
        model.days,
        rule=coverage_rule,
    )

    model.total_employees = pyo.Objective(
        expr=sum(model.starts[day] for day in model.days),
        sense=pyo.minimize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_employees))
    except ValueError:
        return {
            "objective": None,
            "status": "solve_failed" if solve_failed else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}