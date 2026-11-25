import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    node_supply = params["node_supply"]

    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4), (3, 7),
        (4, 5),
        (5, 6), (5, 7),
        (6, 7), (6, 8),
        (7, 8),
    ]
    nodes = list(range(9))

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.nodes = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        idx = arcs.index((i, j))
        return mdl.flow[i, j] <= arc_capacities[idx]

    model.cap_con = pyo.Constraint(model.arcs, rule=cap_rule)

    def flow_balance_rule(mdl, n):
        out_flow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        in_flow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        return out_flow - in_flow == node_supply[n]

    model.flow_balance = pyo.Constraint(model.nodes, rule=flow_balance_rule)

    def obj_rule(mdl):
        return sum(arc_costs[arcs.index((i, j))] * mdl.flow[i, j]
                   for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}