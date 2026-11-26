import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = ["Alpha", "Bravo", "Charlie", "Delta"]
    abbrev = {"Alpha": "A", "Bravo": "B", "Charlie": "C", "Delta": "D"}
    
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_" + abbrev[i] + abbrev[j]]
    
    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])
    
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    
    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in m.arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1
    model.out_cons = pyo.Constraint(model.cities, rule=out_rule)
    
    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1
    model.in_cons = pyo.Constraint(model.cities, rule=in_rule)
    
    # Subtour elimination (MTZ)
    model.u = pyo.Var(model.cities, domain=pyo.NonNegativeReals, bounds=(0, len(cities) - 1))
    model.u["Alpha"].fix(0)
    
    non_alpha = [c for c in cities if c != "Alpha"]
    
    def mtz_rule(m, i, j):
        if i != "Alpha" and j != "Alpha" and i != j:
            return m.u[i] - m.u[j] + (len(cities) - 1) * m.x[(i, j)] <= len(cities) - 2
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(model.arcs, rule=mtz_rule)
    
    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}