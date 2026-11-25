import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_cities"])

    cost = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                cost[i, j] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.CITIES = pyo.RangeSet(0, n - 1)
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)
    model.u = pyo.Var(
        model.CITIES,
        domain=pyo.Integers,
        bounds=(0, params["position_upper_bound"]),
    )
    model.u[0].fix(params["city0_position_fixed"])

    def obj_rule(m):
        return sum(cost[i, j] * m.x[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[i, j] for j in range(n) if j != i) == 1

    model.out_deg = pyo.Constraint(model.CITIES, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[i, j] for i in range(n) if i != j) == 1

    model.in_deg = pyo.Constraint(model.CITIES, rule=in_rule)

    def mt_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1

    model.subtour = pyo.Constraint(model.ARCS, rule=mt_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}