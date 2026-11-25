# {
#   "sets": {"origins": "0..6", "destinations": "0..6"},
#   "params": {"supply": "nonnegative vector indexed by origin", "demand": "nonnegative vector indexed by destination", "cost": "real matrix indexed by origin and destination"},
#   "variables": {"shipment[i,j]": "nonnegative continuous"},
#   "constraints": [
#     "For each origin i: sum(shipment[i,j] for j in destinations) == supply[i]",
#     "For each destination j: sum(shipment[i,j] for i in origins) == demand[j]"
#   ],
#   "objective": "minimize sum(cost[i,j] * shipment[i,j] for i in origins for j in destinations)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 6)
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

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return sum(
            mdl.shipment[i, j] for j in mdl.destinations
        ) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(
            mdl.shipment[i, j] for i in mdl.origins
        ) == mdl.demand[j]

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=supply_rule,
    )
    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=demand_rule,
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}