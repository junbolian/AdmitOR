import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supplies = params["node_supplies"]

    nodes = list(range(10))
    arcs = [
        (0, 1), (0, 7), (1, 2), (1, 7), (2, 3), (2, 6),
        (3, 4), (3, 5), (3, 8), (3, 9), (4, 5), (4, 8),
        (5, 6), (6, 7), (7, 8), (7, 9), (8, 9),
    ]

    cost = {arc: arc_costs[i] for i, arc in enumerate(arcs)}
    cap = {arc: arc_capacities[i] for i, arc in enumerate(arcs)}
    supply = {node: node_supplies[i] for i, node in enumerate(nodes)}

    model = pyo.ConcreteModel()

    model.arc_set = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.arc_set, domain=pyo.NonNegativeReals,
                         bounds=lambda m, i, j: (0, cap[(i, j)]))

    def obj_rule(m):
        return sum(cost[(i, j)] * m.flow[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def flow_balance_rule(m, k):
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == k)
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == k)
        return outflow - inflow == supply[k]

    model.flow_balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}