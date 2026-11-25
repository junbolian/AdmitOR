import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_weights = params["edge_weights"]
    capacities = params["station_capacities"]

    edges = [
        (0, 6), (0, 8), (1, 3), (1, 6), (1, 7), (1, 9),
        (2, 6), (2, 8), (2, 9), (3, 7), (4, 5), (4, 7),
        (4, 8), (4, 9), (5, 6), (5, 9), (6, 8),
    ]
    num_edges = len(edges)

    model = pyo.ConcreteModel()

    model.EDGES = pyo.RangeSet(0, num_edges - 1)
    model.STATIONS = pyo.RangeSet(0, 9)

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    def obj_rule(m):
        return sum(edge_weights[i] * m.x[i] for i in m.EDGES)

    model.total_score = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def cap_rule(m, s):
        return sum(
            m.x[i] for i in m.EDGES
            if edges[i][0] == s or edges[i][1] == s
        ) <= capacities[s]

    model.capacity_constraint = pyo.Constraint(model.STATIONS, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_score))
    return {"objective": obj_val, "status": "optimal"}