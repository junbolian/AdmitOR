import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    pairs = [
        ('E', 'F', 'cost_E_to_F'),
        ('E', 'G', 'cost_E_to_G'),
        ('E', 'H', 'cost_E_to_H'),
        ('E', 'I', 'cost_E_to_I'),
        ('F', 'G', 'cost_F_to_G'),
        ('F', 'H', 'cost_F_to_H'),
        ('F', 'I', 'cost_F_to_I'),
        ('G', 'H', 'cost_G_to_H'),
        ('G', 'I', 'cost_G_to_I'),
        ('H', 'I', 'cost_H_to_I'),
    ]

    cost = {}
    for a, b, key in pairs:
        val = params[key]
        cost[(a, b)] = val
        cost[(b, a)] = val

    arcs = [(a, b) for a in cities for b in cities if a != b]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(a, b)] * m.x[a, b] for (a, b) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_cons = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ)
    model.order = pyo.Var(cities, bounds=(0, len(cities) - 1))
    non_root = cities[1:]
    root = cities[0]

    def mtz_rule(m, i, j):
        if i == root or j == root:
            return pyo.Constraint.Skip
        return m.order[i] - m.order[j] + len(cities) * m.x[i, j] <= len(cities) - 1
    model.mtz = pyo.Constraint(non_root, non_root, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}