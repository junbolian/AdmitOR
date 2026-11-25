# IR: {"sets":{"packages":[0,1,2,3,4,5,6,7,8,9,10],"legs":[0,1,2,3,4,5,6],"uses":{"0":[0,8,10],"1":[1,2,4,5,6,8,9],"2":[2,3,5,6,7,8],"3":[2,6,7,8,10],"4":[1,2,9,10],"5":[2,4,5,6,8,9],"6":[0,1,3,4,5,7,8,9]}},"params":{"revenue":"params['revenue'][package]","demand":"params['demand'][package]","capacity":"params['capacity'][leg]"},"variables":{"sales[package]":"nonnegative integer"},"constraints":["sales[p] <= demand[p] for every package p","sum(sales[p] for p in uses[l]) <= capacity[l] for every leg l"],"objective":"maximize sum(revenue[p] * sales[p] for every package p)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    uses = {
        0: (0, 8, 10),
        1: (1, 2, 4, 5, 6, 8, 9),
        2: (2, 3, 5, 6, 7, 8),
        3: (2, 6, 7, 8, 10),
        4: (1, 2, 9, 10),
        5: (2, 4, 5, 6, 8, 9),
        6: (0, 1, 3, 4, 5, 7, 8, 9),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 10)
    model.legs = pyo.RangeSet(0, 6)

    model.revenue = pyo.Param(
        model.packages, initialize=lambda mdl, p: revenue[p]
    )
    model.demand = pyo.Param(
        model.packages, initialize=lambda mdl, p: demand[p]
    )
    model.capacity = pyo.Param(
        model.legs, initialize=lambda mdl, leg: capacity[leg]
    )

    model.sales = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    model.demand_limits = pyo.Constraint(
        model.packages,
        rule=lambda mdl, p: mdl.sales[p] <= mdl.demand[p],
    )
    model.capacity_limits = pyo.Constraint(
        model.legs,
        rule=lambda mdl, leg: (
            sum(mdl.sales[p] for p in uses[leg]) <= mdl.capacity[leg]
        ),
    )

    model.total_revenue = pyo.Objective(
        expr=sum(model.revenue[p] * model.sales[p] for p in model.packages),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, RuntimeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}