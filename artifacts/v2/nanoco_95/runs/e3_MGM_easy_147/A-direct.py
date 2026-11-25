import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 6), (0, 7),
        (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 3),
        (3, 5), (3, 6), (3, 7),
        (4, 5),
        (5, 6),
        (6, 7),
    ]
    nodes = list(range(8))

    model = pyo.ConcreteModel()

    model.EDGES = pyo.Set(initialize=edges, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    def degree_rule(model, i):
        incident = [e for e in edges if i in e]
        return sum(model.x[e] for e in incident) <= 1
    model.degree_con = pyo.Constraint(model.NODES, rule=degree_rule)

    model.obj = pyo.Objective(expr=sum(model.x[e] for e in model.EDGES), sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}