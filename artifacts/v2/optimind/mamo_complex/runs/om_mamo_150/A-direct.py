import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    pairs = [(i, j) for i in cities for j in cities if i != j]

    def cost_of(i, j):
        return params["cost_" + i + "_" + j]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.NonNegativeReals, bounds=(0, len(cities) - 1))

    model.obj = pyo.Objective(
        expr=sum(cost_of(i, j) * model.x[i, j] for (i, j) in pairs),
        sense=pyo.minimize,
    )

    model.in_degree = pyo.Constraint(
        model.cities,
        rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1,
    )
    model.out_degree = pyo.Constraint(
        model.cities,
        rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1,
    )

    def subtour(m, i, j):
        return m.u[i] - m.u[j] + (len(cities) - 1) * m.x[i, j] <= len(cities) - 2

    model.subtour = pyo.Constraint(
        [(i, j) for (i, j) in pairs if j != cities[0]],
        rule=subtour,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}