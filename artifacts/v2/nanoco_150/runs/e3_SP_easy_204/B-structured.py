# IR: {"sets":{"nodes":[0,1,2,3,4,5,6,7,8,9],"arcs":[[0,1],[1,2],[1,4],[1,5],[1,6],[1,7],[2,3],[3,4],[4,5],[4,8],[4,9],[5,6],[5,7],[6,7],[7,8],[7,9],[8,9]]},"params":{"arc_cost":"arc_cost_i_j for each listed arc (i,j), read from params","arc_capacity":"params['arc_capacity']","source_supply":"params['source_supply']","sink_supply":"params['sink_supply']"},"variables":{"x[i,j]":"Binary for each arc"},"constraints":["x[i,j] <= arc_capacity for each arc","sum(x[v,j]) - sum(x[i,v]) = source_supply if v=0, sink_supply if v=9, otherwise 0"],"objective":"minimize sum(arc_cost[i,j] * x[i,j] for each arc)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(10))
    arcs = (
        (0, 1),
        (1, 2),
        (1, 4),
        (1, 5),
        (1, 6),
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
        (7, 9),
        (8, 9),
    )

    arc_costs = {
        (0, 1): params["arc_cost_0_1"],
        (1, 2): params["arc_cost_1_2"],
        (1, 4): params["arc_cost_1_4"],
        (1, 5): params["arc_cost_1_5"],
        (1, 6): params["arc_cost_1_6"],
        (1, 7): params["arc_cost_1_7"],
        (2, 3): params["arc_cost_2_3"],
        (3, 4): params["arc_cost_3_4"],
        (4, 5): params["arc_cost_4_5"],
        (4, 8): params["arc_cost_4_8"],
        (4, 9): params["arc_cost_4_9"],
        (5, 6): params["arc_cost_5_6"],
        (5, 7): params["arc_cost_5_7"],
        (6, 7): params["arc_cost_6_7"],
        (7, 8): params["arc_cost_7_8"],
        (7, 9): params["arc_cost_7_9"],
        (8, 9): params["arc_cost_8_9"],
    }

    supplies = {node: 0 for node in nodes}
    supplies[0] = params["source_supply"]
    supplies[9] = params["sink_supply"]

    outgoing = {
        node: tuple((tail, head) for tail, head in arcs if tail == node)
        for node in nodes
    }
    incoming = {
        node: tuple((tail, head) for tail, head in arcs if head == node)
        for node in nodes
    }

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.arc_cost = pyo.Param(
        model.arcs, initialize=arc_costs, within=pyo.Reals
    )
    model.arc_capacity = pyo.Param(
        initialize=params["arc_capacity"], within=pyo.Reals
    )
    model.net_supply = pyo.Param(
        model.nodes, initialize=supplies, within=pyo.Reals
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(instance, tail, head):
        return instance.x[tail, head] <= instance.arc_capacity

    model.capacity_limit = pyo.Constraint(model.arcs, rule=capacity_rule)

    def balance_rule(instance, node):
        return (
            sum(instance.x[tail, head] for tail, head in outgoing[node])
            - sum(instance.x[tail, head] for tail, head in incoming[node])
            == instance.net_supply[node]
        )

    model.flow_balance = pyo.Constraint(model.nodes, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[tail, head] * model.x[tail, head]
            for tail, head in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}