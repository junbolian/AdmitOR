# IR: {"sets":{"cities":"0..num_cities-1","arcs":"(i,j) in cities^2 where i != j","transit":"cities excluding 0 and num_cities-1"},"params":{"num_cities":"params['num_cities']","capacity[i,j]":"params[f'capacity_{i}_{j}'] for every arc"},"variables":{"flow[i,j]":"continuous, nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every arc","sum(flow[j,i] for j != i) == sum(flow[i,j] for j != i) for every transit city i"],"objective":"maximize sum(flow[0,j] - flow[j,0] for j != 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.city_count = pyo.Param(
        initialize=params["num_cities"],
        within=pyo.PositiveIntegers,
    )
    city_count = int(pyo.value(model.city_count))

    model.cities = pyo.Set(
        initialize=range(city_count),
        ordered=True,
    )
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in range(city_count)
            for destination in range(city_count)
            if origin != destination
        ],
    )
    model.transit_cities = pyo.Set(
        initialize=range(1, city_count - 1),
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"capacity_{origin}_{destination}"]
            for origin, destination in model.arcs
        },
        within=pyo.Reals,
    )

    model.flow = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(network, city):
        incoming = sum(
            network.flow[other, city]
            for other in network.cities
            if other != city
        )
        outgoing = sum(
            network.flow[city, other]
            for other in network.cities
            if other != city
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.transit_cities,
        rule=conservation_rule,
    )

    model.max_flow_objective = pyo.Objective(
        expr=sum(
            model.flow[0, city] - model.flow[city, 0]
            for city in model.cities
            if city != 0
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}