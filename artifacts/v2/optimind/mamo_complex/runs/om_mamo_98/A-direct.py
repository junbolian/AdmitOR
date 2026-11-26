import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4, 5, 6]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(params["c_%d%d" % (i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Each city has exactly one outgoing arc
    model.out_cons = pyo.Constraint(
        cities, rule=lambda mm, i: sum(mm.x[(i, j)] for j in cities if j != i) == 1
    )
    # Each city has exactly one incoming arc
    model.in_cons = pyo.Constraint(
        cities, rule=lambda mm, j: sum(mm.x[(i, j)] for i in cities if i != j) == 1
    )

    # Subtour elimination (MTZ formulation)
    model.u = pyo.Var(cities, bounds=(1, len(cities) - 1))
    model.mtz = pyo.Constraint(
        [(i, j) for (i, j) in arcs if i != 1 and j != 1],
        rule=lambda mm, i, j: mm.u[i] - mm.u[j] + len(cities) * mm.x[(i, j)] <= len(cities) - 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}