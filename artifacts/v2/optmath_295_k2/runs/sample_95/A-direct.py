import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    items = range(9)
    value = {i: params[f"value_{i}"] for i in items}
    weight = {i: params[f"weight_{i}"] for i in items}
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(items, domain=pyo.Binary)
    model.obj = pyo.Objective(
        expr=sum(value[i] * model.x[i] for i in items), sense=pyo.maximize
    )
    model.cap = pyo.Constraint(
        expr=sum(weight[i] * model.x[i] for i in items) <= capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}