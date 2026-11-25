# IR: {"sets":{"nodes":[0,1,2,3,4,5,6,7,8,9],"arcs":[[0,1],[1,2],[1,4],[1,5],[1,7],[2,3],[3,4],[4,5],[4,8],[4,9],[5,6],[5,7],[6,7],[7,8],[8,9]]},"params":{"capacity[i,j]":"params['capacity_i_j'] for each arc","cost[i,j]":"params['cost_i_j'] for each arc"},"variables":{"flow[i,j]":"continuous nonnegative","throughput":"continuous nonnegative"},"constraints":["flow[i,j] <= capacity[i,j] for every arc","outflow[v] - inflow[v] = throughput if v=0, -throughput if v=9, and 0 otherwise","stage 2: throughput = optimal stage-1 throughput"],"objective":{"stage_1":"maximize throughput","stage_2":"minimize sum(cost[i,j] * flow[i,j] for every arc)","returned_objective":"stage-2 minimum total operational cost"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = (
        (0, 1),
        (1, 2),
        (1, 4),
        (1, 5),
        (1, 7),
        (2, 3),
        (3, 4),
        (4, 5),
        (4, 8),
        (4, 9),
        (5, 6),
        (5, 7),
        (6, 7),
        (7, 8),
        (8, 9),
    )

    capacities = {
        (tail, head): params[f"capacity_{tail}_{head}"]
        for tail, head in arcs
    }
    costs = {
        (tail, head): params[f"cost_{tail}_{head}"]
        for tail, head in arcs
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(10), ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.pipe_capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.unit_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, tail, head):
        return mdl.flow[tail, head] <= mdl.pipe_capacity[tail, head]

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def balance_rule(mdl, node):
        outgoing = sum(
            mdl.flow[tail, head]
            for tail, head in arcs
            if tail == node
        )
        incoming = sum(
            mdl.flow[tail, head]
            for tail, head in arcs
            if head == node
        )
        if node == 0:
            return outgoing - incoming == mdl.throughput
        if node == 9:
            return outgoing - incoming == -mdl.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=balance_rule
    )

    model.max_flow_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )

    # Stage 1: obtain the maximum feasible throughput.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage_1_solve_failed"}

    try:
        max_throughput = float(pyo.value(model.max_flow_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "stage_1_objective_unavailable"}

    # Stage 2: minimize operating cost at exactly that throughput.
    model.max_flow_objective.deactivate()
    model.maximum_throughput_requirement = pyo.Constraint(
        expr=model.throughput == max_throughput
    )
    model.min_cost_objective = pyo.Objective(
        expr=sum(
            model.unit_cost[tail, head] * model.flow[tail, head]
            for tail, head in arcs
        ),
        sense=pyo.minimize,
    )

    # Clear stage-1 values so an unavailable stage-2 solution cannot
    # accidentally be evaluated using stale values.
    for tail, head in arcs:
        model.flow[tail, head].set_value(None)
    model.throughput.set_value(None)

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage_2_solve_failed"}

    try:
        obj_val = float(pyo.value(model.min_cost_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "stage_2_objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}