import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    N = 4
    cities = list(range(N))
    pairs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(pairs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.Reals)

    def cost_rule(m, i, j):
        return params[f"travel_cost_{i}_{j}"]
    model.obj = pyo.Objective(
        expr=sum(model.x[i, j] * cost_rule(model, i, j) for (i, j) in pairs),
        sense=pyo.minimize
    )

    # Each city departed from exactly once
    def out_rule(m, i):
        return sum(m.x[i, j] for j in cities if j != i) == 1
    model.out_cons = pyo.Constraint(cities, rule=out_rule)

    # Each city entered exactly once
    def in_rule(m, j):
        return sum(m.x[i, j] for i in cities if i != j) == 1
    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ)
    def mtz_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[j] >= m.u[i] + 1 - N * (1 - m.x[i, j])
    model.mtz = pyo.Constraint(pairs, rule=mtz_rule)

    # Fix depot position
    model.depot_fix = pyo.Constraint(expr=model.u[0] == params["u_depot_fixed"])

    # Bounds for non-depot cities
    for c in cities:
        if c == 0:
            continue
        model.u[c].setlb(params["u_bound_lower"])
        model.u[c].setub(params["u_bound_upper"])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}