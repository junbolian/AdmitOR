# IR: {"sets":{"C":"0..4 (cities 1..5)","A":"{(i,j) in C x C: i != j}"},"params":{"supply":"supply[i] from params['supply'][i]","demand":"demand[i] from params['demand'][i]","cost":"cost[i,j] from params['cost'][i][j]"},"variables":{"transfer[i,j]":"nonnegative continuous, (i,j) in A"},"constraints":["For each i in C: supply[i] + sum(transfer[j,i] for j != i) - sum(transfer[i,j] for j != i) >= demand[i]"],"objective":"minimize sum(cost[i,j] * transfer[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve resource redistribution using zero-based supply, demand, and cost arrays."""
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 4)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )

    model.city_supply = pyo.Param(
        model.cities,
        initialize={city: params["supply"][city] for city in model.cities},
    )
    model.city_demand = pyo.Param(
        model.cities,
        initialize={city: params["demand"][city] for city in model.cities},
    )
    model.transfer_cost = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): params["cost"][origin][destination]
            for origin, destination in model.routes
        },
    )

    model.transfer = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def resource_balance_rule(model, city):
        incoming = sum(
            model.transfer[other, city]
            for other in model.cities
            if other != city
        )
        outgoing = sum(
            model.transfer[city, other]
            for other in model.cities
            if other != city
        )
        return (
            model.city_supply[city] + incoming - outgoing
            >= model.city_demand[city]
        )

    model.resource_balance = pyo.Constraint(
        model.cities, rule=resource_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transfer_cost[origin, destination]
            * model.transfer[origin, destination]
            for origin, destination in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
    except (RuntimeError, ValueError):
        return {"objective": None, "status": "solve_failed"}

    return {"objective": obj_val, "status": "optimal"}