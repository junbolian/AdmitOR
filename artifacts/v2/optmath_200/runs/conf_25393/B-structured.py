# IR: {"sets":{"C":"{0,...,7}","A":"{(i,j) in C x C: i != j}"},"params":{"net_demand":"params['net_demand'][i] for i in C","cost":"params[f'cost_{i}_to_{j}'] for (i,j) in A","capacity":"params[f'cap_{i}_to_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) == net_demand[i] for i in C","flow[i,j] <= capacity[i,j] for (i,j) in A"],"objective":{"sense":"minimize","expression":"sum(cost[i,j] * flow[i,j] for (i,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 7)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(8)
            for destination in range(8)
            if origin != destination
        ],
    )

    demand_data = params["net_demand"]
    model.net_demand = pyo.Param(
        model.cities,
        initialize={city: demand_data[city] for city in range(8)},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): params[f"cost_{origin}_to_{destination}"]
            for origin, destination in model.routes
        },
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.routes,
        initialize={
            (origin, destination): params[f"cap_{origin}_to_{destination}"]
            for origin, destination in model.routes
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

    model.city_balance = pyo.Constraint(
        model.cities,
        rule=balance_rule,
    )

    def capacity_rule(instance, origin, destination):
        return (
            instance.flow[origin, destination]
            <= instance.route_capacity[origin, destination]
        )

    model.capacity_limit = pyo.Constraint(
        model.routes,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.flow[origin, destination]
            for origin, destination in model.routes
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