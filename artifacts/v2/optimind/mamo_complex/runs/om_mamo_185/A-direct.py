import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    n = 8
    source = 0
    dest = 7

    arcs = [(i, j) for i in range(n) for j in range(n)
            if i != j and capacity[i][j] > 0]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    # flow variable on each arc
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    # capacity constraints
    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= capacity[i][j]
    model.cap_rule = pyo.Constraint(model.arcs, rule=cap_rule)

    # flow conservation at intermediate nodes (net outflow = 0)
    internals = [k for k in range(n) if k != source and k != dest]

    def cons_rule(mdl, k):
        out_flow = sum(mdl.flow[k, j] for j in range(n) if (k, j) in arcs)
        in_flow = sum(mdl.flow[i, k] for i in range(n) if (i, k) in arcs)
        return out_flow - in_flow == 0
    model.cons_rule = pyo.Constraint(internals, rule=cons_rule)

    # objective: maximize net outflow from source
    model.net_out = pyo.Expression(
        expr=sum(model.flow[source, j] for j in range(n) if (source, j) in arcs)
        - sum(model.flow[i, source] for i in range(n) if (i, source) in arcs)
    )
    model.obj = pyo.Objective(expr=model.net_out, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}