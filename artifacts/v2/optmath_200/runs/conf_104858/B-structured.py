# IR: {"sets":{"P":"0..16","L":"0..4","uses":{"0":[0,1,5,6,11,15,16],"1":[1,8,16],"2":[0,2,3,8,11,16],"3":[4,5,6,7,13,16],"4":[1,2,4,5,6,8,11,12,13]}},"params":{"revenue":"params['revenue'][p], p in P","demand":"params['demand'][p], p in P","flight_capacity":"params['flight_capacity'][l], l in L"},"variables":{"sold[p]":"nonnegative integer, p in P"},"constraints":["sold[p] <= demand[p] for p in P","sum(sold[p] for p in uses[l]) <= flight_capacity[l] for l in L"],"objective":"maximize sum(revenue[p] * sold[p] for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    uses = {
        0: (0, 1, 5, 6, 11, 15, 16),
        1: (1, 8, 16),
        2: (0, 2, 3, 8, 11, 16),
        3: (4, 5, 6, 7, 13, 16),
        4: (1, 2, 4, 5, 6, 8, 11, 12, 13),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 16)
    model.legs = pyo.RangeSet(0, 4)

    model.revenue = pyo.Param(
        model.packages, initialize=lambda mdl, p: revenue[p]
    )
    model.demand = pyo.Param(
        model.packages, initialize=lambda mdl, p: demand[p]
    )
    model.flight_capacity = pyo.Param(
        model.legs, initialize=lambda mdl, leg: flight_capacity[leg]
    )

    model.sold = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    model.demand_limit = pyo.Constraint(
        model.packages,
        rule=lambda mdl, p: mdl.sold[p] <= mdl.demand[p],
    )
    model.capacity_limit = pyo.Constraint(
        model.legs,
        rule=lambda mdl, leg: (
            sum(mdl.sold[p] for p in uses[leg]) <= mdl.flight_capacity[leg]
        ),
    )
    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[p] * model.sold[p] for p in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}