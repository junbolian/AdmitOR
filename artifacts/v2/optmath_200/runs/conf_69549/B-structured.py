# IR: {"sets":{"packages":[0,1,2,3,4,5,6,7,8,9],"legs":[0,1,2,3,4,5,6],"users":{"0":[0,1,2,3,6,7,9],"1":[0,1,4,6],"2":[1,5,8,9],"3":[0,1,4,8],"4":[1,3,4],"5":[0,2,5],"6":[2,3,4,7,8]}},"params":{"revenue":"revenue[p] from params","demand":"demand[p] from params","flight_capacity":"flight_capacity[l] from params"},"variables":{"sold[p]":"nonnegative integer"},"constraints":["sold[p] <= demand[p] for every package p","sum(sold[p] for p in users[l]) <= flight_capacity[l] for every leg l"],"objective":"maximize sum(revenue[p] * sold[p] for every package p)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    users = {
        0: (0, 1, 2, 3, 6, 7, 9),
        1: (0, 1, 4, 6),
        2: (1, 5, 8, 9),
        3: (0, 1, 4, 8),
        4: (1, 3, 4),
        5: (0, 2, 5),
        6: (2, 3, 4, 7, 8),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 9)
    model.legs = pyo.RangeSet(0, 6)

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
            sum(mdl.sold[p] for p in users[leg])
            <= mdl.flight_capacity[leg]
        ),
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[p] * model.sold[p]
            for p in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}