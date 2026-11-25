# IR: {"sets":{"cities":"0..5","routes":"(i,j) for i,j in cities if i != j"},"params":{"net_demand":"params['net_demand'][i]","cost":"params['cost'][i][j if j < i else j-1]","capacity":"params['capacity'][i][j if j < i else j-1]"},"variables":{"flow[i,j]":"continuous, nonnegative"},"constraints":["For each city i: sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) == net_demand[i]","For each route (i,j): flow[i,j] <= capacity[i,j]"},"objective":"Minimize sum(cost[i,j] * flow[i,j] for (i,j) in routes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_demand = params["net_demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    cities = range(6)
    routes = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=routes, ordered=True)

    model.net_demand = pyo.Param(
        model.cities,
        initialize={i: net_demand[i] for i in cities},
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.routes,
        initialize={
            (i, j): cost[i][j if j < i else j - 1]
            for i, j in routes
        },
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.routes,
        initialize={
            (i, j): capacity[i][j if j < i else j - 1]
            for i, j in routes
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def balance_rule(instance, city):
        inflow = sum(
            instance.flow[source, city]
            for source in instance.cities
            if source != city
        )
        outflow = sum(
            instance.flow[city, destination]
            for destination in instance.cities
            if destination != city
        )
        return inflow - outflow == instance.net_demand[city]

    model.flow_balance = pyo.Constraint(
        model.cities, rule=balance_rule
    )

    def capacity_rule(instance, source, destination):
        return (
            instance.flow[source, destination]
            <= instance.route_capacity[source, destination]
        )

    model.capacity_limit = pyo.Constraint(
        model.routes, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.flow[i, j]
            for i, j in model.routes
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