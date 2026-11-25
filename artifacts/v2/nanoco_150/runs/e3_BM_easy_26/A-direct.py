import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    edges = [
        (0, 3), (0, 4), (1, 8), (2, 3), (2, 6), (2, 7),
        (3, 6), (3, 7), (3, 8), (3, 9), (4, 5), (4, 6),
        (4, 7), (4, 8), (4, 9), (5, 7), (6, 7),
    ]
    nodes = list(range(10))

    rev = {i: params["revenue_%d_%d" % (u, v)] for i, (u, v) in enumerate(edges)}
    cap = {n: params["capacity_%d" % n] for n in nodes}
    incident = {n: [] for n in nodes}
    for i, (u, v) in enumerate(edges):
        incident[u].append(i)
        incident[v].append(i)

    model = pyo.ConcreteModel()
    model.E = pyo.Set(initialize=list(range(len(edges))))
    model.x = pyo.Var(model.E, domain=pyo.Binary)

    model.obj_expr = pyo.Expression(expr=sum(rev[i] * model.x[i] for i in model.E))
    model.obj = pyo.Objective(expr=model.obj_expr, sense=pyo.maximize)

    model.port = pyo.Constraint(
        nodes,
        rule=lambda m, n: sum(m.x[i] for i in incident[n]) <= cap[n],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}