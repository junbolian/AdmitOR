import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = list(range(7))

    model = pyo.ConcreteModel()

    model.x = pyo.Var([(i, j) for i in cities for j in cities if i != j], domain=pyo.Binary)
    model.u = pyo.Var(cities, bounds=(params["position_min"], params["position_max"]))

    def obj_rule(mdl):
        return sum(
            params["distance_%d_%d" % (i, j)] * mdl.x[i, j]
            for (i, j) in mdl.x
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i) == 1
    model.out_con = pyo.Constraint(cities, rule=out_rule)

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j) == 1
    model.in_con = pyo.Constraint(cities, rule=in_rule)

    def position_rule(mdl, i, j):
        if i != j and i != 0 and j != 0:
            return mdl.u[i] - mdl.u[j] + 7 * mdl.x[i, j] <= 6
        return pyo.Constraint.Skip
    model.position_con = pyo.Constraint(
        [(i, j) for i in cities for j in cities if i != j], rule=position_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}