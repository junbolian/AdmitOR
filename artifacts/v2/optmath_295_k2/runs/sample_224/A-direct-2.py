import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 6
    cities = list(range(N))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(
        [(i, j) for i in cities for j in cities if i != j], domain=pyo.Binary
    )
    model.pos = pyo.Var(
        cities, bounds=(params["pos_lower_bound"], params["pos_upper_bound"])
    )

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model.obj = pyo.Objective(
        expr=sum(
            cost[(i, j)] * model.x[(i, j)]
            for i in cities
            for j in cities
            if i != j
        ),
        sense=pyo.minimize,
    )

    def out_rule(mdl, i):
        return sum(mdl.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[(i, j)] for i in cities if i != j) == 1

    model.out_con = pyo.Constraint(cities, rule=out_rule)
    model.in_con = pyo.Constraint(cities, rule=in_rule)

    model.pos_fix_0 = pyo.Constraint(expr=model.pos[0] == params["pos_0_fixed"])

    # MTZ subtour elimination: pos_i - pos_j + n*x_ij <= n - 1 for i,j != 0, i != j
    n = N

    def subtour_rule(mdl, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return mdl.pos[i] - mdl.pos[j] + n * mdl.x[(i, j)] <= n - 1

    model.subtour_con = pyo.Constraint(
        [(i, j) for i in cities for j in cities if i != j], rule=subtour_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}