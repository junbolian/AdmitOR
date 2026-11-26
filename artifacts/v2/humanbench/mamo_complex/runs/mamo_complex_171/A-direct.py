import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 8
    source = 0
    sink = 7

    def cap_key(i, j):
        return "capacity_%d_%d" % (i, j)

    # Build arc list only from capacity keys actually present in params
    arcs = []
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            key = cap_key(i, j)
            if key in params:
                arcs.append((i, j))

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    cap_dict = {}
    for (i, j) in arcs:
        cap_dict[(i, j)] = params[cap_key(i, j)]

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap_dict[(i, j)]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    model.F = pyo.Var(domain=pyo.NonNegativeReals)

    # Precompute in/out arc lists per node present in the arc set
    out_arcs = {k: [] for k in range(N)}
    in_arcs = {k: [] for k in range(N)}
    for (i, j) in arcs:
        out_arcs[i].append((i, j))
        in_arcs[j].append((i, j))

    def node_rule(mdl, k):
        out_expr = sum(mdl.flow[i, j] for (i, j) in out_arcs[k])
        in_expr = sum(mdl.flow[i, j] for (i, j) in in_arcs[k])
        if k == source:
            return out_expr - in_expr == mdl.F
        elif k == sink:
            return in_expr - out_expr == mdl.F
        else:
            return out_expr - in_expr == 0
    model.node_con = pyo.Constraint(range(N), rule=node_rule)

    model.obj = pyo.Objective(expr=model.F, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}