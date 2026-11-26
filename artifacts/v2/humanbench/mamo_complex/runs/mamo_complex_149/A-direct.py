import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)
    cities = list(range(n))

    model = pyo.ConcreteModel()

    # Binary arc variables: x[i,j] = 1 if the route goes from city i directly to city j
    model.x = pyo.Var(cities, cities, domain=pyo.Binary)

    # Objective: minimize total travel cost
    model.total_cost = pyo.Objective(
        expr=sum(cost_matrix[i][j] * model.x[i, j]
                 for i in cities for j in cities if i != j),
        sense=pyo.minimize,
    )

    # Each city is departed exactly once
    model.depart = pyo.ConstraintList()
    for i in cities:
        model.depart.add(
            sum(model.x[i, j] for j in cities if j != i) == 1
        )

    # Each city is entered exactly once
    model.arrive = pyo.ConstraintList()
    for j in cities:
        model.arrive.add(
            sum(model.x[i, j] for i in cities if i != j) == 1
        )

    # Subtour elimination (order/MTZ formulation)
    # u[i] is the position of city i in the tour (used for all but a reference city)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(0, n - 1))
    # Fix reference city 0 position to 0 (removes symmetry)
    model.u[0].fix(0)

    model.subtour = pyo.ConstraintList()
    for i in cities:
        for j in cities:
            if i != j and i != 0 and j != 0:
                model.subtour.add(
                    model.u[i] - model.u[j] + (n - 1) * model.x[i, j] <= n - 2
                )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}