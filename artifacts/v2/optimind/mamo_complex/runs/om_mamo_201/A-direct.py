import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = ['A', 'B', 'C', 'D', 'E']
    
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params["cost_%s_%s" % (i, j)]
    
    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j], dimen=2)
    
    model.x = pyo.Var(model.arcs, within=pyo.Binary)
    
    def obj_rule(m):
        return sum(cost[i, j] * m.x[i, j] for (i, j) in m.arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_degree = pyo.Constraint(model.cities, rule=out_rule)
    
    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_degree = pyo.Constraint(model.cities, rule=in_rule)
    
    # Subtour elimination via MTZ
    model.order = pyo.Var(model.cities, bounds=(1, len(cities)))
    model.order['A'].fix(1)
    
    def mtz_rule(m, i, j):
        if i == 'A' or j == 'A':
            return pyo.Constraint.Skip
        return m.order[i] - m.order[j] + len(cities) * m.x[i, j] <= len(cities) - 1
    model.mtz = pyo.Constraint(model.arcs, rule=mtz_rule)
    
    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}