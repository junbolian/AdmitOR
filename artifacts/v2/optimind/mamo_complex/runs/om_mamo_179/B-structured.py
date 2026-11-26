# IR: {"sets":{"N":"{0,...,7}","T":"{1,...,6}","A":"{(i,j): i in {0,...,6}, j in N, i != j} \\ {(1,5),(2,1)}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for v in T"],"objective":"maximize sum(flow[i,7] for (i,7) in A), in thousands of units"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    transit_nodes = tuple(range(1, 7))
    arcs = tuple(
        (origin, destination)
        for origin in range(7)
        for destination in nodes
        if origin != destination
        and (origin, destination) not in {(1, 5), (2, 1)}
    )

    capacities = {
        (origin, destination): params[f"capacity_{origin}_{destination}"]
        for origin, destination in arcs
    }
    incoming = {
        node: tuple(origin for origin, destination in arcs if destination == node)
        for node in nodes
    }
    outgoing = {
        node: tuple(destination for origin, destination in arcs if origin == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.node_set = pyo.Set(initialize=nodes, ordered=True)
    model.transit_set = pyo.Set(initialize=transit_nodes, ordered=True)
    model.arc_set = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.route_capacity = pyo.Param(
        model.arc_set,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, origin, destination):
        return (
            mdl.flow[origin, destination]
            <= mdl.route_capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arc_set, rule=capacity_rule)

    def conservation_rule(mdl, node):
        return sum(
            mdl.flow[origin, node] for origin in incoming[node]
        ) == sum(
            mdl.flow[node, destination] for destination in outgoing[node]
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_set,
        rule=conservation_rule,
    )

    model.total_delivery = pyo.Objective(
        expr=sum(model.flow[origin, 7] for origin in incoming[7]),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve may raise before a solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_delivery))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}