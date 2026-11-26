# IR: {"sets":{"N":[0,1,2,3,4,5,6,7],"T":[1,2,3,4,5,6],"A":"{(0,j): j=1..7} union {(i,j): i,j=1..7, i!=j, (i,j)!=(3,6)}"},"params":{"capacity[i,j]":"params['cap_'+str(i)+'_'+str(j)] for every (i,j) in A"},"variables":{"flow[i,j]":{"type":"continuous","domain":"nonnegative","index":"A"}},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for every v in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for (0,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        [(0, target) for target in range(1, 8)]
        + [
            (origin, target)
            for origin in range(1, 8)
            for target in range(1, 8)
            if origin != target and (origin, target) != (3, 6)
        ]
    )

    capacities = {
        (origin, target): params[f"cap_{origin}_{target}"]
        for origin, target in arcs
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(8), ordered=True)
    model.transit_nodes = pyo.Set(initialize=range(1, 7), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, target):
        return (
            network.flow[origin, target]
            <= network.capacity[origin, target]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(network, node):
        incoming = sum(
            network.flow[origin, target]
            for origin, target in arcs
            if target == node
        )
        outgoing = sum(
            network.flow[origin, target]
            for origin, target in arcs
            if origin == node
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=sum(
            model.flow[origin, target]
            for origin, target in arcs
            if origin == 0
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}