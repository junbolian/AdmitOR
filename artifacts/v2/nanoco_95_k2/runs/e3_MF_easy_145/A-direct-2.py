import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    ]
    source, sink = 0, 8

    model = pyo.ConcreteModel()
    model.EDGES = pyo.Set(initialize=edges, dimen=2)

    model.flow = pyo.Var(
        model.EDGES,
        bounds=lambda m, i, j: (0, params["capacity_%d_%d" % (i, j)]),
    )

    def _obj(m):
        return sum(
            params["cost_%d_%d" % (i, j)] * m.flow[(i, j)] for (i, j) in edges
        )

    model.obj = pyo.Objective(rule=_obj, sense=pyo.minimize)

    def _balance(m, n):
        inflow = sum(m.flow[(i, j)] for (i, j) in edges if j == n)
        outflow = sum(m.flow[(i, j)] for (i, j) in edges if i == n)
        if n == sink:
            return inflow - outflow >= 0
        return outflow - inflow == 0

    model.balance = pyo.Constraint(range(9), rule=_balance)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}