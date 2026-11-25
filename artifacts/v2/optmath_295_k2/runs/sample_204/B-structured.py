# IR: {"sets":{"cities":[0,1,2,3,4,5],"routes":"{(i,j): i,j in cities, i != j}"},"params":{"supply":"params['supply'][i], real","cost":"params['cost'][i][j], real","capacity":"params['capacity'][i][j], nonnegative real"},"variables":{"flow[i,j]":"nonnegative continuous, (i,j) in routes"},"constraints":["For each city i: sum(flow[i,j] for j != i) - sum(flow[j,i] for j != i) = supply[i]","For each route (i,j): flow[i,j] <= capacity[i,j]"],"objective":"Minimize sum(cost[i,j] * flow[i,j] for (i,j) in routes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 5)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )

    model.supply = pyo.Param(
        model.cities,
        initialize={city: params["supply"][city] for city in model.cities},
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): params["cost"][origin][destination]
            for origin, destination in model.routes
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): params["capacity"][origin][destination]
            for origin, destination in model.routes
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def balance_rule(instance, city):
        outgoing = sum(
            instance.flow[city, destination]
            for destination in instance.cities
            if destination != city
        )
        incoming = sum(
            instance.flow[origin, city]
            for origin in instance.cities
            if origin != city
        )
        return outgoing - incoming == instance.supply[city]

    model.city_balance = pyo.Constraint(model.cities, rule=balance_rule)

    def capacity_rule(instance, origin, destination):
        return (
            instance.flow[origin, destination]
            <= instance.capacity[origin, destination]
        )

    model.route_capacity = pyo.Constraint(model.routes, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination] * model.flow[origin, destination]
            for origin, destination in model.routes
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
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}