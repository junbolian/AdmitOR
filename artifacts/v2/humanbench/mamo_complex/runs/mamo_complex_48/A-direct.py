import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 9
    source = 0
    sink = 8

    capacity = {}

    for j in range(1, n):
        capacity[(0, j)] = params[f"capacity_0_{j}"]

    for i in range(1, n):
        for j in range(1, n):
            if i == j:
                continue
            capacity[(i, j)] = params["capacity_range_high"]

    capacity[(2, 1)] = params["capacity_1_5_high"]
    capacity[(2, 5)] = params["capacity_1_5_high"]

    arcs = list(capacity.keys())

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(model.flow[a] for a in arcs if a[0] == source),
        sense=pyo.maximize,
    )

    def conservation_rule(mdl, v):
        inflow = sum(mdl.flow[(u, v)] for (u, w) in arcs if w == v)
        outflow = sum(mdl.flow[(v, w)] for (u, w) in arcs if u == v)
        return inflow == outflow

    internal = [v for v in range(n) if v != source and v != sink]
    model.cons = pyo.Constraint(internal, rule=conservation_rule)

    model.cap = pyo.Constraint(
        arcs, rule=lambda mdl, i, j: mdl.flow[(i, j)] <= capacity[(i, j)]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}