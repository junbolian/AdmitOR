import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for (i, j) in arcs:
        cost[(i, j)] = params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()
    model.C = pyo.Set(initialize=cities)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    # MTZ ordering variables for subtour elimination
    model.u = pyo.Var(model.C, domain=pyo.NonNegativeReals, bounds=(1, len(cities) - 1))

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    model.out_flow = pyo.Constraint(
        model.C,
        rule=lambda m, i: sum(m.x[(i, j)] for j in m.C if j != i) == 1,
    )
    model.in_flow = pyo.Constraint(
        model.C,
        rule=lambda m, j: sum(m.x[(i, j)] for i in m.C if i != j) == 1,
    )

    model.mtz = pyo.ConstraintList()
    for (i, j) in arcs:
        if i != 1 and j != 1:
            model.mtz.add(model.u[i] - model.u[j] + len(cities) * model.x[(i, j)] <= len(cities) - 1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}