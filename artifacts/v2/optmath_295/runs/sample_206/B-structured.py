# IR: {
#   "sets": {"origins": "0..9", "destinations": "0..7"},
#   "params": {"supply": "params['supply'][i]", "demand": "params['demand'][j]", "transport_cost": "params['transport_cost'][i][j]", "transport_limit": "params['transport_limit'][i][j]"},
#   "variables": {"flow[i,j]": "continuous, nonnegative"},
#   "constraints": [
#     "sum_j flow[i,j] <= supply[i] for each origin i",
#     "sum_i flow[i,j] == demand[j] for each destination j",
#     "flow[i,j] <= transport_limit[i,j] for each origin i and destination j"
#   ],
#   "objective": "minimize sum_i sum_j transport_cost[i,j] * flow[i,j]"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 9)
    model.destinations = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: params["supply"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: params["transport_cost"][i][j],
        within=pyo.Reals,
    )
    model.transport_limit = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: params["transport_limit"][i][j],
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_capacity = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: sum(
            mdl.flow[i, j] for j in mdl.destinations
        ) <= mdl.supply[i],
    )
    model.demand_fulfillment = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.flow[i, j] for i in mdl.origins
        ) == mdl.demand[j],
    )
    model.pair_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: (
            mdl.flow[i, j] <= mdl.transport_limit[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.flow[i, j]
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}