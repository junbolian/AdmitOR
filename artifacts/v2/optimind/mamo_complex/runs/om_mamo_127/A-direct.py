import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = range(7)
    source = 0
    sink = 6
    
    arcs = []
    for i in nodes:
        for j in nodes:
            if i != j and f"capacity_{i}_{j}" in params:
                arcs.append((i, j))
    
    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)
    
    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= params[f"capacity_{i}_{j}"]
    model.cap = pyo.Constraint(model.ARCS, rule=cap_rule)
    
    def flow_rule(mdl, k):
        if k == source:
            return pyo.Constraint.Skip
        if k == sink:
            return pyo.Constraint.Skip
        inflow = sum(mdl.x[i, k] for (i, j) in arcs if j == k)
        outflow = sum(mdl.x[k, j] for (i, j) in arcs if i == k)
        return inflow == outflow
    model.flow = pyo.Constraint(nodes, rule=flow_rule)
    
    def obj_rule(mdl):
        return sum(mdl.x[source, j] for (i, j) in arcs if i == source)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)
    
    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}