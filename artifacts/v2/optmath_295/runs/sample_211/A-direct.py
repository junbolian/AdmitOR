import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 5
    cities = list(range(N))

    cost_map = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost_map[(i, j)] = params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j], dimen=2)
    model.city_set = pyo.Set(initialize=cities)
    model.cities = pyo.Set(initialize=cities)
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.NonNegativeReals, bounds=(0, N - 1))

    model.obj_expr = pyo.Objective(
        expr=sum(cost_map[(i, j)] * model.x[(i, j)] for (i, j) in model.arcs),
        sense=pyo.minimize,
    )

    def depart_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    def arrive_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.depart_con = pyo.Constraint(model.cities, rule=depart_rule)
    model.arrive_con = pyo.Constraint(model.cities, rule=arrive_rule)

    def subtour_rule(m, i, j):
        if i != j and i != 0 and j != 0:
            return m.u[i] - m.u[j] + N * m.x[(i, j)] <= N - 1
        return pyo.Constraint.Skip

    model.subtour_con = pyo.Constraint(model.arcs, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj_expr))
    return {"objective": obj_val, "status": "optimal"}