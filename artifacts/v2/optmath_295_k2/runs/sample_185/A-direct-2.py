import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_cities"])
    cities = list(range(n))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    def dist(i, j):
        return params["distance_%d_%d" % (i, j)]

    lb = params["position_lower_bound"]
    ub = params["position_upper_bound"]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, bounds=(lb, ub))

    model.obj = pyo.Objective(
        expr=sum(dist(i, j) * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    model.out_deg = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1,
    )
    model.in_deg = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1,
    )

    # MTZ subtour elimination
    mtz_pairs = [(i, j) for (i, j) in arcs if i != 0 and j != 0]
    model.mtz = pyo.Constraint(
        mtz_pairs,
        rule=lambda m, i, j: m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}