import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    coords = params["coords"]
    dist = params["distance_matrix"]

    n = len(coords)
    nodes = list(range(n))
    edges = [(i, j) for i in nodes for j in nodes if i != j]
    required = [(0, 2), (0, 6), (1, 3), (1, 6), (2, 4), (2, 7), (3, 5), (3, 7)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(edges, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(dist[i][j] * m.x[i, j] for (i, j) in edges)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def flow_rule(m, k):
        outflow = sum(m.x[k, j] for j in nodes if j != k)
        inflow = sum(m.x[i, k] for i in nodes if i != k)
        return outflow - inflow == 0

    model.flow = pyo.Constraint(nodes, rule=flow_rule)

    def required_rule(m, a, b):
        return m.x[a, b] + m.x[b, a] >= 1

    model.required = pyo.Constraint(required, rule=required_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}