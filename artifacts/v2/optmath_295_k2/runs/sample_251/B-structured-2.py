# IR: {"sets":{"packages":"0..10","legs":"0..6"},"params":{"revenue":"real[packages]","demand":"nonnegative real[packages]","capacity":"nonnegative real[legs]","leg_utilization":"binary[legs,packages], frozen"},"variables":{"sales":"nonnegative integer[packages]"},"constraints":["sales[j] <= demand[j] for each package j","sum(leg_utilization[i,j]*sales[j] for j in packages) <= capacity[i] for each leg i"],"objective":"maximize sum(revenue[j]*sales[j] for j in packages)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]
    leg_utilization = params["leg_utilization"]

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 10)
    model.legs = pyo.RangeSet(0, 6)

    model.revenue = pyo.Param(
        model.packages,
        initialize=lambda mdl, j: revenue[j],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.packages,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.legs,
        initialize=lambda mdl, i: capacity[i],
        within=pyo.NonNegativeReals,
    )
    model.leg_utilization = pyo.Param(
        model.legs,
        model.packages,
        initialize=lambda mdl, i, j: leg_utilization[i][j],
        within=pyo.Binary,
        mutable=False,
    )

    model.sales = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    model.demand_limits = pyo.Constraint(
        model.packages,
        rule=lambda mdl, j: mdl.sales[j] <= mdl.demand[j],
    )
    model.capacity_limits = pyo.Constraint(
        model.legs,
        rule=lambda mdl, i: sum(
            mdl.leg_utilization[i, j] * mdl.sales[j]
            for j in mdl.packages
        ) <= mdl.capacity[i],
    )
    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[j] * model.sales[j]
            for j in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}