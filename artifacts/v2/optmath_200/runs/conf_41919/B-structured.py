# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3,4,5]},"params":{"capacity":"params['capacity'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","min_producers":"params['min_producers'][j]","min_delivery":"params['min_delivery'][i]"},"variables":{"x[i,j]":"NonNegativeReals","y[i,j]":"Binary"},"constraints":["sum(j in C, x[i,j]) <= capacity[i] for i in P","sum(i in P, x[i,j]) >= demand[j] for j in C","sum(i in P, y[i,j]) >= min_producers[j] for j in C","x[i,j] >= min_delivery[i]*y[i,j] for (i,j) in P cross C","x[i,j] <= capacity[i]*y[i,j] for (i,j) in P cross C"],"objective":"minimize sum((i,j) in P cross C, cost[i,j]*x[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed sequences; cost is indexed as cost[i][j]."""
    capacity = params["capacity"]
    demand = params["demand"]
    cost = params["cost"]
    min_producers = params["min_producers"]
    min_delivery = params["min_delivery"]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 5)

    model.capacity = pyo.Param(
        model.P, initialize=lambda mdl, i: capacity[i]
    )
    model.demand = pyo.Param(
        model.C, initialize=lambda mdl, j: demand[j]
    )
    model.cost = pyo.Param(
        model.P, model.C, initialize=lambda mdl, i, j: cost[i][j]
    )
    model.min_producers = pyo.Param(
        model.C, initialize=lambda mdl, j: min_producers[j]
    )
    model.min_delivery = pyo.Param(
        model.P, initialize=lambda mdl, i: min_delivery[i]
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    model.capacity_limit = pyo.Constraint(
        model.P,
        rule=lambda mdl, i: (
            sum(mdl.x[i, j] for j in mdl.C) <= mdl.capacity[i]
        ),
    )
    model.demand_requirement = pyo.Constraint(
        model.C,
        rule=lambda mdl, j: (
            sum(mdl.x[i, j] for i in mdl.P) >= mdl.demand[j]
        ),
    )
    model.producer_requirement = pyo.Constraint(
        model.C,
        rule=lambda mdl, j: (
            sum(mdl.y[i, j] for i in mdl.P) >= mdl.min_producers[j]
        ),
    )
    model.minimum_delivery_link = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, i, j: (
            mdl.x[i, j] >= mdl.min_delivery[i] * mdl.y[i, j]
        ),
    )
    model.maximum_delivery_link = pyo.Constraint(
        model.P,
        model.C,
        rule=lambda mdl, i, j: (
            mdl.x[i, j] <= mdl.capacity[i] * mdl.y[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.P
            for j in model.C
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}