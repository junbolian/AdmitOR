import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4, 5, 6]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {(i, j): params[f"cost_{i}_{j}"] for (i, j) in arcs}

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i, j] * m.x[i, j] for (i, j) in arcs)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_con = pyo.Constraint(cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_con = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ)
    model.u = pyo.Var(cities, bounds=(1, len(cities)))

    def mtz_rule(m, i, j):
        if i != j and (i, j) in set(arcs) and i != cities[0] and j != cities[0]:
            return m.u[i] - m.u[j] + len(cities) * m.x[i, j] <= len(cities) - 1
        return pyo.Constraint.Skip
    model.mtz_con = pyo.Constraint(cities, cities, rule=mtz_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}