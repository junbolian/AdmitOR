import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = int(params["num_cities"])
    cities = list(range(n))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = float(params["cost_%d_%d" % (i, j)])

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, bounds=(float(params["position_lower"]),
                                      float(params["position_upper"])))

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[(i, j)] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.out_deg = pyo.Constraint(
        cities, rule=lambda mdl, i: sum(mdl.x[(i, j)] for j in cities if j != i) == 1
    )
    model.in_deg = pyo.Constraint(
        cities, rule=lambda mdl, j: sum(mdl.x[(i, j)] for i in cities if i != j) == 1
    )

    inner = [(i, j) for i in cities for j in cities if i != j and i != 0 and j != 0]

    def mt_rule(mdl, i, j):
        return mdl.u[i] - mdl.u[j] + n * mdl.x[(i, j)] <= n - 1

    model.mtz = pyo.Constraint(inner, rule=mt_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}