import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    item_values = params["item_values"]
    item_weights = params["item_weights"]

    n = len(item_values)
    items = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(items, domain=pyo.Binary)

    model.revenue = pyo.Objective(
        expr=sum(item_values[i] * model.x[i] for i in items),
        sense=pyo.maximize,
    )

    model.weight_capacity = pyo.Constraint(
        expr=sum(item_weights[i] * model.x[i] for i in items) <= capacity
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.revenue))
    return {"objective": obj_val, "status": "optimal"}