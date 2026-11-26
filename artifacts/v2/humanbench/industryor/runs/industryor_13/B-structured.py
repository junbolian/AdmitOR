# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"demand":{"source":"params['demand']","index":"T","domain":"nonnegative real"}},"variables":{"staff_start":{"index":"T","type":"nonnegative integer"}},"constraints":["coverage[t]: staff_start[t] + staff_start[(t-1) % 6] >= demand[t] for t in T"],"objective":{"sense":"minimize","expression":"sum(staff_start[t] for t in T)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    if len(demand) != 6:
        raise ValueError("params['demand'] must contain exactly six values.")

    model = pyo.ConcreteModel()
    model.periods = pyo.RangeSet(0, 5)

    model.required_staff = pyo.Param(
        model.periods,
        initialize={period: demand[period] for period in model.periods},
        within=pyo.NonNegativeReals,
    )

    # Each shift covers its starting period and the following period.
    model.staff_start = pyo.Var(
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, period):
        return (
            instance.staff_start[period]
            + instance.staff_start[(period - 1) % 6]
            >= instance.required_staff[period]
        )

    model.coverage = pyo.Constraint(
        model.periods,
        rule=coverage_rule,
    )

    model.total_staff = pyo.Objective(
        expr=sum(model.staff_start[period] for period in model.periods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_staff))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}