# IR: {"sets":{"origins":"0..6","destinations":"0..5"},"params":{"supply":"supply[i] from params","demand":"demand[j] from params","cost":"cost[i][j] from params","capacity":"capacity[i][j] from params"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum_j shipment[i,j] = supply[i] for each origin i","sum_i shipment[i,j] = demand[j] for each destination j","shipment[i,j] <= capacity[i][j] for each lane (i,j)"],"objective":"minimize sum_i sum_j cost[i][j] * shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 6)
    model.destinations = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.origins, initialize=lambda mdl, i: supply[i]
    )
    model.demand = pyo.Param(
        model.destinations, initialize=lambda mdl, j: demand[j]
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: capacity[i][j],
    )

    model.shipment = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
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
    model.lane_limit = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: mdl.shipment[i, j] <= mdl.capacity[i, j],
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
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}