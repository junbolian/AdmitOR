import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    link_weights = params["link_weights"]
    port_limits = params["port_limits"]

    edges = [
        (0, 1), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 7),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 7),
        (6, 7),
    ]
    nodes = list(range(8))

    model = pyo.ConcreteModel()

    model.E = pyo.Set(initialize=range(len(edges)))
    model.V = pyo.Set(initialize=nodes)

    model.w = pyo.Param(model.E, initialize={e: link_weights[e] for e in range(len(edges))})
    model.b = pyo.Param(model.V, initialize={v: port_limits[v] for v in nodes})

    model.x = pyo.Var(model.E, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.w[e] * model.x[e] for e in model.E),
        sense=pyo.maximize,
    )

    model.port = pyo.ConstraintList()
    for v in model.V:
        incident = [e for e in model.E if edges[e][0] == v or edges[e][1] == v]
        model.port.add(sum(model.x[e] for e in incident) <= model.b[v])

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}