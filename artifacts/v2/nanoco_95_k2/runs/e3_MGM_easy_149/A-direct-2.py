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

    model = pyo.ConcreteModel()
    model.edges = pyo.Set(initialize=edges, dimen=2)
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def objective_rule(m):
        return sum(m.x[e] for e in m.edges)
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    nodes = range(8)
    model.node_constraints = pyo.Constraint(
        nodes,
        rule=lambda m, n: sum(
            m.x[e] for e in m.edges if n in e
        ) <= 1
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}