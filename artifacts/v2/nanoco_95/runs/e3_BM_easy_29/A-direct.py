import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_weights = params["edge_weights"]
    station_capacities = params["station_capacities"]

    edges = [
        (0, 6), (0, 8), (1, 3), (1, 6), (1, 7), (1, 9),
        (2, 6), (2, 8), (2, 9), (3, 7), (4, 5), (4, 7),
        (4, 8), (4, 9), (5, 6), (5, 9), (6, 8),
    ]
    stations = list(range(10))

    model = pyo.ConcreteModel()
    model.EDGES = pyo.Set(initialize=list(range(len(edges))))
    model.STATIONS = pyo.Set(initialize=stations)

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(edge_weights[e] * model.x[e] for e in model.EDGES),
        sense=pyo.maximize,
    )

    def capacity_rule(m, s):
        return sum(
            m.x[e] for e in m.EDGES if edges[e][0] == s or edges[e][1] == s
        ) <= station_capacities[s]

    model.capacity = pyo.Constraint(model.STATIONS, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}