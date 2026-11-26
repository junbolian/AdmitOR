# IR: {"sets":{"N":[0,1,2,3,4,5],"A":[[0,1],[0,2],[0,3],[0,4],[0,5],[1,0],[1,2],[1,3],[1,5],[2,0],[2,1],[2,3],[2,4],[3,0],[3,1],[3,2],[3,4],[4,0],[4,2],[4,3],[4,5],[5,0],[5,1],[5,2],[5,3],[5,4]],"I":[1,2,3,4]},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for (i,j) in A; nonnegative; thousand packets/time"},"variables":{"flow[i,j]":"continuous nonnegative for (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for (i,j) in A","sum(flow[i,j] for outgoing arcs of k) == sum(flow[i,j] for incoming arcs of k) for k in I"],"objective":"maximize sum(flow[0,j] for outgoing arcs of 0) - sum(flow[i,0] for incoming arcs of 0)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4),
        (3, 0), (3, 1), (3, 2), (3, 4),
        (4, 0), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    ]

    capacities = {
        (i, j): params[f"capacity_{i}_{j}"]
        for i, j in arcs
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(6), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.intermediate_nodes = pyo.Set(
        initialize=[1, 2, 3, 4], ordered=True
    )
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, i, j):
        return network.flow[i, j] <= network.capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, node):
        outgoing = pyo.quicksum(
            network.flow[i, j] for i, j in arcs if i == node
        )
        incoming = pyo.quicksum(
            network.flow[i, j] for i, j in arcs if j == node
        )
        return outgoing == incoming

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes,
        rule=conservation_rule,
    )

    model.total_flow = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.flow[i, j] for i, j in arcs if i == 0
            )
            - pyo.quicksum(
                model.flow[i, j] for i, j in arcs if j == 0
            )
        ),
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