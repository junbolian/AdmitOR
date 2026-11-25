# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"I":[1,2,3,4,5,6,7],"D":[0,1],"A":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[4,5],[5,6],[6,7],[6,8],[7,8]]},"params":{"coordinates[N,D]":"real; from params['coordinates']; descriptive only","capacity[A]":"nonnegative real; from params['capacity_i_j']","cost[A]":"real; from params['cost_i_j']; descriptive only"},"variables":{"flow[A]":"nonnegative continuous"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,v] for (i,v) in A) = sum(flow[v,j] for (v,j) in A) for v in I"],"objective":"maximize sum(flow[0,j] for (0,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1),
        (0, 2),
        (0, 6),
        (0, 8),
        (1, 2),
        (1, 5),
        (2, 3),
        (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7),
        (6, 8),
        (7, 8),
    )

    coordinates = params["coordinates"]
    capacities = {
        (src, dst): params[f"capacity_{src}_{dst}"]
        for src, dst in arcs
    }
    costs = {
        (src, dst): params[f"cost_{src}_{dst}"]
        for src, dst in arcs
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(9), ordered=True)
    model.intermediate_nodes = pyo.Set(initialize=range(1, 8), ordered=True)
    model.coordinate_axes = pyo.Set(initialize=(0, 1), ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.coordinates = pyo.Param(
        model.nodes,
        model.coordinate_axes,
        initialize={
            (node, axis): coordinates[node][axis]
            for node in range(9)
            for axis in (0, 1)
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.arcs,
        initialize=costs,
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, src, dst):
        return network.flow[src, dst] <= network.capacity[src, dst]

    model.capacity_constraints = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, node):
        inflow = sum(
            network.flow[src, dst]
            for src, dst in network.arcs
            if dst == node
        )
        outflow = sum(
            network.flow[src, dst]
            for src, dst in network.arcs
            if src == node
        )
        return inflow == outflow

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.total_settlement = pyo.Objective(
        expr=sum(
            model.flow[src, dst]
            for src, dst in model.arcs
            if src == 0
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_settlement))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}