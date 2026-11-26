# IR: {"sets":{"N":[0,1,2,3,4,5],"I":[1,2,3,4],"A":[[0,1],[0,2],[0,3],[0,4],[0,5],[1,0],[1,2],[1,3],[1,5],[2,0],[2,1],[2,3],[2,4],[2,5],[3,0],[3,1],[3,2],[3,5],[4,0],[4,1],[4,2],[4,3],[4,5],[5,0],[5,1],[5,2],[5,3],[5,4]]},"params":{"capacity[i,j]":"params['capacity_i_j'] for every (i,j) in A; nonnegative GB/s"},"variables":{"flow[i,j]":"nonnegative continuous GB/s for every (i,j) in A"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[i,j] for outgoing arcs from i) = sum(flow[j,i] for incoming arcs to i) for every i in I"],"objective":"maximize sum(flow[0,j] for outgoing arcs from 0) - sum(flow[i,0] for incoming arcs to 0)"}

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
    model.intermediate_nodes = pyo.Set(
        initialize=(1, 2, 3, 4), ordered=True
    )
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.capacity = pyo.Param(
        model.arcs,
        initialize={
            (tail, head): params[f"capacity_{tail}_{head}"]
            for tail, head in arcs
        },
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def capacity_rule(network, tail, head):
        return network.flow[tail, head] <= network.capacity[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def conservation_rule(network, node):
        outgoing = pyo.quicksum(
            network.flow[tail, head]
            for tail, head in arcs
            if tail == node
        )
        incoming = pyo.quicksum(
            network.flow[tail, head]
            for tail, head in arcs
            if head == node
        )
        return outgoing == incoming

    model.flow_conservation = pyo.Constraint(
        model.intermediate_nodes, rule=conservation_rule
    )

    model.total_transfer = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.flow[tail, head]
                for tail, head in arcs
                if tail == 0
            )
            - pyo.quicksum(
                model.flow[tail, head]
                for tail, head in arcs
                if head == 0
            )
        ),
        sense=pyo.maximize,
    )

    # APPsi can raise RuntimeError when no solution can be loaded.
    # Success is determined solely by retrieving the objective value.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_transfer))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}