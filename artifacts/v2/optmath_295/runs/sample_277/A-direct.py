import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["n_cities"])
    cities = list(range(n))

    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[(i, j)] = params["dist_%d_%d" % (i, j)]

    pos_min = params["position_min"]
    pos_max = params["position_max"]

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(
        initialize=[(i, j) for i in cities for j in cities if i != j],
        dimen=2,
    )

    model.x = pyo.Var(model.arcs, within=pyo.Binary)
    model.u = pyo.Var(model.cities, bounds=(pos_min, pos_max))

    def obj_rule(m):
        return sum(dist[(i, j)] * m.x[(i, j)] for (i, j) in m.arcs)

    model.total_distance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in m.cities if j != i) == 1

    model.out_flow = pyo.Constraint(model.cities, rule=out_rule)

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in m.cities if i != j) == 1

    model.in_flow = pyo.Constraint(model.cities, rule=in_rule)

    model.u[0].fix(pos_min)

    def subtour_rule(m, i, j):
        if i != 0 and j != 0:
            return m.u[j] - m.u[i] >= 1 - n * (1 - m.x[(i, j)])
        return pyo.Constraint.Skip

    model.subtour = pyo.Constraint(model.arcs, rule=subtour_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_distance))
    return {"objective": obj_val, "status": "optimal"}