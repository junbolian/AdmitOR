import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    def travel_cost(i, j):
        return params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    def obj_rule(m):
        return sum(travel_cost(i, j) * m.x[i, j] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each city entered exactly once
    model.in_deg = pyo.Constraint(
        cities, rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1
    )

    # Each city left exactly once
    model.out_deg = pyo.Constraint(
        cities, rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1
    )

    # Subtour elimination (MTZ) for the 4 nodes
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(0, 4))

    def mtz_rule(m, i, j):
        if i != j and i != 1 and j != 1:
            return m.u[i] - m.u[j] + 4 * m.x[i, j] <= 3
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(arcs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}