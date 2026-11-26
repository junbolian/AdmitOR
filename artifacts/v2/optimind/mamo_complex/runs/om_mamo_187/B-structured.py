# IR: {"sets":{"N":"{0,...,8}","A":"{(i,j) in N x N: i != j and (i,j) != (8,7)}","T":"{1,...,7}"},"params":{"capacity[i,j]":"params['capacity_' + str(i) + '_' + str(j)] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,j] for outgoing arcs of i) = sum(flow[j,i] for incoming arcs of i) for i in T"],"objective":"maximize sum(flow[0,j] for outgoing arcs of 0) - sum(flow[i,0] for incoming arcs of 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Return the maximum net flow from node 0 to node 8."""
    nodes = tuple(range(9))
    arcs = tuple(
        (i, j)
        for i in nodes
        for j in nodes
        if i != j and (i, j) != (8, 7)
    )
    outgoing = {
        node: tuple((i, j) for i, j in arcs if i == node)
        for node in nodes
    }
    incoming = {
        node: tuple((i, j) for i, j in arcs if j == node)
        for node in nodes
    }
    capacity_data = {
        (i, j): params[f"capacity_{i}_{j}"]
        for i, j in arcs
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.transit_nodes = pyo.Set(initialize=range(1, 8), ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, node):
        return (
            sum(network.flow[i, j] for i, j in outgoing[node])
            == sum(network.flow[i, j] for i, j in incoming[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes, rule=conservation_rule
    )

    model.max_flow_objective = pyo.Objective(
        expr=(
            sum(model.flow[i, j] for i, j in outgoing[0])
            - sum(model.flow[i, j] for i, j in incoming[0])
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}