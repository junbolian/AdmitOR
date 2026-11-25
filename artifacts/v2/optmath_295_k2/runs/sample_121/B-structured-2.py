# {
#   "sets": {"I": "origins 0..13", "J": "destinations 0..11"},
#   "params": {"supply": "params['supply'][i]", "demand": "params['demand'][j]", "cost_matrix": "params['cost_matrix'][i][j]"},
#   "variables": {"shipment[i,j]": "continuous, nonnegative, for i in I and j in J"},
#   "constraints": [
#     "For each i in I: sum(shipment[i,j] for j in J) == supply[i] (explicit exact-shipment requirement).",
#     "For each j in J: sum(shipment[i,j] for i in I) == demand[j]."
#   ],
#   "objective": "minimize sum(cost_matrix[i][j] * shipment[i,j] for i in I and j in J)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 13)
    model.destinations = pyo.RangeSet(0, 11)

    model.supply_amount = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand_amount = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost_matrix[i][j],
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
        ) == mdl.supply_amount[i],
    )

    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.origins
        ) == mdl.demand_amount[j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}