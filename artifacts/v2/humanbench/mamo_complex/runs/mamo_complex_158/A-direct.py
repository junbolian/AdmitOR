import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cap_flat = params["capacity"]

    n = 9
    capacity = [[cap_flat[i * n + j] for j in range(n)] for i in range(n)]

    arcs = [(i, j) for i in range(n) for j in range(n) if i != j and capacity[i][j] > 0]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    def flow_bounds(mdl, i, j):
        return (0, capacity[i][j])

    model.flow = pyo.Var(model.arcs, bounds=flow_bounds)

    model.obj = pyo.Objective(
        expr=sum(model.flow[0, j] for j in range(n) if (0, j) in arcs),
        sense=pyo.maximize,
    )

    def flow_balance(mdl, k):
        outflow = sum(mdl.flow[k, j] for (a, j) in arcs if a == k)
        inflow = sum(mdl.flow[i, k] for (i, b) in arcs if b == k)
        if k == 0:
            return outflow - inflow >= 0
        elif k == 8:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(range(n), rule=flow_balance)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}