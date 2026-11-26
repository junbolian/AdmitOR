# IR: {"sets":{"N":"{0,...,num_nodes-1}","A":"{(i,j) in N x N: i != j}","I":"N minus {0,num_nodes-1}"},"params":{"num_nodes":"params['num_nodes']; must equal 8","capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[j,v] for j != v) = sum(flow[v,j] for j != v) for v in I"],"objective":"maximize sum(flow[0,j] for j != 0) - sum(flow[j,0] for j != 0)"}

import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = operator.index(params["num_nodes"])
    if num_nodes != 8:
        raise ValueError("num_nodes must equal 8 for the specified network.")

    nodes = range(num_nodes)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    capacities = {
        (i, j): params[f"capacity_{i}_{j}"]
        for i, j in arcs
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.internal_nodes = pyo.Set(
        initialize=range(1, num_nodes - 1),
        ordered=True,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.Reals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.arc_capacity = pyo.Constraint(
        model.arcs,
        rule=capacity_rule,
    )

    def conservation_rule(network, node):
        incoming = sum(
            network.flow[other, node]
            for other in network.nodes
            if other != node
        )
        outgoing = sum(
            network.flow[node, other]
            for other in network.nodes
            if other != node
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.internal_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[0, j] for j in model.nodes if j != 0)
            - sum(model.flow[j, 0] for j in model.nodes if j != 0)
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_flow))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}