import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(9))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]
    cap = {}
    for (i, j) in arcs:
        key = f"capacity_{i}_{j}"
        if key in params:
            cap[(i, j)] = params[key]
        else:
            cap[(i, j)] = 0

    source, sink = 0, 8

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap[(i, j)]
    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def cons_rule(mdl, n):
        if n == sink:
            return pyo.Constraint.Skip
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        if n == source:
            return outflow - inflow >= 0
        else:
            return outflow - inflow == 0
    model.cons = pyo.Constraint(nodes, rule=cons_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[i, j] for (i, j) in arcs if j == sink) - \
               sum(mdl.flow[i, j] for (i, j) in arcs if i == sink)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}