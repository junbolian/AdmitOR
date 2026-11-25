import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_weights = list(params["edge_weights"])
    station_capacities = list(params["station_capacities"])

    edges = [
        (0, 6), (0, 8), (1, 3), (1, 6), (1, 7), (1, 9),
        (2, 6), (2, 8), (2, 9), (3, 7), (4, 5), (4, 7),
        (4, 8), (4, 9), (5, 6), (5, 9), (6, 8),
    ]
    stations = list(range(10))

    model = pyo.ConcreteModel()

    model.EDGES = pyo.Set(initialize=range(len(edges)), ordered=True)
    model.STATIONS = pyo.Set(initialize=stations, ordered=True)

    model.w = pyo.Param(model.EDGES, initialize={i: edge_weights[i] for i in range(len(edges))})
    model.cap = pyo.Param(model.STATIONS, initialize={s: station_capacities[s] for s in stations})

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.w[i] * model.x[i] for i in model.EDGES), sense=pyo.maximize)

    model.capacity = pyo.ConstraintList()
    for s in stations:
        incident = [i for i, (u, v) in enumerate(edges) if u == s or v == s]
        if incident:
            model.capacity.add(sum(model.x[i] for i in incident) <= model.cap[s])
        else:
            model.capacity.add(0 <= model.cap[s])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}