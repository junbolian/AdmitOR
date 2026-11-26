# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"T":[1,2,3,4,5,6,7],"A":"{(0,j): j=1..8} union {(i,j): i,j=1..8, i!=j, (i,j)!=(4,7)}"},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for every v in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for (0,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(9))
    transit_nodes = tuple(range(1, 8))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in range(1, 9)
        if origin != destination and (origin, destination) != (4, 7)
    )

    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }

    incoming = {
        node: tuple(arc for arc in arcs if arc[1] == node)
        for node in nodes
    }
    outgoing = {
        node: tuple(arc for arc in arcs if arc[0] == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=nodes, ordered=True)
    model.transit_hubs = pyo.Set(initialize=transit_nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, node):
        return (
            sum(network.flow[arc] for arc in incoming[node])
            == sum(network.flow[arc] for arc in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_hubs, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=sum(model.flow[arc] for arc in outgoing[0]),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}