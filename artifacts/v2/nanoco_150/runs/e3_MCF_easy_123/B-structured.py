# IR: {"sets":{"nodes":[0,1,2,3,4,5],"arcs":[[0,2],[0,3],[1,2],[1,3],[2,4],[2,5],[3,4],[3,5],[0,4],[0,5],[1,4],[1,5]]},"params":{"supplies":"net supply indexed by node","capacities":"capacity indexed by arc position","costs":"unit cost indexed by arc position"},"variables":{"flow[i,j]":"nonnegative continuous for each arc"},"constraints":["For each node n: sum(flow[n,j]) - sum(flow[i,n]) = supplies[n].","For each arc (i,j) at position k: flow[i,j] <= capacities[k]."],"objective":"Minimize sum(costs[k] * flow[i,j]) over arcs (i,j) at position k."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = tuple(range(6))
    arcs = (
        (0, 2),
        (0, 3),
        (1, 2),
        (1, 3),
        (2, 4),
        (2, 5),
        (3, 4),
        (3, 5),
        (0, 4),
        (0, 5),
        (1, 4),
        (1, 5),
    )

    supplies = params["supplies"]
    capacities = params["capacities"]
    costs = params["costs"]

    model = pyo.ConcreteModel()
    model.node_set = pyo.Set(initialize=nodes, ordered=True)
    model.arc_set = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.net_supply = pyo.Param(
        model.node_set,
        initialize={node: supplies[node] for node in nodes},
        within=pyo.Reals,
    )
    model.arc_capacity = pyo.Param(
        model.arc_set,
        initialize={arc: capacities[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.unit_cost = pyo.Param(
        model.arc_set,
        initialize={arc: costs[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    def balance_rule(mdl, node):
        outgoing = sum(
            mdl.flow[source, target]
            for source, target in arcs
            if source == node
        )
        incoming = sum(
            mdl.flow[source, target]
            for source, target in arcs
            if target == node
        )
        return outgoing - incoming == mdl.net_supply[node]

    model.flow_balance = pyo.Constraint(
        model.node_set,
        rule=balance_rule,
    )

    def capacity_rule(mdl, source, target):
        return mdl.flow[source, target] <= mdl.arc_capacity[source, target]

    model.capacity_limit = pyo.Constraint(
        model.arc_set,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[source, target] * model.flow[source, target]
            for source, target in arcs
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