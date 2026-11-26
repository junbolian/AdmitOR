# IR: {"sets":{"hubs":"0..7","intermediate_hubs":"1..6","arcs":{"0":[1,2,3,5,6,7],"1":[0,2,3,4,5,6],"2":[0,1,3,4,5,6,7],"3":[0,1,2,4,5,7],"4":[0,1,2,3,5,6,7],"5":[0,1,2,3,4,6,7],"6":[0,1,2,3,4,5,7],"7":[0,1,3,4,5,6]}},"params":{"capacity[i,j]":"params['cap_i_j'] for each arc (i,j)"},"variables":{"flow[i,j]":{"type":"continuous","lower_bound":0}},"constraints":["flow[i,j] <= capacity[i,j] for each arc (i,j)","sum(flow[i,j] for outgoing arcs) = sum(flow[j,i] for incoming arcs) for each intermediate hub i"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for outgoing source arcs) - sum(flow[i,0] for incoming source arcs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    adjacency = {
        0: (1, 2, 3, 5, 6, 7),
        1: (0, 2, 3, 4, 5, 6),
        2: (0, 1, 3, 4, 5, 6, 7),
        3: (0, 1, 2, 4, 5, 7),
        4: (0, 1, 2, 3, 5, 6, 7),
        5: (0, 1, 2, 3, 4, 6, 7),
        6: (0, 1, 2, 3, 4, 5, 7),
        7: (0, 1, 3, 4, 5, 6),
    }
    arcs = [
        (origin, destination)
        for origin, destinations in adjacency.items()
        for destination in destinations
    ]
    incoming = {
        hub: tuple(origin for origin, destination in arcs if destination == hub)
        for hub in range(8)
    }
    capacities = {
        (origin, destination): params[f"cap_{origin}_{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.RangeSet(0, 7)
    model.intermediate_hubs = pyo.RangeSet(1, 6)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def conservation_rule(network, hub):
        return (
            sum(network.flow[hub, destination] for destination in adjacency[hub])
            == sum(network.flow[origin, hub] for origin in incoming[hub])
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_hubs,
        rule=conservation_rule,
    )
    model.total_delivery = pyo.Objective(
        expr=(
            sum(model.flow[0, destination] for destination in adjacency[0])
            - sum(model.flow[origin, 0] for origin in incoming[0])
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_delivery))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}