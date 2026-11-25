import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(6))
    edges = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(edges, domain=pyo.Binary)
    model.u = pyo.Var(
        cities,
        bounds=(params["position_bound_lower"], params["position_bound_upper"]),
    )

    cost_map = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost_map[(i, j)] = params[f"cost_{i}_{j}"]

    model.obj = pyo.Objective(
        expr=sum(cost_map[e] * model.x[e] for e in edges),
        sense=pyo.minimize,
    )

    # Flow conservation: one outgoing and one incoming edge per city
    model.out_flow = pyo.Constraint(
        cities, rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1
    )
    model.in_flow = pyo.Constraint(
        cities, rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1
    )

    # Fix position of city 0
    model.city0_pos = pyo.Constraint(expr=model.u[0] == params["city0_position"])

    # Subtour elimination (MTZ)
    model.mtz = pyo.Constraint(
        [(i, j) for (i, j) in edges if i != 0 and j != 0],
        rule=lambda m, i, j: m.u[i] - m.u[j] + 6 * m.x[(i, j)] <= 5,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}