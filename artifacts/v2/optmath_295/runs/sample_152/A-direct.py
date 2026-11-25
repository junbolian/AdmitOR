import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n_cities"])
    cities = list(range(n))

    # Cost dictionary from params (no hardcoded numeric values)
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=cities, ordered=True)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.C, domain=pyo.NonNegativeReals,
                      bounds=(0, params["position_upper_bound"]))

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[i, j] for (i, j) in arcs)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city departed from exactly once
    def depart_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.depart = pyo.Constraint(model.C, rule=depart_rule)

    # Each city arrived at exactly once
    def arrive_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.arrive = pyo.Constraint(model.C, rule=arrive_rule)

    # MTZ subtour elimination (position 0 fixed at city 0)
    model.u[0].setlb(0)
    model.u[0].setub(0)

    def mtz_rule(m, i, j):
        if i == 0 or j == 0 or i == j:
            return pyo.Constraint.Skip
        return m.u[j] - m.u[i] >= 1 - n * (1 - m.x[i, j])
    model.mtz = pyo.Constraint(model.A, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}