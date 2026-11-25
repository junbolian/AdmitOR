import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    weights = params["resource_weights"]
    cap = params["center_capacity"]
    n_res = len(weights)
    n_cen = n_res  # at most one center per resource

    resources = list(range(n_res))
    centers = list(range(n_cen))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(resources, centers, domain=pyo.Binary)
    model.y = pyo.Var(centers, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    model.assign = pyo.ConstraintList()
    for i in resources:
        model.assign.add(sum(model.x[i, j] for j in centers) == 1)

    model.link = pyo.ConstraintList()
    for i in resources:
        for j in centers:
            model.link.add(model.x[i, j] <= model.y[j])

    model.capacity = pyo.ConstraintList()
    for j in centers:
        model.capacity.add(sum(weights[i] * model.x[i, j] for i in resources) <= cap * model.y[j])

    model.obj = pyo.Objective(expr=sum(model.y[j] for j in centers), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}