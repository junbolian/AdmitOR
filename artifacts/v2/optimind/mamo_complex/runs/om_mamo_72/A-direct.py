import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5, 6]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    def arc_cost(i, j):
        return params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(0, len(cities) - 1))

    model.obj = pyo.Objective(
        expr=sum(arc_cost(i, j) * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j) == 1

    model.out_con = pyo.Constraint(cities, rule=out_rule)
    model.in_con = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ); fix root city's u to 0.
    subtour_arcs = [(i, j) for (i, j) in arcs if i != 1 and j != 1]

    def mtz_rule(mdl, i, j):
        return mdl.u[i] - mdl.u[j] + (len(cities) - 1) * mdl.x[i, j] <= len(cities) - 2

    model.mtz_con = pyo.Constraint(subtour_arcs, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}