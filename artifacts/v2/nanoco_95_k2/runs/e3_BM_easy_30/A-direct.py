import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_weights = params["edge_weights"]
    cell_capacities = params["cell_capacities"]

    edge_list = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 7),
        (1, 5), (1, 7), (2, 3), (2, 6), (2, 7),
        (2, 8), (3, 7), (4, 5), (4, 6), (5, 7), (5, 8),
    ]
    edges = list(range(len(edge_list)))
    cells = list(range(9))

    model = pyo.ConcreteModel()

    model.EDGES = pyo.Set(initialize=edges)
    model.CELLS = pyo.Set(initialize=cells)

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    def weight_rule(model, e):
        return edge_weights[e]

    model.weight = pyo.Param(model.EDGES, initialize=weight_rule)

    model.obj = pyo.Objective(
        expr=sum(model.weight[e] * model.x[e] for e in model.EDGES),
        sense=pyo.maximize,
    )

    def cap_rule(model, c):
        incident = [e for e in edges if edge_list[e][0] == c or edge_list[e][1] == c]
        return sum(model.x[e] for e in incident) <= cell_capacities[c]

    model.cap = pyo.Constraint(model.CELLS, rule=cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}