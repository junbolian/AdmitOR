# IR: {
#   "sets": {"centers": "1..7", "routes": "ordered pairs (i,j) with i != j, in row-major order"},
#   "params": {"supply": "params['supply'], length 7", "demand": "params['demand'], length 7", "cost": "params['cost'], length 42, indexed by routes"},
#   "variables": {"transfer[i,j]": "nonnegative continuous units transferred on route (i,j)"},
#   "constraints": [
#     "For each i: supply[i] + sum(transfer[j,i], j != i) - sum(transfer[i,j], j != i) >= demand[i]"
#   ],
#   "objective": "minimize sum(cost[i,j] * transfer[i,j] for (i,j) in routes)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    centers = list(range(1, 8))
    routes = [
        (origin, destination)
        for origin in centers
        for destination in centers
        if origin != destination
    ]

    model = pyo.ConcreteModel()
    model.centers = pyo.Set(initialize=centers, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=routes, ordered=True)

    model.initial_supply = pyo.Param(
        model.centers,
        initialize={center: supply[center - 1] for center in centers},
        within=pyo.NonNegativeReals,
    )
    model.required_demand = pyo.Param(
        model.centers,
        initialize={center: demand[center - 1] for center in centers},
        within=pyo.NonNegativeReals,
    )
    model.route_cost = pyo.Param(
        model.routes,
        initialize={route: cost[position] for position, route in enumerate(routes)},
        within=pyo.Reals,
    )

    model.transfer = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def supply_balance_rule(instance, center):
        incoming = sum(
            instance.transfer[other, center]
            for other in instance.centers
            if other != center
        )
        outgoing = sum(
            instance.transfer[center, other]
            for other in instance.centers
            if other != center
        )
        return (
            instance.initial_supply[center] + incoming - outgoing
            >= instance.required_demand[center]
        )

    model.supply_balance = pyo.Constraint(
        model.centers, rule=supply_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}