# IR: {"sets":{"N":"{0,...,7}","A":"{(i,j) in N x N: i != j and (i,j) != (1,2)}"},"params":{"capacity[i,j]":"params['cap_i_j'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative for (i,j) in A","total_flow":"continuous, nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,j] for outgoing arcs) - sum(flow[j,i] for incoming arcs) = total_flow if i=0, -total_flow if i=7, and 0 otherwise, for every i in N"],"objective":"maximize total_flow"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    arcs = tuple(
        (origin, destination)
        for origin in nodes
        for destination in nodes
        if origin != destination and (origin, destination) != (1, 2)
    )

    capacities = {
        (origin, destination): params[f"cap_{origin}_{destination}"]
        for origin, destination in arcs
    }
    outgoing = {
        node: tuple(destination for origin, destination in arcs if origin == node)
        for node in nodes
    }
    incoming = {
        node: tuple(origin for origin, destination in arcs if destination == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.capacity = pyo.Param(model.arcs, initialize=capacities)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(network, origin, destination):
        return (
            network.flow[origin, destination]
            <= network.capacity[origin, destination]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(network, node):
        net_outflow = sum(
            network.flow[node, destination]
            for destination in outgoing[node]
        ) - sum(
            network.flow[origin, node]
            for origin in incoming[node]
        )

        if node == 0:
            return net_outflow == network.total_flow
        if node == 7:
            return net_outflow == -network.total_flow
        return net_outflow == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)
    model.max_flow_objective = pyo.Objective(
        expr=model.total_flow,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Leave success determination to objective retrieval below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}