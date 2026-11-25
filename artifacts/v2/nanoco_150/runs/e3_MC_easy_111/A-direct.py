import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(10))
    links = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6),
        (3, 4), (3, 8), (3, 9), (4, 5), (4, 8),
        (5, 6), (6, 7), (7, 8), (7, 9), (8, 9),
    ]

    capacity = {}
    for (u, v) in links:
        capacity[(u, v)] = params["capacity_{}_{}".format(u, v)]

    source = 0
    sink = 9

    model = pyo.ConcreteModel()

    model.y = pyo.Var(nodes, domain=pyo.Binary)

    # Forward indicator: 1 if link (u,v) is severed (u on source side, v on sink side)
    model.sev = pyo.Var(links, domain=pyo.Binary)

    model.source_side = pyo.Constraint(expr=model.y[source] == 1)
    model.sink_side = pyo.Constraint(expr=model.y[sink] == 0)

    def sev_ub_rule(m, u, v):
        return m.sev[(u, v)] >= m.y[u] - m.y[v]

    model.sev_ub = pyo.Constraint(links, rule=sev_ub_rule)

    def cut_cost_rule(m):
        return sum(capacity[(u, v)] * m.sev[(u, v)] for (u, v) in links)

    model.cut_cost = pyo.Objective(rule=cut_cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.cut_cost))
    return {"objective": obj_val, "status": "optimal"}