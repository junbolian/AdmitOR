# IR: {"sets":{"O":"range(num_origins)","D":"range(num_destinations)"},"params":{"num_origins":"frozen integer from params","num_destinations":"frozen integer from params","supply":"nonnegative vector indexed by O from params","demand":"nonnegative vector indexed by D from params","cost":"real matrix indexed by O x D from params"},"variables":{"shipment[i,j]":"nonnegative continuous for (i,j) in O x D"},"constraints":["sum(shipment[i,j] for j in D) == supply[i] for each i in O","sum(shipment[i,j] for i in O) == demand[j] for each j in D"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in O x D)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_origins = params["num_origins"]
    num_destinations = params["num_destinations"]
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(
        initialize=range(num_origins), ordered=True
    )
    model.destinations = pyo.Set(
        initialize=range(num_destinations), ordered=True
    )

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

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.destinations
        ) == mdl.supply[i],
    )
    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.origins
        ) == mdl.demand[j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}