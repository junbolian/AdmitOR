# IR: {"sets":{"cities":"0..5","routes":"(i,j) in cities x cities where i != j"},"params":{"net_demand":"params['net_demand'][i]","cost":"params['cost'][i][j if j < i else j-1]","capacity":"params['capacity'][i][j if j < i else j-1]"},"variables":{"flow[i,j]":"continuous, nonnegative, for each route"},"constraints":["For each city i: sum(flow[j,i], j != i) - sum(flow[i,j], j != i) == net_demand[i]","For each route (i,j): flow[i,j] <= capacity[i,j]"],"objective":"Minimize sum(cost[i,j] * flow[i,j] for each route)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_demand = params["net_demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    cities = range(6)
    routes = [(source, destination)
              for source in cities
              for destination in cities
              if source != destination]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.routes = pyo.Set(initialize=routes, dimen=2, ordered=True)

    model.net_demand = pyo.Param(
        model.cities,
        initialize={city: net_demand[city] for city in cities},
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.routes,
        initialize={
            (source, destination): cost[source][
                destination if destination < source else destination - 1
            ]
            for source, destination in routes
        },
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.routes,
        initialize={
            (source, destination): capacity[source][
                destination if destination < source else destination - 1
            ]
            for source, destination in routes
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def balance_rule(instance, city):
        inflow = sum(
            instance.flow[other, city]
            for other in instance.cities
            if other != city
        )
        outflow = sum(
            instance.flow[city, other]
            for other in instance.cities
            if other != city
        )
        return inflow - outflow == instance.net_demand[city]

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)

    def capacity_rule(instance, source, destination):
        return (
            instance.flow[source, destination]
            <= instance.route_capacity[source, destination]
        )

    model.capacity_limits = pyo.Constraint(model.routes, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[source, destination]
            * model.flow[source, destination]
            for source, destination in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}