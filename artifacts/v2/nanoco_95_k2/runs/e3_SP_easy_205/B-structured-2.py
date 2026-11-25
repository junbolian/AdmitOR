# IR: {"sets":{"N":"0..8","A":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[3,7],[4,5],[5,6],[5,7],[6,7],[6,8],[7,8]]},"params":{"arc_costs":"cost per arc in A order","arc_capacities":"capacity per arc in A order","node_supply":"net supply per node in N order"},"variables":{"x[a]":"Binary for a in A"},"constraints":["x[a] <= arc_capacities[a] for each a in A","sum(x[i,j] for outgoing arcs at i) - sum(x[j,i] for incoming arcs at i) == node_supply[i] for each i in N"],"objective":"minimize sum(arc_costs[a] * x[a] for a in A)"}

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
        (3, 7),
        (4, 5),
        (5, 6),
        (5, 7),
        (6, 7),
        (6, 8),
        (7, 8),
    )

    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supply = params["node_supply"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=range(9), ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={arc: arc_costs[idx] for idx, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.arc_capacity = pyo.Param(
        model.arcs,
        initialize={arc: arc_capacities[idx] for idx, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.supply = pyo.Param(
        model.nodes,
        initialize={node: node_supply[node] for node in range(9)},
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def capacity_rule(current_model, tail, head):
        return (
            current_model.x[tail, head]
            <= current_model.arc_capacity[tail, head]
        )

    model.capacity_limits = pyo.Constraint(
        model.arcs, rule=capacity_rule
    )

    def flow_rule(current_model, node):
        outgoing = sum(
            current_model.x[tail, head]
            for tail, head in arcs
            if tail == node
        )
        incoming = sum(
            current_model.x[tail, head]
            for tail, head in arcs
            if head == node
        )
        return outgoing - incoming == current_model.supply[node]

    model.flow_balance = pyo.Constraint(
        model.nodes, rule=flow_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[tail, head] * model.x[tail, head]
            for tail, head in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}