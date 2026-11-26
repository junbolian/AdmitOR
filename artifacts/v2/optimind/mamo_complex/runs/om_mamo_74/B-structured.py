# IR: {"sets":{"N":"0..7","A":"{(i,j) in N x N: i != j and (i,j) != (4,3)}","T":"N minus {0,7}"},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for each (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for each v in T"],"objective":{"sense":"maximize","expression":"sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(8))
    arcs = tuple(
        (i, j)
        for i in nodes
        for j in nodes
        if i != j and (i, j) != (4, 3)
    )

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.transit_nodes = pyo.Set(
        initialize=[v for v in nodes if v not in (0, 7)],
        ordered=True,
    )

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"capacity_{i}_{j}"]
            for i, j in arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, v):
        incoming = sum(
            network.flow[i, j] for i, j in arcs if j == v
        )
        outgoing = sum(
            network.flow[i, j] for i, j in arcs if i == v
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[i, j] for i, j in arcs if i == 0)
            - sum(model.flow[i, j] for i, j in arcs if j == 0)
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