# IR: {"sets":{"T":[0,1,2,3,4,5]},"params":{"demand_2_6":"nonnegative real","demand_6_10":"nonnegative real","demand_10_14":"nonnegative real","demand_14_18":"nonnegative real","demand_18_22":"nonnegative real","demand_22_2":"nonnegative real"},"variables":{"x[t]":{"index":"t in T","type":"nonnegative integer","meaning":"salespeople starting an eight-hour shift in period t"}},"constraints":["x[0]+x[5]>=demand_2_6","x[1]+x[0]>=demand_6_10","x[2]+x[1]>=demand_10_14","x[3]+x[2]>=demand_14_18","x[4]+x[3]>=demand_18_22","x[5]+x[4]>=demand_22_2"],"objective":"minimize sum(x[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()
    model.periods = pyo.RangeSet(0, 5)

    demand_data = {
        0: params["demand_2_6"],
        1: params["demand_6_10"],
        2: params["demand_10_14"],
        3: params["demand_14_18"],
        4: params["demand_18_22"],
        5: params["demand_22_2"],
    }
    model.demand = pyo.Param(
        model.periods,
        initialize=demand_data,
        within=pyo.NonNegativeReals,
    )

    model.shift_starts = pyo.Var(
        model.periods,
        domain=pyo.NonNegativeIntegers,
    )

    def coverage_rule(instance, period):
        previous_period = (period - 1) % 6
        return (
            instance.shift_starts[period]
            + instance.shift_starts[previous_period]
            >= instance.demand[period]
        )

    model.coverage = pyo.Constraint(model.periods, rule=coverage_rule)
    model.total_staff = pyo.Objective(
        expr=sum(model.shift_starts[period] for period in model.periods),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_staff))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}