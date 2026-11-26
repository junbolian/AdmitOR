# IR: {"sets":{"N":"{0,...,num_centers-1}","A":"{(i,j) in N x N: j != 0 and i != j}","T":"N minus {0,num_centers-1}"},"params":{"num_centers":"params['num_centers']; fixed network size","capacity[i,j]":"params['cap_i_j'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,v] for incoming arcs) = sum(flow[v,j] for outgoing arcs) for every v in T"],"objective":"maximize total incoming flow to node num_centers-1 minus total outgoing flow from that node"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_centers = params["num_centers"]
    nodes = list(range(num_centers))
    source = 0
    sink = num_centers - 1

    arcs = [
        (i, j)
        for i in nodes
        for j in nodes
        if j != source and i != j
    ]
    intermediate_nodes = [
        node for node in nodes if node != source and node != sink
    ]

    capacities = {
        (i, j): params[f"cap_{i}_{j}"]
        for i, j in arcs
    }
    incoming = {
        node: [(i, j) for i, j in arcs if j == node]
        for node in nodes
    }
    outgoing = {
        node: [(i, j) for i, j in arcs if i == node]
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.intermediate_nodes = pyo.Set(
        initialize=intermediate_nodes, ordered=True
    )
    model.capacity = pyo.Param(model.arcs, initialize=capacities)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, node):
        return (
            sum(network.flow[i, j] for i, j in incoming[node])
            == sum(network.flow[i, j] for i, j in outgoing[node])
        )

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[i, j] for i, j in incoming[sink])
            - sum(model.flow[i, j] for i, j in outgoing[sink])
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