# IR: {"sets":{"N":"{0,...,8}","A":"{(i,j) in N x N: i != j and (i,j) != (8,7)}","T":"{1,...,7}"},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'] for every (i,j) in A"},"variables":{"flow[i,j]":"continuous, nonnegative for every (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,k] for (i,k) in A) = sum(flow[k,j] for (k,j) in A) for every k in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    nodes = tuple(range(9))
    arcs = tuple(
        (i, j)
        for i in nodes
        for j in nodes
        if i != j and (i, j) != (8, 7)
    )
    incoming = {
        node: tuple((i, j) for i, j in arcs if j == node)
        for node in nodes
    }
    outgoing = {
        node: tuple((i, j) for i, j in arcs if i == node)
        for node in nodes
    }

    model.node_set = pyo.Set(initialize=nodes)
    model.arc_set = pyo.Set(dimen=2, initialize=arcs)
    model.transit_set = pyo.Set(initialize=range(1, 8))

    model.arc_capacity = pyo.Param(
        model.arc_set,
        initialize={
            (i, j): params[f"capacity_{i}_{j}"]
            for i, j in arcs
        },
        within=pyo.Reals,
    )
    model.flow = pyo.Var(
        model.arc_set,
        domain=pyo.NonNegativeReals,
    )

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.arc_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arc_set,
        rule=capacity_rule,
    )

    def conservation_rule(network, node):
        return (
            sum(network.flow[i, j] for i, j in incoming[node])
            == sum(network.flow[i, j] for i, j in outgoing[node])
        )

    model.flow_balance = pyo.Constraint(
        model.transit_set,
        rule=conservation_rule,
    )

    model.total_flow_objective = pyo.Objective(
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
        obj_val = float(pyo.value(model.total_flow_objective))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}