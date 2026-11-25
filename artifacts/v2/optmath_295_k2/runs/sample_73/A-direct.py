import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    value = params["value"]
    weight = params["weight"]

    n = len(value)
    items = list(range(n))

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(value[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.capacity_con = pyo.Constraint(
        expr=sum(weight[i] * model.x[i] for i in items) <= capacity
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}