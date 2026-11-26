import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 8
    source = 0
    sink = 7

    arcs = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            key = f"cap_{i}_{j}"
            if key in params:
                val = params[key]
                if val is not None and float(val) > 0:
                    arcs.append((i, j))

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    def _cap_init(mdl, i, j):
        return float(params[f"cap_{i}_{j}"])

    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)
    model.cap = pyo.Param(model.ARCS, initialize=_cap_init)

    def _cap_rule(mdl, i, j):
        return mdl.x[i, j] <= mdl.cap[i, j]

    model.cap_constraint = pyo.Constraint(model.ARCS, rule=_cap_rule)

    model.flow = pyo.Var(domain=pyo.NonNegativeReals)

    out_arcs = {i: [(a, b) for (a, b) in arcs if a == i] for i in range(n)}
    in_arcs = {i: [(a, b) for (a, b) in arcs if b == i] for i in range(n)}

    def _flow_balance_rule(mdl, k):
        outflow = sum((mdl.x[a, b] for (a, b) in out_arcs[k]), 0.0)
        inflow = sum((mdl.x[a, b] for (a, b) in in_arcs[k]), 0.0)
        if k == source:
            return outflow - inflow == mdl.flow
        elif k == sink:
            return inflow - outflow == mdl.flow
        else:
            return outflow - inflow == 0

    model.NODES = pyo.Set(initialize=list(range(n)))
    model.flow_balance = pyo.Constraint(model.NODES, rule=_flow_balance_rule)

    model.obj = pyo.Objective(expr=model.flow, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}