import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(7))
    n = len(cities)

    model = pyo.ConcreteModel()

    # Cost dictionary
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    # Binary arc variables
    model.x = pyo.Var([(i, j) for i in cities for j in cities if i != j],
                      domain=pyo.Binary)

    # Position variables (order in tour), City 0 fixed at 0
    model.u = pyo.Var(cities, bounds=(0, n - 1), domain=pyo.NonNegativeReals)
    model.u[0].fix(0)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)]
                 for i in cities for j in cities if i != j),
        sense=pyo.minimize,
    )

    # Each city: exactly one outgoing arc
    model.out_cons = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1,
    )

    # Each city: exactly one incoming arc
    model.in_cons = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1,
    )

    # MTZ subtour elimination for cities 1..n-1
    nonstart = [i for i in cities if i != 0]

    def mtz_rule(m, i, j):
        if i != j and i != 0 and j != 0:
            return m.u[i] - m.u[j] + n * m.x[(i, j)] <= n - 1
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(nonstart, nonstart, rule=mtz_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}