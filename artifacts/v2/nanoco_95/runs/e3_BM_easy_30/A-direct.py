import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

EDGES = [
    (0, 1), (0, 2), (0, 3), (0, 5), (0, 7),
    (1, 5), (1, 7),
    (2, 3), (2, 6), (2, 7), (2, 8),
    (3, 7),
    (4, 5), (4, 6),
    (5, 7), (5, 8),
]


def solve(params):
    weights = params["link_weights"]
    caps = params["cell_capacities"]

    model = pyo.ConcreteModel()
    model.E = pyo.RangeSet(0, len(EDGES) - 1)

    edge_list = list(EDGES)

    def cell_of(i, pos):
        return edge_list[i][pos]

    # x[i] = 1 if edge i selected
    model.x = pyo.Var(model.E, domain=pyo.Binary)

    def obj_rule(m):
        return sum(weights[i] * m.x[i] for i in m.E)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Capacity constraints per cell
    for c in range(len(caps)):
        incident = [i for i, (u, v) in enumerate(edge_list) if u == c or v == c]
        if not incident:
            continue
        con = pyo.Constraint(
            expr=sum(model.x[i] for i in incident) <= caps[c]
        )
        setattr(model, f"cap_{c}", con)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}