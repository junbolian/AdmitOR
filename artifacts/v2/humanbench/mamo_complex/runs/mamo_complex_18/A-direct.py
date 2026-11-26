import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 9
    caps_flat = params["capacities"]

    # Build capacity lookup over ordered pairs i != j (row-major)
    cap = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i != j:
                cap[(i, j)] = caps_flat[idx]
                idx += 1

    arc_list = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arc_list, dimen=2)

    def cap_rule(mdl, i, j):
        return float(cap[(i, j)])

    model.capacity = pyo.Param(model.arcs, initialize=cap_rule, mutable=False)

    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def flow_bound_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.capacity[i, j]
    model.flow_bound = pyo.Constraint(model.arcs, rule=flow_bound_rule)

    source = 0
    sink = 8
    nodes = range(n)

    def balance_rule(mdl, k):
        inflow = sum(mdl.flow[i, k] for i in nodes if i != k)
        outflow = sum(mdl.flow[k, j] for j in nodes if j != k)
        if k == source:
            return outflow - inflow == mdl.net_out
        elif k == sink:
            return inflow - outflow == mdl.net_out
        else:
            return inflow - outflow == 0

    model.net_out = pyo.Var(within=pyo.NonNegativeReals)
    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    model.obj = pyo.Objective(expr=model.net_out, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}