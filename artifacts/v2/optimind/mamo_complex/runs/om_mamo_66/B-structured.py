# IR: {"sets":{"N":[0,1,2,3,4,5],"T":[1,2,3,4],"A":[[0,1],[0,2],[0,3],[0,4],[0,5],[1,0],[1,2],[1,3],[1,5],[2,0],[2,1],[2,3],[2,4],[2,5],[3,0],[3,1],[3,2],[3,5],[4,0],[4,1],[4,2],[4,3],[4,5],[5,0],[5,1],[5,2],[5,3],[5,4]]},"params":{"capacity[i,j]":"params[f'capacity_{i}_{j}'], nonnegative, for (i,j) in A"},"variables":{"flow[i,j]":"continuous nonnegative, for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for v in T"],"objective":"maximize sum(flow[0,j] for (0,j) in A) - sum(flow[i,0] for (i,0) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 5),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    )

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(6), ordered=True)
    model.transit_nodes = pyo.Set(initialize=(1, 2, 3, 4), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

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

    def conservation_rule(network, vertex):
        incoming = sum(
            network.flow[i, j]
            for i, j in network.arcs
            if j == vertex
        )
        outgoing = sum(
            network.flow[i, j]
            for i, j in network.arcs
            if i == vertex
        )
        return incoming == outgoing

    model.flow_conservation = pyo.Constraint(
        model.transit_nodes, rule=conservation_rule
    )

    model.total_flow = pyo.Objective(
        expr=(
            sum(model.flow[i, j] for i, j in model.arcs if i == 0)
            - sum(model.flow[i, j] for i, j in model.arcs if j == 0)
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