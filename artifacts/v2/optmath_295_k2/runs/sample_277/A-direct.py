import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 6
    cities = list(range(N))

    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[(i, j)] = params["dist_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    # Binary arc selection variables
    model.x = pyo.Var(
        [(i, j) for i in cities for j in cities if i != j],
        domain=pyo.Binary,
    )

    # Position variables: u[i] in 1..N for i != 0, u[0] fixed at 1
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(1, N))
    model.u[0].fix(1)

    # Objective: minimize total distance
    model.obj = pyo.Objective(
        expr=sum(dist[(i, j)] * model.x[(i, j)]
                 for i in cities for j in cities if i != j),
        sense=pyo.minimize,
    )

    # Each city has exactly one outgoing arc
    model.out_flow = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1,
    )

    # Each city has exactly one incoming arc
    model.in_flow = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1,
    )

    # Subtour elimination (MTZ): u[j] >= u[i] + 1 - N*(1 - x[i,j]) for i,j in V \ {0}
    def mtz_rule(m, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return m.u[j] >= m.u[i] + 1 - N * (1 - m.x[(i, j)])

    model.mtz = pyo.Constraint(
        [(i, j) for i in cities for j in cities if i != j],
        rule=mtz_rule,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}