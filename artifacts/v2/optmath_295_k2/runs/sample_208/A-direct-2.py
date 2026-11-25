import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    resource_weights = params["resource_weights"]
    facility_capacity = params["facility_capacity"]

    num_resources = len(resource_weights)
    num_facilities = 7

    resources = list(range(num_resources))
    facilities = list(range(num_facilities))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(resources, facilities, domain=pyo.Binary)
    model.y = pyo.Var(facilities, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[j] for j in facilities))

    model.capacity = pyo.Constraint(
        facilities,
        rule=lambda m, j: sum(resource_weights[i] * m.x[i, j] for i in resources)
        <= facility_capacity * m.y[j],
    )

    model.assign = pyo.Constraint(
        resources,
        rule=lambda m, i: sum(m.x[i, j] for j in facilities) == 1,
    )

    model.link = pyo.Constraint(
        resources,
        facilities,
        rule=lambda m, i, j: m.x[i, j] <= m.y[j],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}