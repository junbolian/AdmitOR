import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    raw = params["capacity_matrix"]
    # Normalize to a 2D list of floats regardless of nesting/flattening
    if isinstance(raw[0], (list, tuple)):
        cap = [[float(raw[i][j]) for j in range(len(raw[i]))] for i in range(len(raw))]
    else:
        n_flat = int(round(len(raw) ** 0.5))
        cap = [[float(raw[i * n_flat + j]) for j in range(n_flat)] for i in range(n_flat)]
    n = len(cap)

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, n - 1)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in range(n) for j in range(n)
                    if i != j and cap[i][j] > 0],
        dimen=2
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def arc_ub(mdl, i, j):
        return mdl.flow[i, j] <= cap[i][j]

    model.cap_rule = pyo.Constraint(model.arcs, rule=arc_ub)

    def cons_rule(mdl, k):
        if k == 0:
            outflow = sum(mdl.flow[0, j] for (i, j) in mdl.arcs if i == 0)
            inflow = sum(mdl.flow[i, 0] for (i, j) in mdl.arcs if j == 0)
            return outflow - inflow >= 0
        elif k == n - 1:
            inflow = sum(mdl.flow[i, k] for (i, j) in mdl.arcs if j == k)
            outflow = sum(mdl.flow[k, j] for (i, j) in mdl.arcs if i == k)
            return inflow - outflow >= 0
        else:
            inflow = sum(mdl.flow[i, k] for (i, j) in mdl.arcs if j == k)
            outflow = sum(mdl.flow[k, j] for (i, j) in mdl.arcs if i == k)
            return inflow == outflow

    model.balance = pyo.Constraint(model.nodes, rule=cons_rule)

    model.total_flow = pyo.Expression(
        expr=sum(model.flow[i, n - 1] for (i, j) in model.arcs if j == n - 1)
    )

    model.obj = pyo.Objective(expr=model.total_flow, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}