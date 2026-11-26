import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(7))
    arcs = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    ]

    source = 0
    sink = 6

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arcs, within=pyo.NonNegativeReals)

    def cap_rule(m, i, j):
        return params[f"capacity_{i}_{j}"]
    model.cap = pyo.Param(model.arcs, initialize=cap_rule, mutable=False)

    def flow_bound(m, i, j):
        return m.flow[i, j] <= m.cap[i, j]
    model.cap_con = pyo.Constraint(model.arcs, rule=flow_bound)

    def balance_rule(m, k):
        if k == source:
            return pyo.Constraint.Skip
        if k == sink:
            return pyo.Constraint.Skip
        inflow = sum(m.flow[i, j] for (i, j) in arcs if j == k)
        outflow = sum(m.flow[i, j] for (i, j) in arcs if i == k)
        return inflow - outflow == 0
    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    total_out = sum(model.flow[source, j] for (i, j) in arcs if i == source)
    total_in = sum(model.flow[i, sink] for (i, j) in arcs if j == sink)
    model.balance_source = pyo.Constraint(expr=total_out - total_in == 0)

    model.obj = pyo.Objective(expr=total_out, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}