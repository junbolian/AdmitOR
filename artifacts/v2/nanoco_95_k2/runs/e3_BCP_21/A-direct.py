import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_weights = params["edge_weights"]
    edges = [
        (0, 1), (0, 2), (1, 3), (1, 4), (1, 5), (2, 7),
        (3, 4), (3, 5), (4, 5), (4, 6), (4, 7), (5, 6),
    ]
    num_nodes = 8
    nodes = list(range(num_nodes))
    num_edges = len(edges)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(nodes, domain=pyo.NonNegativeIntegers, bounds=(0, 32))
    model.span = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, 32))
    model.y = pyo.Var(range(num_edges), domain=pyo.Binary)

    model.obj = pyo.Objective(expr=model.span, sense=pyo.minimize)

    def span_rule(mdl, i):
        return mdl.x[i] <= mdl.span

    model.span_con = pyo.Constraint(nodes, rule=span_rule)

    M = 32.0

    def dir1_rule(mdl, k):
        u, v = edges[k]
        d = edge_weights[k]
        return mdl.x[u] - mdl.x[v] >= d * mdl.y[k] - M * (1 - mdl.y[k])

    def dir2_rule(mdl, k):
        u, v = edges[k]
        d = edge_weights[k]
        return mdl.x[v] - mdl.x[u] >= d * (1 - mdl.y[k]) - M * mdl.y[k]

    model.dir1_con = pyo.Constraint(range(num_edges), rule=dir1_rule)
    model.dir2_con = pyo.Constraint(range(num_edges), rule=dir2_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}