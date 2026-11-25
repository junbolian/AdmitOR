# IR: {"sets":{"N":[0,1,2,3,4,5,6,7,8],"A":[[0,1],[0,2],[0,6],[0,8],[1,2],[1,5],[2,3],[2,6],[3,4],[3,7],[4,5],[5,6],[5,7],[6,7],[6,8],[7,8]]},"params":{"arc_costs":"real[A], supplied in fixed arc order","arc_capacities":"nonnegative real[A], supplied in fixed arc order","node_supply":"real[N], supplied in node order"},"variables":{"x[i,j]":"binary, for (i,j) in A"},"constraints":["x[i,j] <= arc_capacities[i,j] for each (i,j) in A","sum(x[i,j] for outgoing arcs) - sum(x[j,i] for incoming arcs) == node_supply[i] for each i in N"],"objective":"minimize sum(arc_costs[i,j] * x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(9))
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

    costs = params["arc_costs"]
    capacities = params["arc_capacities"]
    supplies = params["node_supply"]

    if len(costs) != len(arcs):
        raise ValueError("arc_costs must contain exactly 16 entries.")
    if len(capacities) != len(arcs):
        raise ValueError("arc_capacities must contain exactly 16 entries.")
    if len(supplies) != len(nodes):
        raise ValueError("node_supply must contain exactly 9 entries.")

    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes, ordered=True)
    model.A = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.arc_costs = pyo.Param(
        model.A,
        initialize={arc: costs[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.arc_capacities = pyo.Param(
        model.A,
        initialize={arc: capacities[k] for k, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
    )
    model.node_supply = pyo.Param(
        model.N,
        initialize={node: supplies[node] for node in nodes},
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def capacity_rule(instance, tail, head):
        return instance.x[tail, head] <= instance.arc_capacities[tail, head]

    model.capacity_limits = pyo.Constraint(model.A, rule=capacity_rule)

    def balance_rule(instance, node):
        outgoing = sum(
            instance.x[tail, head] for tail, head in arcs if tail == node
        )
        incoming = sum(
            instance.x[tail, head] for tail, head in arcs if head == node
        )
        return outgoing - incoming == instance.node_supply[node]

    model.flow_balance = pyo.Constraint(model.N, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_costs[tail, head] * model.x[tail, head]
            for tail, head in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}