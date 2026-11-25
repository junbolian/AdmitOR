import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (0, 1), (0, 4), (0, 5),
        (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (2, 5),
        (3, 4), (3, 7),
        (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]

    nodes = sorted({n for e in edges for n in e})

    model = pyo.ConcreteModel()
    model.E = pyo.Set(initialize=edges, dimen=2)
    model.V = pyo.Set(initialize=nodes)
    model.x = pyo.Var(model.E, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.x[e] for e in model.E), sense=pyo.maximize
    )

    model.incident = pyo.Constraint(
        model.V,
        rule=lambda m, v: sum(
            m.x[e] for e in edges if v in e
        ) <= 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}