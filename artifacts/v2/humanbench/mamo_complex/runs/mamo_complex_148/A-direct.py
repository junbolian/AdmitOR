import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = int(params["num_cities"])
    cities = list(range(1, num_cities + 1))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()
    model.CITY = pyo.Set(initialize=cities)
    model.ARC = pyo.Set(initialize=list(cost.keys()), dimen=2)

    model.x = pyo.Var(model.ARC, domain=pyo.Binary)
    model.u = pyo.Var(model.CITY, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in m.ARC)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in m.CITY if i != j) == 1
    model.out_deg = pyo.Constraint(model.CITY, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in m.CITY if i != j) == 1
    model.in_deg = pyo.Constraint(model.CITY, rule=in_rule)

    # MTZ subtour elimination
    def mtz_rule(m, i, j):
        if i != j and i >= 2 and j >= 2:
            return m.u[i] - m.u[j] + num_cities * m.x[(i, j)] <= num_cities - 1
        return pyo.Constraint.Skip
    model.mtz = pyo.Constraint(model.CITY, model.CITY, rule=mtz_rule)

    def lb_rule(m, i):
        if i >= 2:
            return m.u[i] >= 1
        return pyo.Constraint.Skip
    model.u_lb = pyo.Constraint(model.CITY, rule=lb_rule)

    def ub_rule(m, i):
        if i >= 2:
            return m.u[i] <= num_cities - 1
        return pyo.Constraint.Skip
    model.u_ub = pyo.Constraint(model.CITY, rule=ub_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}