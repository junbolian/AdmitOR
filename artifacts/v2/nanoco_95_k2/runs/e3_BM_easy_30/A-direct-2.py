import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edge_weights = params["edge_weights"]
    cell_capacities = params["cell_capacities"]

    # Structural constants: cells 0-8, 16 candidate links in the stated order
    cells = list(range(9))
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 7),
        (1, 5), (1, 7), (2, 3), (2, 6), (2, 7),
        (2, 8), (3, 7), (4, 5), (4, 6), (5, 7),
        (5, 8),
    ]

    model = pyo.ConcreteModel()

    model.EDGES = pyo.Set(initialize=range(len(edges)), ordered=True)
    model.CELLS = pyo.Set(initialize=cells, ordered=True)

    model.w = pyo.Param(model.EDGES, initialize={i: edge_weights[i] for i in model.EDGES})
    model.cap = pyo.Param(model.CELLS, initialize={c: cell_capacities[c] for c in model.CELLS})

    model.x = pyo.Var(model.EDGES, domain=pyo.Binary)

    # Incident edges per cell (structural)
    incident = {c: [] for c in cells}
    for i, (u, v) in enumerate(edges):
        incident[u].append(i)
        incident[v].append(i)

    def capacity_rule(model, c):
        return sum(model.x[i] for i in incident[c]) <= model.cap[c]

    model.capacity_con = pyo.Constraint(model.CELLS, rule=capacity_rule)

    def obj_rule(model):
        return sum(model.w[i] * model.x[i] for i in model.EDGES)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}