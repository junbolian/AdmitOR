# IR: {"sets":{"V":[0,1,2,3,4,5,6],"A":[[0,1],[0,2],[0,3],[0,4],[0,5],[0,6],[1,0],[1,2],[1,3],[1,5],[1,6],[2,0],[2,1],[2,3],[2,4],[2,5],[2,6],[3,0],[3,2],[3,4],[3,5],[3,6],[4,0],[4,1],[4,2],[4,3],[4,5],[4,6],[5,0],[5,1],[5,2],[5,3],[5,4],[5,6],[6,0],[6,1],[6,2],[6,3],[6,4],[6,5]]},"params":{"capacity[i,j]":"params['capacity_'+str(i)+'_'+str(j)] for every (i,j) in A; nonnegative real"},"variables":{"flow[i,j]":"nonnegative real for every (i,j) in A","throughput":"nonnegative real"},"constraints":["flow[i,j] <= capacity[i,j] for every (i,j) in A","sum(flow[v,j] for outgoing arcs)-sum(flow[i,v] for incoming arcs) = throughput if v=0, -throughput if v=6, otherwise 0; for every v in V"],"objective":"maximize throughput"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 5), (1, 6),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5), (2, 6),
        (3, 0), (3, 2), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    )

    capacities = {
        (tail, head): params[f"capacity_{tail}_{head}"]
        for tail, head in arcs
    }
    outgoing = {
        node: tuple(head for tail, head in arcs if tail == node)
        for node in range(7)
    }
    incoming = {
        node: tuple(tail for tail, head in arcs if head == node)
        for node in range(7)
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 6)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.capacity = pyo.Param(
        model.arcs,
        initialize=capacities,
        within=pyo.NonNegativeReals,
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(grid, tail, head):
        return grid.flow[tail, head] <= grid.capacity[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(grid, node):
        net_outflow = (
            sum(grid.flow[node, head] for head in outgoing[node])
            - sum(grid.flow[tail, node] for tail in incoming[node])
        )
        if node == 0:
            return net_outflow == grid.throughput
        if node == 6:
            return net_outflow == -grid.throughput
        return net_outflow == 0

    model.flow_balances = pyo.Constraint(
        model.nodes, rule=balance_rule
    )
    model.total_power = pyo.Objective(
        expr=model.throughput, sense=pyo.maximize
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_power))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}