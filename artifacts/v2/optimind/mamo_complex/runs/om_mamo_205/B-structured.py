# IR: {"sets":{"V":[0,1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j} excluding (1,6) and (2,4)"},"params":{"capacity[i,j]":"params['cap_i_j'] for every (i,j) in A; keys denote directed arcs i -> j, including keys starting with cap_6_"},"variables":{"flow[i,j]":"nonnegative continuous for (i,j) in A","throughput":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum_j flow[0,j] - sum_i flow[i,0] = throughput","sum_j flow[v,j] - sum_i flow[i,v] = 0 for v in {1,2,3,4,5}","sum_i flow[i,6] - sum_j flow[6,j] = throughput"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = tuple(range(7))
    arcs = tuple(
        (origin, destination)
        for origin in vertices
        for destination in vertices
        if origin != destination
        and (origin, destination) not in {(1, 6), (2, 4)}
    )
    capacities = {
        (origin, destination): params[f"cap_{origin}_{destination}"]
        for origin, destination in arcs
    }
    outgoing = {
        city: tuple(destination for origin, destination in arcs if origin == city)
        for city in vertices
    }
    incoming = {
        city: tuple(origin for origin, destination in arcs if destination == city)
        for city in vertices
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=vertices, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.arc_capacity = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(network, city):
        departures = sum(
            network.flow[city, destination]
            for destination in outgoing[city]
        )
        arrivals = sum(
            network.flow[origin, city]
            for origin in incoming[city]
        )
        if city == 0:
            return departures - arrivals == network.throughput
        if city == 6:
            return arrivals - departures == network.throughput
        return departures - arrivals == 0

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)
    model.max_throughput = pyo.Objective(
        expr=model.throughput, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.max_throughput))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}