import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_nodes = 8
    edges = [
        (0, 1), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 2), (1, 4), (1, 5), (1, 6),
        (2, 4), (2, 7),
        (3, 4),
        (4, 5), (4, 6), (4, 7),
        (5, 7),
        (6, 7),
    ]

    model = pyo.ConcreteModel()

    model.EDGES = pyo.Set(initialize=edges, dimen=2)
    model.NODES = pyo.Set(initialize=range(n_nodes))

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    model.incident = pyo.ConstraintList()
    for i in model.NODES:
        model.incident.add(
            sum(model.x[e] for e in edges if i in e) <= 1
        )

    model.obj = pyo.Objective(
        expr=sum(model.x[e] for e in model.EDGES), sense=pyo.maximize
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}