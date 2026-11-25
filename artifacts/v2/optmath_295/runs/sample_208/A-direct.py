import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["resource_weights"]
    capacity = params["facility_capacity"]

    n_res = len(weights)
    n_fac = 7

    model = pyo.ConcreteModel()

    model.RES = pyo.RangeSet(0, n_res - 1)
    model.FAC = pyo.RangeSet(0, n_fac - 1)

    model.x = pyo.Var(model.RES, model.FAC, domain=pyo.Binary)
    model.y = pyo.Var(model.FAC, domain=pyo.Binary)

    # Minimize number of facilities used
    model.obj = pyo.Objective(
        expr=sum(model.y[j] for j in model.FAC),
        sense=pyo.minimize,
    )

    # Capacity constraints
    def cap_rule(mdl, j):
        return sum(weights[i] * mdl.x[i, j] for i in mdl.RES) <= capacity * mdl.y[j]

    model.cap = pyo.Constraint(model.FAC, rule=cap_rule)

    # Assignment constraints: each resource assigned to exactly one facility
    def assign_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.FAC) == 1

    model.assign = pyo.Constraint(model.RES, rule=assign_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}