# IR: {
#   "sets": {"origins": "0..13", "destinations": "0..13"},
#   "params": {"supply[i]": "params['supply'][i]", "demand[j]": "params['demand'][j]", "cost[i,j]": "params['cost'][i][j]"},
#   "variables": {"shipment[i,j]": "continuous, nonnegative"},
#   "constraints": [
#     "For each origin i: sum(shipment[i,j] for j in destinations) == supply[i]",
#     "For each destination j: sum(shipment[i,j] for i in origins) == demand[j]"
#   ],
#   "objective": "minimize sum(cost[i,j] * shipment[i,j] for i in origins for j in destinations)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using supply/demand sequences and a nested cost matrix."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 13)
    model.destinations = pyo.RangeSet(0, 13)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.Reals,
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
        return (
            sum(mdl.shipment[i, j] for j in mdl.destinations)
            == mdl.supply[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.origins)
            == mdl.demand[j]
        )

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    # APPSI can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}