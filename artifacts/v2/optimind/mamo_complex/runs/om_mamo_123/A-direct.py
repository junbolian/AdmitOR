import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]
    cost_data = {(i, j): params["cost_%d_%d" % (i, j)] for (i, j) in arcs}

    model = pyo.ConcreteModel()
    model.city_set = pyo.Set(initialize=cities)
    model.arc_set = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arc_set, within=pyo.Binary)

    model.cost = pyo.Param(model.arc_set, initialize=cost_data, mutable=False)

    def obj_rule(m):
        return sum(m.cost[i, j] * m.x[i, j] for (i, j) in m.arc_set)
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in m.city_set if j != i) == 1
    model.out_degree = pyo.Constraint(model.city_set, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in m.city_set if i != j) == 1
    model.in_degree = pyo.Constraint(model.city_set, rule=in_rule)

    model.u = pyo.Var(model.city_set, bounds=(0, len(cities) - 1))

    def subtour_rule(m, i, j):
        if i != j:
            return m.u[i] - m.u[j] + len(cities) * m.x[i, j] <= len(cities) - 1
        return pyo.Constraint.Skip
    model.subtour = pyo.Constraint(model.arc_set, rule=subtour_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}