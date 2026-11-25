# IR: {"sets":{"packages":"0..10","legs":"0..6"},"params":{"revenue":"real[packages]","demand":"nonnegative real[packages]","capacity":"nonnegative real[legs]","leg_utilization":"binary[legs,packages], frozen"},"variables":{"sales":"nonnegative integer[packages]"},"constraints":["sales[j] <= demand[j] for each package j","sum(leg_utilization[i,j]*sales[j] for j in packages) <= capacity[i] for each leg i"],"objective":"maximize sum(revenue[j]*sales[j] for j in packages)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.packages = pyo.RangeSet(0, 10)
    model.legs = pyo.RangeSet(0, 6)

    model.revenue = pyo.Param(
        model.packages,
        initialize={j: params["revenue"][j] for j in model.packages},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.packages,
        initialize={j: params["demand"][j] for j in model.packages},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.legs,
        initialize={i: params["capacity"][i] for i in model.legs},
        within=pyo.NonNegativeReals,
    )
    model.leg_utilization = pyo.Param(
        model.legs,
        model.packages,
        initialize={
            (i, j): params["leg_utilization"][i][j]
            for i in model.legs
            for j in model.packages
        },
        within=pyo.Binary,
        mutable=False,
    )

    model.sales = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    def demand_rule(model, j):
        return model.sales[j] <= model.demand[j]

    model.demand_limits = pyo.Constraint(model.packages, rule=demand_rule)

    def capacity_rule(model, i):
        return sum(
            model.leg_utilization[i, j] * model.sales[j]
            for j in model.packages
        ) <= model.capacity[i]

    model.capacity_limits = pyo.Constraint(model.legs, rule=capacity_rule)

    model.total_revenue = pyo.Objective(
        expr=sum(model.revenue[j] * model.sales[j] for j in model.packages),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}