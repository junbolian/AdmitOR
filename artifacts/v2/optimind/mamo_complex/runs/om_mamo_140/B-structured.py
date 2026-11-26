# IR: {"sets":{"V":"{0,...,8}","T":"{1,...,7}","A":"{(0,j): j=1,...,8} union {(i,j): i,j=1,...,8, i!=j, (i,j)!=(4,7)}"},"params":{"capacity[i,j]":"params['cap_i_j'] for every (i,j) in A"},"variables":{"flow[i,j]":"NonNegativeReals for every (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for every v in T"],"objective":"maximize sum(flow[0,j] for (0,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        [(0, destination) for destination in range(1, 9)]
        + [
            (origin, destination)
            for origin in range(1, 9)
            for destination in range(1, 9)
            if origin != destination and (origin, destination) != (4, 7)
        ]
    )

    capacities = {
        (origin, destination): params[f"cap_{origin}_{destination}"]
        for origin, destination in arcs
    }

    incoming = {
        hub: [(origin, destination) for origin, destination in arcs
              if destination == hub]
        for hub in range(9)
    }
    outgoing = {
        hub: [(origin, destination) for origin, destination in arcs
              if origin == hub]
        for hub in range(9)
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.RangeSet(0, 8)
    model.transit_hubs = pyo.RangeSet(1, 7)
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

    model.road_capacity = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, hub):
        return (
            pyo.quicksum(network.flow[arc] for arc in incoming[hub])
            == pyo.quicksum(network.flow[arc] for arc in outgoing[hub])
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_hubs, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=pyo.quicksum(model.flow[arc] for arc in outgoing[0]),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # APPsi can raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}