import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    n = 8
    source = 0
    sink = 7

    edges = [(i, j) for i in range(n) for j in range(n) if i != j]
    cap = {(i, j): capacity[idx] for idx, (i, j) in enumerate(edges)}

    model = pyo.ConcreteModel()
    model.E = pyo.Set(initialize=edges, dimen=2)
    model.x = pyo.Var(model.E, within=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return m.x[i, j] <= cap[(i, j)]

    model.cap = pyo.Constraint(model.E, rule=cap_rule)

    def flow_balance_rule(m, k):
        inflow = sum(m.x[i, j] for (i, j) in edges if j == k)
        outflow = sum(m.x[i, j] for (i, j) in edges if i == k)
        if k == source:
            return outflow - inflow == 0
        elif k == sink:
            return inflow - outflow == 0
        else:
            return outflow - inflow == 0

    model.balance = pyo.Constraint(range(n), rule=flow_balance_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[source, j] for j in range(n) if j != source),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}