import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 5
    cities = list(range(N))
    non_zero = list(range(1, N))

    model = pyo.ConcreteModel()

    model.x = pyo.Var([(i, j) for i in cities for j in cities if i != j], domain=pyo.Binary)
    model.u = pyo.Var(non_zero, domain=pyo.NonNegativeReals, bounds=(1, N - 1))

    def cost_expr(m):
        return sum(params["cost_%d_%d" % (i, j)] * m.x[i, j]
                   for i in cities for j in cities if i != j)
    model.obj = pyo.Objective(rule=cost_expr, sense=pyo.minimize)

    def depart_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.depart = pyo.Constraint(cities, rule=depart_rule)

    def arrive_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.arrive = pyo.Constraint(cities, rule=arrive_rule)

    def subtour_rule(m, i, j):
        if i != j and i in non_zero and j in non_zero:
            return m.u[j] >= m.u[i] + 1 - N * (1 - m.x[i, j])
        return pyo.Constraint.Skip
    model.subtour = pyo.Constraint(
        [(i, j) for i in cities for j in cities if i != j], rule=subtour_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}