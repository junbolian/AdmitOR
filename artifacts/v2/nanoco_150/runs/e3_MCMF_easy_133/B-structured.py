# IR: {"sets":{"nodes":[0,1,2,3,4,5,6,7],"arcs":[[0,1],[0,2],[0,3],[0,7],[1,2],[1,5],[2,3],[2,5],[2,6],[3,4],[3,5],[4,5],[4,6],[4,7],[5,6],[5,7]]},"params":{"arc_capacity":"17 nonnegative capacities in listed arc order","arc_cost":"17 real unit costs in listed arc order"},"variables":{"flow[a]":"continuous, 0 <= flow[a] <= arc_capacity[a]","throughput":"continuous, nonnegative"},"constraints":["For every node v: outgoing flow minus incoming flow equals throughput at node 0, negative throughput at node 7, and zero otherwise.","Stage 2: throughput equals the optimal Stage 1 objective value."],"objective":{"stage_1":"maximize throughput","stage_2":"minimize sum(arc_cost[a] * flow[a]) with maximum throughput fixed","returned":"Stage 2 minimum total cost"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1),
        (0, 2),
        (0, 3),
        (0, 7),
        (1, 2),
        (1, 5),
        (2, 3),
        (2, 5),
        (2, 6),
        (3, 4),
        (3, 5),
        (4, 5),
        (4, 6),
        (4, 7),
        (5, 6),
        (5, 7),
        (6, 7),
    ]

    capacities = list(params["arc_capacity"])
    costs = list(params["arc_cost"])

    if len(capacities) != len(arcs) or len(costs) != len(arcs):
        return {"objective": None, "status": "invalid_parameter_length"}

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, 7)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.pipeline_capacity = pyo.Param(
        model.arcs,
        initialize=dict(zip(arcs, capacities)),
        within=pyo.NonNegativeReals,
    )
    model.pumping_cost = pyo.Param(
        model.arcs,
        initialize=dict(zip(arcs, costs)),
        within=pyo.Reals,
    )

    def flow_bounds(block, tail, head):
        return (0, block.pipeline_capacity[tail, head])

    model.flow = pyo.Var(
        model.arcs,
        domain=pyo.NonNegativeReals,
        bounds=flow_bounds,
    )
    model.throughput = pyo.Var(domain=pyo.NonNegativeReals)

    def flow_balance_rule(block, node):
        outgoing = sum(
            block.flow[tail, head]
            for tail, head in arcs
            if tail == node
        )
        incoming = sum(
            block.flow[tail, head]
            for tail, head in arcs
            if head == node
        )

        if node == 0:
            return outgoing - incoming == block.throughput
        if node == 7:
            return outgoing - incoming == -block.throughput
        return outgoing - incoming == 0

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_balance_rule
    )

    model.throughput_objective = pyo.Objective(
        expr=model.throughput,
        sense=pyo.maximize,
    )
    model.cost_objective = pyo.Objective(
        expr=sum(
            model.pumping_cost[tail, head] * model.flow[tail, head]
            for tail, head in arcs
        ),
        sense=pyo.minimize,
    )
    model.cost_objective.deactivate()

    # Stage 1: maximize throughput.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage_1_solve_failed"}

    try:
        obj_val = float(pyo.value(model.throughput_objective))
    except ValueError:
        return {"objective": None, "status": "stage_1_objective_unavailable"}

    model.maximum_throughput = pyo.Constraint(
        expr=model.throughput == obj_val
    )
    model.throughput_objective.deactivate()
    model.cost_objective.activate()

    # Clear previous values so Stage 2 cannot return a stale objective.
    for tail, head in arcs:
        model.flow[tail, head].set_value(None)
    model.throughput.set_value(None)

    # Stage 2: minimize cost subject to maximum throughput.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "stage_2_solve_failed"}

    try:
        obj_val = float(pyo.value(model.cost_objective))
    except ValueError:
        return {"objective": None, "status": "stage_2_objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}