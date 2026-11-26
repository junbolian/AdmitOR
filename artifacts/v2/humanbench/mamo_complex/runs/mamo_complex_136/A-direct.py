import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.cities = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.arcs, within=pyo.Binary)

    # Objective: minimize total travel cost
    model.total_cost = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Each city entered exactly once
    model.in_flow = pyo.Constraint(
        model.cities,
        rule=lambda model, j: sum(model.x[(i, j)] for i in cities if i != j) == 1,
    )

    # Each city left exactly once
    model.out_flow = pyo.Constraint(
        model.cities,
        rule=lambda model, i: sum(model.x[(i, j)] for j in cities if j != i) == 1,
    )

    # Subtour elimination (Miller-Tucker-Zemlin)
    model.u = pyo.Var(model.cities, within=pyo.NonNegativeReals, bounds=(1, 5))

    def mtz_rule(model, i, j):
        if i != j and i != 1 and j != 1:
            return model.u[i] - model.u[j] + 5 * model.x[(i, j)] <= 4
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(model.arcs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}