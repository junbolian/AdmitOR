import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    n = 9
    stations = list(range(n))

    model = pyo.ConcreteModel()
    model.stations = pyo.Set(initialize=stations)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in stations for j in stations if i != j],
        dimen=2,
    )

    cap = {}
    for i in stations:
        for j in stations:
            if i != j:
                cap[(i, j)] = float(capacity[i][j])

    source = 0
    sink = 8

    def cap_rule(model, i, j):
        return (0.0, cap[(i, j)])

    model.flow = pyo.Var(model.arcs, bounds=cap_rule)

    def balance_rule(model, k):
        if k == source or k == sink:
            return pyo.Constraint.Skip
        inflow = sum(model.flow[i, k] for i in stations if i != k)
        outflow = sum(model.flow[k, j] for j in stations if j != k)
        return inflow == outflow

    model.balance = pyo.Constraint(model.stations, rule=balance_rule)

    model.obj = pyo.Objective(
        expr=sum(model.flow[source, j] for j in stations if j != source),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}