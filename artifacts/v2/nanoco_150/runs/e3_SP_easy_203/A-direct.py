import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    source_supply = params["source_supply"]
    sink_supply = params["sink_supply"]

    # Directed arcs (ordered exactly as listed in the problem)
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 6), (0, 7),
        (1, 2), (1, 5), (1, 7),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]
    nodes = list(range(8))
    supplies = {0: source_supply, 7: sink_supply}
    for n in nodes:
        if n not in supplies:
            supplies[n] = 0

    model = pyo.ConcreteModel()

    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.node_set = pyo.Set(initialize=nodes)

    model.cost = pyo.Param(model.arc_set, initialize=dict(zip(arcs, arc_costs)))
    model.cap = pyo.Param(model.arc_set, initialize=dict(zip(arcs, arc_capacities)))
    model.supply = pyo.Param(model.node_set, initialize=supplies)

    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals)

    # Capacity constraints
    model.capacity_rule = pyo.Constraint(
        model.arc_set,
        rule=lambda m, i, j: m.flow[i, j] <= m.cap[i, j],
    )

    # Flow conservation at every node
    model.flow_balance = pyo.Constraint(
        model.node_set,
        rule=lambda m, n: (
            sum(m.flow[i, j] for (i, j) in m.arc_set if j == n)
            - sum(m.flow[i, j] for (i, j) in m.arc_set if i == n)
            == -m.supply[n]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i, j] * model.flow[i, j] for (i, j) in model.arc_set),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}