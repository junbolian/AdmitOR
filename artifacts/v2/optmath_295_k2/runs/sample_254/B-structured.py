# {"sets":{"I":"0..4","J":"0..6"},"params":{"supply":"I -> nonnegative real, from params['supply']","demand":"J -> nonnegative real, from params['demand']","cost":"I x J -> real, from params['cost']","limit":"I x J -> nonnegative real, from params['limit']"},"variables":{"x[i,j]":"nonnegative continuous"},"constraints":["sum(x[i,j] for j in J) <= supply[i], for each i in I","sum(x[i,j] for i in I) == demand[j], for each j in J","x[i,j] <= limit[i,j], for each (i,j) in I x J"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 4)
    model.destinations = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.limit = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: limit[i][j],
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_constraints = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: (
            sum(mdl.x[i, j] for j in mdl.destinations) <= mdl.supply[i]
        ),
    )
    model.demand_constraints = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: (
            sum(mdl.x[i, j] for i in mdl.origins) == mdl.demand[j]
        ),
    )
    model.route_constraints = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: mdl.x[i, j] <= mdl.limit[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}