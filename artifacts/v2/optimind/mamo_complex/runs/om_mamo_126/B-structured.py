# IR: {"sets":{"V":[0,1,2,3,4,5],"A":"{(i,j) in V x V: i != j}","T":[1,2,3,4]},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for every (i,j) in A"},"variables":{"flow[i,j]":{"domain":"NonNegativeIntegers","indices":"A"}},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,j] for j != i) == sum(flow[j,i] for j != i) for every i in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for j != 0) - sum(flow[j,0] for j != 0)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(6))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.transit_cities = pyo.Set(initialize=(1, 2, 3, 4))

    model.capacity = pyo.Param(model.arcs, initialize=capacities)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeIntegers)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.track_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, city):
        outgoing = sum(
            network.flow[city, destination]
            for destination in cities
            if destination != city
        )
        incoming = sum(
            network.flow[origin, city]
            for origin in cities
            if origin != city
        )
        return outgoing == incoming

    model.flow_balance = pyo.Constraint(
        model.transit_cities, rule=conservation_rule
    )

    model.total_trains = pyo.Objective(
        expr=(
            sum(model.flow[0, destination] for destination in cities if destination != 0)
            - sum(model.flow[origin, 0] for origin in cities if origin != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_trains))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}