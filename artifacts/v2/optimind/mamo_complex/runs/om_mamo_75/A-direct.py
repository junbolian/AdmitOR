import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    hubs = list(range(8))
    source = 0
    sink = 7

    # Build the set of existing arcs (capacity > 0)
    arcs = []
    for i in hubs:
        for j in hubs:
            if i == j:
                continue
            key = f"capacity_{i}_{j}"
            if key in params and params[key] > 0:
                arcs.append((i, j))

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.HUBS = pyo.Set(initialize=hubs)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def arc_cap(model, i, j):
        return params[f"capacity_{i}_{j}"]

    model.cap = pyo.Param(model.ARCS, initialize=arc_cap, mutable=False)

    model.flow_con = pyo.Constraint(
        model.ARCS, rule=lambda model, i, j: model.flow[i, j] <= model.cap[i, j]
    )

    def flow_balance_rule(model, k):
        outflow = sum(model.flow[i, j] for (i, j) in model.ARCS if i == k)
        inflow = sum(model.flow[i, j] for (i, j) in model.ARCS if j == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(model.HUBS, rule=flow_balance_rule)

    model.obj = pyo.Objective(
        expr=sum(model.flow[i, j] for (i, j) in model.ARCS if i == source)
        - sum(model.flow[i, j] for (i, j) in model.ARCS if j == source),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}