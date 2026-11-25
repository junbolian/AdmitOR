import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [0, 1, 2, 3, 4]
    arcs = [(a, b) for a in cities for b in cities if a != b]

    cost = {}
    for a, b in arcs:
        cost[(a, b)] = params["cost_%d_%d" % (a, b)]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.cities = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.Reals)

    def obj_rule(m):
        return sum(cost[(a, b)] * m.x[(a, b)] for (a, b) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def depart_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    model.depart = pyo.Constraint(model.cities, rule=depart_rule)

    def arrive_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.arrive = pyo.Constraint(model.cities, rule=arrive_rule)

    def subtour_rule(m, i, j):
        if i != j and i != 0 and j != 0:
            return m.u[i] - m.u[j] + 5 * m.x[(i, j)] <= 4
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(model.cities, model.cities, rule=subtour_rule)

    lo = params["u_lower"]
    hi = params["u_upper"]

    def ub_rule(m, i):
        if i == 0:
            return pyo.Constraint.Skip
        return pyo.inequality(lo, m.u[i], hi)

    model.ub = pyo.Constraint(model.cities, rule=ub_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}